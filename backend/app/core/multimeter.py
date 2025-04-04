import pyvisa
import time


class BKPrecision5493C:
    def __init__(self, resource_name=None):
        try:
            self.rm = pyvisa.ResourceManager()
            if resource_name is None:
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
            self.inst.write("*RST")
            self.inst.write("CONF:VOLT:DC")
            self.inst.write("SENS:VOLT:DC:NPLC 0.2")
            self.inst.write("rear")
            print(f"---Multimeter initialized with {self.inst.query("ROUT:TERM?")} terminal and {self.inst.query("SENS:VOLT:DC:NPLC?")} PLC aperture.")
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
