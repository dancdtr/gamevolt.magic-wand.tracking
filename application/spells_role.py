from __future__ import annotations

from gamevolt.application.role import Role


class SpellsRole(Role):
    def __init__(self) -> None:
        super().__init__("spells")

    async def entry_point(self):
        import spells_main

        return await spells_main.main()
