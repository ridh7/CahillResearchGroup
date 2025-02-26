import clr
import time
from datetime import datetime
from app.models.state import global_state
from app.utils.file_utils import save_to_file

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
            print(f"---Connecting to device with serial number: {serial_number}")
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
            print(f"---Device initialization error: {e}")

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
        self, x1, y1, x2, y2, x_steps, y_steps, x_step_size, y_step_size, movement_mode
    ):
        try:
            if movement_mode == "steps":
                x_step_size = abs(x2 - x1) / x_steps
                y_step_size = abs(y2 - y1) / y_steps
            x, y = x1, y1
            data = []
            while y < y2:
                y += y_step_size
                self.channel[2].MoveTo(Decimal(y), 60000)
                print(
                    f"---Current position: ({self.channel[1].DevicePosition}, {self.channel[2].DevicePosition})"
                )
                while x < x2:
                    x += x_step_size
                    self.channel[1].MoveTo(Decimal(x), 60000)
                    print(
                        f"---Current position: ({self.channel[1].DevicePosition}, {self.channel[2].DevicePosition})"
                    )
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    values = global_state.lockin.read_values()
                    values["timestamp"] = timestamp
                    values["positionX"] = self.channel[1].DevicePosition
                    values["positionY"] = self.channel[2].DevicePosition
                    values["voltage"] = global_state.multimeter.read_value()
                    data.append(values)
                    time.sleep(0.1)
                x = x1
                self.channel[1].MoveTo(Decimal(x), 60000)
            save_to_file(data)
        except Exception as e:
            print(f"---Error in moving: {e}")

    def read_values(self):
        try:
            x = global_state.stage.channel[1].DevicePosition
            y = global_state.stage.channel[2].DevicePosition
            return {"x": f"{x}", "y": f"{y}"}
        except Exception as e:
            print(f"Error reading from stage: {e}")
            return None
