from __future__ import annotations

import asyncio
import logging
import math

from gamevolt.logging._logger import Logger
from gamevolt.logging._levels import register_custom_levels
from gamevolt.tcp.configuration.tcp_client_settings import TcpClientSettings
from gamevolt.tcp.tcp_client import TcpClient
from wand.data.assembled_packet import AssembledPacket
from wand.streaming.eliko.configuration.eliko_connection_settings import ElikoConnectionSettings
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings
from wand.streaming.eliko.eliko_client import ElikoClient
from wand.streaming.eliko.eliko_wand_imu_stream import ElikoWandImuStream

TAG = "1DC6"
ANCHOR = "A0"
NSAMP = 10
DT_US = 8333


def _logger() -> Logger:
    register_custom_levels()
    logging.setLoggerClass(Logger)
    log = logging.getLogger("test.eliko_stream")
    log.setLevel(logging.WARNING)
    return log  # type: ignore[return-value]


def _quat_about_z(angle_rad: float) -> tuple[float, float, float, float]:
    half = angle_rad / 2.0
    return (0.0, 0.0, math.sin(half), math.cos(half))


async def _run_mock_server(nsamp: int) -> tuple[asyncio.AbstractServer, int]:
    seq = 0

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        nonlocal seq
        # Consume the SET_REPORT_LIST request the client sends on connect.
        await reader.readline()
        t_ms = 1_000
        try:
            while not writer.is_closing():
                quats = []
                for i in range(nsamp):
                    angle = 0.02 * (seq * nsamp + i)
                    qx, qy, qz, qw = _quat_about_z(angle)
                    quats.append(f"{qx};{qy};{qz};{qw}")
                line = f"$PEKIO,PR_Q,{seq},{ANCHOR},{TAG},{t_ms}," + ",".join(quats) + "\r\n"
                writer.write(line.encode("ascii"))
                await writer.drain()
                seq += 1
                t_ms += nsamp * DT_US // 1000
                await asyncio.sleep(0.005)
        except (ConnectionResetError, asyncio.CancelledError):
            pass

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, port


async def _drive() -> list[AssembledPacket]:
    server, port = await _run_mock_server(NSAMP)

    connection_settings = ElikoConnectionSettings(
        host="127.0.0.1",
        port=port,
        reconnect_delay_s=0.5,
        report_type="PR_Q",
    )
    parsing_settings = ElikoParsingSettings(
        sample_dt_us=DT_US,
        nsamp_per_packet=NSAMP,
        body_forward_x=0.0,
        body_forward_y=1.0,
        body_forward_z=0.0,
    )

    logger = _logger()
    tcp_client = TcpClient(
        logger=logger,
        settings=TcpClientSettings(
            host=connection_settings.host,
            port=connection_settings.port,
            reconnect_delay_s=connection_settings.reconnect_delay_s,
        ),
    )
    client = ElikoClient(logger=logger, settings=connection_settings, client=tcp_client)
    stream = ElikoWandImuStream(logger=logger, client=client, settings=parsing_settings, report_type="PR_Q")

    packets: list[AssembledPacket] = []
    stream.packet_received.subscribe(packets.append)

    await stream.start_async()
    await asyncio.sleep(1.0)
    await stream.stop_async()
    server.close()
    await server.wait_closed()
    return packets


def test_eliko_stream_parses_pr_q_packets() -> None:
    packets = asyncio.run(_drive())

    assert len(packets) > 0, "expected at least one PR_Q packet from mock server"
    first = packets[0]
    assert first.tag_hex == TAG
    assert first.nsamp == NSAMP
    assert first.fmt == "forward"
    assert first.sample_dt_us == DT_US
    # Each sample is "fx,fy,fz"; data_str packs nsamp samples joined by ';'.
    assert first.data_str.count(";") == NSAMP - 1
