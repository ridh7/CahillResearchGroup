from datetime import datetime


def save_to_file(data, filename=None):
    if filename is None:
        filename = f"SR865A_measurements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w") as f:
        f.write(
            "Timestamp,PositionX,PositionY,X(V),Y(V),R(V),Theta(deg),Frequency(Hz),Phase(deg),Voltage(V)\n"
        )
        for measurement in data:
            f.write(
                f"{measurement['timestamp']},{measurement['positionX']},{measurement['positionY']},"
                f"{measurement['X']:.6f},{measurement['Y']:.6f},{measurement['R']:.6f},"
                f"{measurement['theta']:.2f},{measurement['frequency']:.6f},"
                f"{measurement['phase']:.2f},{measurement['voltage']}\n"
            )
    print(f"\nData saved to {filename}")
