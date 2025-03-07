import pyvisa


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
        self.volatage_sensitivity_map = [
            1.0,
            0.5,
            0.2,
            0.1,
            0.05,
            0.02,
            0.01,
            5e-3,
            2e-3,
            1e-3,
            5e-4,
            2e-4,
            1e-4,
            5e-5,
            2e-5,
            1e-5,
            5e-6,
            2e-6,
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
        ]
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

    def get_units_and_scale(self):
        input_mode = int(self.inst.query("IVMD?"))
        sensitivity_idx = int(self.inst.query("SCAL?"))
        sensitivity = (
            self.volatage_sensitivity_map[sensitivity_idx]
            if input_mode == 0
            else self.current_sensitivity_map[sensitivity_idx]
        )
        if input_mode == 0:
            if sensitivity >= 1:
                unit = "V"
                scale_factor = 1
            elif sensitivity >= 1e-3:
                unit = "mV"
                scale_factor = 1e3
            elif sensitivity >= 1e-6:
                unit = "μV"
                scale_factor = 1e6
            else:
                unit = "nV"
                scale_factor = 1e9
        else:
            if sensitivity >= 1e-6:
                unit = "μA"
                scale_factor = 1e6
            elif sensitivity >= 1e-9:
                unit = "nA"
                scale_factor = 1e9
            elif sensitivity >= 1e-12:
                unit = "pA"
                scale_factor = 1e12
            else:
                unit = "fA"
                scale_factor = 1e15
        return unit, scale_factor

    def read_values(self):
        unit, scale_factor = self.get_units_and_scale()
        x = float(self.inst.query("OUTP? 0")) * scale_factor
        y = float(self.inst.query("OUTP? 1")) * scale_factor
        r = float(self.inst.query("OUTP? 2")) * scale_factor
        theta = float(self.inst.query("OUTP? 3"))
        freq = float(self.inst.query("FREQ?"))
        phase = float(self.inst.query("PHAS?"))
        return {
            "X": x,
            "Y": y,
            "R": r,
            "unit": unit,
            "theta": theta,
            "frequency": freq,
            "phase": phase,
        }
