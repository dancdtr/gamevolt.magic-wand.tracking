# appsettings_base.py
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Self, cast

import jsonmerge
from gamevolt.io import JsonObject, YamlObject
from gamevolt.io.file_handlers.file_handler import FileHandler
from gamevolt.io.file_handlers.json_file_handler import JsonFileHandler
from gamevolt.io.file_handlers.yaml_file_handler import YamlFileHandler

from gamevolt.configuration.errors.appsettings_error import AppsettingsError
from gamevolt.configuration.settings_base import SettingsBase

logger = logging.getLogger(__name__)

type ConfigObject = JsonObject | YamlObject


@dataclass
class AppSettingsBase(SettingsBase):

    @classmethod
    def load(
        cls,
        config_file_path: str,
        config_env_file_path: str | None = None,
        *,
        strict: bool = True,
    ) -> Self:
        """Load config, auto-detecting YAML vs JSON by extension or content."""
        base_handler = cls._pick_handler(config_file_path)
        env_handler = (
            cls._pick_handler(config_env_file_path) if config_env_file_path else None
        )
        if env_handler is None:
            logger.debug("AppSettings env override path not provided.")
        return cls._load_and_merge(
            base_handler, config_file_path, env_handler, config_env_file_path, strict=strict
        )

    @classmethod
    def from_yaml(
        cls, config_path: str, config_env_path: str | None = None, strict: bool = True
    ) -> Self:
        env_handler: FileHandler | None = YamlFileHandler() if config_env_path else None
        return cls._load_and_merge(
            YamlFileHandler(), config_path, env_handler, config_env_path, strict=strict
        )

    @classmethod
    def from_json(
        cls, config_path: str, config_env_path: str | None = None, strict: bool = True
    ) -> Self:
        env_handler: FileHandler | None = JsonFileHandler() if config_env_path else None
        return cls._load_and_merge(
            JsonFileHandler(), config_path, env_handler, config_env_path, strict=strict
        )

    @classmethod
    def from_configs(
        cls,
        file_handler: FileHandler,
        config_path: str,
        config_env_path: str | None = None,
        strict: bool = True,
    ) -> Self:
        """Legacy path: both files must be the same format as file_handler."""
        env_handler: FileHandler | None = file_handler if config_env_path else None
        return cls._load_and_merge(
            file_handler, config_path, env_handler, config_env_path, strict=strict
        )

    @classmethod
    def _load_and_merge(
        cls,
        base_handler: FileHandler,
        base_path: str,
        env_handler: FileHandler | None,
        env_path: str | None,
        *,
        strict: bool,
    ) -> Self:
        """Load base config, optionally deep-merge an env override, then deserialise."""
        try:
            base_json = cast(ConfigObject, base_handler.load(base_path))
        except Exception as e:
            raise AppsettingsError(
                f"failed to load '{base_path}': {e}", path="AppSettings"
            ) from e

        if env_path is None or env_handler is None:
            return cls.from_json_like(base_json, strict=strict)

        if not os.path.exists(env_path):
            logger.warning(
                "AppSettings env override not found (will ignore): %s", env_path
            )
            return cls.from_json_like(base_json, strict=strict)

        logger.info("AppSettings env override found: %s", env_path)

        try:
            env_json = cast(ConfigObject | None, env_handler.load_if_exists(env_path))
        except Exception as e:
            raise AppsettingsError(
                f"failed to load env override '{env_path}': {e}", path="AppSettings"
            ) from e

        if not env_json:
            logger.info(
                "AppSettings env override not applied (empty): %s", env_path
            )
            return cls.from_json_like(base_json, strict=strict)

        logger.info(
            "AppSettings env override loaded and will be merged: %s", env_path
        )
        try:
            merged = cast(ConfigObject, jsonmerge.merge(base_json, env_json))  # type: ignore[arg-type]
        except Exception as e:
            raise AppsettingsError(
                f"failed to merge '{env_path}' into '{base_path}': {e}",
                path="AppSettings",
            ) from e

        return cls.from_json_like(merged, strict=strict)

    @staticmethod
    def _pick_handler(path: str | None) -> FileHandler:
        if not path:
            raise AppsettingsError("no config path provided", path="AppSettings")

        ext = os.path.splitext(path)[1].lower()
        if ext in (".yml", ".yaml"):
            return YamlFileHandler()
        if ext == ".json":
            return JsonFileHandler()

        # Fallback: sniff first non-whitespace byte to guess JSON vs YAML
        try:
            with open(path, "rb") as f:
                head = f.read(64).lstrip()
        except OSError as e:
            raise AppsettingsError(
                f"cannot open '{path}': {e}", path="AppSettings"
            ) from e

        # JSON always starts with '{' or '['; default to YAML (safe superset)
        if head.startswith(b"{") or head.startswith(b"["):
            return JsonFileHandler()
        return YamlFileHandler()
