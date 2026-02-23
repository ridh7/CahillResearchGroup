import queue
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Thread

import clr

from app.config import settings
from app.models.state import global_state
from app.utils.file_utils import save_to_file

clr.AddReference(settings.kinesis_device_manager_dll)
clr.AddReference(settings.kinesis_generic_motor_dll)
clr.AddReference(settings.kinesis_brushless_motor_dll)

from System import Decimal
from Thorlabs.MotionControl.Benchtop.BrushlessMotorCLI import *
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *


class ThorlabsBBD302:
    """
    Thorlabs BBD302 2-channel brushless motor controller driver.

    Controls X-Y motorized stage via Thorlabs .NET SDK (pythonnet).
    Initialization sequence:
    1. Build device list and connect to controller
    2. For each channel: start polling → enable → load config → home
    3. Homing ensures absolute position reference (finds limit switches)

    Delays between steps allow .NET SDK to complete hardware initialization.
    """

    def __init__(self, serial_number=None, channel_count=2):
        try:
            self.channel = {}
            self.motor_config = {}
            self.channel_count = channel_count

            # Build device list from Thorlabs .NET SDK
            DeviceManagerCLI.BuildDeviceList()  # type: ignore[name-defined]
            if serial_number is None:
                # Auto-detect BBD302 by known serial number
                devices = DeviceManagerCLI.GetDeviceList()  # type: ignore[name-defined]
                for dev in devices:
                    if dev == settings.stage_serial:
                        serial_number = dev
            print(f"---Connecting to stage with serial number: {serial_number}")
            self.device = BenchtopBrushlessMotor.CreateBenchtopBrushlessMotor(  # type: ignore[name-defined]
                serial_number
            )
            self.device.Connect(serial_number)
            if self.device.IsConnected:
                print(f"---Connected to: {self.device.GetDeviceInfo().Description}")
            else:
                print("---Device initialization error")

            # Initialize each channel (1=X axis, 2=Y axis)
            for channel_number in range(1, self.channel_count + 1):
                print(f"---Initializing channel {channel_number}")
                self.channel[channel_number] = self.device.GetChannel(channel_number)

                # StartPolling(250ms) enables position updates from hardware
                self.channel[channel_number].StartPolling(250)
                time.sleep(0.25)

                # EnableDevice powers on the motor driver
                self.channel[channel_number].EnableDevice()
                time.sleep(0.25)

                # Load motor configuration (acceleration, velocity limits)
                self.motor_config[channel_number] = self.channel[
                    channel_number
                ].LoadMotorConfiguration(self.channel[channel_number].DeviceID)

                print(f"---Channel {channel_number} initialized")
        except Exception as e:
            print(f"---Stage initialization error: {e}")
            raise

    def stop(self):
        """Immediately stop all channels and wait for deceleration to complete."""
        for ch_num in range(1, self.channel_count + 1):
            try:
                self.channel[ch_num].Stop(0)
            except Exception as e:
                print(f"---Stop error on channel {ch_num}: {e}")
        time.sleep(0.5)  # let stages decelerate before next MoveTo is safe
        print("---All channels stopped")

    def _safe_move_to(
        self, channel, position, timeout, max_retries=10, retry_wait=0.5, aborted=None
    ):
        """
        Call channel.MoveTo, retrying if DeviceMovingException is raised.

        After a Stop(), the stage may still be decelerating. Retrying avoids
        crashing the scan when a new MoveTo is issued before motion fully ceases.

        aborted: optional callable that returns True if the scan should stop
                 (checked before each retry so the old scan exits quickly)
        """
        for attempt in range(max_retries):
            if aborted is not None and aborted():
                return  # scan was superseded or stopped during retries
            try:
                channel.MoveTo(position, timeout)
                return
            except Exception as e:
                if (
                    "DeviceMovingException" in type(e).__name__
                    or "already moving" in str(e).lower()
                ):
                    print(
                        f"---Stage still moving, retrying in {retry_wait}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_wait)
                else:
                    raise
        # Final attempt — propagate if still failing
        if aborted is not None and aborted():
            return
        channel.MoveTo(position, timeout)

    def home_channel(self, channel_number):
        try:
            print(f"---Homing channel {channel_number}")
            self.channel[channel_number].Home(60000)
            time.sleep(1)
        except Exception as e:
            print(f"---Homing error: {e}")

    def home_all(self):
        """Home both channels in parallel."""
        t1 = Thread(target=self.home_channel, args=(1,))
        t2 = Thread(target=self.home_channel, args=(2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    def get_movement_params(self, channel_number):
        try:
            print(f"---Get channel {channel_number} params")
            home_params = self.channel[channel_number].GetHomingParams()
            vel_params = self.channel[channel_number].GetVelocityParams()
            return home_params, vel_params
        except Exception as e:
            print(f"---Error getting movement params: {e}")
            raise

    def move_in_rectangle(
        self,
        x1,
        y1,
        x2,
        y2,
        x_steps,
        y_steps,
        x_step_size,
        y_step_size,
        movement_mode,
        delay,
        scan_pattern="bidirectional",
        fast_axis="y",
        sample_id="",
        comments="",
        save_dir="",
    ):
        if delay is None:
            delay = 1

        # Determine step sizes based on movement mode
        if movement_mode == "steps":
            x_step_size = abs(x2 - x1) / x_steps if x_steps else 0
            y_step_size = abs(y2 - y1) / y_steps if y_steps else 0

        num_x_steps = round(abs(x2 - x1) / x_step_size) if x_step_size else 0
        num_y_steps = round(abs(y2 - y1) / y_step_size) if y_step_size else 0

        # Assign slow/fast based on fast_axis selection
        # Channel 1 = X, Channel 2 = Y
        if fast_axis == "x":
            slow_ch, fast_ch = self.channel[2], self.channel[1]
            num_slow, num_fast = num_y_steps, num_x_steps
            slow_start, slow_end = y1, y2
            fast_start, fast_end = x1, x2
            slow_step = y_step_size
            fast_step = x_step_size
        else:
            slow_ch, fast_ch = self.channel[1], self.channel[2]
            num_slow, num_fast = num_x_steps, num_y_steps
            slow_start, slow_end = x1, x2
            fast_start, fast_end = y1, y2
            slow_step = x_step_size
            fast_step = y_step_size

        slow_dir = 1 if slow_end >= slow_start else -1
        fast_dir = 1 if fast_end >= fast_start else -1

        lockin = global_state.lockin
        multimeter = global_state.multimeter

        try:
            global_state.scan_active = True
            global_state.scan_data_queue = queue.Queue()
            global_state.pause_lockin_reading.set()
            global_state.pause_stage_reading.set()
            global_state.pause_multimeter_reading.set()
            time.sleep(0.05)

            freq = float(lockin.inst.query("FREQ?")) if lockin else 0.0

            data = []
            forward = True  # for bidirectional pattern

            for slow_i in range(num_slow + 1):
                if not global_state.scan_active:
                    print("---Scan aborted by user")
                    break
                slow_pos = slow_start + slow_i * slow_step * slow_dir
                slow_ch.MoveTo(Decimal(slow_pos), 60000)

                # Determine fast axis iteration order
                if scan_pattern == "bidirectional" and not forward:
                    fast_range = range(num_fast, -1, -1)
                else:
                    fast_range = range(num_fast + 1)

                for fast_i in fast_range:
                    if not global_state.scan_active:
                        break
                    fast_pos = fast_start + fast_i * fast_step * fast_dir
                    fast_ch.MoveTo(Decimal(fast_pos), 60000)
                    time.sleep(delay)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                    snap_x, snap_y = lockin.snap() if lockin else (0.0, 0.0)
                    voltage = multimeter.read_value() if multimeter else 0.0

                    if fast_axis == "x":
                        pos_x, pos_y = fast_pos, slow_pos
                    else:
                        pos_x, pos_y = slow_pos, fast_pos

                    point = {
                        "timestamp": timestamp,
                        "positionX": pos_x,
                        "positionY": pos_y,
                        "X": snap_x,
                        "Y": snap_y,
                        "frequency": freq,
                        "voltage": voltage,
                    }
                    data.append(point)
                    global_state.scan_data_queue.put(point)
                    print(
                        f"---({pos_x}, {pos_y}) X={snap_x:.6e} Y={snap_y:.6e} V={voltage:.6f}"
                    )

                # Handle pattern after each fast-axis sweep
                if scan_pattern == "bidirectional":
                    forward = not forward
                # unidirectional: fast_range is always forward, stage returns
                # to fast_start at the top of the next slow_i iteration

        except Exception as e:
            print(f"---Error in move_in_rectangle: {e}")
            traceback.print_exc()
        finally:
            if data:
                scan_info = (
                    f"x1={x1}, y1={y1}, x2={x2}, y2={y2}, "
                    f"fast_axis={fast_axis}, scan_pattern={scan_pattern}, "
                    f"mode=step_and_measure, delay={delay}"
                )
                save_to_file(
                    data,
                    sample_id=sample_id,
                    comments=comments,
                    scan_params=scan_info,
                    save_dir=save_dir,
                )
            global_state.scan_active = False
            global_state.pause_lockin_reading.clear()
            global_state.pause_stage_reading.clear()
            global_state.pause_multimeter_reading.clear()

    def read_values(self):
        try:
            x = self.channel[1].DevicePosition
            y = self.channel[2].DevicePosition
            return {"x": f"{x}", "y": f"{y}"}
        except Exception as e:
            print(f"Error reading from stage: {e}")
            return None

    def move(self, x, y):
        try:
            t1 = Thread(target=self.channel[1].MoveTo, args=(Decimal(x), 60000))
            t2 = Thread(target=self.channel[2].MoveTo, args=(Decimal(y), 60000))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
        except Exception as e:
            print(f"---Error in moving: {e}")

    @staticmethod
    def calculate_position(elapsed, start, end, max_vel, accel):
        """Predict position at elapsed time using trapezoidal motion profile."""
        distance = abs(end - start)
        direction = 1 if end >= start else -1
        t_accel = max_vel / accel
        d_accel = 0.5 * accel * t_accel**2

        if 2 * d_accel >= distance:
            # Triangular profile — never reaches max velocity
            t_peak = (distance / accel) ** 0.5
            total_time = 2 * t_peak
            if elapsed >= total_time:
                return end
            if elapsed <= t_peak:
                return start + direction * 0.5 * accel * elapsed**2
            else:
                dt = elapsed - t_peak
                peak_vel = accel * t_peak
                return start + direction * (
                    0.5 * distance + peak_vel * dt - 0.5 * accel * dt**2
                )
        else:
            # Trapezoidal profile
            d_const = distance - 2 * d_accel
            t_const = d_const / max_vel
            total_time = 2 * t_accel + t_const
            if elapsed >= total_time:
                return end
            if elapsed <= t_accel:
                return start + direction * 0.5 * accel * elapsed**2
            elif elapsed <= t_accel + t_const:
                dt = elapsed - t_accel
                return start + direction * (d_accel + max_vel * dt)
            else:
                dt = elapsed - t_accel - t_const
                return start + direction * (
                    d_accel + d_const + max_vel * dt - 0.5 * accel * dt**2
                )

    def validate_position(self, channel_number, start, end):
        """
        Move one axis and record calculated vs actual positions.
        Returns list of {time, calculated, actual} dicts plus motion params.
        """
        ch = self.channel[channel_number]

        # Read velocity params
        vel_params = ch.GetVelocityParams()
        max_vel = float(str(vel_params.MaxVelocity))
        accel = float(str(vel_params.Acceleration))
        print(
            f"---validate_position ch{channel_number}: max_vel={max_vel}, accel={accel}"
        )

        # Move to start position and wait
        ch.MoveTo(Decimal(float(start)), 60000)
        time.sleep(0.5)

        # Set 1ms polling for high-resolution position updates
        ch.StartPolling(1)
        time.sleep(0.1)

        records = []

        # Start move in background thread
        move_thread = Thread(target=ch.MoveTo, args=(Decimal(float(end)), 600000))
        t0 = time.time()
        move_thread.start()

        while move_thread.is_alive():
            elapsed = time.time() - t0
            calculated = self.calculate_position(elapsed, start, end, max_vel, accel)
            actual = float(str(ch.DevicePosition))
            records.append(
                {
                    "time": round(elapsed, 6),
                    "calculated": round(calculated, 6),
                    "actual": round(actual, 6),
                }
            )

        move_thread.join()

        # Restore normal polling
        ch.StartPolling(250)

        print(f"---validate_position: {len(records)} samples recorded")
        return {
            "records": records,
            "max_vel": max_vel,
            "accel": accel,
        }

    def continuous_scan(
        self,
        x1,
        y1,
        x2,
        y2,
        slow_axis_step_size,
        scan_pattern="bidirectional",
        record_retrace=False,
        fast_axis="y",
        fast_axis_step_size=None,
        sample_id="",
        comments="",
        save_dir="",
        scan_generation: int = 0,
    ):
        """
        Continuous scan with parallel device reads.

        The fast axis moves continuously while the slow axis steps.
        Lock-in (SNAP? 0,1) and multimeter (READ?) are read in parallel
        via ThreadPoolExecutor — no sleep between reads.
        """
        print(
            f"---continuous_scan called: ({x1},{y1})→({x2},{y2}), "
            f"step={slow_axis_step_size}, pattern={scan_pattern}, fast={fast_axis}"
        )
        lockin = global_state.lockin
        multimeter = global_state.multimeter
        if lockin is None or multimeter is None:
            print("---Error: lockin or multimeter not initialized")
            return

        # Map fast/slow to channels
        # Channel 1 = X, Channel 2 = Y
        if fast_axis == "x":
            slow_ch, fast_ch = self.channel[2], self.channel[1]
            slow_start, slow_end = Decimal(float(y1)), Decimal(float(y2))
            fast_start, fast_end = Decimal(float(x1)), Decimal(float(x2))
        else:
            slow_ch, fast_ch = self.channel[1], self.channel[2]
            slow_start, slow_end = Decimal(float(x1)), Decimal(float(x2))
            fast_start, fast_end = Decimal(float(y1)), Decimal(float(y2))

        slow_step = Decimal(float(slow_axis_step_size))
        slow_dir = Decimal(1) if slow_end >= slow_start else Decimal(-1)
        num_slow_steps = int(
            abs(float(str(slow_end - slow_start))) / slow_axis_step_size + 0.5
        )

        # Capture this scan's generation at entry so we can detect if a newer
        # scan has started (which would set scan_generation to a higher value).
        my_generation = scan_generation

        def aborted() -> bool:
            return global_state.scan_generation != my_generation

        try:
            global_state.pause_lockin_reading.set()
            global_state.pause_stage_reading.set()
            global_state.pause_multimeter_reading.set()
            time.sleep(0.5)  # wait for any in-flight WebSocket VISA queries to complete
            print("---WebSocket reads paused")

            freq = float(lockin.inst.query("FREQ?"))
            print(f"---Frequency: {freq}")

            # High-resolution position polling
            self.channel[1].StartPolling(1)
            self.channel[2].StartPolling(1)

            # Save current velocity params for retrace restore
            fast_ch_num = 1 if fast_axis == "x" else 2
            original_vel_params = self.channel[fast_ch_num].GetVelocityParams()

            data = []
            sample_count = 0
            prev_sample_count = 0
            start_time = time.time()
            going_forward = True
            executor = ThreadPoolExecutor(max_workers=2)

            try:
                for slow_i in range(num_slow_steps + 1):
                    if aborted():
                        print("---Scan aborted by user")
                        break
                    current_slow = slow_start + Decimal(slow_i) * slow_step * slow_dir
                    print(f"---Slow axis at {current_slow}, forward={going_forward}")
                    self._safe_move_to(slow_ch, current_slow, 60000, aborted=aborted)
                    if aborted():
                        break

                    # Determine fast axis target for this sweep
                    if scan_pattern == "bidirectional":
                        fast_target = fast_end if going_forward else fast_start
                        # Pre-position to the correct start of the first sweep
                        if slow_i == 0:
                            self._safe_move_to(
                                fast_ch, fast_start, 60000, aborted=aborted
                            )
                    else:
                        # Unidirectional: always sweep same direction
                        fast_target = fast_end
                        # Ensure fast axis is at start before each forward sweep
                        self._safe_move_to(fast_ch, fast_start, 60000, aborted=aborted)
                    if aborted():
                        break

                    # Compute valid position bounds for this sweep
                    ft_start_f = float(str(fast_start))
                    ft_end_f = float(str(fast_end))
                    pos_lo = min(ft_start_f, ft_end_f) - 0.5
                    pos_hi = max(ft_start_f, ft_end_f) + 0.5
                    # Grid origin for bin-based gating
                    grid_origin = min(ft_start_f, ft_end_f)

                    # Start fast axis movement in background
                    move_thread = Thread(
                        target=fast_ch.MoveTo, args=(fast_target, 600000), daemon=True
                    )
                    move_thread.start()

                    # Track last recorded grid bin for bin-gated sampling
                    last_recorded_bin = None

                    # Tight read loop — parallel reads via executor
                    sweep_start_time = time.time()
                    while move_thread.is_alive():
                        if aborted():
                            fast_ch.Stop(0)
                            move_thread.join(
                                timeout=2.0
                            )  # SDK keeps blocking until MoveTimeoutException; don't wait 600s
                            time.sleep(0.5)  # let stage decelerate
                            break
                        # Read actual fast axis position from device
                        fast_pos = float(str(fast_ch.DevicePosition))

                        # Skip bogus reads (stale cache returning 0 or out-of-range)
                        if fast_pos < pos_lo or fast_pos > pos_hi:
                            continue

                        # If step size given, only record once per grid bin
                        if fast_axis_step_size is not None:
                            current_bin = round(
                                (fast_pos - grid_origin) / fast_axis_step_size
                            )
                            if current_bin == last_recorded_bin:
                                continue

                        future_snap = executor.submit(lockin.snap)
                        future_voltage = executor.submit(multimeter.read_value)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                        snap_x, snap_y = future_snap.result()
                        voltage = future_voltage.result()

                        if fast_axis == "x":
                            pos_x = fast_pos
                            pos_y = float(str(current_slow))
                        else:
                            pos_x = float(str(current_slow))
                            pos_y = fast_pos

                        point = {
                            "timestamp": timestamp,
                            "positionX": pos_x,
                            "positionY": pos_y,
                            "X": snap_x,
                            "Y": snap_y,
                            "frequency": freq,
                            "voltage": voltage,
                        }
                        data.append(point)
                        global_state.scan_data_queue.put(point)
                        sample_count += 1
                        if fast_axis_step_size is not None:
                            last_recorded_bin = current_bin

                    move_thread.join(
                        timeout=2.0
                    )  # no-op for completed move; caps wait if thread is still stopping
                    sweep_time = time.time() - sweep_start_time
                    sweep_samples = sample_count - prev_sample_count
                    sweep_rate = sweep_samples / sweep_time if sweep_time > 0 else 0
                    print(
                        f"---  Sweep: {sweep_samples} samples in "
                        f"{sweep_time:.3f}s ({sweep_rate:.1f} samples/s)"
                    )
                    prev_sample_count = sample_count

                    # Handle retrace / direction reversal
                    if scan_pattern == "bidirectional":
                        going_forward = not going_forward
                    else:
                        # Unidirectional: retrace to fast_start
                        if slow_i < num_slow_steps:  # skip retrace after last sweep
                            if record_retrace:
                                # Retrace at same speed, recording data
                                retrace_thread = Thread(
                                    target=fast_ch.MoveTo,
                                    args=(fast_start, 600000),
                                    daemon=True,
                                )
                                retrace_thread.start()
                                r_last_recorded_bin = None
                                while retrace_thread.is_alive():
                                    if aborted():
                                        fast_ch.Stop(0)
                                        retrace_thread.join(
                                            timeout=2.0
                                        )  # same as move_thread: SDK won't return until MoveTimeoutException
                                        time.sleep(0.5)  # let stage decelerate
                                        break
                                    r_fast_pos = float(str(fast_ch.DevicePosition))
                                    if r_fast_pos < pos_lo or r_fast_pos > pos_hi:
                                        continue
                                    if fast_axis_step_size is not None:
                                        r_bin = round(
                                            (r_fast_pos - grid_origin)
                                            / fast_axis_step_size
                                        )
                                        if r_bin == r_last_recorded_bin:
                                            continue

                                    future_snap = executor.submit(lockin.snap)
                                    future_voltage = executor.submit(
                                        multimeter.read_value
                                    )
                                    timestamp = datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S.%f"
                                    )
                                    s_x, s_y = future_snap.result()
                                    v = future_voltage.result()

                                    if fast_axis == "x":
                                        r_pos_x, r_pos_y = (
                                            r_fast_pos,
                                            float(str(current_slow)),
                                        )
                                    else:
                                        r_pos_x, r_pos_y = (
                                            float(str(current_slow)),
                                            r_fast_pos,
                                        )

                                    pt = {
                                        "timestamp": timestamp,
                                        "positionX": r_pos_x,
                                        "positionY": r_pos_y,
                                        "X": s_x,
                                        "Y": s_y,
                                        "frequency": freq,
                                        "voltage": v,
                                    }
                                    data.append(pt)
                                    if fast_axis_step_size is not None:
                                        r_last_recorded_bin = r_bin
                                    global_state.scan_data_queue.put(pt)
                                    sample_count += 1
                                retrace_thread.join(timeout=2.0)
                            else:
                                # Fast retrace: max velocity, no recording
                                fast_ch.SetVelocityParams(
                                    Decimal(100.0), Decimal(1000.0)
                                )
                                fast_ch.MoveTo(fast_start, 600000)
                                # Restore original velocity
                                fast_ch.SetVelocityParams(
                                    original_vel_params.MaxVelocity,
                                    original_vel_params.Acceleration,
                                )

            finally:
                executor.shutdown(wait=False)

            elapsed = time.time() - start_time
            rate = sample_count / elapsed if elapsed > 0 else 0
            print(
                f"---Continuous scan: {sample_count} samples in {elapsed:.2f}s "
                f"({rate:.1f} samples/second)"
            )

        except Exception as e:
            print(f"---Error in continuous_scan: {e}")
            traceback.print_exc()
        finally:
            if data:
                scan_info = (
                    f"x1={x1}, y1={y1}, x2={x2}, y2={y2}, "
                    f"fast_axis={fast_axis}, scan_pattern={scan_pattern}, "
                    f"mode=continuous, slow_step={slow_axis_step_size}, fast_step={fast_axis_step_size}"
                )
                save_to_file(
                    data,
                    sample_id=sample_id,
                    comments=comments,
                    scan_params=scan_info,
                    save_dir=save_dir,
                )
            # Only deactivate scan if we're still the current generation —
            # a new scan may have already started and reset scan_active to True.
            if not aborted():
                global_state.scan_active = False
            self.channel[1].StartPolling(250)
            self.channel[2].StartPolling(250)
            if not aborted():
                global_state.pause_lockin_reading.clear()
                global_state.pause_stage_reading.clear()
                global_state.pause_multimeter_reading.clear()
