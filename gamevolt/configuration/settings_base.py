# gamevolt/configuration/settings_base.py
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from types import NoneType, UnionType
from typing import Any, ClassVar, Dict, Iterable, Type, TypeVar, get_args, get_origin, get_type_hints

from gamevolt.configuration.errors.appsettings_error import AppsettingsError

T = TypeVar("T", bound="SettingsBase")

import numbers
import typing
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, ClassVar, Dict, Iterable, Type, TypeVar, get_args, get_origin, get_type_hints

T = TypeVar("T", bound="SettingsBase")


def _issubclass_safe(t: Any, base: type) -> bool:
    try:
        return isinstance(t, type) and issubclass(t, base)
    except Exception:
        return False


def _ensure_settings_dataclass(tp: Any, path: str) -> None:
    if not isinstance(tp, type):
        raise AppsettingsError(f"annotation must be a class type, got {tp!r}", path=path)
    if not is_dataclass(tp):
        raise AppsettingsError(f"'{tp.__name__}' must be a @dataclass.", path=path)
    if not _issubclass_safe(tp, SettingsBase):
        raise AppsettingsError(f"'{tp.__name__}' must inherit SettingsBase.", path=path)


def _type_name(tp: Any) -> str:
    try:
        return str(tp).replace("typing.", "")
    except Exception:
        return repr(tp)


def _assert_type(value: Any, hint: Any, path: str) -> None:
    """Raise TypeError if value doesn't conform to hint. Non-destructive (no coercion)."""
    # Handle Annotated[..., meta]
    if get_origin(hint) is typing.Annotated:
        hint = get_args(hint)[0]

    # Optional/Union
    if get_origin(hint) in (typing.Union, typing.Optional):
        options = get_args(hint)
        if value is None and type(None) in options:
            return
        # Pass if any option matches
        last_error = None
        for opt in options:
            if opt is type(None):
                continue
            try:
                _assert_type(value, opt, path)
                return
            except TypeError as e:
                last_error = e
        raise TypeError(f"{path}: {value!r} does not match any of {_type_name(hint)}") from last_error

    # Enums
    if _issubclass_safe(hint, Enum):
        if isinstance(value, hint):
            return
        raise TypeError(f"{path}: expected {_type_name(hint)}, got {type(value).__name__}: {value!r}")

    # Nested SettingsBase
    if _issubclass_safe(hint, SettingsBase):
        if isinstance(value, hint):
            # recurse into nested
            value._validate_types(path)  # type: ignore[attr-defined]
            return
        raise TypeError(f"{path}: expected {_type_name(hint)}, got {type(value).__name__}")

    origin = get_origin(hint)
    args = get_args(hint)

    # Typed containers
    if origin in (list, set, tuple):
        if not isinstance(value, origin if origin is not tuple else (tuple, list)):
            raise TypeError(
                f"{path}: expected {origin.__name__}, got {type(value).__name__}."
                f"Is the appsettings/environment file defined correctly?"
                f" Is the FIELD_HANDLERS for {path} properly overridden?"
            )
        elem_hint = args[0] if args else Any

        # Fixed-length tuple like tuple[float, float, float]
        if origin is tuple and len(args) > 1 and args[-1] is not ...:
            seq = list(value)
            if len(seq) != len(args):
                raise TypeError(f"{path}: expected tuple of len {len(args)}, got len {len(seq)}")
            for i, (elem, eh) in enumerate(zip(seq, args)):
                _assert_type(elem, eh, f"{path}[{i}]")
            return

        # Variadic tuple or list/set
        for i, elem in enumerate(value):
            _assert_type(elem, elem_hint, f"{path}[{i}]")
        return

    if origin is dict:
        if not isinstance(value, dict):
            raise TypeError(f"{path}: expected dict, got {type(value).__name__}")
        key_hint, val_hint = args if args else (Any, Any)
        for k, v in value.items():
            _assert_type(k, key_hint, f"{path}.<key>")
            _assert_type(v, val_hint, f"{path}[{k!r}]")
        return

    # Primitives
    if hint in (int, float, str, bool):
        if hint is bool:
            if isinstance(value, bool):
                return
            raise TypeError(f"{path}: expected bool, got {type(value).__name__}")
        if hint is int:
            if isinstance(value, bool):  # bool is subclass of int; reject
                raise TypeError(f"{path}: expected int, got bool")
            if isinstance(value, int):
                return
            raise TypeError(f"{path}: expected int, got {type(value).__name__}")
        if hint is float:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return
            raise TypeError(f"{path}: expected float, got {type(value).__name__}")
        if hint is str:
            if isinstance(value, str):
                return
            raise TypeError(f"{path}: expected str, got {type(value).__name__}")

    # Any / no hint
    if hint is Any or hint is None:
        return

    # Fallback nominal check
    if isinstance(value, hint):
        return

    # Last resort: callable slipped in unexpectedly?
    if callable(value):
        raise TypeError(f"{path}: unexpected callable value {value!r} for {_type_name(hint)}")

    raise TypeError(f"{path}: {value!r} is not of expected type {_type_name(hint)}")


def _coerce_enum(value: Any, enum_cls: type[Enum]) -> Enum:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        key = value.strip()
        name = key.upper().replace("-", "_")
        if name in enum_cls.__members__:
            return enum_cls.__members__[name]
        # accept by value when enum values are strings
        for m in enum_cls:
            if isinstance(m.value, str) and m.value.lower() == key.lower():
                return m
    try:
        return enum_cls(value)
    except Exception as e:
        allowed = ", ".join(sorted(list(enum_cls.__members__.keys()) + [str(m.value) for m in enum_cls]))
        raise ValueError(f"{enum_cls.__name__}: {value!r} not in {{{allowed}}}") from e


@dataclass
class SettingsBase:
    FIELD_HANDLERS: ClassVar[Dict[str, Any]] = {}

    def __post_init__(self) -> None:
        # Validate after construction; subclasses inherit this automatically.
        self._validate_types(self.__class__.__name__)

    def __str__(self) -> str:
        return self.format_settings(self, indent=0)

    def _validate_types(self, path: str) -> None:
        hints = get_type_hints(self.__class__, include_extras=True)
        for f in fields(self.__class__):
            key = f.name
            if key not in hints:
                continue
            val = getattr(self, key)
            try:
                _assert_type(val, hints[key], f"{path}.{key}")
            except TypeError as e:
                # Re-raise with clear message
                raise

    def format_settings(self, obj: Any, indent: int = 0) -> str:
        """Pretty-print nested SettingsBase dataclasses and simple containers."""
        indent_str = "  " * indent
        cls_name = obj.__class__.__name__
        lines: list[str] = [f"{indent_str}-> {cls_name}:"]

        # Only iterate declared dataclass fields so we don't show ClassVars, etc.
        for f in fields(obj.__class__):
            key = f.name
            value = getattr(obj, key)
            pad = "  " * (indent + 1)

            if isinstance(value, SettingsBase):
                lines.append(self.format_settings(value, indent + 1))
                continue

            if isinstance(value, Enum):
                lines.append(f"{pad}-> {key}: {value}")
                continue

            if isinstance(value, (list, tuple, set)):
                if not value:
                    lines.append(f"{pad}-> {key}: []")
                else:
                    lines.append(f"{pad}-> {key}: [")
                    for item in value:
                        if isinstance(item, SettingsBase):
                            lines.append(self.format_settings(item, indent + 2))
                        else:
                            lines.append(f"{'  '*(indent+2)}{item}")
                    lines.append(f"{pad}]")
                continue

            lines.append(f"{pad}-> {key}: {value}")

        return "\n".join(lines)

    @classmethod
    def from_json_like(cls: Type[T], json: Dict[str, Any], *, strict: bool = True) -> T:
        _ensure_settings_dataclass(cls, cls.__name__)
        return cls._from_json_like_impl(json, path=cls.__name__, strict=strict)

    @classmethod
    def _from_json_like_impl(cls: Type[T], json: Dict[str, Any], *, path: str, strict: bool) -> T:
        cls_fields = {f.name for f in fields(cls)}
        unneeded = {k: v for k, v in (json or {}).items() if k not in cls_fields}
        if unneeded:
            if strict:
                raise ValueError(f"[{path}] unexpected keys: {sorted(unneeded)}")
            else:
                print(f"[SettingsBase] Warning: unexpected keys in {path}: {sorted(unneeded)}")

        filtered = {k: v for k, v in (json or {}).items() if k in cls_fields}
        hints = get_type_hints(cls)

        def is_optional(tp: Any) -> bool:
            return (type(tp) is UnionType and NoneType in tp.__args__) or (get_origin(tp) is not None and NoneType in get_args(tp))

        optionals = {k for k, v in hints.items() if is_optional(v)}
        missing = cls_fields - filtered.keys() - optionals
        if missing:
            raise ValueError(f"[{path}] missing required keys: {sorted(missing)}")

        out: Dict[str, Any] = {}
        for key, value in filtered.items():
            # 1) Per-field handler (with context)
            if key in cls.FIELD_HANDLERS:
                try:
                    out[key] = cls.FIELD_HANDLERS[key](value)
                except Exception as e:
                    raise ValueError(f"[{path}.{key}] handler failed for value={value!r}: {e}") from e
                continue

            hint = hints.get(key)
            if hint is None:
                out[key] = value
                continue

            # Unwrap Optional[T] → base
            base = hint
            if is_optional(base):
                args = [a for a in get_args(base) if a is not NoneType]
                base = args[0] if args else base

            # 2) Nested settings object (dict → dataclass subclass of SettingsBase)
            if isinstance(value, dict) and isinstance(base, type):
                _ensure_settings_dataclass(base, f"{path}.{key}")  # raises if not @dataclass or not SettingsBase
                out[key] = base._from_json_like_impl(value, path=f"{path}.{key}", strict=strict)
                continue
            if isinstance(value, dict):
                # Got a dict but annotation isn’t a class type — likely a missing/incorrect annotation
                raise TypeError(
                    f"[{path}.{key}] got a dict but annotation is {base!r}; "
                    "did you forget to annotate this field with SettingsBase dataclass?"
                )

            # 3) Enum scalar
            try:
                if isinstance(base, type) and issubclass(base, Enum):
                    out[key] = _coerce_enum(value, base)
                    continue
            except Exception as e:
                raise ValueError(f"[{path}.{key}] enum parse failed for value={value!r}: {e}") from e

            # 4) Containers (list/set/tuple) of Enums or Settings
            origin = get_origin(base)
            args = get_args(base)
            if origin in (list, set, tuple) and args:
                elem = args[0]
                if isinstance(elem, type) and issubclass(elem, Enum):
                    try:
                        seq = [_coerce_enum(v, elem) for v in (value or [])]
                        out[key] = type(value)(seq) if isinstance(value, tuple) else seq
                        continue
                    except Exception as e:
                        raise ValueError(f"[{path}.{key}] enum-seq parse failed for value={value!r}: {e}") from e
                if isinstance(elem, type) and issubclass(elem, SettingsBase):
                    try:
                        seq = [elem._from_json_like_impl(v, path=f"{path}.{key}[{i}]", strict=strict) for i, v in enumerate(value or [])]
                        out[key] = type(value)(seq) if isinstance(value, tuple) else seq
                        continue
                    except Exception:
                        raise  # nested adds its own path

            # 5) Fallback
            out[key] = value
            for k in optionals:
                if k not in out:
                    out[k] = None

        return cls(**out)
