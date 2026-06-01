from __future__ import annotations

import asyncio
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.data.assembled_packet import AssembledPacket
from wand.streaming.configuration.eliko_stream_settings import ElikoStreamSettings


class ElikoWandImuStream:
    """WandImuStream backed by an Eliko RTLS Server TCP feed.

    Connects to <host>:<port>, requests PR_Q (per-tag quaternion bursts), and
    emits one AssembledPacket per PR_Q line. The wand's body-frame forward
    axis is +Y, so each sample's forward vector is q * (0,1,0); the 10 forward
    vectors are Q15-encoded into the existing data_str format consumed by
    WandClient. Per-sample dt is taken as a fixed value from settings (the wand
    IMU's hardware rate); the packet's tag_ts_ms is used as t0.
    """

    _FORWARD_FMT = "forward"
    _Q15_MAX = 32767

    # Quick + dirty: pulse the tag's onboard LED on a spell cast.
    # _LED_PULSE_CMD = "$PEKIO,SET_TAG_LEDH,{tag_id},0x0AF0002\r\n"
    _LED_PULSE_CMD = "$PEKIO,SET_TAG_LEDH,{tag_id},0x0A0F0001\r\n"

    def __init__(self, logger: Logger, settings: ElikoStreamSettings) -> None:
        self._packet_received: Event[Callable[[AssembledPacket], None]] = Event()

        self._logger = logger
        self._settings = settings

        self._line_prefix = f"$PEKIO,{settings.report_type},"
        self._request = f"$PEKIO,SET_REPORT_LIST,{settings.report_type}\r\n".encode("ascii")

        self._task: asyncio.Task[None] | None = None
        self._writer: asyncio.StreamWriter | None = None

    @property
    def packet_received(self) -> Event[Callable[[AssembledPacket], None]]:
        return self._packet_received

    async def start_async(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name="ElikoWandImuStream")

    async def stop_async(self) -> None:
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await self._close_writer()

    def update(self) -> None:
        return

    def send_led_pulse(self, tag_id: str) -> None:
        writer = self._writer
        if writer is None:
            self._logger.warning(f"Eliko LED pulse dropped, no connection (tag={tag_id})")
            return
        command = self._LED_PULSE_CMD.format(tag_id=tag_id)
        writer.write(command.encode("ascii"))
        self._logger.debug(f"Eliko sent: {command.strip()}")

    async def _run(self) -> None:
        host = self._settings.host
        port = self._settings.port
        delay_s = self._settings.reconnect_delay_s

        while True:
            try:
                self._logger.info(f"Eliko stream connecting to {host}:{port}")
                reader, writer = await asyncio.open_connection(host, port)
                self._writer = writer
                writer.write(self._request)
                await writer.drain()
                self._logger.info(f"Eliko stream connected, requested {self._settings.report_type} reports")
                await self._read_loop(reader)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.warning(f"Eliko stream connection error: {e!r}")
            finally:
                await self._close_writer()

            await asyncio.sleep(delay_s)

    async def _read_loop(self, reader: asyncio.StreamReader) -> None:
        while True:
            raw = await reader.readline()
            if not raw:
                self._logger.info("Eliko stream EOF, will reconnect")
                return
            line = raw.decode("ascii", errors="replace").strip()
            if not line:
                continue
            self._handle_line(line)

    async def _close_writer(self) -> None:
        writer = self._writer
        self._writer = None
        if writer is None:
            return
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    def _handle_line(self, line: str) -> None:
        if not line.startswith(self._line_prefix):
            self._logger.trace(f"Eliko non-{self._settings.report_type} line: {line}")
            return

        try:
            packet = self._parse_quat_burst(line)
        except _ParseError as e:
            self._logger.debug(f"Eliko {self._settings.report_type} parse error: {e}. line='{line}'")
            return

        self._packet_received.invoke(packet)

    def _parse_quat_burst(self, line: str) -> AssembledPacket:
        fields = line.split(",")
        # $PEKIO,<report>,seq,anchor_sn,tag_sn,tag_ts_ms, q0, q1, ..., q(N-1)
        nsamp = self._settings.nsamp_per_packet
        expected = 6 + nsamp
        if len(fields) < expected:
            raise _ParseError(f"expected >= {expected} fields, got {len(fields)}")

        try:
            seq = int(fields[2])
            tag_hex = self._normalise_id(fields[4])
            tag_ts_ms = int(fields[5])
        except ValueError as e:
            raise _ParseError(f"header parse: {e}")

        forward_q15 = [self._quat_to_forward_q15(fields[6 + i]) for i in range(nsamp)]
        data_str = ";".join(f"{fx},{fy},{fz}" for (fx, fy, fz) in forward_q15)

        return AssembledPacket(
            seq=seq,
            t0_ms=tag_ts_ms,
            sample_dt_us=self._settings.sample_dt_us,
            tag_hex=tag_hex,
            nsamp=nsamp,
            fmt=self._FORWARD_FMT,
            data_str=data_str,
            header_age_s=0.0,
        )

    @staticmethod
    def _normalise_id(raw: str) -> str:
        s = raw.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        return s.upper()

    def _quat_to_forward_q15(self, quat_field: str) -> tuple[int, int, int]:
        parts = quat_field.split(";")
        if len(parts) != 4:
            raise _ParseError(f"quat must have 4 components, got {len(parts)}: {quat_field!r}")
        try:
            qx = float(parts[0])
            qy = float(parts[1])
            qz = float(parts[2])
            qw = float(parts[3])
        except ValueError as e:
            raise _ParseError(f"quat parse: {e}")

        vx = self._settings.body_forward_x
        vy = self._settings.body_forward_y
        vz = self._settings.body_forward_z

        # Algebra mirrored from firmware rotate_vec_by_quat so results match
        # the legacy path exactly when fed equivalent quats.
        tx = 2.0 * (qy * vz - qz * vy)
        ty = 2.0 * (qz * vx - qx * vz)
        tz = 2.0 * (qx * vy - qy * vx)

        fx = vx + qw * tx + (qy * tz - qz * ty)
        fy = vy + qw * ty + (qz * tx - qx * tz)
        fz = vz + qw * tz + (qx * ty - qy * tx)

        mag2 = fx * fx + fy * fy + fz * fz
        if mag2 > 1e-12:
            inv = mag2**-0.5
            fx *= inv
            fy *= inv
            fz *= inv

        return (self._to_q15(fx), self._to_q15(fy), self._to_q15(fz))

    @classmethod
    def _to_q15(cls, v: float) -> int:
        if v >= 1.0:
            return cls._Q15_MAX
        if v <= -1.0:
            return -cls._Q15_MAX
        return int(round(v * cls._Q15_MAX))


class _ParseError(Exception):
    pass
