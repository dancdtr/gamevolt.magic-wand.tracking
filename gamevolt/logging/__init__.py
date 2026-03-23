import logging
import os

from gamevolt.logging.configuration.logging_settings import LoggingSettings

from ._formatting import GameVoltFormatter
from ._levels import CRITICAL, ERROR, INFORMATION, PACKET, TRACE, VERBOSE, WARNING, name_to_level_map, register_custom_levels
from ._logger import Logger


def _remove_and_close_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def get_logger(
    settings: LoggingSettings | None = None,
    name: str = "gamevolt",
) -> Logger:
    register_custom_levels()
    logging.setLoggerClass(Logger)

    settings = settings or LoggingSettings()

    minimum_level_name = settings.minimum_level.upper()
    if minimum_level_name not in name_to_level_map:
        valid_levels = ", ".join(name_to_level_map.keys())
        raise ValueError(f"Invalid minimum log level '{settings.minimum_level}'. " f"Valid values: {valid_levels}")

    minimum_level = name_to_level_map[minimum_level_name]
    formatter = GameVoltFormatter()

    log_dir = os.path.dirname(os.path.abspath(settings.file_path))
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    if not isinstance(logger, Logger):
        raise TypeError(
            f"Logger '{name}' was created before GameVoltLogger was registered. " "Call get_logger() before creating named loggers."
        )

    _remove_and_close_handlers(logger)

    logger.setLevel(minimum_level)
    logger.propagate = False

    file_handler = logging.FileHandler(settings.file_path, encoding="utf-8")
    file_handler.setLevel(minimum_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(minimum_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


__all__ = [
    "CRITICAL",
    "ERROR",
    "GameVoltFormatter",
    "Logger",
    "INFORMATION",
    "LoggingSettings",
    "TRACE",
    "VERBOSE",
    "WARNING",
    "PACKET",
    "get_logger",
]
