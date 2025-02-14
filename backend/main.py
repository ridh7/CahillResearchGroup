from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import endpoints
from contextlib import asynccontextmanager
from app.core.devices import *
from app.models.state import global_state

        
@asynccontextmanager
async def lifespan(app: FastAPI):
    global_state.device = initialize_device("103387864")
    global_state.channel1, global_state.motor_config1 = initialize_channel(
        global_state.device, 1
    )
    global_state.channel2, global_state.motor_config2 = initialize_channel(
        global_state.device, 2
    )
    global_state.lockin = SR865A()
    global_state.multimeter = BKPrecision5493C()
    yield
    global_state.device.Disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)


# from typing import Union
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from datetime import datetime
# from contextlib import asynccontextmanager
# import time
# import clr
# import pyvisa

# class GlobalState:
#     def __init__(self):
#         self.device, self.channel1, self.channel2, self.motor_config1, self.motor_config2, self.lockin = None, None, None, None, None, None

# class SR865A:
#     def __init__(self, resource_name = None):
#         self.rm = pyvisa.ResourceManager()

#         if resource_name is None:
#             resources = self.rm.list_resources()
#             for res in resources:
#                 if '3769' in res:
#                     resource_name = res
#                     break

#         if resource_name is None:
#             raise Exception("SR865A not found!")

#         self.inst = self.rm.open_resource(resource_name)
#         self.inst.timeout = 5000

#     def read_values(self):
#         x = float(self.inst.query('OUTP? 0'))
#         y = float(self.inst.query('OUTP? 1'))
#         r = float(self.inst.query('OUTP? 2'))
#         theta = float(self.inst.query('OUTP? 3'))
#         freq = float(self.inst.query('FREQ?'))
#         phase = float(self.inst.query('PHAS?'))

#         return {'X': x, 'Y': y, 'R': r, 'theta': theta, 'frequency': freq, 'phase': phase}

# clr.AddReference(
#     "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll"
# )
# clr.AddReference(
#     "C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll"
# )
# clr.AddReference(
#     "C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.Benchtop.BrushlessMotorCLI.dll"
# )

# from Thorlabs.MotionControl.DeviceManagerCLI import *
# from Thorlabs.MotionControl.GenericMotorCLI import *
# from Thorlabs.MotionControl.Benchtop.BrushlessMotorCLI import *
# from System import Decimal


# global_state = GlobalState()

# # Define the request model
# class RectangleParams(BaseModel):
#     x1: float
#     x2: float
#     y1: float
#     y2: float
#     steps: int


# def initialize_device(serial_number):
#     try:
#         print(f"---Connecting to device with serial number: {serial_number}")
#         DeviceManagerCLI.BuildDeviceList()
#         device = BenchtopBrushlessMotor.CreateBenchtopBrushlessMotor(serial_number)
#         device.Connect(serial_number)
#         if device.IsConnected:
#             print(f"---Connected to: {device.GetDeviceInfo().Description}")
#         else:
#             print("---Device initialization error")
#         return device

#     except Exception as e:
#         print(f"---Device initialization error: {e}")


# def initialize_channel(device, channel_number):
#     try:
#         print(f"---Initializing channel {channel_number}")
#         channel = device.GetChannel(channel_number)
#         channel.StartPolling(250)
#         time.sleep(0.25)
#         channel.EnableDevice()
#         time.sleep(0.25)
#         motor_config = channel.LoadMotorConfiguration(channel.DeviceID)
#         print(f"---Homing channel {channel_number}")
#         channel.Home(60000)
#         time.sleep(1)
#         return channel, motor_config

#     except Exception as e:
#         print(f"---Channel {channel_number} initialization error: {e}")

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global_state.device = initialize_device("103387864")
#     global_state.channel1, global_state.motor_config1 = initialize_channel(global_state.device, 1)
#     global_state.channel2, global_state.motor_config2 = initialize_channel(global_state.device, 2)
#     global_state.lockin = SR865A()
#     yield
#     global_state.device.Disconnect()

# # Create FastAPI app
# app = FastAPI(lifespan=lifespan)

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# def home_channel(channel):
#     print(f"---Homing channel {channel.ChannelNo}")
#     channel.Home(60000)
#     time.sleep(1)

# def save_to_file(data, filename=None):
#     """Save measurements to a CSV file"""
#     if filename is None:
#         filename = f"SR865A_measurements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

#     with open(filename, 'w') as f:
#         # Write header
#         f.write("Timestamp,PositionX,PositionY,X(V),Y(V),R(V),Theta(deg),Frequency(Hz),Phase(deg)\n")

#         # Write data
#         for measurement in data:
#             f.write(f"{measurement['timestamp']},{measurement['positionX']},{measurement['positionY']},{measurement['X']:.6f},"
#                     f"{measurement['Y']:.6f},{measurement['R']:.6f},"
#                     f"{measurement['theta']:.2f},{measurement['frequency']:.6f},"
#                     f"{measurement['phase']:.2f}\n")

#     print(f"\nData saved to {filename}")

# def move_in_rectangle(x1, y1, x2, y2, steps, channel1, channel2):
#     try:
#         print(
#             f"---Current position: ({channel1.DevicePosition}, {channel2.DevicePosition})"
#         )
#         step_size_x = abs(x2 - x1) / steps
#         step_size_y = abs(y2 - y1) / steps
#         x, y = x1, y1
#         data = []

#         while y < y2:
#             y += step_size_y
#             channel2.MoveTo(Decimal(y), 60000)
#             print(
#                 f"---Current position: ({channel1.DevicePosition}, {channel2.DevicePosition})"
#             )
#             while x < x2:
#                 x += step_size_x
#                 channel1.MoveTo(Decimal(x), 60000)
#                 print(
#                     f"---Current position: ({channel1.DevicePosition}, {channel2.DevicePosition})"
#                 )
#                 timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
#                 values = global_state.lockin.read_values()
#                 values['timestamp'] = timestamp
#                 values['positionX'] = channel1.DevicePosition
#                 values['positionY'] = channel2.DevicePosition
#                 data.append(values)
#                 time.sleep(0.1)
#             x = x1
#             channel1.MoveTo(Decimal(x), 60000)

#         save_to_file(data)

#     except Exception as e:
#         print(f"---Error in moving: {e}")

# @app.post("/start")
# async def start_movement(params: RectangleParams):
#     try:
#         # Execute movement
#         move_in_rectangle(
#             params.x1, params.y1, params.x2, params.y2, params.steps, global_state.channel1, global_state.channel2
#         )

#         return {"status": "success", "message": "Movement completed"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @app.get('/home_x')
# async def home_x():
#     try:
#         home_channel(global_state.channel1)
#         return {"status": "success", "message": "Homing completed"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @app.get('/home_y')
# async def home_y():
#     try:
#         home_channel(global_state.channel2)
#         return {"status": "success", "message": "Homing completed"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @app.get("/")
# def read_root():
#     return {"status": "API is running"}
