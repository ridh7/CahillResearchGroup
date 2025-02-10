from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define the request model
class RectangleParams(BaseModel):
    x1: float
    x2: float
    y1: float
    y2: float
    steps: int


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


@app.post("/start")
async def start_movement(params: RectangleParams):
    try:
        # Initialize device and channels
        device = initialize_device("103387864")
        channel1, motor_config1 = initialize_channel(device, 1)
        channel2, motor_config2 = initialize_channel(device, 2)

        # Execute movement
        move_in_rectangle(
            params.x1, params.y1, params.x2, params.y2, params.steps, channel1, channel2
        )

        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/")
def read_root():
    return {"status": "API is running"}
