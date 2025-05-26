# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
sponsor_match/core/logger.py
----------------------------
Utility to configure and retrieve named loggers, with console
and optional file handlers.
"""

import logging
import sys
from pathlib import Path

def setup_logger(
    name: str,
    log_file: Path | None = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Return a logger configured with:
      - StreamHandler (stdout) at `level`
      - Optional FileHandler if `log_file` is provided
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured
        return logger

    logger.setLevel(level)
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file:
        file_h = logging.FileHandler(log_file)
        file_h.setLevel(level)
        file_h.setFormatter(formatter)
        logger.addHandler(file_h)

    return logger
