from dataclasses import dataclass


@dataclass()
class WandsRole:
    name: str = "wands"

    async def run(self) -> int:
        import wands_main

        return int(await wands_main.main() or 0)
