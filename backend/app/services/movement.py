import time
from datetime import datetime
from app.models.state import global_state
from app.utils.file_utils import save_to_file
import clr
from System import Decimal


def home_channel(channel):
    print(f"---Homing channel {channel.ChannelNo}")
    channel.Home(60000)
    time.sleep(1)


def move_in_rectangle(x1, y1, x2, y2, steps, channel1, channel2):
    try:
        print(
            f"---Current position: ({channel1.DevicePosition}, {channel2.DevicePosition})"
        )
        step_size_x = abs(x2 - x1) / steps
        step_size_y = abs(y2 - y1) / steps
        x, y = x1, y1
        data = []
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
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                values = global_state.lockin.read_values()
                values["timestamp"] = timestamp
                values["positionX"] = channel1.DevicePosition
                values["positionY"] = channel2.DevicePosition
                data.append(values)
                time.sleep(0.1)
            x = x1
            channel1.MoveTo(Decimal(x), 60000)
        save_to_file(data)
    except Exception as e:
        print(f"---Error in moving: {e}")
        
def get_movement_params(channel):
    home_params = channel.GetHomingParams()
    vel_params = channel.GetVelocityParams()
    return home_params, vel_params
