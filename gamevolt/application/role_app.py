# roles.py

from dataclasses import dataclass
from typing import Protocol


class Role(Protocol):
    """A role app must implement a single async entrypoint."""

    name: str

    # Import app entry point inside run() so PyInstaller sees it, and so import cost is role-specific
    async def run(self) -> int: ...

    # eg. import app_main
