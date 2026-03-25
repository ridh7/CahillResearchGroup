"""Router modules for FastAPI endpoints."""

from . import analysis, sse

__all__ = ["analysis", "sse"]

# Hardware-dependent routers are imported lazily in main.py
# to allow running in analysis-only mode without pythonnet/pyvisa.
