#!/usr/bin/env python3
"""
Thermoelastic surface-displacement & probe-beam deflection model
for transversely isotropic material, translated from MATLAB code2 to Python.
"""

import numpy as np
import scipy.io as sio
import scipy.linalg as la
import scipy.special as sp  # Added for Bessel function
import matplotlib.pyplot as plt
import warnings

# Assuming data_processing.py contains the necessary functions
from data_processing import load_data, calculate_leaking, correct_data

# -----------------------------------------------------------------------------
# —— Hard-coded Input Parameters (from code2) ——————————————————————————
# (Change these only at the top of the file)
# -----------------------------------------------------------------------------

# Data file (must contain variables named exactly as below)
DATA_FILENAME = "68_2024-09-12_good_MT200_30k-30Hz_40P_122mV_0p6pump_0.83probe_5X"

# Lock-in correction parameters (same as code1)
F_AMP = 95e3  # Hz
DELAY_1 = 0.89e-5  # s
DELAY_2 = -1.3e-11  # s^2

# Optical / detection
INCIDENT_PUMP = 0.69e-3  # W (from code2)
V_SUM_FIXED = 0.18  # V (fixed value from code2)

# Beam geometry
W_RMS = 11.2e-6  # m (from code2, no 0.25 factor)
R_0 = 12.6e-6  # m (from code2, no 0.25 factor)
# PHI is not needed for transverse isotropy
LENS_TRANSMITTANCE = 0.92  # (from code2)
DETECTOR_GAIN = 37.0  # V/rad (assumed same base gain, scaling handled later)

# Material stack: layer 1 = Al film, 2 = Bulk, 3 = air
# — Layer 1 (Al) - Properties updated from code2
LAYER1 = {
    "thickness": 70e-9,  # m (from code2)
    "sigma": 129.0,  # W/(m·K) (from code2)
    "capac": 2.42e6,  # J/(m^3·K) (same as code1)
    "rho": 2.70e3,  # kg/m^3 (same as code1)
    "alphaT": 23.1e-6,  # 1/K (same as code1)
    # elastic constants (Pa) (same as code1)
    "C11_0": 107.4e9,
    "C12_0": 60.5e9,
    "C44_0": 28.3e9,
}
N_AL, K_AL = 2.9, 8.2  # (same as code1)

# — Layer 2 (transversely isotropic bulk) - Properties updated from code2
LAYER2 = {
    "sigma_r": 0.64,  # W/(m·K) (in-plane)
    "sigma_z": 0.21,  # W/(m·K) (through-plane)
    "capac": 1.56e6,  # J/(m^3·K)
    "rho": 1430.0,  # kg/m^3
    "alphaT_perp": 28e-6,  # 1/K (in-plane CTE)
    "alphaT_para": 120e-6,  # 1/K (through-plane CTE)
    # elastic constants (Pa) - using the second set from code2 comments
    "C11_0": 8.9e9,
    "C12_0": 5.4e9,
    "C13_0": 5.4e9,
    "C33_0": 5.6e9,
    "C44_0": 2.1e9,
}

# — Layer 3 (air) - Properties same as code1
LAYER3 = {
    "sigma": 0.028,  # W/(m·K)
    "capac": 1192.0,  # J/(m^3·K)
}


C_PROBE = 0.65  # approximation factor (from code2)


# Simulation grid
N_P = 63  # Must be odd for Simpson integration
N_PSI = 1  # Only need one angle for transverse isotropy (Option C)

# Model frequencies (from 5e3 Hz down to 3e2 Hz, 40 pts, from code2)
MODEL_FREQS = np.logspace(np.log10(5e3), np.log10(300), 40)

# Thermal boundary conductance of Al / bulk interface (same as code1)
G_int = 100e6  # W/(m²·K)

# Compute how much of the pump power actually goes into the film
REFL_AL = abs((N_AL - 1 + 1j * K_AL) / (N_AL + 1 + 1j * K_AL)) ** 2
ABSORBED_PUMP = 1.0 - REFL_AL

# A0: amplitude of the thermal source term (matches MATLAB A0 definition)
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
    if n < 3:
        # Handle cases with fewer than 3 points if necessary (e.g., trapezoid)
        # For now, raise error as per original design
        if n == 2:
            warnings.warn(
                "Only 2 points provided, using trapezoid rule instead of Simpson."
            )
            return dx * (y[0] + y[1]) / 2.0
        elif n == 1:
            warnings.warn("Only 1 point provided for integration, result is 0.")
            return 0.0
        else:
            raise ValueError("Integration requires at least 1 point.")
    if n % 2 == 0:
        # If even number of points, can use Simpson's 3/8 rule for first/last 3
        # or fallback to trapezoid for last interval. Sticking to MATLAB's apparent
        # assumption of odd N for simplicity, raise error.
        raise ValueError("Simpson integration requires odd number of points ≥ 3.")
    # Standard Simpson's 1/3 rule
    return dx / 3 * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum())


def compute_surface_displacement(
    freqs: np.ndarray,
    p_vals: np.ndarray,
    psi_vals: np.ndarray,  # psi_vals expected but only first element used
) -> np.ndarray:
    """
    Build and solve the 9×9 thermo‐elastic boundary‐condition system
    to get the complex surface displacement Z(p,ω) for transversely
    isotropic case. Only calculates for the first psi value provided.

    Returns:
        Z: array of shape (len(p_vals), len(freqs))
           containing Z(p,ω) for each mode and frequency.
    """
    n_p, n_f = len(p_vals), len(freqs)
    # Store result only for p and f, as psi is redundant
    Z = np.zeros((n_p, n_f), dtype=complex)

    # — Precompute thermal diffusivities —
    Dif1 = LAYER1["sigma"] / LAYER1["capac"]
    # Use sigma_z for Dif2 definition as per MATLAB code2
    Dif2 = LAYER2["sigma_z"] / LAYER2["capac"]
    Dif3 = LAYER3["sigma"] / LAYER3["capac"]
    L1 = LAYER1["thickness"]
    sigma1 = LAYER1["sigma"]
    sigma2z = LAYER2["sigma_z"]  # Through-plane conductivity
    sigma2r = LAYER2["sigma_r"]  # In-plane conductivity
    sigma3 = LAYER3["sigma"]

    # — Layer 1 effective elastic constants (Isotropic) —
    # (Same derivation as in code1 Python)
    C11_0_1, C12_0_1, C44_0_1 = (LAYER1["C11_0"], LAYER1["C12_0"], LAYER1["C44_0"])
    alpha1 = LAYER1["alphaT"]
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

    # — Layer 2 effective elastic constants & betas (Transversely Isotropic) —
    # Mapping based on code2 MATLAB derived parameters section
    C11_0_2 = LAYER2["C11_0"]
    C12_0_2 = LAYER2["C12_0"]
    C13_0_2 = LAYER2["C13_0"]
    C33_0_2 = LAYER2["C33_0"]
    C44_0_2 = LAYER2["C44_0"]
    alpha_v = LAYER2["alphaT_perp"]  # In-plane (vertical in code2 comment)
    alpha_p = LAYER2["alphaT_para"]  # Through-plane (parallel in code2 comment)

    # Betas based on MATLAB code2 derivation
    betax2 = (C11_0_2 + C12_0_2) * alpha_v + C13_0_2 * alpha_p
    betay2 = betax2  # Transverse isotropy
    betaz2 = 2 * C13_0_2 * alpha_v + C33_0_2 * alpha_p

    # Effective constants based on MATLAB code2 derivation
    C11_2 = C11_0_2
    C12_2 = C12_0_2
    C13_2 = C13_0_2
    C33_2 = C33_0_2
    C44_2 = C44_0_2
    # These follow from transverse isotropy (z is symmetry axis)
    C22_2 = C11_2  # = C11_0_2
    C23_2 = C13_2  # = C13_0_2
    C55_2 = C44_2  # = C44_0_2
    C66_2 = (C11_0_2 - C12_0_2) / 2

    C22C11_2 = C22_2 / C11_2
    C33C11_2 = C33_2 / C11_2
    C12C11_2 = C12_2 / C11_2
    C13C11_2 = C13_2 / C11_2
    C23C11_2 = C23_2 / C11_2
    C44C11_2 = C44_2 / C11_2
    C55C11_2 = C55_2 / C11_2
    C66C11_2 = C66_2 / C11_2
    betaxC11_2 = betax2 / C11_2
    betayC11_2 = betay2 / C11_2  # = betaxC11_2
    betazC11_2 = betaz2 / C11_2
    # Add small imaginary part for numerical stability as in MATLAB
    sqrtC11rho_2 = np.sqrt((1 + 1e-6j) * C11_2 / LAYER2["rho"])

    # Use only the first (or only) psi value provided (Option C)
    psi = psi_vals[0]

    for i_f, f in enumerate(freqs):
        ω = 2 * np.pi * f
        qn2_1 = 1j * ω / Dif1
        qn2_2 = 1j * ω / Dif2
        qn2_3 = 1j * ω / Dif3

        for i_p, p in enumerate(p_vals):
            flx = A0 * np.exp(-(W_RMS**2) * p**2 / 8)

            # Calculate k, xi based on the single representative psi
            # If psi=0, k=p, xi=0. If psi=pi/4, k=p/sqrt(2), xi=p/sqrt(2)
            # The matrix math should yield the same result regardless due to symmetry
            k = p * np.cos(psi)
            xi = p * np.sin(psi)

            zeta1 = np.sqrt(qn2_1 + p**2)
            # zeta2 depends on sigma_r (in-plane) and sigma_z (through-plane)
            zeta2 = np.sqrt(qn2_2 + p**2 * sigma2r / sigma2z)
            zeta3 = np.sqrt(qn2_3 + p**2)

            # Thermal boundary G (calculation logic is the same)
            z1L = zeta1 * L1
            s1z = sigma1 * zeta1
            s2z = sigma2z * zeta2
            s3z = sigma3 * zeta3

            G_d_num = (
                s2z * np.sinh(z1L)
                + s1z * np.cosh(z1L)
                + s1z * s2z / G_int * np.cosh(z1L)
            )
            # Avoid division by zero if s1z is zero (though unlikely for complex zeta1)
            if s1z == 0:
                G_d_num = np.inf  # Or handle appropriately

            G_d_den = (
                s2z * np.cosh(z1L)
                + s1z * np.sinh(z1L)
                + s1z * s2z / G_int * np.sinh(z1L)
            )

            if G_d_den == 0 or s1z == 0:
                G_d = np.inf  # Or handle appropriately
            else:
                G_d = (G_d_num / s1z) / (G_d_den / s1z)  # Simpler division

            # Avoid division by zero for s3z
            G_u = 1.0 / s3z if s3z != 0 else np.inf

            # Handle potential infinities
            if np.isinf(G_u) and np.isinf(G_d):
                G = 0  # No heat flow anywhere
            elif np.isinf(G_u):
                G = G_d
            elif np.isinf(G_d):
                G = G_u
            elif (1.0 / G_u + 1.0 / G_d) == 0:
                G = np.inf  # Avoid division by zero
            else:
                G = 1.0 / (1.0 / G_u + 1.0 / G_d)

            θ_s = flx * G

            # Calculate theta_bs carefully for potential zero divisors
            term1 = np.cosh(z1L) * θ_s
            term2 = (s1z / G_int * np.sinh(z1L) * θ_s) if G_int != 0 else 0
            term3 = (np.sinh(z1L) * flx / s1z) if s1z != 0 else 0
            term4 = (np.cosh(z1L) * flx / G_int) if G_int != 0 else 0
            θ_bs = term1 + term2 - term3 - term4

            # Calculate C_s1, C_s2 carefully
            exp_z1L = np.exp(z1L)
            exp_neg_z1L = np.exp(-z1L)
            denom_cs = exp_z1L - exp_neg_z1L
            if denom_cs == 0:
                # Handle singular case (e.g., limit L1->0 or zeta1->0)
                C_s1 = 0  # Or other appropriate limit
                warnings.warn(
                    f"Singular denominator in C_s1 calculation at f={f}, p={p}"
                )
            else:
                num_cs1 = (
                    (s2z / G_int * θ_bs + θ_bs - θ_s * exp_neg_z1L)
                    if G_int != 0
                    else (θ_bs - θ_s * exp_neg_z1L)
                )
                C_s1 = num_cs1 / denom_cs

            C_s2 = θ_s - C_s1

            # — Layer1 matrices A1, B1, D1 — (Same structure as code1)
            A1 = np.zeros((6, 6), dtype=complex)
            B1 = np.zeros((6, 6), dtype=complex)
            D1 = np.zeros(6, dtype=complex)
            # ... [Matrix filling identical to code1 Python] ...
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

            # solve generalized eigenproblem for Layer 1
            try:
                eigvals1, Q1 = la.eig(B1, A1)
                # Check condition number (optional, MATLAB checks rcond)
                cond_Q1 = np.linalg.cond(Q1)
                if cond_Q1 > 1 / np.finfo(float).eps:  # Check if ill-conditioned
                    warnings.warn(
                        f"Matrix Q1 may be ill-conditioned (cond={cond_Q1}) at f={f}, p={p}"
                    )

                N1 = la.solve(A1, D1)
                U1 = la.solve(Q1, N1)
            except la.LinAlgError as e:
                warnings.warn(f"Linear algebra error in Layer 1 at f={f}, p={p}: {e}")
                # Assign NaN or skip this point
                Z[i_p, i_f] = np.nan
                continue  # Skip to next p

            # — Layer2 matrices A2, B2, D2 — (Using Layer 2 properties)
            A2 = np.zeros((6, 6), dtype=complex)
            B2 = np.zeros((6, 6), dtype=complex)
            D2 = np.zeros(6, dtype=complex)

            # Fill matrices based on general form, but using Layer 2 CijC11_2 etc.
            # Structure follows code1 Python / MATLAB closely
            A2[0, 3] = A2[1, 4] = A2[2, 5] = 1.0
            A2[3, 0] = C55C11_2
            A2[4, 1] = C44C11_2
            A2[5, 2] = C33C11_2
            B2[3, 3] = B2[4, 4] = B2[5, 5] = 1.0
            # D2 uses beta*C11_2 values
            D2[0] = betaxC11_2 * 1j * k
            D2[1] = betayC11_2 * 1j * xi  # betay=betax for transverse
            D2[5] = betazC11_2

            # Variable parts using k, xi and Layer 2 properties
            A2[0, 2] = C13C11_2 * 1j * k
            A2[1, 2] = C23C11_2 * 1j * xi  # C23 = C13 for transverse

            B2[0, 0] = k**2 + C66C11_2 * xi**2 - ω**2 / sqrtC11rho_2**2
            B2[1, 1] = (
                C22C11_2 * xi**2 + C66C11_2 * k**2 - ω**2 / sqrtC11rho_2**2
            )  # C22=C11
            B2[0, 1] = B2[1, 0] = (C12C11_2 + C66C11_2) * k * xi
            B2[2, 2] = -(ω**2) / sqrtC11rho_2**2
            B2[2, 3] = -1j * k
            B2[2, 4] = -1j * xi
            B2[3, 2] = -C55C11_2 * 1j * k  # C55=C44
            B2[4, 2] = -C44C11_2 * 1j * xi
            B2[5, 0] = -C13C11_2 * 1j * k
            B2[5, 1] = -C23C11_2 * 1j * xi  # C23=C13

            # solve generalized eigenproblem for Layer 2
            try:
                eigvals2_raw, Q2_raw = la.eig(B2, A2)
                # reorder modes: decaying first (real<0), then growing
                neg_idx = [i for i, lam in enumerate(eigvals2_raw) if lam.real < 0]
                pos_idx = [i for i, lam in enumerate(eigvals2_raw) if lam.real >= 0]
                # Ensure we only take the first 3 decaying modes if more exist
                if len(neg_idx) < 3:
                    warnings.warn(
                        f"Fewer than 3 decaying modes found in Layer 2 at f={f}, p={p}"
                    )
                    # Need robust handling here - for now, proceed but might fail
                idx_order = (
                    neg_idx[:3] + pos_idx[: 6 - len(neg_idx[:3])]
                )  # Get 6 total indices

                Q2 = Q2_raw[:, idx_order]
                L2 = eigvals2_raw[idx_order]  # Reordered eigenvalues

                cond_Q2 = np.linalg.cond(Q2)
                if cond_Q2 > 1 / np.finfo(float).eps:
                    warnings.warn(
                        f"Matrix Q2 may be ill-conditioned (cond={cond_Q2}) at f={f}, p={p}"
                    )

                N2 = la.solve(A2, D2)
                U2 = la.solve(Q2, N2)
            except la.LinAlgError as e:
                warnings.warn(f"Linear algebra error in Layer 2 at f={f}, p={p}: {e}")
                Z[i_p, i_f] = np.nan
                continue  # Skip to next p

            # — Build 9×9 BCM & BCC — (Structure same as code1 Python)
            BCM = np.zeros((9, 9), dtype=complex)
            BCC = np.zeros(9, dtype=complex)

            # Interface conditions at z=0 (rows 0-2) and z=L1 (rows 3-8)
            for m in range(6):  # modes in layer 1
                BCM[0:3, m] = Q1[3:6, m]  # Traction continuity at z=0
                BCM[3:9, m] = Q1[0:6, m] * np.exp(
                    eigvals1[m] * L1
                )  # Disp/Traction at z=L1

            # Contribution from layer 2 (decaying modes only)
            for m in range(3):  # first 3 modes in L2 (decaying)
                BCM[3:6, 6 + m] = -Q2[0:3, m] * np.exp(
                    L2[m] * L1
                )  # Displacement continuity at z=L1
                # Traction continuity at z=L1, scaled by C11 ratio
                BCM[6:9, 6 + m] = -(C11_0_2 / C11_1) * Q2[3:6, m] * np.exp(L2[m] * L1)

            # assemble BCC (source terms from thermal fields)
            # Use safe division helper
            def safe_div(num, den):
                if den == 0:
                    # Return large number or handle based on physical limit
                    warnings.warn("Division by zero prevented in BCC calculation.")
                    return np.inf * np.sign(num) if num != 0 else 0
                return num / den

            for rw in range(3):  # Traction boundary conditions at z=0
                s = 0
                for j in range(6):  # Sum over layer 1 modes
                    s += (
                        Q1[rw + 3, j]
                        * U1[j]
                        * (
                            safe_div(C_s1, (zeta1 - eigvals1[j]))
                            + safe_div(C_s2, (-zeta1 - eigvals1[j]))
                        )
                    )
                BCC[rw] = -s

            for rw in range(3, 6):  # Displacement continuity at z=L1
                s1 = s2 = 0
                for j in range(6):  # Sum over layer 1 modes (s1) & layer 2 modes (s2)
                    s1 += (
                        Q1[rw - 3, j]
                        * U1[j]
                        * (
                            safe_div(C_s1 * exp_z1L, (zeta1 - eigvals1[j]))
                            + safe_div(C_s2 * exp_neg_z1L, (-zeta1 - eigvals1[j]))
                        )
                    )
                    # Contribution from layer 2 particular solution (only first 3 modes needed for BC)
                    if j < 3:
                        s2 += Q2[rw - 3, j] * U2[j] * safe_div(θ_bs, (-zeta2 - L2[j]))
                BCC[rw] = -s1 + s2

            for rw in range(6, 9):  # Traction continuity at z=L1
                s1 = s2 = 0
                for j in range(6):  # Sum over layer 1 modes (s1) & layer 2 modes (s2)
                    s1 += (
                        Q1[rw - 3, j]
                        * U1[j]
                        * (
                            safe_div(C_s1 * exp_z1L, (zeta1 - eigvals1[j]))
                            + safe_div(C_s2 * exp_neg_z1L, (-zeta1 - eigvals1[j]))
                        )
                    )
                    if j < 3:
                        s2 += Q2[rw - 3, j] * U2[j] * safe_div(θ_bs, (-zeta2 - L2[j]))
                # Apply scaling factor C11_0_2 / C11_1 to layer 2 traction term
                BCC[rw] = -s1 + (C11_0_2 / C11_1) * s2

            # solve for coefficients J
            try:
                J = la.solve(BCM, BCC)
            except la.LinAlgError as e:
                warnings.warn(f"Could not solve BCM*J=BCC at f={f}, p={p}: {e}")
                Z[i_p, i_f] = np.nan
                continue

            # compute displacement W = w_H + w_P
            w_H = sum(Q1[2, m] * J[m] for m in range(6))  # Homogeneous solution at z=0
            w_P = sum(  # Particular solution at z=0
                Q1[2, j]
                * U1[j]
                * (
                    safe_div(C_s1, (zeta1 - eigvals1[j]))
                    + safe_div(C_s2, (-zeta1 - eigvals1[j]))
                )
                for j in range(6)
            )

            Z[i_p, i_f] = -(w_H + w_P)  # Vertical displacement uz at surface z=0

    return Z


def compute_probe_deflection(
    Z: np.ndarray, p_vals: np.ndarray, freqs: np.ndarray
) -> np.ndarray:
    """
    Integrate Z(p,ω) over p using the Bessel function kernel for
    transversely isotropic case to get the probe–beam deflection angle.

    Args:
        Z: 2D array Z[i_p, i_f] from compute_surface_displacement.
        p_vals: 1D array of p values.
        freqs: 1D array of frequencies.

    Returns:
        angles: 1D array, one deflection angle per freqs entry.
    """
    n_p, n_f = Z.shape
    d_p = p_vals[1] - p_vals[0] if n_p > 1 else 0  # Handle case of single p value

    angles = np.zeros(n_f, dtype=complex)

    for i_f in range(n_f):
        # Build the p-integrand: Z * exp(-w^2*p^2/8) * (-J1(p*r0)) * p^2
        integrand_p = np.zeros(n_p, dtype=complex)
        for i_p, p in enumerate(p_vals):
            # Use sp.jv(order, argument) for Bessel J1
            bessel_term = -sp.jv(1, p * R_0)
            integrand_p[i_p] = (
                Z[i_p, i_f] * np.exp(-(W_RMS**2) * p**2 / 8) * bessel_term * p**2
            )

        # Integrate over p using Simpson's rule
        # Note: Z might contain NaNs if previous steps failed.
        # simpson_integration needs finite values. Handle this.
        finite_integrand_mask = np.isfinite(integrand_p)
        if not np.all(finite_integrand_mask):
            warnings.warn(
                f"NaNs detected in PBD integrand at frequency {freqs[i_f]}. Result may be inaccurate."
            )
            # Option: integrate only over finite parts, or return NaN
            # Simple approach: return NaN if any part is NaN
            if not np.any(finite_integrand_mask):  # All NaN
                angles[i_f] = np.nan
                continue
            # If some are finite, try integrating them (requires adjustment to Simpson)
            # For now, just warn and proceed, Simpson might fail or give NaN
            # Let's try setting NaNs to zero for integration, but this is an approximation
            integrand_p[~finite_integrand_mask] = 0.0

        # Check if N_P is suitable for Simpson integration before calling
        if n_p >= 3 and n_p % 2 != 0:
            angles[i_f] = C_PROBE / np.pi * simpson_integration(integrand_p, d_p)
        elif n_p > 0:
            # Fallback for N_P < 3 or even N_P (e.g., trapezoid)
            warnings.warn(
                f"N_P={n_p} not suitable for Simpson rule. Using numpy.trapz."
            )
            angles[i_f] = C_PROBE / np.pi * np.trapz(integrand_p, dx=d_p)
        else:
            angles[i_f] = 0.0  # No points to integrate

    return angles


def compute_lockin_signals(
    angles: np.ndarray, v_sum_fixed: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert deflection angles into simulated lock-in in-phase,
    out-of-phase, and their ratio using code2 scaling.

    Args:
        angles: 1D array of complex deflection angles.
        v_sum_fixed: The fixed detector sum voltage (e.g., 0.18 V).

    Returns:
        in_phase, out_of_phase, ratio  (all 1D arrays matching angles)
    """
    # Scaling from code2: angle/sqrt(2) * 2 * Gain * V_sum
    raw = angles / np.sqrt(2) * 2.0 * DETECTOR_GAIN * v_sum_fixed
    in_phase = np.abs(np.real(raw))
    out_of_phase = -np.imag(raw)
    # Handle division by zero for ratio
    ratio = np.full_like(in_phase, np.nan)
    # Use a small tolerance instead of exact zero comparison
    nonzero_mask = np.abs(out_of_phase) > 1e-15  # Adjust tolerance if needed
    ratio[nonzero_mask] = -in_phase[nonzero_mask] / out_of_phase[nonzero_mask]

    # Handle cases where in_phase is also zero (ratio should be 0 or NaN)
    zero_inphase_mask = np.abs(in_phase) < 1e-15
    ratio[nonzero_mask & zero_inphase_mask] = 0.0  # Define 0/non-zero as 0

    return in_phase, out_of_phase, ratio


# Rough analysis function is omitted as requested


def plot_results(
    model_freqs: np.ndarray,
    in_model: np.ndarray,
    out_model: np.ndarray,
    exp_freqs: np.ndarray,  # Should be the middle frequencies
    in_exp: np.ndarray,  # Should be the middle in-phase
    out_exp: np.ndarray,  # Should be the middle out-phase
    ratio_model: np.ndarray,
    ratio_exp: np.ndarray,  # Should be the middle ratio
) -> None:
    """
    Two‐panel comparison plots: semilog of in/out‐phase
    and log-log of ratio, model vs. experiment (middle data).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # --- Left panel: in/out-phase ---
    # Model results
    ax1.semilogx(
        model_freqs, in_model, "ko--", lw=1.5, label="Model In-phase"
    )  # Dashed lines like MATLAB
    ax1.semilogx(model_freqs, out_model, "kx--", lw=1.5, label="Model Out-phase")
    # Experimental results (middle data)
    ax1.semilogx(
        exp_freqs, in_exp, "ro--", lw=1.5, label="Data In-phase"
    )  # Dashed lines like MATLAB
    ax1.semilogx(exp_freqs, out_exp, "rx--", lw=1.5, label="Data Out-phase")

    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Signal (V)")
    # Use handles for legend to match MATLAB appearance if needed
    h_exp_in = plt.Line2D(
        [], [], color="r", marker="o", linestyle="--", label="Experiment In"
    )
    h_exp_out = plt.Line2D(
        [], [], color="r", marker="x", linestyle="--", label="Experiment Out"
    )
    h_mod_in = plt.Line2D(
        [], [], color="k", marker="o", linestyle="--", label="Model In"
    )
    h_mod_out = plt.Line2D(
        [], [], color="k", marker="x", linestyle="--", label="Model Out"
    )
    # Create combined legend entries
    h_exp = plt.Line2D([], [], color="r", linestyle="--", label="Experiment")
    h_mod = plt.Line2D([], [], color="k", linestyle="--", label="Model")
    ax1.legend(handles=[h_exp, h_mod], loc="best")
    ax1.grid(True, which="both", linestyle=":")  # Add grid
    # Apply axis limits if needed to match MATLAB 'axis tight'
    ax1.autoscale(enable=True, axis="both", tight=True)

    # --- Right panel: ratio ---
    # Model results
    ax2.loglog(model_freqs, ratio_model, "ko--", lw=1.5, label="Model Ratio")
    # Experimental results (middle data)
    ax2.loglog(exp_freqs, ratio_exp, "ro--", lw=1.5, label="Data Ratio")

    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Ratio")
    ax2.legend(loc="best")
    ax2.grid(True, which="both", linestyle=":")  # Add grid
    ax2.autoscale(enable=True, axis="both", tight=True)

    # Apply font styling like MATLAB if desired
    for ax in [ax1, ax2]:
        for item in (
            [ax.title, ax.xaxis.label, ax.yaxis.label]
            + ax.get_xticklabels()
            + ax.get_yticklabels()
        ):
            item.set_fontname("Times New Roman")
            item.set_fontsize(16)  # Match MATLAB font size
        # Match MATLAB box and linewidth
        ax.spines["top"].set_linewidth(1.5)
        ax.spines["right"].set_linewidth(1.5)
        ax.spines["bottom"].set_linewidth(1.5)
        ax.spines["left"].set_linewidth(1.5)

    fig.tight_layout()  # Use tight_layout instead of axis tight
    plt.show()


# -----------------------------------------------------------------------------
# —— Main Script ————————————————————————————————————————————————
# -----------------------------------------------------------------------------


def main():
    # 1) Load & correct experimental data
    try:
        v_out, v_in, v_ratio_data, v_sum_data, Fexp = load_data(DATA_FILENAME)
    except FileNotFoundError:
        print(f"Error: Data file not found at '{DATA_FILENAME}'")
        return
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    complex_leaking = calculate_leaking(Fexp, F_AMP, DELAY_1, DELAY_2)
    Vin_exp, Vout_exp, ratio_exp = correct_data(v_out, v_in, complex_leaking)
    # v_sum_avg is not used, using V_SUM_FIXED instead

    # --- Select middle 15 points (as per MATLAB code2) ---
    num_points = len(Fexp)
    num_middle = 15
    if num_points >= num_middle:
        start_idx = (num_points - num_middle) // 2  # Integer division
        end_idx = start_idx + num_middle
        # Slice the experimental data
        Fexp_middle = Fexp[start_idx:end_idx]
        Vin_exp_middle = Vin_exp[start_idx:end_idx]
        Vout_exp_middle = Vout_exp[start_idx:end_idx]
        ratio_exp_middle = ratio_exp[start_idx:end_idx]
    else:
        warnings.warn(
            f"Fewer than {num_middle} data points available. Using all points for plotting."
        )
        Fexp_middle = Fexp
        Vin_exp_middle = Vin_exp
        Vout_exp_middle = Vout_exp
        ratio_exp_middle = ratio_exp
    # ---------------------------------------------------------

    # 2) Build p grid
    up_p = 8 / W_RMS  # Upper limit for p integration
    d_p = up_p / N_P  # Step size for p
    # Ensure p starts slightly away from 0 if needed by formulas, but matches linspace logic
    p_vals = np.linspace(
        d_p, up_p, N_P
    )  # Matches MATLAB d_p:d_p:up_p if N_P = up_p/d_p

    # Define psi_vals for function signature - only one value needed (Option C)
    psi_vals = np.array([0.0])  # e.g., psi=0

    # 3) Compute the model surface displacement Z(p,f)
    # Pass the single psi value
    print("Starting surface displacement calculation...")
    Z_pf = compute_surface_displacement(MODEL_FREQS, p_vals, psi_vals)
    print("... Displacement calculation finished.")

    # Check if Z_pf contains NaNs before proceeding
    if np.isnan(Z_pf).any():
        warnings.warn(
            "NaNs found in surface displacement results. Subsequent calculations may fail or be inaccurate."
        )

    # 4) Integrate to get probe-beam deflection angle vs. freq
    print("Starting probe deflection calculation...")
    pbd_angles = compute_probe_deflection(Z_pf, p_vals, MODEL_FREQS)
    print("... Probe deflection calculation finished.")

    if np.isnan(pbd_angles).any():
        warnings.warn("NaNs found in PBD angle results.")

    # 5) Convert to lock-in signals using fixed V_sum
    in_mod, out_mod, ratio_mod = compute_lockin_signals(pbd_angles, V_SUM_FIXED)

    # 6) Rough analysis is skipped (as requested)

    # 7) Plot model vs MIDDLE experimental data
    print("Plotting results...")
    plot_results(
        MODEL_FREQS,
        in_mod,
        out_mod,
        Fexp_middle,  # Pass middle data
        Vin_exp_middle,  # Pass middle data
        Vout_exp_middle,  # Pass middle data
        ratio_mod,
        ratio_exp_middle,  # Pass middle data
    )


if __name__ == "__main__":
    # Add basic error handling for imports if needed
    try:
        main()
    except NameError as e:
        if (
            "load_data" in str(e)
            or "calculate_leaking" in str(e)
            or "correct_data" in str(e)
        ):
            print(
                f"Error: Make sure the 'data_processing.py' module is in the same directory or Python path."
            )
        else:
            print(f"An unexpected NameError occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
