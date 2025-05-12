from pydantic import BaseModel
from typing import List


class FDPBDParams(BaseModel):
    f_amp: float
    delay_1: float
    delay_2: float
    lambda_down: List[float]
    eta_down: List[float]
    c_down: List[float]
    h_down: List[float]
    niu: float
    alpha_t: float
    lambda_up: float
    eta_up: float
    c_up: float
    h_up: float
    w_rms: float
    x_offset: float
    incident_pump: float
    incident_probe: float
    n_al: float
    k_al: float
    lens_transmittance: float
    detector_factor: float


class PlotData(BaseModel):
    freq_fit: List[float]
    v_corr_in_fit: List[float]
    v_corr_out_fit: List[float]
    v_corr_ratio_fit: List[float]
    delta_in: List[float]
    delta_out: List[float]
    delta_ratio: List[float]


class FDPBDResult(BaseModel):
    lambda_measure: float
    alpha_t_fitted: float
    t_ss_heat: float
    plot_data: PlotData
