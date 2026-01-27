"""Functions for thermal modeling in FD-PBD analysis."""

import numpy as np
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

    Uses Hankel transform to solve 3D heat diffusion in cylindrical coordinates.
    The spatial frequency k integration bounds are chosen based on beam geometry:
    - k_max: high-frequency cutoff where beam overlap becomes negligible
    - k_min: low-frequency cutoff to avoid singularities at k=0

    Args:
        lambda_down, c_down, h_down, eta_down: Sample parameters (thermal conductivity,
            volumetric heat capacity, layer thickness, thermal diffusion length ratio).
        lambda_up, c_up, h_up, eta_up: Air parameters (above sample).
        r_pump, r_probe: Pump and probe beam radii (1/e^2 intensity).
        a_dc: Total absorbed DC power from pump laser.

    Returns:
        Steady-state temperature rise at sample surface (K).
    """
    # Integration bounds for Hankel transform in spatial frequency domain
    # k_max set by beam overlap: beyond this k, pump-probe correlation is negligible
    k_max = 2 / np.sqrt(r_pump**2 + r_probe**2)
    # k_min avoids singularity at k=0 while capturing low-frequency response
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
    Compute temperature field in Hankel transform space for multilayer system.

    Uses transfer matrix method to compute thermal Green's function G(k,ω)
    for layered sample. Each layer is characterized by thermal parameters and
    thickness. Boundary conditions enforce continuity of temperature and
    heat flux at interfaces.

    Mathematical approach:
    1. Compute thermal impedance for each layer using complex wave vector u_n
    2. Build transfer matrices relating temperature/flux at layer interfaces
    3. Propagate from substrate (semi-infinite) up through layers to air
    4. Combine air and sample thermal impedances to get total Green's function
    5. Multiply by Gaussian beam profiles S(k) and P(k)

    Args:
        k: Spatial frequency (1/meters) - scalar or array
        freq: Modulation frequency (Hz) - 0 for steady-state
        lambda_up, c_up, h_up, eta_up: Air thermal parameters
        lambda_down, c_down, h_down, eta_down: Sample layer parameters (arrays)
        r_pump, r_probe: Pump and probe beam radii (meters)
        a_pump: Absorbed pump power (Watts)

    Returns:
        Complex temperature field integrand G(k)*S(k)*P(k)
    """
    # Handle scalar vs array input
    is_scalar = np.isscalar(k)
    k = np.atleast_1d(k)

    # Air layer thermal impedance
    alpha_up = lambda_up / c_up  # Thermal diffusivity
    omega = 2 * np.pi * freq  # Angular frequency
    q2 = 1j * omega / alpha_up  # Complex frequency term
    un = np.sqrt(4 * np.pi**2 * eta_up * k**2 + q2)  # Complex wave vector
    gamman = lambda_up * un  # Thermal impedance
    g_up = 1 / gamman  # Air thermal admittance

    # Sample layers thermal impedance (transfer matrix method)
    n_layers = len(lambda_down)
    alpha_down = lambda_down / c_down  # Layer diffusivities
    q2 = 1j * omega / alpha_down[-1]
    un = np.sqrt(4 * np.pi**2 * eta_down[-1] * k**2 + q2)
    gamman = lambda_down[-1] * un
    # Initialize substrate (bottom layer, semi-infinite)
    b_plus = np.zeros_like(k, dtype=complex)  # No upward-propagating wave
    b_minus = np.ones_like(k, dtype=complex)  # Only downward-propagating wave

    # Propagate through layers from bottom to top
    if n_layers > 1:
        for n in range(n_layers - 1, 0, -1):
            q2 = 1j * omega / alpha_down[n - 1]
            un_minus = np.sqrt(eta_down[n - 1] * 4 * np.pi**2 * k**2 + q2)
            gamman_minus = lambda_down[n - 1] * un_minus

            # Transfer matrix coefficients for interface matching
            aa = gamman_minus + gamman
            bb = gamman_minus - gamman
            temp1 = aa * b_plus + bb * b_minus
            temp2 = bb * b_plus + aa * b_minus
            exp_term = np.exp(un_minus * h_down[n - 1])

            # Update wave amplitudes for current layer
            b_plus = 0.5 / (gamman_minus * exp_term) * temp1
            b_minus = 0.5 / gamman_minus * exp_term * temp2

            # Penetration depth check: if layer >> thermal penetration depth,
            # treat as semi-infinite (no reflection from bottom interface)
            penetration_logic = h_down[n - 1] * np.abs(un_minus) > 100
            b_plus[penetration_logic] = 0
            b_minus[penetration_logic] = 1

            un = un_minus
            gamman = gamman_minus

    # Combine air and sample thermal admittances
    denominator = b_minus - b_plus
    denominator = np.where(np.abs(denominator) < 1e-10, 1e-10, denominator)
    g_down = (b_plus + b_minus) / denominator / gamman  # Sample admittance

    # Series combination of air and sample thermal resistances
    g = g_up * g_down / (g_up + g_down)  # Total Green's function

    # Gaussian beam profiles in Hankel space (Fourier transform of exp(-r²/w²))
    s = np.exp(-np.pi**2 * r_probe**2 / 2 * k**2)  # Probe sensitivity profile
    p = a_pump * np.exp(-np.pi**2 * r_pump**2 / 2 * k**2)  # Pump heating profile

    # Complete integrand: thermal response × probe × pump
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
    Compute photothermal beam deflection (PBD) signal vs frequency.

    Physical principle:
    - Modulated pump laser creates temperature oscillations in sample
    - Temperature gradient causes refractive index gradient in substrate
    - Probe laser beam deflects by angle proportional to ∇n (mirage effect)
    - Deflection measured by position-sensitive detector

    Mathematical model:
    - Temperature field T(r,z,ω) from bi_fdtr_bo_temp in Hankel space
    - Deflection angle θ = ∫∫ (dn/dT)(∂T/∂x) dz dx
    - Lateral offset x_offset accounts for pump-probe beam separation
    - Bessel function J₁ arises from Hankel transform of x∂/∂x operator

    Args:
        niu: Poisson's ratio of substrate (affects thermal expansion)
        coef: Thermo-optic coefficient dn/dT (1/K)
        freq: Array of modulation frequencies (Hz)
        lambda_down, c_down, h_down, eta_down: Sample layer parameters
        lambda_up, c_up, h_up, eta_up: Air parameters
        r_pump, r_probe: Beam radii (meters)
        a_pump: Pump power (Watts)
        x_offset: Lateral pump-probe offset (meters)

    Returns:
        Complex deflection angle at each frequency (radians)
    """
    # Build fixed k-grid for integration (independent of frequency)
    Nk = 200  # Grid resolution (tune for accuracy vs. speed)
    k_max = 2.0 / np.sqrt(r_pump**2 + r_probe**2)
    k = np.linspace(0.0, k_max, Nk)
    weight = 8 * np.pi**2 * k**2  # Jacobian for Hankel transform
    bessel = -j1(2 * np.pi * k * x_offset)  # J₁ from x∂/∂x operator
    # These two aren't used below but could be reused if needed:
    # S_probe = np.exp(- (np.pi**2 * r_probe**2)/2 * k**2)
    # P_pump  = a_pump * np.exp(- (np.pi**2 * r_pump**2)/2 * k**2)

    alpha_sub = lambda_down[2] / c_down[2]  # CaF2 substrate diffusivity
    c_probe = 0.7  # Calibration constant (empirical correction factor)

    # Allocate output array
    delta_theta = np.zeros(freq.shape, dtype=complex)

    # Loop over frequencies, integrate vectorized over k
    for i, f in enumerate(freq):
        ω = 2 * np.pi * f
        q2 = 1j * ω / alpha_sub  # Frequency-dependent term
        qk = np.sqrt(4 * np.pi**2 * eta_down[2] * k**2 + q2)  # Complex wave vector

        # Deflection susceptibility: combines thermo-optic effect and thermal penetration
        # Factor (1+ν) accounts for thermal expansion contribution to refractive index
        defl = (2 * (1 + niu) * coef) / (qk + 2 * np.pi * k)

        # Get temperature field G(k,f)*S(k)*P(k) from multilayer thermal model
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
        )  # Returns array of length Nk

        # Complete integrand: calibration × geometry × Bessel × deflection × temperature
        integrand = -c_probe * weight * bessel * defl * temp
        delta_theta[i] = np.trapz(integrand, k)  # Trapezoidal integration over k

    return delta_theta
