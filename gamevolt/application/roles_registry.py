# gamevolt/application/roles_registry.py
from __future__ import annotations

from typing import Iterable

from gamevolt.application.role import Role


class RolesRegistry:
    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}

    def register(self, role: Role) -> RolesRegistry:
        if role.name in self._roles:
            raise ValueError(f"Role '{role.name}' already registered")
        self._roles[role.name] = role

        return self

    def get(self, name: str) -> Role | None:
        return self._roles.get(name)

    def require(self, name: str) -> Role:
        role = self.get(name)
        if role is None:
            raise KeyError(f"Unknown role: {name}")
        return role

    def all(self) -> Iterable[Role]:
        return self._roles.values()

    def names(self) -> list[str]:
        return list(self._roles.keys())
