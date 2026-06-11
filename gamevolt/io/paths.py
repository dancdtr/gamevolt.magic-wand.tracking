from __future__ import annotations

import sys
from pathlib import Path


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return _entry_dir()


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return _entry_dir()


def bundled_path(*parts: str) -> Path:
    return bundle_root().joinpath(*parts)


def runtime_path(*parts: str) -> Path:
    return runtime_root().joinpath(*parts)


def _entry_dir() -> Path:
    try:
        entry = Path(sys.argv[0]).resolve()
        if entry.is_file():
            return entry.parent
    except Exception:
        pass

    return Path.cwd()
