import pyvisa


class SR865A:
    def __init__(self, resource_name=None):
        try:
            self.rm = pyvisa.ResourceManager()
            if resource_name is None:
                resources = self.rm.list_resources()
                for res in resources:
                    if "3769" in res:
                        resource_name = res
                        break
            if resource_name is None:
                raise Exception("SR865A not found!")
            print(f"---Connecting to lockin: {resource_name}")
            self.inst = self.rm.open_resource(resource_name)
            self.inst.timeout = 5000
            self.volatage_sensitivity_map = {
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
        except Exception as e:
            print(f"---Locking initialization error: {e}")

    def read_values(self):
        x = float(self.inst.query("OUTP? 0"))
        y = float(self.inst.query("OUTP? 1"))
        freq = float(self.inst.query("FREQ?"))
        # sensitivity_code = int(self.inst.query("SCAL?"))
        # unit = self.volatage_sensitivity_map[sensitivity_code]
        return {
            "X": x,
            "Y": y,
            "frequency": freq,
        }
