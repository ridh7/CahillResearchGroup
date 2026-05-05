import copy
import time
from multiprocessing import Pool, cpu_count

import numpy as np
from scipy import linalg as la
from scipy.optimize import differential_evolution

from .fdpbd.data_processing import calculate_leaking, correct_data, load_data

ANISOTROPIC_FIT_PARAMS = [
    "sigma_x",
    "sigma_y",
    "sigma_z",
    "alphaT_perp",
    "alphaT_para",
]


def simpson_integration(y: np.ndarray, dx: float) -> float:
    """Simpson's rule for equally-spaced data."""
    n = y.size
    if n < 3 or n % 2 == 0:
        raise ValueError("Simpson integration requires odd number of points ≥ 3.")
    res: float = dx / 3 * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum())
    return res


def _compute_single_freq(args):
    """Worker: compute Z[:, :] for one frequency. Must be top-level for pickling."""
    i_f, f, p_vals, psi_vals, pc = args

    n_p = len(p_vals)
    n_psi = len(psi_vals)
    Z_slice = np.zeros((n_p, n_psi), dtype=complex)

    # Unpack precomputed constants to local variables for speed
    Dif1 = pc["Dif1"]
    Dif2 = pc["Dif2"]
    Dif3 = pc["Dif3"]
    L1 = pc["L1"]
    sigma1 = pc["sigma1"]
    sigma2z = pc["sigma2z"]
    sigma3 = pc["sigma3"]
    a0 = pc["a0"]
    w_rms = pc["w_rms"]
    g_int = pc["g_int"]
    C11_0_2 = pc["C11_0_2"]
    C11_1 = pc["C11_1"]
    sigma_x_over_z = pc["sigma_x_over_z"]
    sigma_y_over_z = pc["sigma_y_over_z"]

    C55C11_1 = pc["C55C11_1"]
    C44C11_1 = pc["C44C11_1"]
    C33C11_1 = pc["C33C11_1"]
    C22C11_1 = pc["C22C11_1"]
    C12C11_1 = pc["C12C11_1"]
    C13C11_1 = pc["C13C11_1"]
    C23C11_1 = pc["C23C11_1"]
    C66C11_1 = pc["C66C11_1"]
    C46C11_1 = pc["C46C11_1"]
    betaxC11_1 = pc["betaxC11_1"]
    betayC11_1 = pc["betayC11_1"]
    betazC11_1 = pc["betazC11_1"]
    sqrtC11rho_1 = pc["sqrtC11rho_1"]

    C55C11_2 = pc["C55C11_2"]
    C44C11_2 = pc["C44C11_2"]
    C33C11_2 = pc["C33C11_2"]
    C22C11_2 = pc["C22C11_2"]
    C12C11_2 = pc["C12C11_2"]
    C13C11_2 = pc["C13C11_2"]
    C23C11_2 = pc["C23C11_2"]
    C66C11_2 = pc["C66C11_2"]
    betaxC11_2 = pc["betaxC11_2"]
    betayC11_2 = pc["betayC11_2"]
    betazC11_2 = pc["betazC11_2"]
    sqrtC11rho_2 = pc["sqrtC11rho_2"]

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
            zeta2 = np.sqrt(qn2_2 + k**2 * sigma_x_over_z + xi**2 * sigma_y_over_z)
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

            try:
                eigvals1, Q1 = la.eig(B1, A1)
                N1 = la.solve(A1, D1)
                U1 = la.solve(Q1, N1)
            except (ValueError, la.LinAlgError):
                continue

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

            try:
                eigvals2, Q2_raw = la.eig(B2, A2)
                neg = [i for i, lam in enumerate(eigvals2) if lam.real < 0]
                pos = [i for i, lam in enumerate(eigvals2) if lam.real >= 0]
                idx_order = neg + pos
                Q2 = Q2_raw[:, idx_order]
                L2 = eigvals2[idx_order]
                U2 = la.solve(Q2, la.solve(A2, D2))
            except (ValueError, la.LinAlgError):
                continue

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
                        * (C_s1 / (zeta1 - eigvals1[j]) + C_s2 / (-zeta1 - eigvals1[j]))
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

            # Skip if matrices contain NaN/inf (overflow from extreme params)
            if not (np.all(np.isfinite(BCM)) and np.all(np.isfinite(BCC))):
                Z_slice[i_p, i_psi] = 0.0 + 0.0j
                continue

            try:
                J = la.solve(BCM, BCC)
            except (ValueError, la.LinAlgError):
                Z_slice[i_p, i_psi] = 0.0 + 0.0j
                continue

            w_H = sum(Q1[2, m] * J[m] for m in range(6))
            w_P = sum(
                Q1[2, j]
                * U1[j]
                * (C_s1 / (zeta1 - eigvals1[j]) + C_s2 / (-zeta1 - eigvals1[j]))
                for j in range(6)
            )

            Z_slice[i_p, i_psi] = -(w_H + w_P)

    return i_f, Z_slice


def compute_surface_displacement(
    freqs: np.ndarray,
    p_vals: np.ndarray,
    psi_vals: np.ndarray,
    params: dict,
    parallel: bool = True,
) -> np.ndarray:
    """Build and solve the 9×9 thermo-elastic boundary-condition system."""
    n_p, n_psi, n_f = len(p_vals), len(psi_vals), len(freqs)

    # Extract parameters and precompute all constants once
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
    C11_1 = (C11_0_1 + C12_0_1 + 2 * C44_0_1) / 2
    C44_1 = (C11_0_1 - C12_0_1 + C44_0_1) / 3
    C12_1 = (C11_0_1 + 5 * C12_0_1 - 2 * C44_0_1) / 6
    C13_1 = (C11_0_1 + 2 * C12_0_1 - 4 * C44_0_1) / 3
    C33_1 = (C11_0_1 + 2 * C12_0_1 + 4 * C44_0_1) / 3
    C22_1 = C11_1
    C23_1 = C13_1
    C55_1 = C44_1
    C66_1 = (C11_1 - C12_1) / 2

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

    # Pack all precomputed constants into a dict for the worker
    precomputed = {
        "Dif1": Dif1,
        "Dif2": Dif2,
        "Dif3": Dif3,
        "L1": L1,
        "sigma1": sigma1,
        "sigma2z": sigma2z,
        "sigma3": sigma3,
        "a0": a0,
        "w_rms": w_rms,
        "g_int": g_int,
        "C11_0_2": C11_0_2,
        "C11_1": C11_1,
        "sigma_x_over_z": layer2["sigma_x"] / layer2["sigma_z"],
        "sigma_y_over_z": layer2["sigma_y"] / layer2["sigma_z"],
        # Layer 1 normalized constants
        "C55C11_1": C55_1 / C11_1,
        "C44C11_1": C44_1 / C11_1,
        "C33C11_1": C33_1 / C11_1,
        "C22C11_1": C22_1 / C11_1,
        "C12C11_1": C12_1 / C11_1,
        "C13C11_1": C13_1 / C11_1,
        "C23C11_1": C23_1 / C11_1,
        "C66C11_1": C66_1 / C11_1,
        "C46C11_1": 0.0,
        "betaxC11_1": beta1 / C11_1,
        "betayC11_1": beta1 / C11_1,
        "betazC11_1": beta1 / C11_1,
        "sqrtC11rho_1": np.sqrt(C11_1 / layer1["rho"]),
        # Layer 2 normalized constants
        "C55C11_2": C55_2 / C11_2,
        "C44C11_2": C44_2 / C11_2,
        "C33C11_2": C33_2 / C11_2,
        "C22C11_2": C22_2 / C11_2,
        "C12C11_2": C12_2 / C11_2,
        "C13C11_2": C13_2 / C11_2,
        "C23C11_2": C23_2 / C11_2,
        "C66C11_2": C66_2 / C11_2,
        "betaxC11_2": betax2 / C11_2,
        "betayC11_2": betay2 / C11_2,
        "betazC11_2": betaz2 / C11_2,
        "sqrtC11rho_2": np.sqrt((1 + 1e-6j) * C11_2 / layer2["rho"]),
    }

    # Build args for each frequency
    args_list = [(i_f, f, p_vals, psi_vals, precomputed) for i_f, f in enumerate(freqs)]

    # Compute across frequencies
    if parallel:
        n_workers = min(cpu_count(), n_f)
        with Pool(n_workers) as pool:
            results = pool.map(_compute_single_freq, args_list)
    else:
        results = [_compute_single_freq(args) for args in args_list]

    # Assemble Z array from worker results
    Z = np.zeros((n_p, n_psi, n_f), dtype=complex)
    for i_f, Z_slice in results:
        Z[:, :, i_f] = Z_slice

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
            ratio_at_fmax = float(np.exp(np.polyval(p_r, log_fmax_val)))
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
        "laser_option": str(params.get("laser_option", "TOPS 2")),
        "f_rolloff": float(params.get("f_rolloff", 95e3)),
        "delay_0": float(params.get("delay_0", 0.0)),
        "delay_1": float(params.get("delay_1", 0.0)),
        "delay_2": float(params.get("delay_2", 0.0)),
        "amplitude_corrected_0": float(params.get("amplitude_corrected_0", 0.0)),
        "amplitude_corrected_1": float(params.get("amplitude_corrected_1", 0.0)),
        "amplitude_corrected_2": float(params.get("amplitude_corrected_2", 0.0)),
        "amplitude_corrected_3": float(params.get("amplitude_corrected_3", 0.0)),
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
        transformed_params["laser_option"],
        f_rolloff=transformed_params["f_rolloff"],
        delay_0=transformed_params["delay_0"],
        delay_1=transformed_params["delay_1"],
        delay_2=transformed_params["delay_2"],
        amplitude_corrected_0=transformed_params["amplitude_corrected_0"],
        amplitude_corrected_1=transformed_params["amplitude_corrected_1"],
        amplitude_corrected_2=transformed_params["amplitude_corrected_2"],
        amplitude_corrected_3=transformed_params["amplitude_corrected_3"],
    )

    # Correct data
    v_corr_in, v_corr_out, v_corr_ratio = correct_data(v_out, v_in, complex_leaking)

    # Average sum voltage
    v_sum_avg = float(np.mean(v_sum))

    # Build p and psi grids
    up_p = 8 / transformed_params["w_rms"]
    d_p = up_p / n_p
    p_vals = np.linspace(d_p, up_p, n_p)
    up_psi = np.pi / 2
    psi_vals = np.linspace(0, up_psi, n_psi)

    # Compute model (with timing)
    t0 = time.time()
    Z = compute_surface_displacement(model_freqs, p_vals, psi_vals, transformed_params)
    t1 = time.time()
    pbd_angles = compute_probe_deflection(
        Z, p_vals, psi_vals, model_freqs, transformed_params
    )
    t2 = time.time()
    in_mod, out_mod, ratio_mod = compute_lockin_signals(
        pbd_angles, v_sum_avg, transformed_params["detector_factor"]
    )
    t3 = time.time()
    print(f"[anisotropic] compute_surface_displacement: {t1 - t0:.3f}s")
    print(f"[anisotropic] compute_probe_deflection:     {t2 - t1:.3f}s")
    print(f"[anisotropic] compute_lockin_signals:        {t3 - t2:.3f}s")
    print(f"[anisotropic] TOTAL forward model:           {t3 - t0:.3f}s")

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


def run_de_fitting_anisotropic(
    params: dict,
    data_filename: str,
    fit_param: str,
    bounds: tuple[float, float],
    progress_callback=None,
    maxiter: int = 20,
    popsize: int = 8,
    tol: float = 1e-3,
) -> dict:
    """Run DE fitting for a single anisotropic layer2 parameter."""
    if fit_param not in ANISOTROPIC_FIT_PARAMS:
        raise ValueError(
            f"Unknown fit parameter: {fit_param}. Must be one of {ANISOTROPIC_FIT_PARAMS}"
        )

    # Same setup as run_anisotropic_analysis
    c_probe = 0.7
    g_int = 100e6
    n_p = 63
    n_psi = 45
    model_freqs = np.logspace(np.log10(100e3), np.log10(100), 10)

    transformed_params = {
        "laser_option": str(params.get("laser_option", "TOPS 2")),
        "f_rolloff": float(params.get("f_rolloff", 95e3)),
        "delay_0": float(params.get("delay_0", 0.0)),
        "delay_1": float(params.get("delay_1", 0.0)),
        "delay_2": float(params.get("delay_2", 0.0)),
        "amplitude_corrected_0": float(params.get("amplitude_corrected_0", 0.0)),
        "amplitude_corrected_1": float(params.get("amplitude_corrected_1", 0.0)),
        "amplitude_corrected_2": float(params.get("amplitude_corrected_2", 0.0)),
        "amplitude_corrected_3": float(params.get("amplitude_corrected_3", 0.0)),
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

    # Load and correct data
    v_out, v_in, _, v_sum, freq = load_data(data_filename)
    complex_leaking = calculate_leaking(
        freq,
        transformed_params["laser_option"],
        f_rolloff=transformed_params["f_rolloff"],
        delay_0=transformed_params["delay_0"],
        delay_1=transformed_params["delay_1"],
        delay_2=transformed_params["delay_2"],
        amplitude_corrected_0=transformed_params["amplitude_corrected_0"],
        amplitude_corrected_1=transformed_params["amplitude_corrected_1"],
        amplitude_corrected_2=transformed_params["amplitude_corrected_2"],
        amplitude_corrected_3=transformed_params["amplitude_corrected_3"],
    )
    v_corr_in, v_corr_out, v_corr_ratio = correct_data(v_out, v_in, complex_leaking)
    v_sum_avg = float(np.mean(v_sum))

    # Build grids
    up_p = 8 / transformed_params["w_rms"]
    d_p = up_p / n_p
    p_vals = np.linspace(d_p, up_p, n_p)
    psi_vals = np.linspace(0, np.pi / 2, n_psi)

    # Interpolate experimental data to model frequencies for cost comparison
    exp_in_interp = np.interp(model_freqs, freq[::-1], v_corr_in[::-1])
    exp_out_interp = np.interp(model_freqs, freq[::-1], v_corr_out[::-1])

    gen_count = [0]
    t_start = time.time()

    def objective(x):
        try:
            trial_params = copy.deepcopy(transformed_params)
            trial_params["layer2"][fit_param] = x[0]

            Z = compute_surface_displacement(
                model_freqs, p_vals, psi_vals, trial_params, parallel=True
            )
            angles = compute_probe_deflection(
                Z, p_vals, psi_vals, model_freqs, trial_params
            )
            in_mod, out_mod, _ = compute_lockin_signals(
                angles, v_sum_avg, trial_params["detector_factor"]
            )

            if np.isnan(in_mod).any() or np.isnan(out_mod).any():
                return 1e12

            cost = float(
                np.sum((in_mod - exp_in_interp) ** 2)
                + np.sum((out_mod - exp_out_interp) ** 2)
            )
            return cost
        except Exception as e:
            print(f"[anisotropic-fit] OBJECTIVE ERROR: {type(e).__name__}: {e}")
            return 1e12

    def callback(xk, convergence):
        gen_count[0] += 1
        elapsed = time.time() - t_start
        print(
            f"[anisotropic-fit] Gen {gen_count[0]}: "
            f"{fit_param}={xk[0]:.6e}, convergence={convergence:.4e}, "
            f"elapsed={elapsed:.1f}s"
        )
        if progress_callback:
            progress_callback(
                {
                    "type": "progress",
                    "generation": gen_count[0],
                    "best_value": float(xk[0]),
                    "convergence": float(convergence),
                    "elapsed": round(elapsed, 1),
                }
            )

    result = differential_evolution(
        objective,
        bounds=[bounds],
        callback=callback,
        seed=42,
        tol=tol,
        maxiter=maxiter,
        popsize=popsize,
    )

    # Run final forward model with best params
    final_params = copy.deepcopy(transformed_params)
    final_params["layer2"][fit_param] = result.x[0]

    Z = compute_surface_displacement(
        model_freqs, p_vals, psi_vals, final_params, parallel=True
    )
    angles = compute_probe_deflection(Z, p_vals, psi_vals, model_freqs, final_params)
    in_mod, out_mod, ratio_mod = compute_lockin_signals(
        angles, v_sum_avg, final_params["detector_factor"]
    )
    f_peak, ratio_at_peak = fit_rough_analysis(model_freqs, out_mod, ratio_mod)

    total_time = time.time() - t_start
    print(f"[anisotropic-fit] DONE in {total_time:.1f}s: {fit_param}={result.x[0]:.6e}")

    return {
        "type": "result",
        "fit_param": fit_param,
        "best_value": float(result.x[0]),
        "cost": float(result.fun),
        "success": bool(result.success),
        "generations": gen_count[0],
        "elapsed": round(total_time, 1),
        "f_peak": float(f_peak) if not np.isnan(f_peak) else None,
        "ratio_at_peak": float(ratio_at_peak) if not np.isnan(ratio_at_peak) else None,
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
