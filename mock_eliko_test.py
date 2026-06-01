from __future__ import annotations

import asyncio
import dataclasses
import math

from gamevolt.logging import get_logger
from wand.data.assembled_packet import AssembledPacket
from wand.streaming.eliko_wand_imu_stream import ElikoWandImuStream
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server import WandServer
from wands_app.appsettings import AppSettings

TAG = "1DC6"
# TAG = "1DAE"
ANCHOR = "A0"


def quat_about_z(angle_rad: float) -> tuple[float, float, float, float]:
    half = angle_rad / 2.0
    return (0.0, 0.0, math.sin(half), math.cos(half))  # qx;qy;qz;qw


async def run_mock_server(nsamp: int, dt_ms: float) -> tuple[asyncio.AbstractServer, int]:
    seq = 0

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        nonlocal seq
        request = await reader.readline()
        print(f"[mock-server] client connected, request={request!r}")
        t_ms = 1_000
        try:
            while not writer.is_closing():
                quats = []
                for i in range(nsamp):
                    angle = 0.02 * (seq * nsamp + i)  # slow sweep so forward vec moves
                    qx, qy, qz, qw = quat_about_z(angle)
                    quats.append(f"{qx};{qy};{qz};{qw}")
                line = f"$PEKIO,PR_Q,{seq},{ANCHOR},{TAG},{t_ms}," + ",".join(quats) + "\r\n"
                writer.write(line.encode("ascii"))
                await writer.drain()
                seq += 1
                t_ms += int(nsamp * dt_ms)
                await asyncio.sleep(0.02)
        except (ConnectionResetError, asyncio.CancelledError):
            pass

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, port


async def main() -> int:
    settings = AppSettings.load(
        config_file_path="wands_app/appsettings.yml",
        config_env_file_path="wands_app/appsettings.env.yml",
    )
    logger = get_logger(settings.logging)

    eliko = settings.imu_stream.eliko
    assert eliko is not None
    dt_ms = eliko.sample_dt_us / 1000.0

    server, port = await run_mock_server(eliko.nsamp_per_packet, dt_ms)
    print(f"[mock-server] listening on 127.0.0.1:{port}")

    eliko_local = dataclasses.replace(eliko, host="127.0.0.1", port=port)
    stream = ElikoWandImuStream(logger=logger, settings=eliko_local)
    wand_server = WandServer(logger=logger, settings=settings.server, imu_stream=stream)

    packets: list[AssembledPacket] = []
    rotations: list[WandRotationRaw] = []
    connected_ids: list[str] = []
    stream.packet_received.subscribe(packets.append)
    wand_server.wand_rotation_raw_updated.subscribe(rotations.append)

    def on_connected(c) -> None:
        connected_ids.append(c.id)
        print(f"[wand-server] CONNECTED client={c.id}")

    wand_server.wand_connected.subscribe(on_connected)

    wand_server.start()
    await stream.start_async()

    await asyncio.sleep(1.5)

    live_clients = [c.id for c in wand_server.connected_clients()]

    await stream.stop_async()
    wand_server.stop()
    server.close()
    await server.wait_closed()

    print("\n==== RESULTS ====")
    print(f"packets parsed         : {len(packets)}")
    print(f"rotations emitted      : {len(rotations)}")
    print(f"connected (live)       : {live_clients}")
    if packets:
        p = packets[0]
        print(f"first packet           : tag={p.tag_hex} seq={p.seq} nsamp={p.nsamp} fmt={p.fmt}")
        print(f"first packet data_str  : {p.data_str[:60]}...")
    if rotations:
        r0, rN = rotations[0], rotations[-1]
        print(f"first rotation         : id={r0.id} ms={r0.ms} fx={r0.fx:.4f} fy={r0.fy:.4f} fz={r0.fz:.4f}")
        print(f"last  rotation         : id={rN.id} ms={rN.ms} fx={rN.fx:.4f} fy={rN.fy:.4f} fz={rN.fz:.4f}")

    ok = len(packets) > 0 and len(rotations) == len(packets) * eliko.nsamp_per_packet and TAG in connected_ids and TAG in live_clients
    print(f"\nPASS: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
