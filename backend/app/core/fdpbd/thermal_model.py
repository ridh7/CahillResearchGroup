"""Functions for thermal modeling in FD-PBD analysis."""

import numpy as np
import time
from scipy.integrate import quad
from scipy.special import j1
from .integration import romberg_integration


def compute_steady_state_heat(
    lambda_down: np.ndarray,
    c_down: np.ndarray,
    h_down: np.ndarray,
    eta_down: np.ndarray,
    lambda_up: float,
    c_up: float,
    h_up: float,
    eta_up: float,
    r_pump: float,
    r_probe: float,
    a_dc: float,
) -> float:
    """
    Compute steady-state temperature rise due to laser heating.

    Args:
        lambda_down, c_down, h_down, eta_down: Sample parameters.
        lambda_up, c_up, h_up, eta_up: Air parameters.
        r_pump, r_probe: Beam radii.
        a_dc: Total absorbed power.

    Returns:
        Steady-state temperature rise (K).
    """
    k_max = 2 / np.sqrt(r_pump**2 + r_probe**2)
    k_min = 1 / (10000 * max(r_pump, r_probe))

    def integrand(k):
        return k * bi_fdtr_bo_temp(
            k,
            0.0,
            lambda_up,
            c_up,
            h_up,
            eta_up,
            lambda_down,
            c_down,
            h_down,
            eta_down,
            r_pump,
            r_probe,
            a_dc,
        )

    # Integrate and take real part (steady-state should be real)
    result = romberg_integration(integrand, k_min, k_max)
    output = np.real(result)
    return output


def bi_fdtr_bo_temp(
    k: np.ndarray,
    freq: float,
    lambda_up: float,
    c_up: float,
    h_up: float,
    eta_up: float,
    lambda_down: np.ndarray,
    c_down: np.ndarray,
    h_down: np.ndarray,
    eta_down: np.ndarray,
    r_pump: float,
    r_probe: float,
    a_pump: float,
) -> np.ndarray:
    """
    Compute the integrand for steady-state temperature calculation.

    Args:
        k: Spatial frequency (scalar or array).
        freq: Frequency (0 for steady-state).
        lambda_up, c_up, h_up, eta_up: Air parameters.
        lambda_down, c_down, h_down, eta_down: Sample parameters.
        r_pump, r_probe: Beam radii.
        a_pump: Absorbed pump power.

    Returns:
        Integrand (complex, scalar if k is scalar, array otherwise).
    """
    # Handle scalar vs array input
    is_scalar = np.isscalar(k)
    k = np.atleast_1d(k)

    alpha_up = lambda_up / c_up
    omega = 2 * np.pi * freq
    q2 = 1j * omega / alpha_up
    un = np.sqrt(4 * np.pi**2 * eta_up * k**2 + q2)
    gamman = lambda_up * un
    g_up = 1 / gamman

    n_layers = len(lambda_down)
    alpha_down = lambda_down / c_down
    q2 = 1j * omega / alpha_down[-1]
    un = np.sqrt(4 * np.pi**2 * eta_down[-1] * k**2 + q2)
    gamman = lambda_down[-1] * un
    b_plus = np.zeros_like(k, dtype=complex)
    b_minus = np.ones_like(k, dtype=complex)

    if n_layers > 1:
        for n in range(n_layers - 1, 0, -1):
            q2 = 1j * omega / alpha_down[n - 1]
            un_minus = np.sqrt(eta_down[n - 1] * 4 * np.pi**2 * k**2 + q2)
            gamman_minus = lambda_down[n - 1] * un_minus
            aa = gamman_minus + gamman
            bb = gamman_minus - gamman
            temp1 = aa * b_plus + bb * b_minus
            temp2 = bb * b_plus + aa * b_minus
            exp_term = np.exp(un_minus * h_down[n - 1])
            b_plus = 0.5 / (gamman_minus * exp_term) * temp1
            b_minus = 0.5 / gamman_minus * exp_term * temp2
            penetration_logic = h_down[n - 1] * np.abs(un_minus) > 100
            b_plus[penetration_logic] = 0
            b_minus[penetration_logic] = 1
            un = un_minus
            gamman = gamman_minus

    # Avoid division by zero
    denominator = b_minus - b_plus
    denominator = np.where(np.abs(denominator) < 1e-10, 1e-10, denominator)
    g_down = (b_plus + b_minus) / denominator / gamman
    g = g_up * g_down / (g_up + g_down)
    s = np.exp(-np.pi**2 * r_probe**2 / 2 * k**2)
    p = a_pump * np.exp(-np.pi**2 * r_pump**2 / 2 * k**2)

    result = g * s * p
    return result[0] if is_scalar else result


def delta_bo_theta(
    niu: float,
    coef: float,
    freq: np.ndarray,
    lambda_down: np.ndarray,
    c_down: np.ndarray,
    h_down: np.ndarray,
    eta_down: np.ndarray,
    lambda_up: float,
    c_up: float,
    h_up: float,
    eta_up: float,
    r_pump: float,
    r_probe: float,
    a_pump: float,
    x_offset: float,
) -> np.ndarray:
    """
    Compute the photothermal beam deflection response using
    a fixed k‐grid and trapezoidal integration.

    Returns a complex array of deflection angles at each frequency.
    """
    # 1) build fixed k‐grid and k‐only factors
    Nk = 200  # grid resolution (tune for accuracy vs. speed)
    k_max = 2.0 / np.sqrt(r_pump**2 + r_probe**2)
    k = np.linspace(0.0, k_max, Nk)
    weight = 8 * np.pi**2 * k**2
    bessel = -j1(2 * np.pi * k * x_offset)
    # These two aren’t used below but could be reused if needed:
    # S_probe = np.exp(- (np.pi**2 * r_probe**2)/2 * k**2)
    # P_pump  = a_pump * np.exp(- (np.pi**2 * r_pump**2)/2 * k**2)

    alpha_sub = lambda_down[2] / c_down[2]  # CaF2 substrate diffusivity
    c_probe = 0.7  # calibration constant

    # 2) allocate output
    delta_theta = np.zeros(freq.shape, dtype=complex)

    # 3) loop over frequencies, integrate vectorized over k
    for i, f in enumerate(freq):
        ω = 2 * np.pi * f
        q2 = 1j * ω / alpha_sub  # scalar
        qk = np.sqrt(4 * np.pi**2 * eta_down[2] * k**2 + q2)  # (Nk,)
        defl = (2 * (1 + niu) * coef) / (qk + 2 * np.pi * k)  # (Nk,)

        # get the layered G(k,f)*S(k)*P(k) vector
        temp = bi_fdtr_bo_temp(
            k,
            f,
            lambda_up,
            c_up,
            h_up,
            eta_up,
            lambda_down,
            c_down,
            h_down,
            eta_down,
            r_pump,
            r_probe,
            a_pump,
        )  # returns array of length Nk

        # full integrand and trapz
        integrand = -c_probe * weight * bessel * defl * temp
        delta_theta[i] = np.trapz(integrand, k)

    return delta_theta
