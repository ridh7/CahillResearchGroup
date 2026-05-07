"""Functions for loading and correcting FD-PBD experimental data."""

import os

import numpy as np
from numpy.typing import NDArray


def load_data(
    filename: str,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """
    Load experimental data from a text file.

    Args:
        filename: Name of the data file (without .txt extension).

    Returns:
        Tuple of (V_out, V_in, V_ratio, V_sum, freq) arrays.
    """
    filepath = f"data/{filename}.txt"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file {filepath} not found.")

    data: NDArray[np.float64] = np.loadtxt(filepath).T
    v_in = data[0]
    v_out = data[1]
    freq = data[2]
    v_sum = data[3]
    v_ratio = -v_in / v_out
    return v_out, v_in, v_ratio, v_sum, freq


def calculate_leaking(
    freq: NDArray[np.float64],
    *,
    delay_0: float = 0.0,
    delay_1: float = 0.0,
    delay_2: float = 0.0,
    amplitude_corrected_0: float = 0.0,
    amplitude_corrected_1: float = 0.0,
    amplitude_corrected_2: float = 0.0,
    amplitude_corrected_3: float = 0.0,
) -> NDArray[np.complex128]:
    """
    Calculate the complex leaking correction factor.

        complex_leaking = (A0 + A1*sqrt(f) + A2*f + A3*f**1.5)
                          * exp(1j*(delay_0 + delay_1*f + delay_2*f**2)*1.1)
    """
    sf = np.sqrt(freq)
    amp = (
        amplitude_corrected_0
        + amplitude_corrected_1 * sf
        + amplitude_corrected_2 * sf**2
        + amplitude_corrected_3 * sf**3
    )
    phase = np.exp(1j * (delay_0 + delay_1 * freq + delay_2 * freq**2) * 1.1)
    res: NDArray[np.complex128] = amp * phase
    return res


def correct_data(
    v_out: NDArray[np.float64],
    v_in: NDArray[np.float64],
    complex_leaking: NDArray[np.complex128],
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """
    Correct measured data using the leaking factor.

    Args:
        v_out: Out-of-phase signal.
        v_in: In-phase signal.
        complex_leaking: Complex leaking correction factor.

    Returns:
        Tuple of corrected (V_in, V_out, V_ratio).
    """
    v_complex = v_in + 1j * v_out
    v_corrected = v_complex / complex_leaking
    v_corr_in = np.real(v_corrected)
    v_corr_out = np.imag(v_corrected)
    v_corr_ratio = -v_corr_in / v_corr_out
    return v_corr_in, v_corr_out, v_corr_ratio
