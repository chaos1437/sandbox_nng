# shared/logging.py
import logging
import sys
from pathlib import Path


def setup_logger(
    name: str,
    log_file: str | None = None,
    level=logging.DEBUG,
    console: bool = True,
):
    """Configure a logger with optional console and file output."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    if log_file:
        log_path = Path(__file__).parent.parent / "logs" / log_file
        fh = logging.FileHandler(log_path)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
