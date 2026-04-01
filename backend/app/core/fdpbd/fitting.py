"""Functions for fitting FD-PBD data to thermal models."""

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares

from .thermal_model import delta_bo_theta


def fit_in_out(
    x_guess: list,
    v_corr_in: np.ndarray,
    v_corr_out: np.ndarray,
    niu: float,
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
    lb: list,
    ub: list,
    include_air_deflection: bool = False,
    dndt_up: float = -8.9e-7,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fit in-phase and out-of-phase signals to the FD-PBD model.

    Args:
        x_guess: Initial guess for [lambda_down[2], coef].
        v_corr_in: Corrected in-phase signal.
        v_corr_out: Corrected out-of-phase signal.
        niu: Poisson's ratio.
        freq: Frequency array.
        lambda_down, c_down, h_down, eta_down: Sample parameters.
        lambda_up, c_up, h_up, eta_up: Air parameters.
        r_pump, r_probe, a_pump, x_offset: Experimental parameters.
        lb, ub: Lower and upper bounds for fitting.

    Returns:
        Tuple of (fitted parameters, 95% confidence intervals).
    """

    def model(x, freq):
        lambda_down[2] = x[0]
        coef = x[1]
        delta_theta = delta_bo_theta(
            niu,
            coef,
            freq,
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
            include_air_deflection,
            dndt_up,
        )
        delta_out = np.imag(delta_theta)
        delta_in = np.real(delta_theta)
        max_in = np.max(np.abs(v_corr_in))
        return np.concatenate((delta_out / max_in, delta_in / (3 * max_in)))

    v_target = np.concatenate(
        (
            v_corr_out / np.max(np.abs(v_corr_in)),
            v_corr_in / (3 * np.max(np.abs(v_corr_in))),
        )
    )
    result = least_squares(
        lambda x: model(x, freq) - v_target,  # type: ignore[misc]
        x_guess,
        bounds=(lb, ub),
        method="trf",
    )
    x_sol = result.x

    # Approximate 95% confidence intervals (simplified)
    jac = result.jac
    resid = result.fun
    # Convert jac to ndarray for matrix operations
    jac_array: NDArray[np.float64] = (
        np.asarray(jac.todense()) if hasattr(jac, "todense") else np.asarray(jac)
    )
    cov: NDArray[np.float64] = np.linalg.inv(jac_array.T @ jac_array) * np.mean(
        resid**2
    )
    confidence = 1.96 * np.sqrt(np.diag(cov))  # 95% CI
    return x_sol, confidence


def fit_ratio(
    x_guess: float,
    v_corr_ratio: np.ndarray,
    niu: float,
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
) -> float:
    """
    Fit the ratio signal to the FD-PBD model.

    Args:
        x_guess: Initial guess for lambda_down[2].
        v_corr_ratio: Corrected ratio signal.
        Other parameters: Same as fit_in_out.

    Returns:
        Fitted thermal conductivity.
    """

    def model(x, freq):
        lambda_down[2] = x
        coef = 60e-6 * 65 * 0.19 / np.sqrt(2)  # Fixed, does not affect fit
        delta_theta = delta_bo_theta(
            niu,
            coef,
            freq,
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
        return -np.real(delta_theta) / np.imag(delta_theta)

    result = least_squares(
        lambda x: model(x, freq) - v_corr_ratio,  # type: ignore[misc]
        [x_guess],
        method="trf",
    )
    return float(result.x[0])
