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

    def read_values(self):
        x = float(self.inst.query("OUTP? 0"))
        y = float(self.inst.query("OUTP? 1"))
        r = float(self.inst.query("OUTP? 2"))
        theta = float(self.inst.query("OUTP? 3"))
        freq = float(self.inst.query("FREQ?"))
        phase = float(self.inst.query("PHAS?"))
        return {
            "X": x,
            "Y": y,
            "R": r,
            "theta": theta,
            "frequency": freq,
            "phase": phase,
        }
