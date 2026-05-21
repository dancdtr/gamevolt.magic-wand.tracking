from __future__ import annotations

import asyncio
import os

from gamevolt.io.utils import bundled_path, install_path
from gamevolt.logging import get_logger
from wands.appsettings import AppSettings
from wands.system_builder import WandsSystemBuilder

application_dir = os.path.dirname(os.path.abspath(__file__))
config_path = bundled_path("appsettings.yml")
config_env_path = install_path("appsettings.env.yml")
settings = AppSettings.load(config_file_path=config_path, config_env_file_path=config_env_path)
print(settings)

logger = get_logger(settings.logging)

system = WandsSystemBuilder(logger, settings).build()

quit_event = asyncio.Event()
system.tracking.quit.subscribe(lambda: quit_event.set())
system.recognition.quit.subscribe(lambda: quit_event.set())


async def main() -> int:
    logger.info(f"Running '{settings.name}'...")

    try:
        await system.tracking.start_async()
        await system.recognition.start_async()
    except Exception:
        logger.exception("Startup failure in wands_main")
        return 1

    try:
        while not quit_event.is_set():
            system.tracking.update()
            system.recognition.update()
            await asyncio.sleep(0.01)

        return 0
    except asyncio.exceptions.CancelledError:
        pass
    except Exception:
        logger.exception("Unhandled exception in wands_main")
        return 1

    finally:
        logger.info(f"Stopping '{settings.name}'...")
        await system.recognition.stop_async()
        await system.tracking.stop_async()
        logger.info(f"Exited '{settings.name}'.")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
