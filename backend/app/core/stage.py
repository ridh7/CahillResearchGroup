import queue
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Thread

try:
    import clr

    from app.config import settings

    clr.AddReference(settings.kinesis_device_manager_dll)
    clr.AddReference(settings.kinesis_generic_motor_dll)
    clr.AddReference(settings.kinesis_brushless_motor_dll)

    from System import Decimal, Enum
    from Thorlabs.MotionControl.Benchtop.BrushlessMotorCLI import *
    from Thorlabs.MotionControl.DeviceManagerCLI import *
    from Thorlabs.MotionControl.GenericMotorCLI import *
    from Thorlabs.MotionControl.GenericMotorCLI.ControlParameters import TriggerState
except Exception as e:
    raise ImportError(f"Thorlabs SDK not available: {e}") from e

from app.models.state import global_state
from app.utils.file_utils import save_to_file


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

    # ─── Hardware-triggered raster scan (BBD302 AtPositionFwd BNC) ──────────
    #
    # Unidirectional only. Fast axis is Ch2 (Y) — Port 1 of the motherboard
    # routes Ch2's AtPositionFwd pulses to BNC I/O 1, which is then tee'd to
    # the lock-in's rear TRIG IN and the DMM's rear EXT TRIG. Both instruments
    # run in hardware-triggered buffered mode; Python does nothing during each
    # row's sweep. At end of row, both buffers are read in bulk.
    #
    # Known issue (2026-04-24, hardware-triggered-scan branch): the BBD302
    # reliably drops pulse 0 on every sweep after the first. Workaround not
    # yet implemented here — rows 1+ will return N-1 grid-point readings
    # instead of N until that's fixed. Log a warning when this happens.

    def _hw_push_motherboard(self):
        """Push Port 1 = DigitalOutput / MotorChannel2 to hardware."""
        option_type = DeviceConfiguration.DeviceSettingsUseOptionType  # type: ignore[name-defined]
        mb_cfg = self.device.GetMotherboardConfiguration(
            settings.stage_serial, Enum.Parse(option_type, "UseDeviceSettings")
        )
        mb_settings = BBD30XMotherboardSettings.GetSettings(mb_cfg)  # type: ignore[name-defined]
        self.device.SetMotherboardSettings(mb_settings, True)

    def _hw_configure_ch2_triggers(
        self,
        start_pos_mm: float,
        step_mm: float,
        n_pulses: int,
        pulse_width_us: int = 100000,
    ):
        """Set Ch2 TriggerIOConfigParams for AtPositionFwd pulse generation."""
        ch2 = self.channel[2]
        ch2.RequestTriggerIOConfigParameters()
        time.sleep(0.1)
        p = ch2.GetTriggerIOConfigParameters()
        p.TriggerOutMode = Enum.Parse(
            type(p.TriggerOutMode), "TrigOutput_AtPositionFwd"
        )
        p.TriggerOutPolarity = Enum.Parse(type(p.TriggerOutPolarity), "High")
        p.TriggerInMode = Enum.Parse(type(p.TriggerInMode), "Disabled")
        p.StartPositionFwd = Decimal(start_pos_mm)
        p.IntervalFwd = Decimal(step_mm)
        p.PulseCountFwd = int(n_pulses)
        p.PulseWidth = int(pulse_width_us)
        p.CycleCount = 4
        ch2.SetTriggerIOConfigParams(p)

    def _hw_arm(self):
        self.channel[2].SetPositionTriggerState(TriggerState.TrigState_Enabled)
        time.sleep(0.2)

    def _hw_disarm(self):
        import contextlib

        with contextlib.suppress(Exception):
            self.channel[2].SetPositionTriggerState(TriggerState.TrigState_Disabled)

    def hardware_triggered_scan(
        self,
        x1,
        y1,
        x2,
        y2,
        slow_axis_step_size,
        fast_axis_step_size=None,
        sample_id="",
        comments="",
        save_dir="",
        scan_generation: int = 0,
        pre_margin_mm: float = 1.0,
        post_margin_mm: float = 1.0,
        pulse_width_us: int = 100000,
    ):
        """
        Unidirectional hardware-triggered raster. Fast axis = Y (Ch2).

        Per-row sequence:
          1. Reposition fast axis to (fast_grid_start - pre_margin).
          2. Move slow axis to the row's slow coordinate.
          3. Configure Ch2 AtPositionFwd triggers for this row's grid positions.
          4. Arm lock-in SAMPpertrig and DMM EXT multi-trigger.
          5. MoveTo(fast_grid_end + post_margin). Python idle during sweep.
          6. Read both buffers in bulk; emit N points on the WebSocket.

        Aborts via scan_generation: if a newer scan starts, the loop breaks
        out cleanly between rows.
        """
        print(
            f"---hardware_triggered_scan: ({x1},{y1})→({x2},{y2}), "
            f"slow_step={slow_axis_step_size}, fast_step={fast_axis_step_size}"
        )
        lockin = global_state.lockin
        multimeter = global_state.multimeter
        if lockin is None or multimeter is None:
            print("---Error: lockin or multimeter not initialized")
            return

        # This scan requires fast axis = Y (Ch2) because the motherboard routes
        # Ch2's AtPositionFwd to BNC Port 1. Validate at entry.
        fast_ch = self.channel[2]
        slow_ch = self.channel[1]
        fast_start = float(y1)
        fast_end = float(y2)
        slow_start = float(x1)
        slow_end = float(x2)

        if fast_end <= fast_start:
            print(
                "---Error: hardware-triggered scan requires y2 > y1 (unidirectional forward)"
            )
            return

        # Build fast-axis grid positions and step.
        if fast_axis_step_size is None or fast_axis_step_size <= 0:
            print("---Error: fast_axis_step_size required for hardware-triggered scan")
            return
        n_fast = int(round((fast_end - fast_start) / fast_axis_step_size)) + 1
        actual_step = (fast_end - fast_start) / (n_fast - 1) if n_fast > 1 else 0.0
        if n_fast < 2:
            print("---Error: need at least 2 fast-axis grid points")
            return

        slow_step = float(slow_axis_step_size)
        slow_dir = 1.0 if slow_end >= slow_start else -1.0
        num_slow_steps = int(abs(slow_end - slow_start) / slow_step + 0.5)

        my_generation = scan_generation

        def aborted() -> bool:
            return global_state.scan_generation != my_generation

        # Leading sacrificial pulse: the SR865A's SAMPpertrig CAPTURE reliably
        # misses the first falling edge after CAPTURESTART (we tried tweaking
        # the arm sequence and could not eliminate this). To avoid losing
        # grid[0]'s lock-in reading, we configure the stage to fire ONE EXTRA
        # pulse one step before the grid starts. The lock-in's first-edge
        # miss now lands on this sacrificial pulse; the N grid pulses are all
        # captured. The DMM catches all N+1 edges; we discard its first slot
        # at readback.
        pulse_start = fast_start - fast_axis_step_size
        n_pulses_total = n_fast + 1
        move_start = pulse_start - pre_margin_mm
        move_end = fast_end + post_margin_mm

        # Stage-travel guard: if the leading pulse position would go below
        # zero or stage minimum, that's a user-config problem (the scan starts
        # too close to the stage origin to fit a leading pulse + pre-margin).
        if move_start < 0:
            print(
                f"---Error: move_start={move_start:.3f} mm is below stage origin. "
                f"Increase y1 by at least {-move_start:.3f} mm "
                f"(scan needs room for a leading pulse + {pre_margin_mm} mm pre-margin)."
            )
            return

        data: list[dict] = []
        start_time = time.time()

        try:
            global_state.pause_lockin_reading.set()
            global_state.pause_stage_reading.set()
            global_state.pause_multimeter_reading.set()
            time.sleep(0.5)

            freq = float(lockin.inst.query("FREQ?"))
            print(f"---Frequency: {freq}")

            self.channel[1].StartPolling(1)
            self.channel[2].StartPolling(1)

            # One-time motherboard config push — routes Ch2 output to BNC Port 1.
            self._hw_push_motherboard()

            # Save the user-configured sweep velocity on Ch2 so we can restore it
            # before each triggered sweep. Reposition moves (disarmed retrace +
            # slow-axis step) use a fast retrace velocity instead.
            #
            # IMPORTANT: Kinesis returns a .NET VelocityParams object whose
            # MaxVelocity/Acceleration fields are mutated in place when
            # SetVelocityParams is called. We must extract scalar values via
            # str()→float→Decimal round-trip so the stored values don't change
            # when we temporarily set retrace velocity.
            retrace_vel = Decimal(100.0)
            retrace_acc = Decimal(1000.0)

            def read_vel_mmps() -> float:
                vp = fast_ch.GetVelocityParams()
                return float(str(vp.MaxVelocity))

            # Sanity check: if we're seeing what looks like leftover retrace
            # velocity from a prior scan whose cleanup didn't land, the user's
            # intended sweep velocity is unknown. Try waiting once; then bail.
            captured_mmps = read_vel_mmps()
            if captured_mmps >= 50.0:
                print(
                    f"---WARNING: captured velocity {captured_mmps:.2f} mm/s "
                    f"looks like leftover retrace. Waiting 1s and retrying."
                )
                time.sleep(1.0)
                captured_mmps = read_vel_mmps()
                if captured_mmps >= 50.0:
                    print(
                        f"---Error: captured velocity {captured_mmps:.2f} mm/s "
                        f"still looks like retrace. Previous scan likely didn't "
                        f"clean up. Set desired velocity via /set_movement_params "
                        f"and retry."
                    )
                    return

            original_fast_vel_params = fast_ch.GetVelocityParams()
            sweep_max_vel = Decimal(float(str(original_fast_vel_params.MaxVelocity)))
            sweep_accel = Decimal(float(str(original_fast_vel_params.Acceleration)))
            print(
                f"---Sweep velocity captured: max={sweep_max_vel} mm/s, "
                f"accel={sweep_accel} mm/s²"
            )

            for slow_i in range(num_slow_steps + 1):
                if aborted():
                    print("---Scan aborted by user")
                    break
                current_slow = slow_start + slow_i * slow_step * slow_dir

                # Disarm triggers while repositioning so we don't fire stray pulses.
                self._hw_disarm()

                # Fast retrace: slow-axis step + fast-axis reposition to start.
                fast_ch.SetVelocityParams(retrace_vel, retrace_acc)
                self._safe_move_to(
                    slow_ch, Decimal(current_slow), 60000, aborted=aborted
                )
                if aborted():
                    break
                self._safe_move_to(fast_ch, Decimal(move_start), 60000, aborted=aborted)
                if aborted():
                    break
                # Restore user-configured sweep velocity for the triggered sweep.
                fast_ch.SetVelocityParams(sweep_max_vel, sweep_accel)

                # Configure triggers for this row's grid plus 1 leading pulse.
                # Stage fires n_pulses_total = n_fast + 1 pulses starting at
                # pulse_start (= fast_start - actual_step). First edge is the
                # decoy that the lock-in will miss; remaining N hit grid[0..N-1].
                self._hw_configure_ch2_triggers(
                    start_pos_mm=pulse_start,
                    step_mm=actual_step,
                    n_pulses=n_pulses_total,
                    pulse_width_us=pulse_width_us,
                )
                self._hw_arm()

                # Arm both instruments for the full N+1 (lead + grid). The
                # readback layer drops the first slot from each.
                try:
                    lockin.arm_samppertrig(n_pulses_total)
                    multimeter.arm_ext_multi_trigger(n_pulses_total)
                except Exception as e:
                    print(f"---Instrument arm error on row {slow_i}: {e}")
                    continue

                # Let SAMPpertrig fully arm before the first edge arrives. Row 0
                # tends to get this settling time incidentally from session
                # startup; rows 1+ see the first-edge dropout if the arm→sweep
                # gap is too short. 1.0 s is generous enough to cover both.
                time.sleep(1.0)

                sweep_start = time.time()
                try:
                    fast_ch.MoveTo(Decimal(move_end), 600000)
                except Exception as e:
                    print(f"---Row {slow_i} MoveTo failed: {e}")
                    self._hw_disarm()
                    continue
                sweep_time = time.time() - sweep_start

                # Settle so any in-flight edge reaches both receivers before we
                # stop / FETC?. 1.0 s is intentionally generous — the BBD302's
                # last pulse can arrive tens of ms after MoveTo returns.
                time.sleep(1.0)

                # Read both buffers in bulk.
                xy_pairs = lockin.read_capture()
                dmm_vals = multimeter.read_readings()

                self._hw_disarm()

                lk = len(xy_pairs)
                dm = len(dmm_vals)
                grid_positions = [fast_start + k * actual_step for k in range(n_fast)]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                # ─── Drop the leading sacrificial slot from each buffer ─────
                # Stage fired n_fast + 1 edges, with the first being a decoy
                # before the grid. Lock-in's chronic first-edge dropout means
                # it usually has only N readings (= grid[0..N-1]). DMM usually
                # captures all N+1 (= [decoy, grid[0..N-1]]). We normalize:
                #   - If a buffer has N+1 entries, drop entry [0] (the decoy).
                #   - If it has N entries, the decoy was already missed — keep all.
                # After normalization, both buffers should have N entries
                # representing grid[0..N-1].
                if len(xy_pairs) == n_pulses_total:
                    xy_pairs = xy_pairs[1:]
                if len(dmm_vals) == n_pulses_total:
                    dmm_vals = dmm_vals[1:]
                lk = len(xy_pairs)
                dm = len(dmm_vals)

                # ─── Count-based alignment ──────────────────────────────────
                # After decoy normalization both buffers should have N entries.
                # Remaining cases handle stage-side or transfer anomalies.
                emitted: list[
                    tuple[int, float, float, float]
                ] = []  # (grid_idx, x, y, v)
                if lk == n_fast and dm == n_fast:
                    # Clean row.
                    for k in range(n_fast):
                        x, y = xy_pairs[k]
                        emitted.append((k, x, y, dmm_vals[k]))
                elif lk == n_fast - 1 and dm == n_fast:
                    # Lock-in missed an EXTRA edge beyond the decoy (rare).
                    # DMM[0] is grid[0], lock-in starts at grid[1].
                    emitted.append((0, float("nan"), float("nan"), dmm_vals[0]))
                    for k in range(n_fast - 1):
                        x, y = xy_pairs[k]
                        emitted.append((k + 1, x, y, dmm_vals[k + 1]))
                elif lk == n_fast - 1 and dm == n_fast - 1:
                    # Both missed an additional edge (after the decoy).
                    for k in range(n_fast - 1):
                        x, y = xy_pairs[k]
                        emitted.append((k + 1, x, y, dmm_vals[k]))
                elif lk == 0 or dm == 0:
                    print(
                        f"---Row {slow_i} DROPPED: lockin={lk}, dmm={dm} "
                        f"(transfer / protocol failure — no points emitted)"
                    )
                else:
                    print(
                        f"---Row {slow_i} DROPPED: lockin={lk}, dmm={dm}, "
                        f"expected={n_fast} — unknown alignment pattern"
                    )

                for grid_idx, x_val, y_val, voltage in emitted:
                    point = {
                        "timestamp": timestamp,
                        "positionX": current_slow,
                        "positionY": grid_positions[grid_idx],
                        "X": x_val,
                        "Y": y_val,
                        "frequency": freq,
                        "voltage": voltage,
                    }
                    data.append(point)
                    global_state.scan_data_queue.put(point)

                n_emitted = len(emitted)
                rate = n_emitted / sweep_time if sweep_time > 0 else 0
                # Count how many emitted points have a real (non-NaN) lock-in
                # reading. When rows 1+ hit the (lk=N-1, dm=N) case we pad the
                # first grid slot with NaN X/Y; the total emitted count is N
                # but only N-1 have real X/Y.
                import math as _math

                n_real_lockin = sum(
                    1
                    for (_, x, y, _v) in emitted
                    if not (_math.isnan(x) or _math.isnan(y))
                )
                if (
                    n_emitted == n_fast
                    and n_real_lockin == n_fast
                    and lk == n_fast
                    and dm == n_fast
                ):
                    print(
                        f"---Row {slow_i}: {n_emitted}/{n_fast} points in "
                        f"{sweep_time:.2f}s ({rate:.1f} pts/s)"
                    )
                elif n_emitted > 0:
                    print(
                        f"---Row {slow_i}: {n_emitted}/{n_fast} points "
                        f"(lockin={lk}, dmm={dm}, real-lockin={n_real_lockin}, "
                        f"aligned to grid[{emitted[0][0]}..{emitted[-1][0]}]) "
                        f"in {sweep_time:.2f}s"
                    )

            elapsed = time.time() - start_time
            total = len(data)
            rate = total / elapsed if elapsed > 0 else 0
            print(
                f"---Hardware-triggered scan: {total} points in {elapsed:.2f}s "
                f"({rate:.1f} pts/s)"
            )

        except Exception as e:
            print(f"---Error in hardware_triggered_scan: {e}")
            traceback.print_exc()
        finally:
            self._hw_disarm()
            # Restore the user-configured sweep velocity on Ch2 so the stage
            # doesn't stay at retrace velocity for subsequent manual moves or
            # scans. Also read back + log to verify the restore committed, so
            # we can spot situations where the write silently fails.
            if "sweep_max_vel" in locals():
                try:
                    fast_ch.SetVelocityParams(sweep_max_vel, sweep_accel)
                    time.sleep(0.2)  # let the write commit before we read back
                    vp_after = fast_ch.GetVelocityParams()
                    readback = float(str(vp_after.MaxVelocity))
                    print(
                        f"---Velocity restored: attempted={sweep_max_vel} mm/s, "
                        f"readback={readback:.4f} mm/s"
                    )
                except Exception as e:
                    print(f"---Velocity restore failed: {e}")

            # Lock-in cleanup: stop any in-flight capture so the next scan's
            # arm_samppertrig starts from a known state. Independent SNAP/OUTP
            # reads used by the WebSocket handlers are unaffected by this.
            if lockin is not None:
                try:
                    lockin.inst.write("CAPTURESTOP")
                    time.sleep(0.1)
                    print("---Lock-in cleanup: CAPTURESTOP issued")
                except Exception as e:
                    print(f"---Lock-in cleanup error: {e}")

            # DMM cleanup: return the meter from EXT multi-trigger back to the
            # single-reading-on-demand configuration the WebSocket poller and
            # subsequent scans expect. Without this, the DMM stays in
            # TRIG:SOUR EXT waiting for edges, which leaves it in a confusable
            # state across scans and causes the "post-RST query failed" path
            # to fire on the next arm_ext_multi_trigger.
            if multimeter is not None:
                try:
                    multimeter.inst.write("ABOR")
                    time.sleep(0.2)
                    multimeter.inst.write("*RST")
                    time.sleep(0.6)
                    multimeter.inst.write("CONF:VOLT:DC")
                    multimeter.inst.write("SENS:VOLT:DC:NPLC 0.2")
                    multimeter.inst.write("rear")
                    print("---DMM cleanup: ABOR + *RST + CONF complete")
                except Exception as e:
                    print(f"---DMM cleanup error: {e}")
            if data:
                scan_info = (
                    f"x1={x1}, y1={y1}, x2={x2}, y2={y2}, "
                    f"fast_axis=y, mode=hardware_triggered, "
                    f"slow_step={slow_axis_step_size}, fast_step={fast_axis_step_size}, "
                    f"pre_margin={pre_margin_mm}, post_margin={post_margin_mm}"
                )
                save_to_file(
                    data,
                    sample_id=sample_id,
                    comments=comments,
                    scan_params=scan_info,
                    save_dir=save_dir,
                )
            if not aborted():
                global_state.scan_active = False
            self.channel[1].StartPolling(250)
            self.channel[2].StartPolling(250)
            if not aborted():
                global_state.pause_lockin_reading.clear()
                global_state.pause_stage_reading.clear()
                global_state.pause_multimeter_reading.clear()
