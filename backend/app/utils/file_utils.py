import os
from datetime import datetime


def save_to_file(data, sample_id="", comments="", scan_params=None, save_dir=""):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = (
        f"{sample_id}_tops2_{timestamp}.csv" if sample_id else f"tops2_{timestamp}.csv"
    )
    filename = os.path.join(save_dir, base_name) if save_dir else base_name

    with open(filename, "w") as f:
        # Write metadata header (lines starting with # are ignored by pandas read_csv with comment='#')
        f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if sample_id:
            f.write(f"# Sample ID: {sample_id}\n")
        if comments:
            for line in comments.splitlines():
                f.write(f"# Comments: {line}\n")
        if scan_params:
            f.write(f"# Scan: {scan_params}\n")
        f.write("Timestamp,PositionX,PositionY,X(V),Y(V),Frequency(Hz),Voltage(V)\n")
        for measurement in data:
            f.write(
                f"{measurement['timestamp']},{measurement['positionX']},{measurement['positionY']},"
                f"{measurement['X']},{measurement['Y']},{measurement['frequency']:.6f},"
                f"{measurement['voltage']}\n"
            )
    print(f"\nData saved to {filename}")
