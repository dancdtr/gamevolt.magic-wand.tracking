# appsettings_base.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Self, cast

import jsonmerge

from gamevolt.configuration.errors.appsettings_error import AppsettingsError
from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.io.file_handlers.file_handler import FileHandler
from gamevolt.io.file_handlers.json_file_handler import JsonFileHandler
from gamevolt.io.file_handlers.yaml_file_handler import YamlFileHandler
from gamevolt.io.typing import JsonLike


@dataclass
class AppSettingsBase(SettingsBase):
    name: str

    @classmethod
    def load(cls, config_file_path: str, config_env_file_path: str | None = None, *, strict: bool = True) -> Self:
        base_handler = cls._pick_handler(config_file_path)
        env_handler: FileHandler | None = cls._pick_handler(config_env_file_path) if config_env_file_path else None

        # Load base
        try:
            base_json = cast(JsonLike, base_handler.load(config_file_path))
        except Exception as e:
            raise AppsettingsError("AppSettings", f"failed to load '{config_file_path}': {e}") from None

        merged: JsonLike = base_json

        # Load env (optional, can be a different format)
        if config_env_file_path:
            try:
                env_json = (
                    cast(JsonLike, env_handler.try_load(config_env_file_path)) if env_handler is not None else None  # type: ignore[union-attr]
                )
            except Exception as e:
                raise AppsettingsError("AppSettings", f"failed to load env override '{config_env_file_path}': {e}") from None

            if env_json:
                try:
                    merged = cast(JsonLike, jsonmerge.merge(base_json, env_json))  # type: ignore[arg-type]
                except Exception as e:
                    raise AppsettingsError(
                        "AppSettings", f"failed to merge '{config_env_file_path}' into '{config_file_path}': {e}"
                    ) from None

        return cls.from_json_like(merged, strict=strict)

    @classmethod
    def from_yaml(cls, config_path: str, config_env_path: str | None = None, strict: bool = True) -> Self:
        return cls.from_configs(YamlFileHandler(), config_path, config_env_path, strict)

    @classmethod
    def from_json(cls, config_path: str, config_env_path: str | None = None, strict: bool = True) -> Self:
        return cls.from_configs(JsonFileHandler(), config_path, config_env_path, strict)

    @classmethod
    def from_configs(cls, file_handler: FileHandler, config_path: str, config_env_path: str | None = None, strict: bool = True) -> Self:
        """Legacy path: both files must be the same format as file_handler."""
        try:
            config_json = cast(JsonLike, file_handler.load(config_path))
        except Exception as e:
            raise AppsettingsError("AppSettings", f"failed to load '{config_path}': {e}") from None

        if config_env_path:
            try:
                config_env_json = cast(JsonLike | None, file_handler.try_load(config_env_path))
            except Exception as e:
                raise AppsettingsError("AppSettings", f"failed to load env override '{config_env_path}': {e}") from None
            if config_env_json:
                try:
                    config_json = cast(JsonLike, jsonmerge.merge(config_json, config_env_json))  # type: ignore[arg-type]
                except Exception as e:
                    raise AppsettingsError("AppSettings", f"failed to merge '{config_env_path}' into '{config_path}': {e}") from None

        return cls.from_json_like(config_json, strict=strict)

    @staticmethod
    def _pick_handler(path: str | None) -> FileHandler:
        if not path:
            raise AppsettingsError("AppSettings", "no config path provided")

        ext = os.path.splitext(path)[1].lower()
        if ext in (".yml", ".yaml"):
            return YamlFileHandler()
        if ext == ".json":
            return JsonFileHandler()

        # Fallback: sniff first non-space byte to guess JSON vs YAML
        try:
            with open(path, "rb") as f:
                head = f.read(64).lstrip()
        except OSError as e:
            raise AppsettingsError("AppSettings", f"cannot open '{path}': {e}") from None

        # JSON usually starts with '{' or '['; otherwise default to YAML (safe superset)
        if head.startswith(b"{") or head.startswith(b"["):
            return JsonFileHandler()
        return YamlFileHandler()
