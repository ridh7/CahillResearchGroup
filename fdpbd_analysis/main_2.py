#!/usr/bin/env python3
"""
Thermoelastic surface-displacement & probe-beam deflection model,
translated from MATLAB to Python.
"""

import numpy as np
import scipy.io as sio
import scipy.linalg as la
import matplotlib.pyplot as plt
import warnings
from data_processing import load_data, calculate_leaking, correct_data
from scipy.optimize import minimize
import copy

# -----------------------------------------------------------------------------
# —— Fitting Configuration (NEW) ——————————————————————————————————————
# -----------------------------------------------------------------------------
FITTING_CONFIG = {
    "parameter_to_fit": "sigma_x",  # Name of the key in LAYER2 to fit
    "initial_guess": 0.3,  # Initial guess for the optimizer
    "bounds": (0.01, 2.0),  # (min, max) bounds for the parameter
    "fixed_values": {  # Values for OTHER L2 target params during this fit
        "sigma_y": 0.5,  # Example: keep sigma_y at its original value
        "alphaT_perp": 70e-6,  # Example: keep alphaT_perp original
        "alphaT_para": 60e-6,  # Example: keep alphaT_para original
    },
}

# Global storage for data needed by objective function (NEW)
EXP_DATA_STORAGE = {}
P_VALS_GLOBAL = np.array([])
PSI_VALS_GLOBAL = np.array([])

# For plotting, distinguish from MODEL_FREQS used in original single run (NEW)
# MODEL_FREQS_PLOT = np.logspace(
#     np.log10(100e3), np.log10(100), 20
# )  # More points for smoother plot

# -----------------------------------------------------------------------------
# —— Hard-coded Input Parameters ————————————————————————————————————————
# (Change these only at the top of the file)
# -----------------------------------------------------------------------------

# Data file (must contain variables named exactly as below)
DATA_FILENAME = (
    "103_Mylar_machine_vertical_12um_145mV-100k-100Hz_40P_20X_0p65pump_0p83probe"
)

# Lock-in correction parameters
F_AMP = 95e3  # Hz
DELAY_1 = 0.89e-5  # s
DELAY_2 = -1.3e-11  # s^2
# Optical / detection
INCIDENT_PUMP = 0.65e-3  # W

# Beam geometry
W_RMS = 11.3e-6 * 0.25  # m
R_0 = 12.6e-6 * 0.25  # m
PHI = np.deg2rad(0.0)  # radians
LENS_TRANSMITTANCE = 0.82
DETECTOR_GAIN = 37.0  # V/rad

# Material stack: layer 1 = Al film, 2 = Mylar, 3 = air
# — Layer 1 (Al)
LAYER1 = {
    "thickness": 80e-9,  # m
    "sigma": 109.0,  # W/(m·K)
    "capac": 2.42e6,  # J/(m^3·K)
    "rho": 2.70e3,  # kg/m^3
    "alphaT": 23.1e-6,  # 1/K
    # elastic constants (Pa)
    "C11_0": 107.4e9,
    "C12_0": 60.5e9,
    "C44_0": 28.3e9,
}
N_AL, K_AL = 2.9, 8.2

# — Layer 2 (anisotropic Mylar-like bulk)
LAYER2 = {
    "sigma_x": 0.3,  # W/(m·K)
    "sigma_y": 0.5,
    "sigma_z": 0.3,
    "capac": 1.59e6,  # J/(m^3·K)
    "rho": 1380.0,  # kg/m^3
    "alphaT_perp": 70e-6,  # 1/K
    "alphaT_para": 60e-6,  # 1/K
    # elastic constants (Pa)
    "C11_0": 12.11e9,
    "C12_0": 5.06e9,
    "C13_0": 5.68e9,
    "C33_0": 7.06e9,
    "C44_0": 1.20e9,
}

# — Layer 3 (air)
LAYER3 = {
    "sigma": 0.028,  # W/(m·K)
    "capac": 1192.0,  # J/(m^3·K)
}


C_PROBE = 0.7  # approximation factor


# Simulation grid
N_P = 63
N_PSI = 45

# Model frequencies (from 1e5 Hz down to 1e2 Hz, 10 pts)
MODEL_FREQS = np.logspace(np.log10(100e3), np.log10(100), 10)

# Thermal boundary conductance of Al / bulk interface
G_int = 100e6  # W/(m²·K)

# Compute how much of the pump power actually goes into the film
REFL_AL = abs((N_AL - 1 + 1j * K_AL) / (N_AL + 1 + 1j * K_AL)) ** 2
ABSORBED_PUMP = 1.0 - REFL_AL

# A0: amplitude of the thermal source term (matches your MATLAB A0)
A0 = INCIDENT_PUMP * LENS_TRANSMITTANCE * (4.0 / np.pi) * ABSORBED_PUMP


# -----------------------------------------------------------------------------
# —— Helper Functions ———————————————————————————————————————————————
# -----------------------------------------------------------------------------


def simpson_integration(y: np.ndarray, dx: float) -> float:
    """
    Simpson’s rule for equally‐spaced data.

    Args:
        y: 1D array of function values at N points (N must be odd and ≥ 3).
        dx: spacing between consecutive samples.

    Returns:
        Approximation of the integral of y over its domain.
    """
    n = y.size
    if n < 3 or n % 2 == 0:
        raise ValueError("Simpson integration requires odd number of points ≥ 3.")
    return dx / 3 * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum())


def compute_surface_displacement(
    freqs: np.ndarray, p_vals: np.ndarray, psi_vals: np.ndarray
) -> np.ndarray:
    """
    Build and solve the 9×9 thermo‐elastic boundary‐condition system
    to get the complex surface displacement Z(p,ψ,ω).

    Returns:
        Z: array of shape (len(p_vals), len(psi_vals), len(freqs))
           containing Z(p,ψ,ω) for each mode and frequency.
    """
    n_p, n_psi, n_f = len(p_vals), len(psi_vals), len(freqs)
    Z = np.zeros((n_p, n_psi, n_f), dtype=complex)

    # — Precompute thermal diffusivities —
    Dif1 = LAYER1["sigma"] / LAYER1["capac"]
    Dif2 = LAYER2["sigma_z"] / LAYER2["capac"]
    Dif3 = LAYER3["sigma"] / LAYER3["capac"]
    L1 = LAYER1["thickness"]
    sigma1 = LAYER1["sigma"]
    sigma2z = LAYER2["sigma_z"]
    sigma3 = LAYER3["sigma"]

    # — Layer 1 effective elastic constants —
    C11_0_1, C12_0_1, C44_0_1 = (LAYER1["C11_0"], LAYER1["C12_0"], LAYER1["C44_0"])
    alpha1 = LAYER1["alphaT"]
    beta1 = (C11_0_1 + 2 * C12_0_1) * alpha1
    # isotropic in layer1:
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

    # normalized constants
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
    sqrtC11rho_1 = np.sqrt(C11_1 / LAYER1["rho"])

    # — Layer 2 effective elastic constants & betas —
    C11_0_2 = LAYER2["C11_0"]
    C12_0_2 = LAYER2["C12_0"]
    C13_0_2 = LAYER2["C13_0"]
    C33_0_2 = LAYER2["C33_0"]
    C44_0_2 = LAYER2["C44_0"]
    alpha_v = LAYER2["alphaT_perp"]
    alpha_p = LAYER2["alphaT_para"]
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
    sqrtC11rho_2 = np.sqrt((1 + 1e-6j) * C11_2 / LAYER2["rho"])

    for i_f, f in enumerate(freqs):
        ω = 2 * np.pi * f
        qn2_1 = 1j * ω / Dif1
        qn2_2 = 1j * ω / Dif2
        qn2_3 = 1j * ω / Dif3

        for i_p, p in enumerate(p_vals):
            flx = A0 * np.exp(-(W_RMS**2) * p**2 / 8)

            for i_psi, psi in enumerate(psi_vals):
                k = p * np.cos(psi)
                xi = p * np.sin(psi)

                zeta1 = np.sqrt(qn2_1 + p**2)
                zeta2 = np.sqrt(
                    qn2_2
                    + k**2 * LAYER2["sigma_x"] / LAYER2["sigma_z"]
                    + xi**2 * LAYER2["sigma_y"] / LAYER2["sigma_z"]
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
                    + s1z * s2z / G_int * np.cosh(z1L)
                ) / s1z
                G_d /= (
                    s2z * np.cosh(z1L)
                    + s1z * np.sinh(z1L)
                    + s1z * s2z / G_int * np.sinh(z1L)
                )
                G_u = 1.0 / s3z
                G = 1.0 / (1.0 / G_u + 1.0 / G_d)

                θ_s = flx * G
                θ_bs = (
                    np.cosh(z1L) * θ_s
                    + s1z / G_int * np.sinh(z1L) * θ_s
                    - np.sinh(z1L) * flx / s1z
                    - np.cosh(z1L) * flx / G_int
                )

                C_s1 = (s2z / G_int * θ_bs + θ_bs - θ_s * np.exp(-z1L)) / (
                    np.exp(z1L) - np.exp(-z1L)
                )
                C_s2 = θ_s - C_s1

                # — Layer1 matrices A1, B1, D1 —
                A1 = np.zeros((6, 6), dtype=complex)
                B1 = np.zeros((6, 6), dtype=complex)
                D1 = np.zeros(6, dtype=complex)

                A1[0, 3] = A1[1, 4] = A1[2, 5] = 1.0
                A1[3, 0] = C55C11_1
                A1[4, 1] = C44C11_1
                A1[5, 2] = C33C11_1
                B1[3, 3] = B1[4, 4] = B1[5, 5] = 1.0
                D1[5] = betazC11_1

                # fill variable parts
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

                # solve generalized eigenproblem
                eigvals1, Q1 = la.eig(B1, A1)

                # N1 = inv(A1) @ D1
                N1 = la.solve(A1, D1)
                U1 = la.solve(Q1, N1)

                # — Layer2 matrices A2, B2, D2 —
                A2 = np.zeros((6, 6), dtype=complex)
                B2 = np.zeros((6, 6), dtype=complex)
                D2 = np.zeros(6, dtype=complex)

                # 1) Identity‐coupling rows (z=0 continuity)
                A2[0, 3] = 1.0  # MATLAB A_2(1,4)=1
                A2[1, 4] = 1.0  # MATLAB A_2(2,5)=1
                A2[2, 5] = 1.0  # MATLAB A_2(3,6)=1

                # 2) Elastic‐continuity rows at z=L (lower‐left block)
                A2[3, 0] = C55C11_2  # MATLAB A_2(4,1)=C55C11_2
                A2[4, 1] = C44C11_2  # MATLAB A_2(5,2)=C44C11_2
                A2[5, 2] = C33C11_2  # MATLAB A_2(6,3)=C33C11_2

                # 3) Displacement‐free rows for B2 (top of air)
                B2[3, 3] = 1.0  # MATLAB B_2(4,4)=1
                B2[4, 4] = 1.0  # MATLAB B_2(5,5)=1
                B2[5, 5] = 1.0  # MATLAB B_2(6,6)=1

                # 4) Source terms in D2
                D2[0] = betaxC11_2 * 1j * k  # MATLAB D_2(1)=…
                D2[1] = betayC11_2 * 1j * xi  # MATLAB D_2(2)=…
                D2[5] = betazC11_2  # MATLAB D_2(6)=…

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
                # reorder modes: decaying first (real<0), then growing
                neg = [i for i, lam in enumerate(eigvals2) if lam.real < 0]
                pos = [i for i, lam in enumerate(eigvals2) if lam.real >= 0]
                idx_order = neg + pos
                Q2 = Q2_raw[:, idx_order]
                L2 = eigvals2[idx_order]
                U2 = la.solve(Q2, la.solve(A2, D2))

                # — Build 9×9 BCM & BCC —
                BCM = np.zeros((9, 9), dtype=complex)
                BCC = np.zeros(9, dtype=complex)

                # continuity at z=0 & z=L
                for m in range(6):
                    BCM[0:3, m] = Q1[3:6, m]
                    BCM[3:9, m] = Q1[0:6, m] * np.exp(eigvals1[m] * L1)

                for m in range(3):
                    BCM[3:6, 6 + m] = -Q2[0:3, m] * np.exp(L2[m] * L1)
                    BCM[6:9, 6 + m] = -C11_0_2 / C11_1 * Q2[3:6, m] * np.exp(L2[m] * L1)

                # assemble BCC
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

                # solve for coefficients
                J = la.solve(BCM, BCC)

                # compute displacement
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
    Z: np.ndarray, p_vals: np.ndarray, psi_vals: np.ndarray, freqs: np.ndarray
) -> np.ndarray:
    """
    Integrate Z(p,ψ,ω) first over ψ, then over p, to yield the
    probe–beam deflection angle versus frequency.

    Returns:
        angles: 1D array, one deflection angle per freqs entry.
    """
    n_p, n_psi, n_f = Z.shape
    d_psi = psi_vals[1] - psi_vals[0]
    d_p = p_vals[1] - p_vals[0]

    angles = np.zeros(n_f, dtype=complex)

    for i_f in range(n_f):
        I_p = np.zeros(n_p, dtype=complex)

        for i_p, p in enumerate(p_vals):
            # build the ψ‐integrand
            integrand = np.zeros(n_psi, dtype=complex)
            for i_psi, psi in enumerate(psi_vals):
                g = -np.cos(psi - PHI) * np.sin(p * R_0 * np.cos(psi - PHI)) - np.cos(
                    psi + PHI
                ) * np.sin(p * R_0 * np.cos(psi + PHI))
                integrand[i_psi] = Z[i_p, i_psi, i_f] * g

            Iψ = (1 / np.pi) * simpson_integration(integrand, d_psi)
            I_p[i_p] = Iψ * np.exp(-(W_RMS**2) * p**2 / 8) * p**2

        # take only the real part of the deflection angle
        angles[i_f] = (1 / np.pi) * C_PROBE * simpson_integration(I_p, d_p)

    return angles


def compute_lockin_signals(
    angles: np.ndarray, v_sum_avg: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert deflection angles into simulated lock-in in-phase,
    out-of-phase, and their ratio.

    Returns:
        in_phase, out_of_phase, ratio  (all 1D arrays matching angles)
    """
    raw = angles / np.sqrt(2) * 0.5 * DETECTOR_GAIN * v_sum_avg
    in_phase = np.abs(np.real(raw))
    out_of_phase = -np.imag(raw)
    ratio = np.full_like(in_phase, np.nan)
    nonzero = out_of_phase != 0
    ratio[nonzero] = -in_phase[nonzero] / out_of_phase[nonzero]
    return in_phase, out_of_phase, ratio


def fit_rough_analysis(
    freqs: np.ndarray, out_of_phase: np.ndarray, ratio: np.ndarray
) -> tuple[float, float]:
    """
    Find the frequency of maximum out-of-phase signal by fitting a
    quadratic to log(f) vs out_of_phase (linear scale), and then the
    ratio at that freq by fitting a line to log(f) vs log(ratio).

    This version is modified to match the logic of the MATLAB analyze_signals
    function as closely as possible, treating the MATLAB code as ground truth.

    NOTE: This version removes the data filtering and minimum point checks
          present in the original Python code. It directly mirrors the MATLAB
          approach of using raw data with np.polyfit and np.log.
          This may produce errors, warnings, or NaNs if 'out_of_phase' contains
          non-finite values, or if 'ratio' contains non-positive or non-finite
          values (due to np.log). MATLAB's internal handling of such edge cases
          in log() and polyfit() might differ subtly.
    """
    f_max = np.nan
    ratio_at_fmax = np.nan

    try:
        # --- fmax Calculation ---
        # Match MATLAB: Fit a 2nd-order polynomial to log(freqs) vs out_of_phase (linear scale)
        log_f = np.log(freqs)
        # Use out_of_phase directly, no filtering, no log
        p_op = np.polyfit(log_f, out_of_phase, 2)

        # Calculate f_max using the vertex formula (-b / 2a) applied in log-frequency space, then exponentiate
        # p_op[0] is coeff of log(f)^2, p_op[1] is coeff of log(f)
        if p_op[0] != 0:  # Avoid division by zero if fit is degenerate
            f_max = np.exp(-p_op[1] / (2 * p_op[0]))
        else:
            warnings.warn(
                "Quadratic fit for f_max resulted in zero leading coefficient."
            )
            # f_max remains NaN

    except (np.linalg.LinAlgError, ValueError, RuntimeWarning) as e:
        # Catch potential errors/warnings from log or polyfit if inputs are problematic
        warnings.warn(
            f"Could not determine f_max due to error in fitting out_of_phase data: {e}"
        )
        f_max = np.nan  # Ensure f_max is NaN if fit failed

    # --- ratio_at_fmax Calculation ---
    # Only proceed if f_max was successfully calculated
    if not np.isnan(f_max):
        try:
            # Match MATLAB: Fit a 1st-order polynomial (line) to log(freqs) vs log(ratio)
            # Take log of ratio - this will warn/error/give nan/inf for non-positive ratios
            log_r = np.log(ratio)
            # Use the same log_f as calculated above
            p_r = np.polyfit(log_f, log_r, 1)

            # Evaluate the linear fit at log(f_max) and exponentiate
            log_fmax_val = np.log(f_max)
            ratio_at_fmax = np.exp(np.polyval(p_r, log_fmax_val))

        except (np.linalg.LinAlgError, ValueError, RuntimeWarning) as e:
            # Catch potential errors/warnings from log, polyfit, or polyval
            warnings.warn(
                f"Could not determine ratio_at_fmax due to error in fitting/evaluating ratio data: {e}"
            )
            ratio_at_fmax = np.nan  # Ensure ratio is NaN if this part failed

    # Note: MATLAB version also prints results, this Python version just returns them.
    return f_max, ratio_at_fmax


def plot_results(
    model_freqs: np.ndarray,
    in_model: np.ndarray,
    out_model: np.ndarray,
    exp_freqs: np.ndarray,
    in_exp: np.ndarray,
    out_exp: np.ndarray,
    ratio_model: np.ndarray,
    ratio_exp: np.ndarray,
    title_suffix: str = "",
) -> None:
    """
    Two‐panel comparison plots: semilog of in/out‐phase
    and log-log of ratio, model vs. experiment.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"FD-PBD Model vs. Experiment{title_suffix}")

    # left panel: in/out
    ax1.semilogx(model_freqs, in_model, "ko-", lw=1.5, label="Model In-phase")
    ax1.semilogx(model_freqs, out_model, "kx--", lw=1.5, label="Model Out-phase")
    ax1.semilogx(exp_freqs, in_exp, "ro-", lw=1.5, label="Data In-phase")
    ax1.semilogx(exp_freqs, out_exp, "rx--", lw=1.5, label="Data Out-phase")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Signal (V)")
    ax1.legend(loc="best")
    ax1.grid(True)

    # right panel: ratio
    ax2.loglog(model_freqs, ratio_model, "ko-", lw=1.5, label="Model Ratio")
    ax2.loglog(exp_freqs, ratio_exp, "ro-", lw=1.5, label="Data Ratio")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Ratio")
    ax2.legend(loc="best")
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


# -----------------------------------------------------------------------------
# —— Objective Function for Fitting —————————————————————————————————————
# -----------------------------------------------------------------------------
def objective_function(param_value_to_fit, param_name_to_fit_str, fixed_params_dict):
    global LAYER2  # Allow modification of global LAYER2 during this function call

    # Store original value of the parameter being fitted to restore it later
    original_param_val = LAYER2[param_name_to_fit_str]

    # Update LAYER2: set the parameter being fitted to the optimizer's current trial value
    current_trial_param_value = param_value_to_fit[
        0
    ]  # param_value_to_fit is a list/array
    LAYER2[param_name_to_fit_str] = current_trial_param_value
    # Update LAYER2: set the parameters that are fixed for this fitting run
    for key, value in fixed_params_dict.items():
        LAYER2[key] = value

    # **** NEW: Print the parameter value being tried ****
    print(f"  Trying {param_name_to_fit_str}: {current_trial_param_value:.6e}")

    # Run the model simulation using experimental frequencies (from global storage)
    # P_VALS_GLOBAL and PSI_VALS_GLOBAL are also used by these functions
    Z = compute_surface_displacement(
        EXP_DATA_STORAGE["freqs"], P_VALS_GLOBAL, PSI_VALS_GLOBAL
    )
    pbd_angles = compute_probe_deflection(
        Z, P_VALS_GLOBAL, PSI_VALS_GLOBAL, EXP_DATA_STORAGE["freqs"]
    )
    in_mod, out_mod, _ = compute_lockin_signals(
        pbd_angles, EXP_DATA_STORAGE["v_sum_avg"]
    )

    cost = 1e12  # Default high cost if NaNs occur
    if not (np.isnan(in_mod).any() or np.isnan(out_mod).any()):
        # Calculate Sum of Squared Differences (SSD)
        ssd_in_phase = np.sum((in_mod - EXP_DATA_STORAGE["in_phase"]) ** 2)
        ssd_out_phase = np.sum((out_mod - EXP_DATA_STORAGE["out_of_phase"]) ** 2)
        cost = ssd_in_phase + ssd_out_phase

    # **** NEW: Print the calculated cost for this parameter value ****
    print(
        f"    Cost for {param_name_to_fit_str} = {current_trial_param_value:.6e} -> {cost:.6e}"
    )

    # Restore the original value of the fitted parameter in global LAYER2
    LAYER2[param_name_to_fit_str] = original_param_val
    # Fixed parameters (from fixed_params_dict) also need to be conceptually restored
    # to the state LAYER2 had before this specific objective_function call if other
    # parts of the code were to rely on it. However, the main fitting loop in main()
    # re-establishes the correct LAYER2 state (based on FITTING_CONFIG) before calling minimize,
    # and then sets the final fitted value after minimize completes.
    # The key is that *within* one call to objective_function, LAYER2 reflects the trial.

    return cost


# -----------------------------------------------------------------------------
# —— Main Script ————————————————————————————————————————————————
# -----------------------------------------------------------------------------


def main():
    global LAYER2, EXP_DATA_STORAGE, P_VALS_GLOBAL, PSI_VALS_GLOBAL  # Declare globals

    # 1) Load & correct experimental data
    v_out, v_in, _, v_sum_data, Fexp = load_data(DATA_FILENAME)
    complex_leaking = calculate_leaking(Fexp, F_AMP, DELAY_1, DELAY_2)
    Vin_exp, Vout_exp, ratio_exp = correct_data(v_out, v_in, complex_leaking)
    v_sum_avg = np.mean(v_sum_data)

    # Populate global storage for objective function
    EXP_DATA_STORAGE = {
        "freqs": Fexp,
        "in_phase": Vin_exp,
        "out_of_phase": Vout_exp,  # Ensure this key matches access in objective_function
        "ratio": ratio_exp,
        "v_sum_avg": v_sum_avg,
    }

    # 2) Build p and psi grids and make them global
    up_p = 8 / W_RMS
    d_p = up_p / N_P
    P_VALS_GLOBAL = np.linspace(d_p, up_p, N_P)  # N_P must be odd
    up_psi = np.pi / 2
    PSI_VALS_GLOBAL = np.linspace(0, up_psi, N_PSI)  # N_PSI must be odd

    # --- Initial Model Run (Before Fitting) ---
    print("--- Running Initial Model (Before Fitting) ---")
    # Save a pristine copy of LAYER2 to ensure this run uses original hardcoded values
    original_hardcoded_layer2 = copy.deepcopy(LAYER2)

    # Simulation with original hardcoded LAYER2 and plot-specific frequencies
    Z_initial = compute_surface_displacement(
        MODEL_FREQS, P_VALS_GLOBAL, PSI_VALS_GLOBAL
    )
    pbd_angles_initial = compute_probe_deflection(
        Z_initial, P_VALS_GLOBAL, PSI_VALS_GLOBAL, MODEL_FREQS
    )
    in_mod_initial, out_mod_initial, ratio_mod_initial = compute_lockin_signals(
        pbd_angles_initial, v_sum_avg
    )

    # Rough analysis for initial parameters
    f_peak_initial, ratio_at_peak_initial = fit_rough_analysis(
        MODEL_FREQS, out_mod_initial, ratio_mod_initial
    )
    print(
        f"Initial: Peak out-of-phase at {f_peak_initial if not np.isnan(f_peak_initial) else 'N/A'} Hz"
    )
    print(
        f"Initial: Ratio at peak: {ratio_at_peak_initial if not np.isnan(ratio_at_peak_initial) else 'N/A'}"
    )

    plot_results(
        MODEL_FREQS,
        in_mod_initial,
        out_mod_initial,
        Fexp,
        Vin_exp,
        Vout_exp,
        ratio_mod_initial,
        ratio_exp,
        title_suffix=" (Initial Parameters)",
    )
    # Restore global LAYER2 to its original hardcoded state before fitting changes it
    LAYER2 = original_hardcoded_layer2
    # --- End of Initial Model Run ---

    # 3) Perform Fitting ---
    print(f"\n--- Starting Fit for: {FITTING_CONFIG['parameter_to_fit']} ---")
    param_to_fit_name = FITTING_CONFIG["parameter_to_fit"]

    # Prepare LAYER2 for fitting:
    # Set the parameter-to-be-fitted to its initial guess from FITTING_CONFIG
    LAYER2[param_to_fit_name] = FITTING_CONFIG["initial_guess"]
    # Set the fixed values for other parameters from FITTING_CONFIG
    for key, value in FITTING_CONFIG["fixed_values"].items():
        LAYER2[key] = value

    initial_guess_for_optimizer = [
        FITTING_CONFIG["initial_guess"]
    ]  # Must be a sequence
    bounds_for_optimizer = [FITTING_CONFIG["bounds"]]  # Sequence of (min, max) pairs

    optimization_result = minimize(
        objective_function,
        initial_guess_for_optimizer,
        args=(
            param_to_fit_name,
            FITTING_CONFIG["fixed_values"],
        ),  # Pass name and fixed dict
        method="L-BFGS-B",  # A good bounded method
        bounds=bounds_for_optimizer,
        options={"disp": True, "ftol": 1e-12, "gtol": 1e-9},  # Optimizer options
    )

    fitted_param_value = optimization_result.x[0]
    print(f"\n--- Fitting Complete ---")
    print(f"Fitted {param_to_fit_name}: {fitted_param_value:.4e}")
    print(f"Optimization message: {optimization_result.message}")
    print(f"Final cost: {optimization_result.fun:.4e}")

    # Update global LAYER2 with the successfully fitted parameter
    LAYER2[param_to_fit_name] = fitted_param_value
    # The fixed_values from FITTING_CONFIG are already set in LAYER2

    # --- Final Model Run (After Fitting) ---
    print("\n--- Running Model with Fitted Parameter ---")
    # Simulation with fitted LAYER2 and plot-specific frequencies
    Z_fitted = compute_surface_displacement(MODEL_FREQS, P_VALS_GLOBAL, PSI_VALS_GLOBAL)
    pbd_angles_fitted = compute_probe_deflection(
        Z_fitted, P_VALS_GLOBAL, PSI_VALS_GLOBAL, MODEL_FREQS
    )
    in_mod_fitted, out_mod_fitted, ratio_mod_fitted = compute_lockin_signals(
        pbd_angles_fitted, v_sum_avg
    )

    # Rough analysis for fitted parameters
    f_peak_fitted, ratio_at_peak_fitted = fit_rough_analysis(
        MODEL_FREQS, out_mod_fitted, ratio_mod_fitted
    )
    print(
        f"After fit: Peak out-of-phase at {f_peak_fitted if not np.isnan(f_peak_fitted) else 'N/A'} Hz"
    )
    print(
        f"After fit: Ratio at peak: {ratio_at_peak_fitted if not np.isnan(ratio_at_peak_fitted) else 'N/A'}"
    )

    plot_results(
        MODEL_FREQS,
        in_mod_fitted,
        out_mod_fitted,
        Fexp,
        Vin_exp,
        Vout_exp,
        ratio_mod_fitted,
        ratio_exp,
        title_suffix=f" (Fitted {param_to_fit_name} = {fitted_param_value:.2e})",
    )


if __name__ == "__main__":
    main()
