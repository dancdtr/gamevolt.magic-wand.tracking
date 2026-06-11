# gamevolt/configuration/appsetting.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar, overload

from gamevolt.configuration.settings_base import SettingsBase

try:
    # Python 3.11+
    from typing import dataclass_transform
except ImportError:  # pragma: no cover
    # pip install typing_extensions for 3.10/3.9
    from typing_extensions import dataclass_transform  # type: ignore


T = TypeVar("T", bound=type[Any])


@overload
def appsetting(
    cls: T,
    /,
    *,
    base: type[SettingsBase] = SettingsBase,
    slots: bool = True,
    kw_only: bool = False,
) -> T: ...
@overload
def appsetting(
    *,
    base: type[SettingsBase] = SettingsBase,
    slots: bool = True,
    kw_only: bool = False,
) -> Any: ...


@dataclass_transform()
def appsetting(
    cls: T | None = None,
    /,
    *,
    base: type[SettingsBase] = SettingsBase,
    slots: bool = True,
    kw_only: bool = False,
):
    """
    Decorator that:
      1) creates a new class that inherits (cls, base)
      2) re-declares the annotated fields (and defaults) so dataclass can see them
      3) applies @dataclass to the new class (so base.__post_init__ runs)

    Your class *definition* does not need to inherit SettingsBase.
    """

    def wrap(user_cls: T) -> T:
        anns = dict(getattr(user_cls, "__annotations__", {}))

        # Copy defaults for fields (dataclasses look on the class dict for defaults)
        ns: dict[str, Any] = {
            "__annotations__": anns,
            "__module__": user_cls.__module__,
        }
        for name in anns.keys():
            if hasattr(user_cls, name):
                ns[name] = getattr(user_cls, name)

        # Allow per-class override of FIELD_HANDLERS without touching the shared base dict
        if "FIELD_HANDLERS" in user_cls.__dict__:
            ns["FIELD_HANDLERS"] = user_cls.__dict__["FIELD_HANDLERS"]

        # Important: keep user_cls as a base (don’t copy its methods), so any zero-arg super()
        # inside methods (if you ever add them) still works correctly.
        New = type(user_cls.__name__, (user_cls, base), ns)

        # dataclass on the final class ensures __init__ calls SettingsBase.__post_init__
        New = dataclass(New, slots=slots, kw_only=kw_only)  # type: ignore[misc]

        return New  # type: ignore[return-value]

    return wrap(cls) if cls is not None else wrap
