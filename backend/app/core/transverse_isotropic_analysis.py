"""
Thermoelastic surface-displacement & probe-beam deflection model
for transversely isotropic material.

Adapted from fdpbd_analysis/main_3.py (MATLAB code2 translation).
Uses single psi=pi/4 and Bessel J1 kernel.
"""

import copy
import time

import numpy as np
import scipy.linalg as la
import scipy.special as sp
from scipy.optimize import differential_evolution

from app.core.anisotropic_analysis import fit_rough_analysis
from app.core.fdpbd.data_processing import calculate_leaking, correct_data, load_data
from app.models.transverse_isotropic import TransverseIsotropicParams  # noqa: E402

TRANSVERSE_FIT_PARAMS = [
    "sigma_r",
    "sigma_z",
    "alphaT_perp",
    "alphaT_para",
]


def simpson_integration(y: np.ndarray, dx: float) -> float:
    """Simpson's rule for equally-spaced data with edge-case handling."""
    n = y.size
    if n < 3:
        if n == 2:
            return dx * (y[0] + y[1]) / 2.0
        elif n == 1:
            return 0.0
        else:
            raise ValueError("Integration requires at least 1 point.")
    if n % 2 == 0:
        raise ValueError("Simpson integration requires odd number of points >= 3.")
    return dx / 3 * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum())


def _safe_div(num, den):
    """Safe division avoiding zero denominators."""
    if den == 0:
        return np.inf * np.sign(num) if num != 0 else 0
    return num / den


def _compute_single_freq_transverse(args):
    """Worker: compute Z[:, i_f] for one frequency (transverse isotropic)."""
    i_f, f, p_vals, pc = args

    n_p = len(p_vals)
    Z_slice = np.zeros(n_p, dtype=complex)

    # Unpack precomputed constants
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
    sigma_r_over_z = pc["sigma_r_over_z"]
    psi = pc["psi"]

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

    omega = 2 * np.pi * f
    qn2_1 = 1j * omega / Dif1
    qn2_2 = 1j * omega / Dif2
    qn2_3 = 1j * omega / Dif3

    for i_p, p in enumerate(p_vals):
        flx = a0 * np.exp(-(w_rms**2) * p**2 / 8)

        k = p * np.cos(psi)
        xi = p * np.sin(psi)

        zeta1 = np.sqrt(qn2_1 + p**2)
        zeta2 = np.sqrt(qn2_2 + p**2 * sigma_r_over_z)
        zeta3 = np.sqrt(qn2_3 + p**2)

        # Thermal boundary G
        z1L = zeta1 * L1
        s1z = sigma1 * zeta1
        s2z = sigma2z * zeta2
        s3z = sigma3 * zeta3

        G_d_num = (
            s2z * np.sinh(z1L) + s1z * np.cosh(z1L) + s1z * s2z / g_int * np.cosh(z1L)
        )
        G_d_den = (
            s2z * np.cosh(z1L) + s1z * np.sinh(z1L) + s1z * s2z / g_int * np.sinh(z1L)
        )

        G_d = np.inf if s1z == 0 or G_d_den == 0 else (G_d_num / s1z) / G_d_den

        G_u = 1.0 / s3z if s3z != 0 else np.inf

        if np.isinf(G_u) and np.isinf(G_d):
            G = 0
        elif np.isinf(G_u):
            G = G_d
        elif np.isinf(G_d):
            G = G_u
        elif (1.0 / G_u + 1.0 / G_d) == 0:
            G = np.inf
        else:
            G = 1.0 / (1.0 / G_u + 1.0 / G_d)

        theta_s = flx * G

        term1 = np.cosh(z1L) * theta_s
        term2 = (s1z / g_int * np.sinh(z1L) * theta_s) if g_int != 0 else 0
        term3 = (np.sinh(z1L) * flx / s1z) if s1z != 0 else 0
        term4 = (np.cosh(z1L) * flx / g_int) if g_int != 0 else 0
        theta_bs = term1 + term2 - term3 - term4

        exp_z1L = np.exp(z1L)
        exp_neg_z1L = np.exp(-z1L)
        denom_cs = exp_z1L - exp_neg_z1L
        if denom_cs == 0:
            C_s1 = 0
        else:
            num_cs1 = (
                (s2z / g_int * theta_bs + theta_bs - theta_s * exp_neg_z1L)
                if g_int != 0
                else (theta_bs - theta_s * exp_neg_z1L)
            )
            C_s1 = num_cs1 / denom_cs

        C_s2 = theta_s - C_s1

        # Layer 1 matrices A1, B1, D1
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
        B1[0, 0] = k**2 + C66C11_1 * xi**2 - omega**2 / sqrtC11rho_1**2
        B1[1, 1] = C22C11_1 * xi**2 + C66C11_1 * k**2 - omega**2 / sqrtC11rho_1**2
        B1[0, 1] = B1[1, 0] = (C12C11_1 + C66C11_1) * k * xi
        B1[2, 2] = -(omega**2) / sqrtC11rho_1**2
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

        # Solve generalized eigenproblem for Layer 1
        try:
            eigvals1, Q1 = la.eig(B1, A1)
            N1 = la.solve(A1, D1)
            U1 = la.solve(Q1, N1)
        except la.LinAlgError:
            Z_slice[i_p] = np.nan
            continue

        # Layer 2 matrices A2, B2, D2
        A2 = np.zeros((6, 6), dtype=complex)
        B2 = np.zeros((6, 6), dtype=complex)
        D2 = np.zeros(6, dtype=complex)

        A2[0, 3] = A2[1, 4] = A2[2, 5] = 1.0
        A2[3, 0] = C55C11_2
        A2[4, 1] = C44C11_2
        A2[5, 2] = C33C11_2
        B2[3, 3] = B2[4, 4] = B2[5, 5] = 1.0
        D2[5] = betazC11_2
        A2[0, 2] = C13C11_2 * 1j * k
        A2[1, 2] = C23C11_2 * 1j * xi
        B2[0, 0] = k**2 + C66C11_2 * xi**2 - omega**2 / sqrtC11rho_2**2
        B2[1, 1] = C22C11_2 * xi**2 + C66C11_2 * k**2 - omega**2 / sqrtC11rho_2**2
        B2[0, 1] = B2[1, 0] = (C12C11_2 + C66C11_2) * k * xi
        B2[2, 2] = -(omega**2) / sqrtC11rho_2**2
        B2[2, 3] = -1j * k
        B2[2, 4] = -1j * xi
        B2[3, 2] = -C55C11_2 * 1j * k
        B2[4, 2] = -C44C11_2 * 1j * xi
        B2[5, 0] = -C13C11_2 * 1j * k
        B2[5, 1] = -C23C11_2 * 1j * xi
        D2[0] = betaxC11_2 * 1j * k
        D2[1] = betayC11_2 * 1j * xi

        # Solve generalized eigenproblem for Layer 2
        try:
            eigvals2_raw, Q2_raw = la.eig(B2, A2)
            neg_idx = [i for i, lam in enumerate(eigvals2_raw) if lam.real < 0]
            pos_idx = [i for i, lam in enumerate(eigvals2_raw) if lam.real >= 0]
            idx_order = neg_idx[:3] + pos_idx[: 6 - len(neg_idx[:3])]

            Q2 = Q2_raw[:, idx_order]
            L2 = eigvals2_raw[idx_order]

            N2 = la.solve(A2, D2)
            U2 = la.solve(Q2, N2)
        except la.LinAlgError:
            Z_slice[i_p] = np.nan
            continue

        # Build 9x9 BCM & BCC
        BCM = np.zeros((9, 9), dtype=complex)
        BCC = np.zeros(9, dtype=complex)

        for m in range(6):
            BCM[0:3, m] = Q1[3:6, m]
            BCM[3:9, m] = Q1[0:6, m] * np.exp(eigvals1[m] * L1)

        for m in range(3):
            BCM[3:6, 6 + m] = -Q2[0:3, m] * np.exp(L2[m] * L1)
            BCM[6:9, 6 + m] = -(C11_0_2 / C11_1) * Q2[3:6, m] * np.exp(L2[m] * L1)

        for rw in range(3):
            s = 0
            for j in range(6):
                s += (
                    Q1[rw + 3, j]
                    * U1[j]
                    * (
                        _safe_div(C_s1, (zeta1 - eigvals1[j]))
                        + _safe_div(C_s2, (-zeta1 - eigvals1[j]))
                    )
                )
            BCC[rw] = -s

        for rw in range(3, 6):
            s1 = s2 = 0
            for j in range(6):
                s1 += (
                    Q1[rw - 3, j]
                    * U1[j]
                    * (
                        _safe_div(C_s1 * exp_z1L, (zeta1 - eigvals1[j]))
                        + _safe_div(C_s2 * exp_neg_z1L, (-zeta1 - eigvals1[j]))
                    )
                )
                s2 += Q2[rw - 3, j] * U2[j] * _safe_div(theta_bs, (-zeta2 - L2[j]))
            BCC[rw] = -s1 + s2

        for rw in range(6, 9):
            s1 = s2 = 0
            for j in range(6):
                s1 += (
                    Q1[rw - 3, j]
                    * U1[j]
                    * (
                        _safe_div(C_s1 * exp_z1L, (zeta1 - eigvals1[j]))
                        + _safe_div(C_s2 * exp_neg_z1L, (-zeta1 - eigvals1[j]))
                    )
                )
                s2 += Q2[rw - 3, j] * U2[j] * _safe_div(theta_bs, (-zeta2 - L2[j]))
            BCC[rw] = -s1 + (C11_0_2 / C11_1) * s2

        # Solve for coefficients J
        try:
            J = la.solve(BCM, BCC)
        except la.LinAlgError:
            Z_slice[i_p] = np.nan
            continue

        # Compute displacement
        w_H = sum(Q1[2, m] * J[m] for m in range(6))
        w_P = sum(
            Q1[2, j]
            * U1[j]
            * (
                _safe_div(C_s1, (zeta1 - eigvals1[j]))
                + _safe_div(C_s2, (-zeta1 - eigvals1[j]))
            )
            for j in range(6)
        )

        Z_slice[i_p] = -(w_H + w_P)

    return i_f, Z_slice


def compute_surface_displacement(
    freqs: np.ndarray,
    p_vals: np.ndarray,
    a0: float,
    w_rms: float,
    g_int: float,
    layer1: dict,
    layer2: dict,
    layer3: dict,
) -> np.ndarray:
    """
    Build and solve the 9x9 thermo-elastic boundary-condition system
    for transversely isotropic case (single psi=pi/4).

    Returns Z[n_p, n_f] complex surface displacement.
    """
    n_p, n_f = len(p_vals), len(freqs)

    # Precompute all constants
    Dif1 = layer1["sigma"] / layer1["capac"]
    Dif2 = layer2["sigma_z"] / layer2["capac"]
    Dif3 = layer3["sigma"] / layer3["capac"]
    L1 = layer1["thickness"]
    sigma1 = layer1["sigma"]
    sigma2z = layer2["sigma_z"]
    sigma2r = layer2["sigma_r"]
    sigma3 = layer3["sigma"]

    # Layer 1 effective elastic constants
    C11_0_1 = layer1["C11_0"]
    C12_0_1 = layer1["C12_0"]
    C44_0_1 = layer1["C44_0"]
    alpha1 = layer1["alphaT"]
    beta1 = (C11_0_1 + 2 * C12_0_1) * alpha1
    C11_1 = (C11_0_1 + C12_0_1 + 2 * C44_0_1) / 2
    C33_1 = (C11_0_1 + 2 * C12_0_1 + 4 * C44_0_1) / 3
    C44_1 = (C11_0_1 - C12_0_1 + C44_0_1) / 3
    C12_1 = (C11_0_1 + 5 * C12_0_1 - 2 * C44_0_1) / 6
    C13_1 = (C11_0_1 + 2 * C12_0_1 - 4 * C44_0_1) / 3
    C22_1 = C11_1
    C23_1 = C13_1
    C55_1 = C44_1
    C66_1 = (C11_1 - C12_1) / 2

    # Layer 2 effective elastic constants
    C11_0_2 = layer2["C11_0"]
    C12_0_2 = layer2["C12_0"]
    C13_0_2 = layer2["C13_0"]
    C33_0_2 = layer2["C33_0"]
    C44_0_2 = layer2["C44_0"]
    alpha_v = layer2["alphaT_perp"]
    alpha_p = layer2["alphaT_para"]
    betax2 = (C11_0_2 + C12_0_2) * alpha_v + C13_0_2 * alpha_p
    betay2 = betax2
    betaz2 = 2 * C13_0_2 * alpha_v + C33_0_2 * alpha_p

    C11_2 = C11_0_2
    C12_2 = C12_0_2
    C13_2 = C13_0_2
    C33_2 = C33_0_2
    C44_2 = C44_0_2
    C22_2 = C11_2
    C23_2 = C13_2
    C55_2 = C44_2
    C66_2 = (C11_0_2 - C12_0_2) / 2

    precomputed = {
        "Dif1": Dif1,
        "Dif2": Dif2,
        "Dif3": Dif3,
        "L1": L1,
        "sigma1": sigma1,
        "sigma2z": sigma2z,
        "sigma2r": sigma2r,
        "sigma3": sigma3,
        "a0": a0,
        "w_rms": w_rms,
        "g_int": g_int,
        "C11_0_2": C11_0_2,
        "C11_1": C11_1,
        "sigma_r_over_z": sigma2r / sigma2z,
        "psi": np.pi / 4,
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

    # Transverse isotropic is lightweight (no psi loop), so run serially
    # to avoid Windows multiprocessing spawn overhead
    Z = np.zeros((n_p, n_f), dtype=complex)
    for i_f, f in enumerate(freqs):
        _, Z_slice = _compute_single_freq_transverse((i_f, f, p_vals, precomputed))
        Z[:, i_f] = Z_slice

    return Z


def compute_probe_deflection(
    Z: np.ndarray,
    p_vals: np.ndarray,
    freqs: np.ndarray,
    w_rms: float,
    r_0: float,
    c_probe: float,
) -> np.ndarray:
    """
    Integrate Z(p,f) using Bessel J1 kernel for transverse isotropy.
    """
    n_p, n_f = Z.shape
    d_p = p_vals[1] - p_vals[0] if n_p > 1 else 0

    angles = np.zeros(n_f, dtype=complex)

    for i_f in range(n_f):
        integrand_p = np.zeros(n_p, dtype=complex)
        for i_p, p in enumerate(p_vals):
            bessel_term = -sp.jv(1, p * r_0)
            integrand_p[i_p] = (
                Z[i_p, i_f] * np.exp(-(w_rms**2) * p**2 / 8) * bessel_term * p**2
            )

        finite_mask = np.isfinite(integrand_p)
        if not np.all(finite_mask):
            if not np.any(finite_mask):
                angles[i_f] = np.nan
                continue
            integrand_p[~finite_mask] = 0.0

        if n_p >= 3 and n_p % 2 != 0:
            angles[i_f] = c_probe / np.pi * simpson_integration(integrand_p, d_p)
        elif n_p > 0:
            angles[i_f] = c_probe / np.pi * np.trapz(integrand_p, dx=d_p)
        else:
            angles[i_f] = 0.0

    return angles


def compute_lockin_signals(
    angles: np.ndarray, v_sum_fixed: float, detector_gain: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert deflection angles into lock-in signals."""
    raw = angles / np.sqrt(2) * 2.0 * detector_gain * v_sum_fixed
    in_phase = np.abs(np.real(raw))
    out_of_phase = -np.imag(raw)
    ratio = np.full_like(in_phase, np.nan)
    nonzero_mask = np.abs(out_of_phase) > 1e-15
    ratio[nonzero_mask] = -in_phase[nonzero_mask] / out_of_phase[nonzero_mask]
    zero_inphase_mask = np.abs(in_phase) < 1e-15
    ratio[nonzero_mask & zero_inphase_mask] = 0.0
    return in_phase, out_of_phase, ratio


def run_transverse_isotropic_analysis(
    params: TransverseIsotropicParams, data_filename: str
) -> dict:
    """Run transversely isotropic FD-PBD analysis."""
    # 1. Load & correct experimental data
    v_out, v_in, _, v_sum, freq = load_data(data_filename)
    complex_leaking = calculate_leaking(
        freq, params.f_rolloff, params.delay_1, params.delay_2
    )
    v_corr_in, v_corr_out, v_corr_ratio = correct_data(v_out, v_in, complex_leaking)

    # 2. Select middle points for comparison
    num_points = len(freq)
    num_middle = params.num_middle_points
    if num_points >= num_middle:
        start_idx = (num_points - num_middle) // 2
        end_idx = start_idx + num_middle
        freq_middle = freq[start_idx:end_idx]
        v_corr_in_middle = v_corr_in[start_idx:end_idx]
        v_corr_out_middle = v_corr_out[start_idx:end_idx]
        v_corr_ratio_middle = v_corr_ratio[start_idx:end_idx]
    else:
        freq_middle = freq
        v_corr_in_middle = v_corr_in
        v_corr_out_middle = v_corr_out
        v_corr_ratio_middle = v_corr_ratio

    # 3. Compute A0 (absorbed pump amplitude)
    refl_al = (
        abs((params.n_al - 1 + 1j * params.k_al) / (params.n_al + 1 + 1j * params.k_al))
        ** 2
    )
    absorbed_pump = 1.0 - refl_al
    a0 = (
        params.incident_pump * params.lens_transmittance * (4.0 / np.pi) * absorbed_pump
    )

    # 4. Build p grid
    up_p = 8 / params.w_rms
    d_p = up_p / params.n_p
    p_vals = np.linspace(d_p, up_p, params.n_p)

    # 5. Model frequencies
    model_freqs = np.logspace(
        np.log10(params.model_freq_start),
        np.log10(params.model_freq_end),
        params.model_freq_points,
    )

    # 6. Build layer dicts
    layer1 = {
        "thickness": params.layer1_thickness,
        "sigma": params.layer1_sigma,
        "capac": params.layer1_capac,
        "rho": params.layer1_rho,
        "alphaT": params.layer1_alphaT,
        "C11_0": params.layer1_C11_0,
        "C12_0": params.layer1_C12_0,
        "C44_0": params.layer1_C44_0,
    }
    layer2 = {
        "sigma_r": params.layer2_sigma_r,
        "sigma_z": params.layer2_sigma_z,
        "capac": params.layer2_capac,
        "rho": params.layer2_rho,
        "alphaT_perp": params.layer2_alphaT_perp,
        "alphaT_para": params.layer2_alphaT_para,
        "C11_0": params.layer2_C11_0,
        "C12_0": params.layer2_C12_0,
        "C13_0": params.layer2_C13_0,
        "C33_0": params.layer2_C33_0,
        "C44_0": params.layer2_C44_0,
    }
    layer3 = {
        "sigma": params.layer3_sigma,
        "capac": params.layer3_capac,
    }

    # 7. Compute model (with timing)
    t0 = time.time()
    Z_pf = compute_surface_displacement(
        model_freqs, p_vals, a0, params.w_rms, params.g_int, layer1, layer2, layer3
    )
    t1 = time.time()

    pbd_angles = compute_probe_deflection(
        Z_pf, p_vals, model_freqs, params.w_rms, params.r_0, params.c_probe
    )
    t2 = time.time()

    in_mod, out_mod, ratio_mod = compute_lockin_signals(
        pbd_angles, params.v_sum_fixed, params.detector_gain
    )
    t3 = time.time()
    print(f"[transverse] compute_surface_displacement: {t1 - t0:.3f}s")
    print(f"[transverse] compute_probe_deflection:     {t2 - t1:.3f}s")
    print(f"[transverse] compute_lockin_signals:        {t3 - t2:.3f}s")
    print(f"[transverse] TOTAL forward model:           {t3 - t0:.3f}s")

    # 8. Return results
    return {
        "plot_data": {
            "model_freqs": model_freqs.tolist(),
            "in_model": in_mod.tolist(),
            "out_model": out_mod.tolist(),
            "ratio_model": ratio_mod.tolist(),
            "exp_freqs": freq_middle.tolist(),
            "in_exp": v_corr_in_middle.tolist(),
            "out_exp": v_corr_out_middle.tolist(),
            "ratio_exp": v_corr_ratio_middle.tolist(),
        },
    }


def run_de_fitting_transverse(
    params: TransverseIsotropicParams,
    data_filename: str,
    fit_param: str,
    bounds: tuple[float, float],
    progress_callback=None,
    maxiter: int = 20,
    popsize: int = 8,
    tol: float = 1e-3,
) -> dict:
    """Run DE fitting for a single transverse isotropic layer2 parameter."""
    if fit_param not in TRANSVERSE_FIT_PARAMS:
        raise ValueError(
            f"Unknown fit parameter: {fit_param}. Must be one of {TRANSVERSE_FIT_PARAMS}"
        )

    # Same setup as run_transverse_isotropic_analysis
    v_out, v_in, _, v_sum, freq = load_data(data_filename)
    complex_leaking = calculate_leaking(
        freq, params.f_rolloff, params.delay_1, params.delay_2
    )
    v_corr_in, v_corr_out, v_corr_ratio = correct_data(v_out, v_in, complex_leaking)

    # Select middle points
    num_points = len(freq)
    num_middle = params.num_middle_points
    if num_points >= num_middle:
        start_idx = (num_points - num_middle) // 2
        end_idx = start_idx + num_middle
        freq_middle = freq[start_idx:end_idx]
        v_corr_in_middle = v_corr_in[start_idx:end_idx]
        v_corr_out_middle = v_corr_out[start_idx:end_idx]
        v_corr_ratio_middle = v_corr_ratio[start_idx:end_idx]
    else:
        freq_middle = freq
        v_corr_in_middle = v_corr_in
        v_corr_out_middle = v_corr_out
        v_corr_ratio_middle = v_corr_ratio

    # Compute A0
    refl_al = (
        abs((params.n_al - 1 + 1j * params.k_al) / (params.n_al + 1 + 1j * params.k_al))
        ** 2
    )
    a0 = (
        params.incident_pump
        * params.lens_transmittance
        * (4.0 / np.pi)
        * (1.0 - refl_al)
    )

    # Build grids
    up_p = 8 / params.w_rms
    d_p = up_p / params.n_p
    p_vals = np.linspace(d_p, up_p, params.n_p)

    model_freqs = np.logspace(
        np.log10(params.model_freq_start),
        np.log10(params.model_freq_end),
        params.model_freq_points,
    )

    # Build layer dicts
    layer1 = {
        "thickness": params.layer1_thickness,
        "sigma": params.layer1_sigma,
        "capac": params.layer1_capac,
        "rho": params.layer1_rho,
        "alphaT": params.layer1_alphaT,
        "C11_0": params.layer1_C11_0,
        "C12_0": params.layer1_C12_0,
        "C44_0": params.layer1_C44_0,
    }
    layer2 = {
        "sigma_r": params.layer2_sigma_r,
        "sigma_z": params.layer2_sigma_z,
        "capac": params.layer2_capac,
        "rho": params.layer2_rho,
        "alphaT_perp": params.layer2_alphaT_perp,
        "alphaT_para": params.layer2_alphaT_para,
        "C11_0": params.layer2_C11_0,
        "C12_0": params.layer2_C12_0,
        "C13_0": params.layer2_C13_0,
        "C33_0": params.layer2_C33_0,
        "C44_0": params.layer2_C44_0,
    }
    layer3 = {
        "sigma": params.layer3_sigma,
        "capac": params.layer3_capac,
    }

    # Interpolate experimental data to model frequencies for cost comparison
    exp_in_interp = np.interp(model_freqs, freq_middle[::-1], v_corr_in_middle[::-1])
    exp_out_interp = np.interp(model_freqs, freq_middle[::-1], v_corr_out_middle[::-1])

    gen_count = [0]
    t_start = time.time()

    def objective(x):
        try:
            trial_layer2 = copy.deepcopy(layer2)
            trial_layer2[fit_param] = x[0]

            Z_pf = compute_surface_displacement(
                model_freqs,
                p_vals,
                a0,
                params.w_rms,
                params.g_int,
                layer1,
                trial_layer2,
                layer3,
            )
            angles = compute_probe_deflection(
                Z_pf, p_vals, model_freqs, params.w_rms, params.r_0, params.c_probe
            )
            in_mod, out_mod, _ = compute_lockin_signals(
                angles, params.v_sum_fixed, params.detector_gain
            )

            if np.isnan(in_mod).any() or np.isnan(out_mod).any():
                return 1e12

            cost = float(
                np.sum((in_mod - exp_in_interp) ** 2)
                + np.sum((out_mod - exp_out_interp) ** 2)
            )
            return cost
        except Exception as e:
            print(f"[transverse-fit] OBJECTIVE ERROR: {e}")
            return 1e12

    def callback(xk, convergence):
        gen_count[0] += 1
        elapsed = time.time() - t_start
        print(
            f"[transverse-fit] Gen {gen_count[0]}: "
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
    final_layer2 = copy.deepcopy(layer2)
    final_layer2[fit_param] = result.x[0]

    Z_pf = compute_surface_displacement(
        model_freqs,
        p_vals,
        a0,
        params.w_rms,
        params.g_int,
        layer1,
        final_layer2,
        layer3,
    )
    angles = compute_probe_deflection(
        Z_pf, p_vals, model_freqs, params.w_rms, params.r_0, params.c_probe
    )
    in_mod, out_mod, ratio_mod = compute_lockin_signals(
        angles, params.v_sum_fixed, params.detector_gain
    )

    total_time = time.time() - t_start
    print(f"[transverse-fit] DONE in {total_time:.1f}s: {fit_param}={result.x[0]:.6e}")

    f_peak, ratio_at_peak = fit_rough_analysis(model_freqs, out_mod, ratio_mod)

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
            "exp_freqs": freq_middle.tolist(),
            "in_exp": v_corr_in_middle.tolist(),
            "out_exp": v_corr_out_middle.tolist(),
            "ratio_exp": v_corr_ratio_middle.tolist(),
        },
    }
