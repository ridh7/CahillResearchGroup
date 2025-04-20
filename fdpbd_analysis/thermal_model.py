"""Functions for thermal modeling in FD-PBD analysis."""

import numpy as np
from scipy.integrate import quad
from scipy.special import j1
from integration import romberg_integration


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
    return np.real(result)


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
    Compute the photothermal beam deflection response.

    Args:
        niu: Poisson's ratio.
        coef: Scaling coefficient for thermal expansion.
        freq: Frequency array (Hz).
        lambda_down, c_down, h_down, eta_down: Sample parameters.
        lambda_up, c_up, h_up, eta_up: Air parameters.
        r_pump, r_probe: Beam radii.
        a_pump: Absorbed pump power.
        x_offset: Beam offset (m).

    Returns:
        Complex array of beam deflection angles.
    """
    k_max = 2 / np.sqrt(r_pump**2 + r_probe**2)
    omega = 2 * np.pi * freq
    alpha_down = lambda_down[2] / c_down[2]  # Substrate (CaF2)
    q2 = 1j * omega / alpha_down
    c_probe = 0.7  # Calibration constant for CaF2

    delta_theta = np.zeros(len(freq), dtype=complex)

    for n, f in enumerate(freq):

        def integrand(k):
            # Ensure scalar computation
            k = float(k)  # Force scalar
            q_k = np.sqrt(4 * np.pi**2 * eta_down[2] * k**2 + q2[n].item())
            deflection = (2 * (1 + niu) * coef) / (q_k + 2 * np.pi * k)
            bessel_term = -j1(2 * np.pi * k * x_offset)
            weight = 8 * np.pi**2 * k**2
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
            )
            return -c_probe * weight * bessel_term * deflection * temp

        # Integrate real and imaginary parts separately
        real_part, _ = quad(
            lambda k: np.real(integrand(k)), 0, k_max, epsabs=1e-8, epsrel=1e-8
        )
        imag_part, _ = quad(
            lambda k: np.imag(integrand(k)), 0, k_max, epsabs=1e-8, epsrel=1e-8
        )
        delta_theta[n] = real_part + 1j * imag_part

    return delta_theta
