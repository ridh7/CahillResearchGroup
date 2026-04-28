from typing import Any, cast

import pyvisa

from app.config import settings


class SR865A:
    """
    SR865A Lock-in Amplifier driver using PyVISA for GPIB communication.

    The SR865A measures weak AC signals by correlating the input with a
    reference frequency. Sensitivity and time constant are controlled via
    integer codes (0-27 and 0-23 respectively) that map to physical units.
    """

    def __init__(self, resource_name=None):
        try:
            self.rm = pyvisa.ResourceManager()
            if resource_name is None:
                # Auto-detect SR865A by USB Product ID in resource string
                resources = self.rm.list_resources()
                for res in resources:
                    if settings.lockin_pid in res:
                        resource_name = res
                        break
            if resource_name is None:
                raise Exception("SR865A not found!")
            print(f"---Connecting to lockin: {resource_name}")
            self.inst: Any = cast(
                Any, self.rm.open_resource(resource_name)
            )  # PyVISA Resource lacks stubs
            self.inst.timeout = 5000

            # SR865A sensitivity mapping (codes 0-27 to voltage units)
            # Code determines full-scale input range for voltage measurements
            # Lower codes = higher sensitivity (1V max), higher codes = lower sensitivity (1nV max)
            self.voltage_sensitivity_map = {
                0: "V",
                1: "mV",
                2: "mV",
                3: "mV",
                4: "mV",
                5: "mV",
                6: "mV",
                7: "mV",
                8: "mV",
                9: "mV",
                10: "µV",
                11: "µV",
                12: "µV",
                13: "µV",
                14: "µV",
                15: "µV",
                16: "µV",
                17: "µV",
                18: "µV",
                19: "nV",
                20: "nV",
                21: "nV",
                22: "nV",
                23: "nV",
                24: "nV",
                25: "nV",
                26: "nV",
                27: "nV",
            }

            # Current sensitivity mapping (codes 0-27 to actual values in Amperes)
            # Used for current input mode measurements
            # Values follow 1-2-5 sequence: 1µA, 500nA, 200nA, 100nA, etc.
            self.current_sensitivity_map = [
                1e-6,
                5e-7,
                2e-7,
                1e-7,
                5e-8,
                2e-8,
                1e-8,
                5e-9,
                2e-9,
                1e-9,
                5e-10,
                2e-10,
                1e-10,
                5e-11,
                2e-11,
                1e-11,
                5e-12,
                2e-12,
                1e-12,
                5e-13,
                2e-13,
                1e-13,
                5e-14,
                2e-14,
                1e-14,
                5e-15,
                2e-15,
                1e-15,
            ]

            # Time constant mapping (codes 0-23 to integration time)
            # Determines low-pass filter cutoff frequency for noise reduction
            # Longer time constant = more averaging = better SNR but slower response
            # Range: 1µs (fast, noisy) to 300ks (slow, clean)
            self.time_constant_map = {
                0: "1 µs",
                1: "3 µs",
                2: "10 µs",
                3: "30 µs",
                4: "100 µs",
                5: "300 µs",
                6: "1 ms",
                7: "3 ms",
                8: "10 ms",
                9: "30 ms",
                10: "100 ms",
                11: "300 ms",
                12: "1 s",
                13: "3 s",
                14: "10 s",
                15: "30 s",
                16: "100 s",
                17: "300 s",
                18: "1 ks",
                19: "3 ks",
                20: "10 ks",
                21: "30 ks",
                22: "100 ks",
                23: "300 ks",
            }
        except Exception as e:
            print(f"---Lock-in initialization error: {e}")
            raise

    def read_values(self):
        """
        Read X, Y, and frequency from the lock-in amplifier.

        X and Y are the in-phase and quadrature components of the
        measured signal, representing amplitude*cos(phase) and
        amplitude*sin(phase) respectively.
        """
        try:
            x = float(self.inst.query("OUTP? 0"))
            y = float(self.inst.query("OUTP? 1"))
            freq = float(self.inst.query("FREQ?"))
            # sensitivity_code = int(self.inst.query("SCAL?"))
            # unit = self.voltage_sensitivity_map[sensitivity_code]
            return {
                "X": x,
                "Y": y,
                "frequency": freq,
            }
        except Exception as e:
            print(f"Error reading from lockin: {e}")
            return {
                "X": 0.0,
                "Y": 0.0,
                "frequency": 0.0,
            }

    def snap(self):
        """Read X and Y simultaneously using SNAP command (single GPIB query)."""
        response = self.inst.query("SNAP? 0,1")
        x_str, y_str = response.split(",")
        return float(x_str), float(y_str)

    def get_sensitivity(self):
        return int(self.inst.query("SCAL?"))

    def set_sensitivity(self, code):
        if 0 <= code <= 27:
            self.inst.write(f"SCAL {code}")
        else:
            raise ValueError("Sensitivity code must be between 0 and 27")

    def get_time_constant(self):
        return int(self.inst.query("OFLT?"))

    def set_time_constant(self, code):
        if 0 <= code <= 23:
            self.inst.write(f"OFLT {code}")
        else:
            raise ValueError("Time constant code must be between 0 and 23")

    def get_frequency(self):
        return float(self.inst.query("FREQ?"))

    def set_frequency(self, freq):
        self.inst.write(f"FREQ {freq}")

    def get_filter_slope(self):
        return int(self.inst.query("OFSL?"))

    def set_filter_slope(self, code):
        if 0 <= code <= 3:
            self.inst.write(f"OFSL {code}")
        else:
            raise ValueError("Filter slope code must be between 0 and 3")

    # ─── Hardware-triggered buffered acquisition (SAMPpertrig) ──────────────
    #
    # Arm the CAPTURE subsystem in "one-sample-per-hardware-trigger" mode.
    # Each falling edge on the rear TRIG IN BNC pushes one sample set into
    # the buffer. Only CAPTURECFG=1 (X,Y) is supported by the read helper.

    def arm_samppertrig(self, n_pulses: int) -> None:
        """Arm OneShot + SAMPpertrig CAPTURE sized for exactly n_pulses X/Y pairs.

        On rows after row 0 the SR865A's trigger-edge detection often misses the
        first falling edge after CAPTURESTART unless the capture subsystem is
        given a strong reset and enough settling time. Strategy:
          1. CAPTURESTOP (idempotent)
          2. Toggle CAPTURECFG through a different value (0) then back to the
             target. Per the manual, CAPTURECFG writes clear sticky status
             bits; a real value change seems to reset the edge-detection state
             more reliably than re-writing the same value.
          3. CAPTURELEN and CAPTURESTART.
          4. Short sleep so the subsystem is actually armed before the stage
             starts moving.
        """
        import contextlib
        import math
        import time

        bytes_needed = n_pulses * 8  # 2 floats per pair × 4 bytes
        kb = max(2, math.ceil(bytes_needed / 2048) * 2)  # min 2 kB, round to even kB
        with contextlib.suppress(Exception):
            self.inst.write("CAPTURESTOP")
        time.sleep(0.1)
        self.inst.write("CAPTURECFG 0")  # dummy value to force a state change
        time.sleep(0.05)
        self.inst.write("CAPTURECFG 1")  # X,Y
        self.inst.write(f"CAPTURELEN {kb}")
        self.inst.write("CAPTURESTART 0,2")
        time.sleep(0.2)  # let the subsystem actually arm
        self._capture_len_kb = kb

    def read_capture(self) -> list[tuple[float, float]]:
        """Stop capture and return list of (X, Y) pairs from the buffer."""
        import time

        self.inst.write("CAPTURESTOP")
        time.sleep(0.1)
        bytes_captured = int(self.inst.query("CAPTUREBYTES?").strip())
        n_pairs = bytes_captured // 8
        kb = getattr(self, "_capture_len_kb", 2)
        floats = self.inst.query_binary_values(
            f"CAPTUREGET? 0,{kb}", datatype="f", is_big_endian=False
        )
        return [(floats[2 * i], floats[2 * i + 1]) for i in range(n_pairs)]
