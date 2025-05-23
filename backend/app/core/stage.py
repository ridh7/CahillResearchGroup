import clr
import time
from datetime import datetime
from app.models.state import global_state
from app.utils.file_utils import save_to_file
from app.core.shared_state import pause_lockin_reading, latest_lockin_values, value_lock

clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll"
)
clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll"
)
clr.AddReference(
    "C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.Benchtop.BrushlessMotorCLI.dll"
)

from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.Benchtop.BrushlessMotorCLI import *
from System import Decimal


class ThorlabsBBD302:
    def __init__(self, serial_number=None, channel_count=2):
        try:
            self.channel = {}
            self.motor_config = {}
            self.channel_count = channel_count
            DeviceManagerCLI.BuildDeviceList()
            if serial_number is None:
                devices = DeviceManagerCLI.GetDeviceList()
                for dev in devices:
                    if dev == "103387864":
                        serial_number = dev
            print(f"---Connecting to stage with serial number: {serial_number}")
            self.device = BenchtopBrushlessMotor.CreateBenchtopBrushlessMotor(
                serial_number
            )
            self.device.Connect(serial_number)
            if self.device.IsConnected:
                print(f"---Connected to: {self.device.GetDeviceInfo().Description}")
            else:
                print("---Device initialization error")
            for channel_number in range(1, self.channel_count + 1):
                print(f"---Initializing channel {channel_number}")
                self.channel[channel_number] = self.device.GetChannel(channel_number)
                self.channel[channel_number].StartPolling(250)
                time.sleep(0.25)
                self.channel[channel_number].EnableDevice()
                time.sleep(0.25)
                self.motor_config[channel_number] = self.channel[
                    channel_number
                ].LoadMotorConfiguration(self.channel[channel_number].DeviceID)
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
        start = time.time()
        sample_count = 0
        if delay == None:
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
                pause_lockin_reading.set()
                try:
                    time.sleep(0.02)
                    values = global_state.lockin.read_values()
                finally:
                    pause_lockin_reading.clear()
                values["timestamp"] = timestamp
                values["positionX"] = self.channel[1].DevicePosition
                values["positionY"] = self.channel[2].DevicePosition
                values["voltage"] = global_state.multimeter.read_value()
                data.append(values)
                time.sleep(delay)
                # Calculate next x position using iteration count to avoid accumulation of floating point error
                x_iteration += 1
                x = smaller_x + x_iteration * x_step_size
                sample_count += 1
            # Calculate next y position using iteration count
            y_iteration += 1
            y = smaller_y + y_iteration * y_step_size
        save_to_file(data)
        elapsed = time.time() - start
        print(
            f"---Logged {sample_count} samples during rectangular zigzag scan in {elapsed}s time\n{sample_count / elapsed} samples/second"
        )

    def read_values(self):
        try:
            x = global_state.stage.channel[1].DevicePosition
            y = global_state.stage.channel[2].DevicePosition
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
