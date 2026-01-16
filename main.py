from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Sequence

import uvloop

from application.spells_role import SpellsRole
from application.wands_role import WandsRole
from gamevolt.application.roles_registry import RolesRegistry

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

roles = RolesRegistry().register(WandsRole()).register(SpellsRole())


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _get_arg_value(prefix: str, default: str | None = None) -> str | None:
    for arg in sys.argv[1:]:
        if arg.startswith(prefix + "="):
            return arg.split("=", 1)[1]
    return default


def _log_build_info() -> None:
    try:
        import build_info

        print(f"Build: v{build_info.VERSION} ({build_info.GIT_SHA}) {build_info.BUILD_TIME_UTC}")
    except Exception:
        print("Build: (no build_info)")


async def _run_supervisor() -> int:
    if _is_frozen():
        cmd_wands: Sequence[str] = [sys.executable, "--role=wands"]
        cmd_spells: Sequence[str] = [sys.executable, "--role=spells"]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        cmd_wands = [sys.executable, os.path.join(here, "wands_main.py")]
        cmd_spells = [sys.executable, os.path.join(here, "spells_main.py")]

    wands_proc = await asyncio.create_subprocess_exec(*cmd_wands, start_new_session=True)
    spells_proc = await asyncio.create_subprocess_exec(*cmd_spells, start_new_session=True)

    async def terminate(proc: asyncio.subprocess.Process) -> None:
        if proc.returncode is not None:
            return
        try:
            proc.send_signal(signal.SIGINT)
        except ProcessLookupError:
            return
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
            return
        except asyncio.TimeoutError:
            pass
        try:
            proc.terminate()
        except ProcessLookupError:
            return
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    t_wands = asyncio.create_task(wands_proc.wait())
    t_spells = asyncio.create_task(spells_proc.wait())
    t_stop = asyncio.create_task(stop_event.wait())

    done, _ = await asyncio.wait({t_wands, t_spells, t_stop}, return_when=asyncio.FIRST_COMPLETED)

    if t_stop in done:
        await terminate(wands_proc)
        await terminate(spells_proc)
        return 0

    if t_wands in done:
        await terminate(spells_proc)
        return int(wands_proc.returncode or 0)

    await terminate(wands_proc)
    return int(spells_proc.returncode or 0)


def main() -> int:
    role = _get_arg_value("--role", default=None)

    # Role mode: run one role app in-process
    if role:
        app = roles.get(role)
        if not app:
            print(f"Unknown role: {role}")
            return 2
        print(f"Starting role: {role}")
        return int(asyncio.run(app.run()) or 0)

    # Supervisor mode
    print("Starting wand demo application...")

    _log_build_info()
    try:
        return int(asyncio.run(_run_supervisor()) or 0)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
