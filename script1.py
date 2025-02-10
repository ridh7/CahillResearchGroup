import time
import clr

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


def initialize_device(serial_number):
    try:
        print(f"---Connecting to device with serial number: {serial_number}")
        DeviceManagerCLI.BuildDeviceList()
        device = BenchtopBrushlessMotor.CreateBenchtopBrushlessMotor(serial_number)
        device.Connect(serial_number)
        if device.IsConnected:
            print(f"---Connected to: {device.GetDeviceInfo().Description}")
        else:
            print("---Device initialization error")
        return device

    except Exception as e:
        print(f"---Device initialization error: {e}")


def initialize_channel(device, channel_number):
    try:
        print(f"---Initializing channel {channel_number}")
        channel = device.GetChannel(channel_number)
        channel.StartPolling(250)
        time.sleep(0.25)
        channel.EnableDevice()
        time.sleep(0.25)
        motor_config = channel.LoadMotorConfiguration(channel.DeviceID)
        print(f"---Homing channel {channel_number}")
        channel.Home(60000)
        time.sleep(1)
        return channel, motor_config

    except Exception as e:
        print(f"---Channel {channel_number} initialization error: {e}")


def move_in_rectangle(x1, y1, x2, y2, steps, channel1, channel2):
    try:
        print(
            f"---Current position: ({channel1.DevicePosition}, {channel2.DevicePosition})"
        )
        step_size_x = abs(x2 - x1) / steps
        step_size_y = abs(y2 - y1) / steps
        x, y = x1, y1

        while y < y2:
            y += step_size_y
            channel2.MoveTo(Decimal(y), 60000)
            print(
                f"---Current position: ({channel1.DevicePosition}, {channel2.DevicePosition})"
            )
            while x < x2:
                x += step_size_x
                channel1.MoveTo(Decimal(x), 60000)
                print(
                    f"---Current position: ({channel1.DevicePosition}, {channel2.DevicePosition})"
                )
                time.sleep(0.1)
            x = x1
            channel1.MoveTo(Decimal(x), 60000)

    except Exception as e:
        print(f"---Error in moving: {e}")


def main():
    device = initialize_device("103387864")
    channel1, motor_config1 = initialize_channel(device, 1)
    channel2, motor_config2 = initialize_channel(device, 2)
    move_in_rectangle(0, 0, 50, 50, 10, channel1, channel2)


if __name__ == "__main__":
    main()
