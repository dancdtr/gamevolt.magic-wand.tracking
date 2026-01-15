from dataclasses import dataclass


@dataclass()
class SpellsRole:
    name: str = "spells"

    async def run(self) -> int:
        import spells_main

        return int(await spells_main.main() or 0)
