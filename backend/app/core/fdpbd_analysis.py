import numpy as np
from app.core.fdpbd.data_processing import load_data, correct_data, calculate_leaking
from app.core.fdpbd.fitting import fit_in_out
from app.core.fdpbd.thermal_model import compute_steady_state_heat, delta_bo_theta


def run_fdpbd_analysis(params, data_filename):
    """Run FD-PBD analysis with given parameters and data file."""
    # Extract parameters
    f_amp = params["f_amp"]
    delay_1 = params["delay_1"]
    delay_2 = params["delay_2"]
    lambda_down = np.array(params["lambda_down"])
    eta_down = np.array(params["eta_down"])
    c_down = np.array(params["c_down"])
    h_down = np.array(params["h_down"])
    niu = params["niu"]
    alpha_t = params["alpha_t"]
    lambda_up = params["lambda_up"]
    eta_up = params["eta_up"]
    c_up = params["c_up"]
    h_up = params["h_up"]
    w_rms = params["w_rms"]
    x_offset = params["x_offset"]
    r_pump = w_rms
    r_probe = w_rms
    incident_pump = params["incident_pump"]
    incident_probe = params["incident_probe"]
    n_al = params["n_al"]
    k_al = params["k_al"]
    lens_transmittance = params["lens_transmittance"]
    detector_gain = params["detector_gain"]

    # Derived parameters
    refl_al = abs(n_al - 1 + 1j * k_al) ** 2 / abs(n_al + 1 + 1j * k_al) ** 2
    absorbed_pump = 1 - refl_al
    a_pump = incident_pump * lens_transmittance * 4.0 / np.pi * absorbed_pump
    a_dc = (incident_pump + incident_probe) * absorbed_pump

    # Load data
    v_out, v_in, v_ratio, v_sum, freq = load_data(data_filename)

    # Calculate leaking correction
    complex_leaking = calculate_leaking(freq, f_amp, delay_1, delay_2)

    # Correct data
    v_corr_in, v_corr_out, v_corr_ratio = correct_data(v_out, v_in, complex_leaking)

    # Calculate average sum voltage
    v_sum_avg = np.mean(v_sum)
    coef = alpha_t * detector_gain * v_sum_avg / np.sqrt(2)  # For 10x objective

    # Compute steady-state heating
    t_ss_heat = compute_steady_state_heat(
        lambda_down,
        c_down,
        h_down,
        eta_down,
        lambda_up,
        c_up,
        h_up,
        eta_up,
        r_pump,
        r_probe,
        a_dc,
    )

    # Determine fitting frequency range
    idx_peak = np.argmax(np.abs(v_corr_out))
    fc = freq[idx_peak]
    mask = (freq >= fc / 10) & (freq <= fc * 10)
    freq_fit = freq[mask]
    v_corr_in_fit = v_corr_in[mask]
    v_corr_out_fit = v_corr_out[mask]
    v_corr_ratio_fit = v_corr_ratio[mask]

    # Perform fitting
    x_guess = [lambda_down[2], coef]
    lb = [0.0, -100.0]
    ub = [100.0, 100.0]
    x_sol, confidence = fit_in_out(
        x_guess,
        v_corr_in_fit,
        v_corr_out_fit,
        niu,
        freq_fit,
        lambda_down,
        c_down,
        h_down,
        eta_down,
        lambda_up,
        c_up,
        h_up,
        eta_up,
        r_pump,
        r_probe,
        a_pump,
        x_offset,
        lb,
        ub,
    )
    lambda_measure = x_sol[0]
    coef_fitted = x_sol[1]
    alpha_t_fitted = coef_fitted / (detector_gain * v_sum_avg / np.sqrt(2))

    # Compute model for plotting
    delta_theta = delta_bo_theta(
        niu,
        coef_fitted,
        freq_fit,
        lambda_down,
        c_down,
        h_down,
        eta_down,
        lambda_up,
        c_up,
        h_up,
        eta_up,
        r_pump,
        r_probe,
        a_pump,
        x_offset,
    )
    delta_in = np.real(delta_theta)
    delta_out = np.imag(delta_theta)
    delta_ratio = -delta_in / delta_out

    # Return results
    return {
        "lambda_measure": lambda_measure,
        "alpha_t_fitted": alpha_t_fitted,
        "t_ss_heat": t_ss_heat,
        "plot_data": {
            "freq_fit": freq_fit.tolist(),
            "v_corr_in_fit": v_corr_in_fit.tolist(),
            "v_corr_out_fit": v_corr_out_fit.tolist(),
            "v_corr_ratio_fit": v_corr_ratio_fit.tolist(),
            "delta_in": delta_in.tolist(),
            "delta_out": delta_out.tolist(),
            "delta_ratio": delta_ratio.tolist(),
        },
    }
