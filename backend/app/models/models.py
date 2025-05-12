from pydantic import BaseModel
from typing import List, Dict, Optional


class Layer1Params(BaseModel):
    thickness: float
    sigma: float
    capac: float
    rho: float
    alphaT: float
    C11_0: float
    C12_0: float
    C44_0: float


class Layer2Params(BaseModel):
    sigma_x: float
    sigma_y: float
    sigma_z: float
    capac: float
    rho: float
    alphaT_perp: float
    alphaT_para: float
    C11_0: float
    C12_0: float
    C13_0: float
    C33_0: float
    C44_0: float


class Layer3Params(BaseModel):
    sigma: float
    capac: float


class AnisotropicFDPBDParams(BaseModel):
    f_rolloff: float
    delay_1: float
    delay_2: float
    lambda_down: List[Optional[float]]
    c_down: List[Optional[float]]
    h_down: List[Optional[float]]
    incident_pump: float
    w_rms: float
    x_offset: float
    phi: float
    lens_transmittance: float
    detector_factor: float
    n_al: float
    k_al: float
    lambda_up: float
    c_up: float
    rho: float
    alphaT: float
    C11_0: float
    C12_0: float
    C44_0: float
    lambda_down_x_sample: float
    lambda_down_y_sample: float
    lambda_down_z_sample: float
    rho_sample: float
    C11_0_sample: float
    C12_0_sample: float
    C13_0_sample: float
    C33_0_sample: float
    C44_0_sample: float
    alphaT_perp: float
    alphaT_para: float


class AnisotropicFDPBDResult(BaseModel):
    f_peak: Optional[float]
    ratio_at_peak: Optional[float]
    lambda_measure: Optional[float]
    alpha_t_fitted: Optional[float]
    t_ss_heat: Optional[float]
    plot_data: Dict[str, List[float]]
