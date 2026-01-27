from __future__ import annotations

from gamevolt.application.role import Role


class WandsRole(Role):
    def __init__(self) -> None:
        super().__init__("wands")

    async def entry_point(self):
        import wands_main

        return await wands_main.main()
