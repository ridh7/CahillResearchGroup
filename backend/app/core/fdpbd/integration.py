"""Numerical integration using the Romberg method."""

import numpy as np


def romberg_integration(
    func: callable, a: float, b: float, dec_digits: int = 10
) -> complex:
    """
    Perform Romberg integration of a function, supporting complex-valued integrands.

    Args:
        func: Function to integrate (may return complex values).
        a, b: Integration limits.
        dec_digits: Number of decimal digits for accuracy.

    Returns:
        Complex integral result.
    """

    def real_integrator(x):
        """Helper function to integrate real part."""
        return np.real(func(x))

    def imag_integrator(x):
        """Helper function to integrate imaginary part."""
        return np.imag(func(x))

    def integrate_part(integrator):
        """Perform Romberg integration for a real-valued integrator."""
        rom = np.zeros((2, dec_digits))
        n_points = 2 ** (dec_digits - 1) + 1
        x = np.linspace(a, b, n_points)
        f_vals = integrator(x)
        h = b - a
        rom[0, 0] = h * (f_vals[0] + f_vals[-1]) / 2

        for i in range(1, dec_digits):
            st = 2 ** (dec_digits - i)
            rom[1, 0] = (
                rom[0, 0] + h * np.sum(f_vals[st // 2 : st : 2 ** (dec_digits - 1)])
            ) / 2
            for k in range(i):
                rom[1, k + 1] = (4 ** (k + 1) * rom[1, k] - rom[0, k]) / (
                    4 ** (k + 1) - 1
                )
            rom[0, : i + 1] = rom[1, : i + 1]
            h /= 2

        return rom[0, dec_digits - 1]

    # Integrate real and imaginary parts separately
    real_result = integrate_part(real_integrator)
    imag_result = integrate_part(imag_integrator)
    return real_result + 1j * imag_result
