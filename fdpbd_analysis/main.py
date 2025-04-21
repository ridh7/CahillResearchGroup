#!/usr/bin/env python3
"""Main script for FD-PBD analysis of thermal properties."""

import numpy as np
import matplotlib.pyplot as plt
from data_processing import load_data, correct_data, calculate_leaking
from fitting import fit_in_out, fit_ratio
from thermal_model import compute_steady_state_heat, delta_bo_theta

# Hard-coded parameters
DATA_FILENAME = "1_CaF2_176mV-100k-100Hz_40P_1pump_0p85probe_5X"
F_AMP = 95e3  # Hz, from fit to Ni and CaF2
DELAY_1 = 0.89e-5  # s, from fit to Ni
DELAY_2 = -1.3e-11  # s, from fit to Ni

# Sample parameters (Al film, interface, CaF2)
LAMBDA_DOWN = np.array([149.0, 0.1, 9.7])  # W/m-K
ETA_DOWN = np.array([1.0, 1.0, 1.0])  # Anisotropy
C_DOWN = np.array([2.44e6, 0.1e6, 2.73e6])  # J/m^3-K
H_DOWN = np.array([70e-9, 1e-9, 1e-6])  # m
NIU = 0.26  # Poisson's ratio
ALPHA_T = 18.85e-6  # /K, coefficient of thermal expansion

# Air parameters
LAMBDA_UP = 0.028  # W/m-K
ETA_UP = 1.0
C_UP = 1192.0  # J/m^3-K
H_UP = 1e-3  # m

# Experimental parameters
R_RMS = 11.20e-6  # m, beam radius
X_OFFSET = 12.6e-6  # m, beam offset
R_PUMP = R_RMS
R_PROBE = R_RMS
INCIDENT_PUMP = 1.06e-3  # W
INCIDENT_PROBE = 0.85e-3  # W
N_AL = 2.9  # Al refractive index
K_AL = 8.2  # Al imaginary index
LENS_TRANSMITTANCE = 0.93
REFL_AL = abs(N_AL - 1 + 1j * K_AL) ** 2 / abs(N_AL + 1 + 1j * K_AL) ** 2
ABSORBED_PUMP = 1 - REFL_AL
A_PUMP = INCIDENT_PUMP * LENS_TRANSMITTANCE * 4.0 / np.pi * ABSORBED_PUMP
A_DC = (INCIDENT_PUMP + INCIDENT_PROBE) * ABSORBED_PUMP


def main():
    """Run the FD-PBD analysis."""
    # Load data
    v_out, v_in, v_ratio, v_sum, freq = load_data(DATA_FILENAME)

    # Calculate leaking correction
    complex_leaking = calculate_leaking(freq, F_AMP, DELAY_1, DELAY_2)

    # Correct data
    v_corr_in, v_corr_out, v_corr_ratio = correct_data(v_out, v_in, complex_leaking)

    # Calculate average sum voltage
    v_sum_avg = np.mean(v_sum)
    coef = ALPHA_T * 2 * 37.0 * v_sum_avg / np.sqrt(2)  # For 10x objective

    # Compute steady-state heating
    t_ss_heat = compute_steady_state_heat(
        LAMBDA_DOWN,
        C_DOWN,
        H_DOWN,
        ETA_DOWN,
        LAMBDA_UP,
        C_UP,
        H_UP,
        ETA_UP,
        R_PUMP,
        R_PROBE,
        A_DC,
    )
    print(f"Steady-state temperature rise: {t_ss_heat:.2f} K")

    # Determine fitting frequency range
    idx_peak = np.argmax(np.abs(v_corr_out))
    fc = freq[idx_peak]
    mask = (freq >= fc / 10) & (freq <= fc * 10)
    freq_fit = freq[mask]
    v_corr_in_fit = v_corr_in[mask]
    v_corr_out_fit = v_corr_out[mask]
    v_corr_ratio_fit = v_corr_ratio[mask]

    # Perform fitting (in-phase and out-of-phase)
    x_guess = [LAMBDA_DOWN[2], coef]
    lb = [0.0, -100.0]
    ub = [100.0, 100.0]
    x_sol, confidence = fit_in_out(
        x_guess,
        v_corr_in_fit,
        v_corr_out_fit,
        NIU,
        freq_fit,
        LAMBDA_DOWN,
        C_DOWN,
        H_DOWN,
        ETA_DOWN,
        LAMBDA_UP,
        C_UP,
        H_UP,
        ETA_UP,
        R_PUMP,
        R_PROBE,
        A_PUMP,
        X_OFFSET,
        lb,
        ub,
    )
    lambda_measure = x_sol[0]
    coef_fitted = x_sol[1]
    alpha_t_fitted = coef_fitted / (2 * 37 * v_sum_avg / np.sqrt(2))
    print(f"Fitted thermal conductivity: {lambda_measure:.4f} W/m-K")
    print(f"Fitted thermal expansion: {alpha_t_fitted:.4e} /K")

    # Compute model for plotting
    delta_theta = delta_bo_theta(
        NIU,
        coef_fitted,
        freq_fit,
        LAMBDA_DOWN,
        C_DOWN,
        H_DOWN,
        ETA_DOWN,
        LAMBDA_UP,
        C_UP,
        H_UP,
        ETA_UP,
        R_PUMP,
        R_PROBE,
        A_PUMP,
        X_OFFSET,
    )
    delta_in = np.real(delta_theta)
    delta_out = np.imag(delta_theta)
    delta_ratio = -delta_in / delta_out

    # Plot results
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.semilogx(freq_fit, v_corr_in_fit, "ko", label="In-phase (data)")
    plt.semilogx(freq_fit, v_corr_out_fit, "ko", label="Out-of-phase (data)")
    plt.semilogx(freq_fit, delta_in, "b-", label="In-phase (model)")
    plt.semilogx(freq_fit, delta_out, "r-", label="Out-of-phase (model)")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("In/Out-of-phase (V)")
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.loglog(freq_fit, v_corr_ratio_fit, "ko", label="Ratio (data)")
    plt.loglog(freq_fit, delta_ratio, "b-", label="Ratio (model)")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Ratio")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
