from __future__ import annotations

import logging
from typing import Final

PACKET: Final[int] = 3
TRACE: Final[int] = 5
VERBOSE: Final[int] = 8

INFORMATION: Final[int] = logging.INFO
WARNING: Final[int] = logging.WARNING
ERROR: Final[int] = logging.ERROR
CRITICAL: Final[int] = logging.CRITICAL


level_to_name_map: dict[int, str] = {
    TRACE: "TRACE",
    VERBOSE: "VERBOSE",
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFORMATION",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
}

name_to_level_map: dict[str, int] = {
    "TRACE": TRACE,
    "VERBOSE": VERBOSE,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "INFORMATION": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.CRITICAL,
}


def register_custom_levels() -> None:
    logging.addLevelName(TRACE, "TRACE")
    logging.addLevelName(VERBOSE, "VERBOSE")
