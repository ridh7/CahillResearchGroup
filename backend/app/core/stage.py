import time
import traceback
from datetime import datetime
from threading import Thread

import clr

from app.models.state import global_state
from app.utils.file_utils import save_to_file

from .shared_state import shared_state

clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll"
)
clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll"
)
clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.Benchtop.BrushlessMotorCLI.dll"
)

from System import Decimal, Math
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
                    if dev == "103387864":
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

                # Home(60000ms timeout) finds limit switch to establish zero position
                print(f"---Homing channel {channel_number}")
                self.channel[channel_number].Home(60000)
                time.sleep(1)
        except Exception as e:
            print(f"---Stage initialization error: {e}")

    def home_channel(self, channel_number):
        try:
            print(f"---Homing channel {channel_number}")
            self.channel[channel_number].Home(60000)
            time.sleep(1)
        except Exception as e:
            print(f"---Homing error: {e}")

    def get_movement_params(self, channel_number):
        try:
            print(f"---Get channel {channel_number} params")
            home_params = self.channel[channel_number].GetHomingParams()
            vel_params = self.channel[channel_number].GetVelocityParams()
            return home_params, vel_params
        except Exception as e:
            print(f"---Error: {e}")

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
    ):
        if delay is None:
            delay = 1
        if movement_mode == "steps":
            x_step_size = abs(x2 - x1) / x_steps
            y_step_size = abs(y2 - y1) / y_steps
        greater_x, greater_y = max(x1, x2), max(y1, y2)
        smaller_x, smaller_y = min(x1, x2), min(y1, y2)
        data = []
        y = smaller_y
        y_iteration = 0
        while (
            y <= greater_y + y_step_size / 2
        ):  # add tolerance because of the floating point inaccuracy in python
            self.channel[2].MoveTo(Decimal(y), 60000)
            x = smaller_x
            x_iteration = 0
            while x <= greater_x:
                self.channel[1].MoveTo(Decimal(x), 60000)
                print(
                    f"---Current position: ({self.channel[1].DevicePosition}, {self.channel[2].DevicePosition})"
                )
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                shared_state.pause_lockin_reading.set()
                shared_state.pause_stage_reading.set()
                try:
                    time.sleep(0.02)
                    # Read all devices while WebSockets are paused
                    lockin_values = (
                        global_state.lockin.read_values()
                        if global_state.lockin
                        else None
                    )
                    multimeter_value = (
                        global_state.multimeter.read_value()
                        if global_state.multimeter
                        else None
                    )
                    position_x = self.channel[1].DevicePosition
                    position_y = self.channel[2].DevicePosition
                finally:
                    shared_state.pause_lockin_reading.clear()
                    shared_state.pause_stage_reading.clear()

                # Build values dict after clearing pause
                if lockin_values:
                    values = lockin_values.copy()
                    values["timestamp"] = timestamp
                    values["positionX"] = position_x
                    values["positionY"] = position_y
                    values["voltage"] = multimeter_value
                    data.append(values)
                time.sleep(delay)
                # Calculate next x position using iteration count to avoid accumulation of floating point error
                x_iteration += 1
                x = smaller_x + x_iteration * x_step_size
            # Calculate next y position using iteration count
            y_iteration += 1
            y = smaller_y + y_iteration * y_step_size
        save_to_file(data)

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
            self.channel[1].MoveTo(Decimal(x), 60000)
            self.channel[2].MoveTo(Decimal(y), 60000)
        except Exception as e:
            print(f"---Error in moving: {e}")

    def move_and_log(self, x, y, x_step_size, sample_rate):
        """
        Perform bidirectional zigzag scan with continuous data logging.

        Algorithm:
        1. Increase polling rate to 1ms for faster position updates
        2. For each X step:
           - Scan Y upward (start_y → target_y) or downward (current_y → start_y)
           - Log instrument data continuously during Y movement
           - Capture first point, continuous points during motion, and end point
           - Reverse Y direction for next X step (bidirectional scan reduces time)
        3. Filter output: remove out-of-bounds and duplicate position samples

        Bidirectional scanning is critical for time-efficient 2D mapping, reducing
        total scan time by ~50% compared to unidirectional (no Y return moves).
        """
        try:
            # Pause stage WebSocket to prevent VISA resource locking conflicts
            shared_state.pause_stage_reading.set()

            # Increase polling frequency for high-resolution position tracking
            self.channel[1].StartPolling(1)
            self.channel[2].StartPolling(1)  # 1ms polling for Y channel
            target_x = float(x)
            target_y = float(y)
            x_step_size = float(x_step_size)
            start_x = self.channel[1].DevicePosition  # Decimal, initial X
            start_y = self.channel[2].DevicePosition  # Decimal, initial Y
            current_x = start_x
            current_y = start_y

            def move_stage(x_pos, y_pos):
                self.channel[1].MoveTo(x_pos, 600000)  # Expects Decimal
                self.channel[2].MoveTo(y_pos, 600000)  # Expects Decimal

            data = []
            start_time = time.time()
            actual_sample_count = 0  # Total samples recorded
            going_up = True  # Start with upward scan

            # Iterate over X positions in bidirectional zigzag pattern
            while current_x <= Decimal(
                target_x + x_step_size / 2
            ):  # Decimal comparison
                if going_up:
                    print(f"---Starting upward Y scan at x={current_x}")
                    end_y = Decimal(target_y)
                else:
                    print(f"---Starting downward Y scan at x={current_x}")
                    end_y = current_y

                # Capture first point before starting movement
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                with shared_state.value_lock:
                    lockin_values = (
                        shared_state.latest_lockin_values.copy()
                        if shared_state.latest_lockin_values
                        else {"X": 0, "Y": 0, "frequency": 0}
                    )
                    multimeter_value = (
                        shared_state.latest_multimeter_value
                        if shared_state.latest_multimeter_value is not None
                        else 0
                    )
                    stage_values = self.read_values()

                first_values = {
                    "timestamp": timestamp,
                    "positionX": stage_values["x"],
                    "positionY": stage_values["y"],
                    "X": lockin_values["X"],
                    "Y": lockin_values["Y"],
                    "frequency": lockin_values["frequency"],
                    "voltage": multimeter_value,
                }
                scan_data = [first_values]  # Start scan_data with first point
                actual_sample_count += 1

                # Move stage in separate thread while logging in main thread
                # This allows continuous data acquisition during motion
                move_thread = Thread(target=move_stage, args=(current_x, end_y))
                move_thread.start()
                print(f"---Started moving to ({current_x}, {end_y})")

                # Poll position and log data continuously until Y reaches target
                while True:
                    pos_y = self.channel[2].DevicePosition  # Decimal
                    if Math.Abs(pos_y - end_y) < Decimal(0.01):
                        break

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                    # Read latest instrument values from shared_state cache
                    # (populated by WebSocket streaming threads at ~200Hz)
                    # This avoids blocking GPIB communication during continuous scan
                    with shared_state.value_lock:
                        lockin_values = (
                            shared_state.latest_lockin_values.copy()
                            if shared_state.latest_lockin_values
                            else {"X": 0, "Y": 0, "frequency": 0}
                        )
                        multimeter_value = (
                            shared_state.latest_multimeter_value
                            if shared_state.latest_multimeter_value is not None
                            else 0
                        )
                        # stage_values = self.read_values()
                        stage_values = (
                            shared_state.latest_stage_values.copy()
                            if shared_state.latest_stage_values
                            else {"x": -1, "y": -1}
                        )

                    values = {
                        "timestamp": timestamp,
                        "positionX": stage_values["x"],
                        "positionY": stage_values["y"],
                        "X": lockin_values["X"],
                        "Y": lockin_values["Y"],
                        "frequency": lockin_values["frequency"],
                        "voltage": multimeter_value,
                    }
                    scan_data.append(values)
                    actual_sample_count += 1
                    time.sleep(sample_rate)

                move_thread.join()

                # Capture end point after movement completes
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                with shared_state.value_lock:
                    lockin_values = (
                        shared_state.latest_lockin_values.copy()
                        if shared_state.latest_lockin_values
                        else {"X": 0, "Y": 0, "frequency": 0}
                    )
                    multimeter_value = (
                        shared_state.latest_multimeter_value
                        if shared_state.latest_multimeter_value is not None
                        else 0
                    )
                    stage_values = self.read_values()

                end_values = {
                    "timestamp": timestamp,
                    "positionX": stage_values["x"],
                    "positionY": stage_values["y"],
                    "X": lockin_values["X"],
                    "Y": lockin_values["Y"],
                    "frequency": lockin_values["frequency"],
                    "voltage": multimeter_value,
                }
                scan_data.append(end_values)  # Add end point to scan_data
                actual_sample_count += 1

                # Append scan data (reverse if downward to maintain Y increasing order)
                # This ensures CSV output has monotonically increasing Y values
                if going_up:
                    data.extend(scan_data)
                else:
                    data.extend(reversed(scan_data))

                # Step to next X position and reverse Y scan direction
                current_x += Decimal(x_step_size)
                self.channel[1].MoveTo(current_x, 600000)
                going_up = not going_up  # Toggle for bidirectional scanning

            # Post-processing: filter out-of-bounds and duplicate samples
            # Bounds extended slightly to account for overshoot/settling
            start_x -= Decimal(x_step_size / 2)
            end_x = Decimal(target_x + x_step_size / 2)
            start_y -= Decimal(0.05)
            end_y = Decimal(target_y + 0.05)
            filtered_data = []
            invalid_sample_count = 0
            prev_pos_x = None  # Initialize previous X position
            prev_pos_y = None  # Initialize previous Y position

            for entry in data:
                pos_x = Decimal(float(entry["positionX"]))
                pos_y = Decimal(float(entry["positionY"]))
                min_y = min(start_y, end_y)
                max_y = max(start_y, end_y)

                # Check bounds (remove samples captured during acceleration/deceleration)
                within_bounds = (start_x <= pos_x <= end_x) and (
                    min_y <= pos_y <= max_y
                )

                # Check for duplicates (occurs when stage is stationary at endpoints)
                is_duplicate = prev_pos_y is not None and pos_y == prev_pos_y

                if within_bounds and not is_duplicate:
                    filtered_data.append(entry)
                    prev_pos_x = (
                        pos_x  # Update previous positions only for kept samples
                    )
                    prev_pos_y = pos_y
                else:
                    if not within_bounds:
                        print(
                            f"---Filtered out (bounds): X={pos_x}, Y={pos_y} outside bounds X:[{start_x}, {end_x}], Y:[{min_y}, {max_y}]"
                        )
                    elif is_duplicate:
                        print(
                            f"---Filtered out (duplicate): X={pos_x}, Y={pos_y} matches previous X={prev_pos_x}, Y={prev_pos_y}"
                        )
                    invalid_sample_count += 1

            valid_sample_count = actual_sample_count - invalid_sample_count

            save_to_file(filtered_data)

            elapsed_time = time.time() - start_time
            sample_rate_achieved = (
                actual_sample_count / elapsed_time if elapsed_time > 0 else 0
            )
            print(
                f"---Logged {actual_sample_count} actual samples, "
                f"{invalid_sample_count} invalid samples discarded, "
                f"{valid_sample_count} valid samples saved during rectangular zigzag scan to ({x}, {y}) "
                f"in {elapsed_time:.2f}s time\n{sample_rate_achieved:.2f} samples/second"
            )
        except Exception as e:
            print(f"---Error in move_and_log: {e}")
            traceback.print_exc()
            tb = traceback.extract_tb(e.__traceback__)
            if tb:
                filename, line_number, func_name, text = tb[-1]
                print(f"---Error occurred at line {line_number} in {filename}: {text}")
        finally:
            # Resume stage WebSocket streaming
            shared_state.pause_stage_reading.clear()
