import numpy as np
from scipy import linalg as la
from app.core.fdpbd.data_processing import load_data, calculate_leaking, correct_data


def simpson_integration(y: np.ndarray, dx: float) -> float:
    """Simpson’s rule for equally-spaced data."""
    n = y.size
    if n < 3 or n % 2 == 0:
        raise ValueError("Simpson integration requires odd number of points ≥ 3.")
    return dx / 3 * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum())


def compute_surface_displacement(
    freqs: np.ndarray, p_vals: np.ndarray, psi_vals: np.ndarray, params: dict
) -> np.ndarray:
    """Build and solve the 9×9 thermo-elastic boundary-condition system."""
    n_p, n_psi, n_f = len(p_vals), len(psi_vals), len(freqs)
    Z = np.zeros((n_p, n_psi, n_f), dtype=complex)

    # Extract parameters
    layer1 = params["layer1"]
    layer2 = params["layer2"]
    layer3 = params["layer3"]
    g_int = params["g_int"]
    incident_pump = params["incident_pump"]
    lens_transmittance = params["lens_transmittance"]
    w_rms = params["w_rms"]
    n_al, k_al = params["n_al"], params["k_al"]
    a0 = (
        incident_pump
        * lens_transmittance
        * (4.0 / np.pi)
        * (1.0 - abs((n_al - 1 + 1j * k_al) / (n_al + 1 + 1j * k_al)) ** 2)
    )

    # Precompute thermal diffusivities
    Dif1 = layer1["sigma"] / layer1["capac"]
    Dif2 = layer2["sigma_z"] / layer2["capac"]
    Dif3 = layer3["sigma"] / layer3["capac"]
    L1 = layer1["thickness"]
    sigma1 = layer1["sigma"]
    sigma2z = layer2["sigma_z"]
    sigma3 = layer3["sigma"]

    # Layer 1 effective elastic constants
    C11_0_1, C12_0_1, C44_0_1 = (layer1["C11_0"], layer1["C12_0"], layer1["C44_0"])
    alpha1 = layer1["alphaT"]
    beta1 = (C11_0_1 + 2 * C12_0_1) * alpha1
    betax1 = betay1 = betaz1 = beta1
    C11_1 = (C11_0_1 + C12_0_1 + 2 * C44_0_1) / 2
    C33_1 = (C11_0_1 + 2 * C12_0_1 + 4 * C44_0_1) / 3
    C44_1 = (C11_0_1 - C12_0_1 + C44_0_1) / 3
    C12_1 = (C11_0_1 + 5 * C12_0_1 - 2 * C44_0_1) / 6
    C13_1 = (C11_0_1 + 2 * C12_0_1 - 4 * C44_0_1) / 3
    C46_1 = 0.0
    C22_1 = C11_1
    C23_1 = C13_1
    C55_1 = C44_1
    C66_1 = (C11_1 - C12_1) / 2

    C22C11_1 = C22_1 / C11_1
    C33C11_1 = C33_1 / C11_1
    C12C11_1 = C12_1 / C11_1
    C13C11_1 = C13_1 / C11_1
    C23C11_1 = C23_1 / C11_1
    C44C11_1 = C44_1 / C11_1
    C55C11_1 = C55_1 / C11_1
    C66C11_1 = C66_1 / C11_1
    C46C11_1 = 0.0
    betaxC11_1 = betax1 / C11_1
    betayC11_1 = betay1 / C11_1
    betazC11_1 = betaz1 / C11_1
    sqrtC11rho_1 = np.sqrt(C11_1 / layer1["rho"])

    # Layer 2 effective elastic constants & betas
    C11_0_2 = layer2["C11_0"]
    C12_0_2 = layer2["C12_0"]
    C13_0_2 = layer2["C13_0"]
    C33_0_2 = layer2["C33_0"]
    C44_0_2 = layer2["C44_0"]
    alpha_v = layer2["alphaT_perp"]
    alpha_p = layer2["alphaT_para"]
    betax2 = (C11_0_2 + C12_0_2) * alpha_v + C13_0_2 * alpha_p
    betay2 = 2 * C13_0_2 * alpha_v + C33_0_2 * alpha_p
    betaz2 = betax2

    C11_2 = C11_0_2
    C22_2 = C33_0_2
    C33_2 = C11_0_2
    C12_2 = C13_0_2
    C13_2 = C12_0_2
    C23_2 = C13_0_2
    C44_2 = C44_0_2
    C55_2 = (C11_0_2 - C12_0_2) / 2
    C66_2 = C44_0_2

    C22C11_2 = C22_2 / C11_2
    C33C11_2 = C33_2 / C11_2
    C12C11_2 = C12_2 / C11_2
    C13C11_2 = C13_2 / C11_2
    C23C11_2 = C23_2 / C11_2
    C44C11_2 = C44_2 / C11_2
    C55C11_2 = C55_2 / C11_2
    C66C11_2 = C66_2 / C11_2
    betaxC11_2 = betax2 / C11_2
    betayC11_2 = betay2 / C11_2
    betazC11_2 = betaz2 / C11_2
    sqrtC11rho_2 = np.sqrt((1 + 1e-6j) * C11_2 / layer2["rho"])

    for i_f, f in enumerate(freqs):
        ω = 2 * np.pi * f
        qn2_1 = 1j * ω / Dif1
        qn2_2 = 1j * ω / Dif2
        qn2_3 = 1j * ω / Dif3

        for i_p, p in enumerate(p_vals):
            flx = a0 * np.exp(-(w_rms**2) * p**2 / 8)

            for i_psi, psi in enumerate(psi_vals):
                k = p * np.cos(psi)
                xi = p * np.sin(psi)

                zeta1 = np.sqrt(qn2_1 + p**2)
                zeta2 = np.sqrt(
                    qn2_2
                    + k**2 * layer2["sigma_x"] / layer2["sigma_z"]
                    + xi**2 * layer2["sigma_y"] / layer2["sigma_z"]
                )
                zeta3 = np.sqrt(qn2_3 + p**2)

                # Thermal boundary G
                z1L = zeta1 * L1
                s1z = sigma1 * zeta1
                s2z = sigma2z * zeta2
                s3z = sigma3 * zeta3

                G_d = (
                    s2z * np.sinh(z1L)
                    + s1z * np.cosh(z1L)
                    + s1z * s2z / g_int * np.cosh(z1L)
                ) / s1z
                G_d /= (
                    s2z * np.cosh(z1L)
                    + s1z * np.sinh(z1L)
                    + s1z * s2z / g_int * np.sinh(z1L)
                )
                G_u = 1.0 / s3z
                G = 1.0 / (1.0 / G_u + 1.0 / G_d)

                θ_s = flx * G
                θ_bs = (
                    np.cosh(z1L) * θ_s
                    + s1z / g_int * np.sinh(z1L) * θ_s
                    - np.sinh(z1L) * flx / s1z
                    - np.cosh(z1L) * flx / g_int
                )

                C_s1 = (s2z / g_int * θ_bs + θ_bs - θ_s * np.exp(-z1L)) / (
                    np.exp(z1L) - np.exp(-z1L)
                )
                C_s2 = θ_s - C_s1

                # Layer1 matrices A1, B1, D1
                A1 = np.zeros((6, 6), dtype=complex)
                B1 = np.zeros((6, 6), dtype=complex)
                D1 = np.zeros(6, dtype=complex)

                A1[0, 3] = A1[1, 4] = A1[2, 5] = 1.0
                A1[3, 0] = C55C11_1
                A1[4, 1] = C44C11_1
                A1[5, 2] = C33C11_1
                B1[3, 3] = B1[4, 4] = B1[5, 5] = 1.0
                D1[5] = betazC11_1

                A1[0, 0] = -C46C11_1 * 1j * k
                A1[1, 1] = C46C11_1 * 1j * k
                A1[0, 1] = C46C11_1 * 1j * xi
                A1[1, 0] = C46C11_1 * 1j * xi
                A1[0, 2] = C13C11_1 * 1j * k
                A1[1, 2] = C23C11_1 * 1j * xi

                B1[0, 0] = k**2 + C66C11_1 * xi**2 - ω**2 / sqrtC11rho_1**2
                B1[1, 1] = C22C11_1 * xi**2 + C66C11_1 * k**2 - ω**2 / sqrtC11rho_1**2
                B1[0, 1] = B1[1, 0] = (C12C11_1 + C66C11_1) * k * xi
                B1[2, 2] = -(ω**2) / sqrtC11rho_1**2
                B1[0, 2] = C46C11_1 * (xi**2 - k**2)
                B1[1, 2] = 2 * C46C11_1 * k * xi
                B1[2, 3] = -1j * k
                B1[2, 4] = -1j * xi
                B1[3, 0] = C46C11_1 * 1j * k
                B1[3, 1] = -C46C11_1 * 1j * xi
                B1[3, 2] = -C55C11_1 * 1j * k
                B1[4, 0] = -C46C11_1 * 1j * xi
                B1[4, 1] = -C46C11_1 * 1j * k
                B1[4, 2] = -C44C11_1 * 1j * xi
                B1[5, 0] = -C13C11_1 * 1j * k
                B1[5, 1] = -C23C11_1 * 1j * xi

                D1[0] = betaxC11_1 * 1j * k
                D1[1] = betayC11_1 * 1j * xi

                eigvals1, Q1 = la.eig(B1, A1)
                N1 = la.solve(A1, D1)
                U1 = la.solve(Q1, N1)

                # Layer2 matrices A2, B2, D2
                A2 = np.zeros((6, 6), dtype=complex)
                B2 = np.zeros((6, 6), dtype=complex)
                D2 = np.zeros(6, dtype=complex)

                A2[0, 3] = 1.0
                A2[1, 4] = 1.0
                A2[2, 5] = 1.0
                A2[3, 0] = C55C11_2
                A2[4, 1] = C44C11_2
                A2[5, 2] = C33C11_2
                B2[3, 3] = 1.0
                B2[4, 4] = 1.0
                B2[5, 5] = 1.0

                D2[0] = betaxC11_2 * 1j * k
                D2[1] = betayC11_2 * 1j * xi
                D2[5] = betazC11_2

                A2[0, 2] = C13C11_2 * 1j * k
                A2[1, 2] = C23C11_2 * 1j * xi

                B2[0, 0] = k**2 + C66C11_2 * xi**2 - ω**2 / sqrtC11rho_2**2
                B2[1, 1] = C22C11_2 * xi**2 + C66C11_2 * k**2 - ω**2 / sqrtC11rho_2**2
                B2[0, 1] = B2[1, 0] = (C12C11_2 + C66C11_2) * k * xi
                B2[2, 2] = -(ω**2) / sqrtC11rho_2**2
                B2[2, 3] = -1j * k
                B2[2, 4] = -1j * xi
                B2[3, 2] = -C55C11_2 * 1j * k
                B2[4, 2] = -C44C11_2 * 1j * xi
                B2[5, 0] = -C13C11_2 * 1j * k
                B2[5, 1] = -C23C11_2 * 1j * xi

                D2[0] = betaxC11_2 * 1j * k
                D2[1] = betayC11_2 * 1j * xi

                eigvals2, Q2_raw = la.eig(B2, A2)
                neg = [i for i, lam in enumerate(eigvals2) if lam.real < 0]
                pos = [i for i, lam in enumerate(eigvals2) if lam.real >= 0]
                idx_order = neg + pos
                Q2 = Q2_raw[:, idx_order]
                L2 = eigvals2[idx_order]
                U2 = la.solve(Q2, la.solve(A2, D2))

                # Build 9×9 BCM & BCC
                BCM = np.zeros((9, 9), dtype=complex)
                BCC = np.zeros(9, dtype=complex)

                for m in range(6):
                    BCM[0:3, m] = Q1[3:6, m]
                    BCM[3:9, m] = Q1[0:6, m] * np.exp(eigvals1[m] * L1)

                for m in range(3):
                    BCM[3:6, 6 + m] = -Q2[0:3, m] * np.exp(L2[m] * L1)
                    BCM[6:9, 6 + m] = -C11_0_2 / C11_1 * Q2[3:6, m] * np.exp(L2[m] * L1)

                for rw in range(3):
                    s = 0
                    for j in range(6):
                        s += (
                            Q1[rw + 3, j]
                            * U1[j]
                            * (
                                C_s1 / (zeta1 - eigvals1[j])
                                + C_s2 / (-zeta1 - eigvals1[j])
                            )
                        )
                    BCC[rw] = -s

                for rw in range(3, 6):
                    s1 = s2 = 0
                    for j in range(6):
                        temp1 = (
                            Q1[rw - 3, j]
                            * U1[j]
                            * (
                                C_s1 * np.exp(z1L) / (zeta1 - eigvals1[j])
                                + C_s2 * np.exp(-z1L) / (-zeta1 - eigvals1[j])
                            )
                        )
                        temp2 = Q2[rw - 3, j] * U2[j] * (θ_bs / (-zeta2 - L2[j]))
                        s1 += temp1
                        s2 += temp2
                    BCC[rw] = -s1 + s2

                for rw in range(6, 9):
                    s1 = s2 = 0
                    for j in range(6):
                        s1 += (
                            Q1[rw - 3, j]
                            * U1[j]
                            * (
                                C_s1 * np.exp(z1L) / (zeta1 - eigvals1[j])
                                + C_s2 * np.exp(-z1L) / (-zeta1 - eigvals1[j])
                            )
                        )
                        s2 += Q2[rw - 3, j] * U2[j] * (θ_bs / (-zeta2 - L2[j]))
                    BCC[rw] = -s1 + (C11_0_2 / C11_1) * s2

                J = la.solve(BCM, BCC)

                w_H = sum(Q1[2, m] * J[m] for m in range(6))
                w_P = sum(
                    Q1[2, j]
                    * U1[j]
                    * (C_s1 / (zeta1 - eigvals1[j]) + C_s2 / (-zeta1 - eigvals1[j]))
                    for j in range(6)
                )

                Z[i_p, i_psi, i_f] = -(w_H + w_P)

    return Z


def compute_probe_deflection(
    Z: np.ndarray,
    p_vals: np.ndarray,
    psi_vals: np.ndarray,
    freqs: np.ndarray,
    params: dict,
) -> np.ndarray:
    """Integrate Z(p,ψ,ω) over ψ and p to yield probe-beam deflection angle."""
    n_p, n_psi, n_f = Z.shape
    d_psi = psi_vals[1] - psi_vals[0]
    d_p = p_vals[1] - p_vals[0]
    w_rms = params["w_rms"]
    r_0 = params["r_0"]
    phi = params["phi"]
    c_probe = params["c_probe"]

    angles = np.zeros(n_f, dtype=complex)

    for i_f in range(n_f):
        I_p = np.zeros(n_p, dtype=complex)
        for i_p, p in enumerate(p_vals):
            integrand = np.zeros(n_psi, dtype=complex)
            for i_psi, psi in enumerate(psi_vals):
                g = -np.cos(psi - phi) * np.sin(p * r_0 * np.cos(psi - phi)) - np.cos(
                    psi + phi
                ) * np.sin(p * r_0 * np.cos(psi + phi))
                integrand[i_psi] = Z[i_p, i_psi, i_f] * g
            Iψ = (1 / np.pi) * simpson_integration(integrand, d_psi)
            I_p[i_p] = Iψ * np.exp(-(w_rms**2) * p**2 / 8) * p**2
        angles[i_f] = (1 / np.pi) * c_probe * simpson_integration(I_p, d_p)

    return angles


def compute_lockin_signals(
    angles: np.ndarray, v_sum_avg: float, detector_factor: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert deflection angles into lock-in signals."""
    raw = angles / np.sqrt(2) * 0.5 * detector_factor * v_sum_avg
    in_phase = np.abs(np.real(raw))
    out_phase = -np.imag(raw)
    ratio = np.full_like(in_phase, np.nan)
    nonzero = out_phase != 0
    ratio[nonzero] = -in_phase[nonzero] / out_phase[nonzero]
    return in_phase, out_phase, ratio


def fit_rough_analysis(
    freqs: np.ndarray, out_of_phase: np.ndarray, ratio: np.ndarray
) -> tuple[float, float]:
    """Find peak out-of-phase frequency and ratio at that frequency."""
    f_max = np.nan
    ratio_at_fmax = np.nan

    try:
        log_f = np.log(freqs)
        p_op = np.polyfit(log_f, out_of_phase, 2)
        if p_op[0] != 0:
            f_max = np.exp(-p_op[1] / (2 * p_op[0]))
    except (np.linalg.LinAlgError, ValueError):
        pass

    if not np.isnan(f_max):
        try:
            log_r = np.log(ratio)
            p_r = np.polyfit(log_f, log_r, 1)
            log_fmax_val = np.log(f_max)
            ratio_at_fmax = np.exp(np.polyval(p_r, log_fmax_val))
        except (np.linalg.LinAlgError, ValueError):
            pass

    return f_max, ratio_at_fmax


def run_anisotropic_analysis(params: dict, data_filename: str) -> dict:
    """Run anisotropic FD-PBD analysis with given parameters and data file."""
    # Fixed parameters
    c_probe = 0.7
    g_int = 100e6
    n_p = 63
    n_psi = 45
    model_freqs = np.logspace(np.log10(100e3), np.log10(100), 10)

    # Transform frontend parameters
    transformed_params = {
        "f_amp": float(params["f_amp"]),
        "delay_1": float(params["delay_1"]),
        "delay_2": float(params["delay_2"]),
        "incident_pump": float(params["incident_pump"]),
        "w_rms": float(params["w_rms"]),
        "r_0": float(params["x_offset"]),
        "phi": float(params["phi"]),
        "lens_transmittance": float(params["lens_transmittance"]),
        "detector_factor": float(params["detector_factor"]),
        "n_al": float(params["n_al"]),
        "k_al": float(params["k_al"]),
        "c_probe": c_probe,
        "g_int": g_int,
        "n_p": n_p,
        "n_psi": n_psi,
        "model_freqs": model_freqs.tolist(),
        "layer1": {
            "thickness": float(params["h_down"][0]),
            "sigma": float(params["lambda_down"][0]),
            "capac": float(params["c_down"][0]),
            "rho": float(params["rho"]),
            "alphaT": float(params["alphaT"]),
            "C11_0": float(params["C11_0"]),
            "C12_0": float(params["C12_0"]),
            "C44_0": float(params["C44_0"]),
        },
        "layer2": {
            "sigma_x": float(params["lambda_down_x_sample"]),
            "sigma_y": float(params["lambda_down_y_sample"]),
            "sigma_z": float(params["lambda_down_z_sample"]),
            "capac": float(params["c_down"][2]),
            "rho": float(params["rho_sample"]),
            "alphaT_perp": float(params["alphaT_perp"]),
            "alphaT_para": float(params["alphaT_para"]),
            "C11_0": float(params["C11_0_sample"]),
            "C12_0": float(params["C12_0_sample"]),
            "C13_0": float(params["C13_0_sample"]),
            "C33_0": float(params["C33_0_sample"]),
            "C44_0": float(params["C44_0_sample"]),
        },
        "layer3": {
            "sigma": float(params["lambda_up"]),
            "capac": float(params["c_up"]),
        },
    }

    # Load data
    v_out, v_in, _, v_sum, freq = load_data(data_filename)

    # Calculate leaking correction
    complex_leaking = calculate_leaking(
        freq,
        transformed_params["f_amp"],
        transformed_params["delay_1"],
        transformed_params["delay_2"],
    )

    # Correct data
    v_corr_in, v_corr_out, v_corr_ratio = correct_data(v_out, v_in, complex_leaking)

    # Average sum voltage
    v_sum_avg = np.mean(v_sum)

    # Build p and psi grids
    up_p = 8 / transformed_params["w_rms"]
    d_p = up_p / n_p
    p_vals = np.linspace(d_p, up_p, n_p)
    up_psi = np.pi / 2
    psi_vals = np.linspace(0, up_psi, n_psi)

    # Compute model
    Z = compute_surface_displacement(model_freqs, p_vals, psi_vals, transformed_params)
    pbd_angles = compute_probe_deflection(
        Z, p_vals, psi_vals, model_freqs, transformed_params
    )
    in_mod, out_mod, ratio_mod = compute_lockin_signals(
        pbd_angles, v_sum_avg, transformed_params["detector_factor"]
    )

    # Rough analysis
    f_peak, ratio_at_peak = fit_rough_analysis(model_freqs, out_mod, ratio_mod)

    # Return results
    return {
        "f_peak": float(f_peak) if not np.isnan(f_peak) else None,
        "ratio_at_peak": float(ratio_at_peak) if not np.isnan(ratio_at_peak) else None,
        "lambda_measure": None,
        "alpha_t_fitted": None,
        "t_ss_heat": None,
        "plot_data": {
            "model_freqs": model_freqs.tolist(),
            "in_model": in_mod.tolist(),
            "out_model": out_mod.tolist(),
            "ratio_model": ratio_mod.tolist(),
            "exp_freqs": freq.tolist(),
            "in_exp": v_corr_in.tolist(),
            "out_exp": v_corr_out.tolist(),
            "ratio_exp": v_corr_ratio.tolist(),
        },
    }
