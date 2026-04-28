from typing import Any, cast

import pyvisa

from app.config import settings


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
                    if settings.multimeter_serial in res:
                        resource_name = res
                        break
            if resource_name is None:
                raise Exception("BK Precision 5493C not found!")
            print(f"---Connecting to multimeter: {resource_name}")
            self.inst: Any = cast(
                Any, self.rm.open_resource(resource_name)
            )  # PyVISA Resource lacks stubs
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
            raise

    def read_value(self):
        try:
            reading = float(self.inst.query("READ?"))
            return reading
        except Exception as e:
            print(f"Error reading from multimeter: {e}")
            return 0.0

    def configure_measurement(self, mode="VOLT:DC"):
        """
        Modes: VOLT:DC, VOLT:AC, CURR:DC, CURR:AC, RES, FREQ, etc.
        """
        try:
            self.inst.write(f"CONF:{mode}")
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

    # ─── Hardware-triggered buffered acquisition (EXT multi-trigger) ────────
    #
    # Arm the DMM to buffer n_pulses readings, one per falling edge on the
    # rear EXT TRIG BNC. Readback via FETC? returns all readings in order.

    def arm_ext_multi_trigger(self, n_pulses: int, nplc: float = 0.2) -> None:
        """Arm TRIG:SOUR EXT + TRIG:COUN N + SAMP:COUN 1 + INIT for n_pulses edges.

        Empirical observation: the FIRST EXT-trigger sequence after a single
        *RST is brittle and FETC? often protocol-violates regardless of how
        many edges arrived. Subsequent sequences work fine. We don't know why,
        but a double-*RST consistently puts the meter into a state where the
        next INIT succeeds. So we always do two resets — costs ~1 second per
        scan-row but eliminates the "row 0 always fails" pattern.
        """
        import contextlib
        import time

        with contextlib.suppress(Exception):
            self.inst.write("ABOR")
        time.sleep(0.3)
        self.inst.write("*RST")
        time.sleep(0.6)
        with contextlib.suppress(Exception):
            self.inst.write("ABOR")
        time.sleep(0.2)
        self.inst.write("*RST")
        time.sleep(0.8)

        self.inst.write("CONF:VOLT:DC")
        self.inst.write(f"SENS:VOLT:DC:NPLC {nplc}")
        self.inst.write("rear")
        self.inst.write("SAMP:COUN 1")
        self.inst.write(f"TRIG:COUN {n_pulses}")
        self.inst.write("TRIG:SOUR EXT")
        time.sleep(0.2)
        self.inst.write("INIT")
        time.sleep(0.3)

    def read_readings(self) -> list[float]:
        """Drain the DMM trigger buffer via ABOR + FETC?.

        FETC? alone will protocol-violate (`VI_ERROR_INP_PROT_VIOL`) when fewer
        triggers arrived than `TRIG:COUN` configured — which happens whenever
        the BBD302 drops a pulse and the meter is left waiting for an edge that
        never comes. Per the 5490C manual §3.1, ABOR terminates the
        measurement-in-progress and returns the instrument to the trigger idle
        state; per §3.3, ABOR does not clear reading memory (only INIT, READ?,
        MEASure?, *RST, SYST:PRESet do). So ABOR + FETC? returns whatever was
        actually captured, partial buffers included.

        Returns [] on a real failure (transfer error, etc.); caller decides how
        to handle a dropped row.
        """
        import contextlib
        import time

        self.inst.timeout = 15000
        with contextlib.suppress(Exception):
            self.inst.write("ABOR")
        time.sleep(0.2)

        for attempt in (1, 2):
            try:
                raw = self.inst.query("FETC?")
                return [float(v) for v in raw.strip().split(",") if v.strip()]
            except Exception as e:
                if attempt == 1:
                    print(f"---DMM FETC? attempt 1 failed ({e}); waiting and retrying")
                    time.sleep(1.0)
                    with contextlib.suppress(Exception):
                        self.inst.write("ABOR")
                    continue
                print(f"---DMM FETC? attempt 2 failed ({e}); giving up on row")
                return []
        return []
