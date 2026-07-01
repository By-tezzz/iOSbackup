"""Modular iOS backup acquisition and extraction framework.

This package intentionally sits beside the legacy ``iOSbackup`` package so the
existing backup decryption API remains stable while newer acquisition and
plugin integrations evolve independently.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
