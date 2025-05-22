#!/usr/bin/env python3
"""
SponsorMatch AI package.

Expose subpackages and provide package version information.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("sponsor_match")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "core",
    "data",
    "models",
    "services",
    "ui",
]
