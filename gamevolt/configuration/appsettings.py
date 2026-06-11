# gamevolt/configuration/appsettings.py
from __future__ import annotations

from typing import Any, Callable, TypeVar, overload

try:
    from typing import dataclass_transform
except ImportError:  # pragma: no cover
    from typing_extensions import dataclass_transform  # type: ignore

from gamevolt.configuration.appsetting import appsetting
from gamevolt.configuration.appsettings_base import AppSettingsBase

T = TypeVar("T", bound=type[Any])


@overload
def appsettings(cls: T, /, *, slots: bool = True, kw_only: bool = False) -> T: ...
@overload
def appsettings(*, slots: bool = True, kw_only: bool = False) -> Callable[[T], T]: ...


@dataclass_transform()
def appsettings(
    cls: T | None = None, /, *, slots: bool = True, kw_only: bool = False
) -> T | Callable[[T], T]:
    dec = appsetting(base=AppSettingsBase, slots=slots, kw_only=kw_only)
    return dec(cls) if cls is not None else dec
