from pydantic import BaseModel


class FDPBDParams(BaseModel):
    f_rolloff: float
    delay_1: float
    delay_2: float
    lambda_down: list[float]
    eta_down: list[float]
    c_down: list[float]
    h_down: list[float]
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
    include_air_deflection: bool = False
    dndt_up: float = -8.9e-7


class PlotData(BaseModel):
    freq_fit: list[float]
    v_corr_in_fit: list[float]
    v_corr_out_fit: list[float]
    v_corr_ratio_fit: list[float]
    delta_in: list[float]
    delta_out: list[float]
    delta_ratio: list[float]


class FDPBDResult(BaseModel):
    lambda_measure: float
    alpha_t_fitted: float
    t_ss_heat: float
    plot_data: PlotData
