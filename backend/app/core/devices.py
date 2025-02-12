import time
import pyvisa
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

# from System import Decimal


class GlobalState:
    def __init__(self):
        self.device = None
        self.channel1 = None
        self.channel2 = None
        self.motor_config1 = None
        self.motor_config2 = None
        self.lockin = None


class SR865A:
    def __init__(self, resource_name=None):
        self.rm = pyvisa.ResourceManager()
        if resource_name is None:
            resources = self.rm.list_resources()
            for res in resources:
                if "3769" in res:
                    resource_name = res
                    break
        if resource_name is None:
            raise Exception("SR865A not found!")
        self.inst = self.rm.open_resource(resource_name)
        self.inst.timeout = 5000

    def read_values(self):
        x = float(self.inst.query("OUTP? 0"))
        y = float(self.inst.query("OUTP? 1"))
        r = float(self.inst.query("OUTP? 2"))
        theta = float(self.inst.query("OUTP? 3"))
        freq = float(self.inst.query("FREQ?"))
        phase = float(self.inst.query("PHAS?"))
        return {
            "X": x,
            "Y": y,
            "R": r,
            "theta": theta,
            "frequency": freq,
            "phase": phase,
        }


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
