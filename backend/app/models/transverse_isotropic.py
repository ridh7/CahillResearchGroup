from pydantic import BaseModel


class TransverseIsotropicParams(BaseModel):
    # Lock-in correction
    f_rolloff: float = 95e3
    delay_1: float = 0.89e-5
    delay_2: float = -1.3e-11

    # Optical / detection
    incident_pump: float = 0.69e-3
    v_sum_fixed: float = 0.18
    w_rms: float = 11.2e-6
    r_0: float = 12.6e-6
    lens_transmittance: float = 0.92
    detector_gain: float = 37.0
    c_probe: float = 0.65
    n_al: float = 2.9
    k_al: float = 8.2

    # Simulation grid
    n_p: int = 63
    model_freq_start: float = 5e3
    model_freq_end: float = 300.0
    model_freq_points: int = 40

    # Thermal boundary conductance
    g_int: float = 100e6

    # Layer 1 (Al film)
    layer1_thickness: float = 70e-9
    layer1_sigma: float = 129.0
    layer1_capac: float = 2.42e6
    layer1_rho: float = 2.70e3
    layer1_alphaT: float = 23.1e-6
    layer1_C11_0: float = 107.4e9
    layer1_C12_0: float = 60.5e9
    layer1_C44_0: float = 28.3e9

    # Layer 2 (transversely isotropic bulk)
    layer2_sigma_r: float = 0.64
    layer2_sigma_z: float = 0.21
    layer2_capac: float = 1.56e6
    layer2_rho: float = 1430.0
    layer2_alphaT_perp: float = 28e-6
    layer2_alphaT_para: float = 120e-6
    layer2_C11_0: float = 8.9e9
    layer2_C12_0: float = 5.4e9
    layer2_C13_0: float = 5.4e9
    layer2_C33_0: float = 5.6e9
    layer2_C44_0: float = 2.1e9

    # Layer 3 (air)
    layer3_sigma: float = 0.028
    layer3_capac: float = 1192.0

    # Middle points for comparison
    num_middle_points: int = 15


class TransverseIsotropicPlotData(BaseModel):
    model_freqs: list[float]
    in_model: list[float]
    out_model: list[float]
    ratio_model: list[float]
    exp_freqs: list[float]
    in_exp: list[float]
    out_exp: list[float]
    ratio_exp: list[float]


class TransverseIsotropicResult(BaseModel):
    plot_data: TransverseIsotropicPlotData
