import pyvisa


class BKPrecision5493C:
    """
    BK Precision 5493C digital multimeter driver using PyVISA for GPIB/USB.

    Default configuration: DC voltage measurement, rear terminals, 0.2 NPLC aperture.
    NPLC (Number of Power Line Cycles) controls integration time:
    - Lower NPLC = faster readings, more noise (0.02 NPLC ≈ 0.33ms @ 60Hz)
    - Higher NPLC = slower readings, better noise rejection (100 NPLC ≈ 1.67s @ 60Hz)
    """

    def __init__(self, resource_name=None):
        try:
            self.rm = pyvisa.ResourceManager()
            if resource_name is None:
                # Auto-detect by serial number in resource string
                resources = self.rm.list_resources()
                for res in resources:
                    if "W114239033" in res:
                        resource_name = res
                        break
            if resource_name is None:
                raise Exception("BK Precision 5493C not found!")
            print(f"---Connecting to multimeter: {resource_name}")
            self.inst = self.rm.open_resource(resource_name)
            self.inst.timeout = 5000

            # Initialize to known state
            self.inst.write("*RST")  # Reset to factory defaults
            self.inst.write("CONF:VOLT:DC")  # DC voltage mode
            self.inst.write(
                "SENS:VOLT:DC:NPLC 0.2"
            )  # 0.2 power line cycles (fast, ~3ms)
            self.inst.write("rear")  # Use rear terminal inputs
            print(
                f"---Multimeter initialized with {self.inst.query('ROUT:TERM?')} terminal and {self.inst.query('SENS:VOLT:DC:NPLC?')} PLC aperture."
            )
        except Exception as e:
            print(f"---Multimeter initialization error: {e}")

    def read_value(self):
        try:
            reading = float(self.inst.query("READ?"))
            return reading
        except Exception as e:
            print(f"Error reading from multimeter: {e}")
            return None

    def configure_measurement(self, mode="VOLT:DC"):
        """
        Modes: VOLT:DC, VOLT:AC, CURR:DC, CURR:AC, RES, FREQ, etc.
        """
        try:
            self.inst.write(f"CONF: {mode}")
            return True
        except Exception as e:
            print(f"Error configuring multimeter: {e}")
            return False

    def set_aperture(self, nplc):
        """
        Set NPLC for aperture (valid values: 0.02, 0.2, 1, 10, 100).
        """
        valid_nplc = [0.02, 0.2, 1, 10, 100]
        if nplc in valid_nplc:
            try:
                self.inst.write(f"SENS:VOLT:DC:NPLC {nplc}")
                return True
            except Exception as e:
                print(f"Error setting aperture: {e}")
                return False
        else:
            raise ValueError(f"Invalid NPLC value: {nplc}. Must be one of {valid_nplc}")

    def get_aperture(self):
        """
        Get current NPLC setting.
        """
        try:
            return float(self.inst.query("SENS:VOLT:DC:NPLC?"))
        except Exception as e:
            print(f"Error getting aperture: {e}")
            return None

    def set_terminal(self, terminal):
        """
        Set terminal to 'fron' or 'rear'.
        """
        if terminal in ["fron", "rear"]:
            try:
                self.inst.write(terminal)
                return True
            except Exception as e:
                print(f"Error setting terminal: {e}")
                return False
        else:
            raise ValueError(f"Invalid terminal: {terminal}. Must be 'fron' or 'rear'")

    def get_terminal(self):
        """
        Get current terminal setting.
        """
        try:
            return "fron" if "Front" in f"{self.inst.query('ROUT:TERM?')}" else "rear"
        except Exception as e:
            print(f"Error getting terminal: {e}")
            return None
