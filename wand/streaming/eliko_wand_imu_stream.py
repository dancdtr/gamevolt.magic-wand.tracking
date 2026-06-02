from __future__ import annotations

from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.data.assembled_packet import AssembledPacket
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings
from wand.streaming.eliko.eliko_client import ElikoClient
from wand.streaming.quat_forward_encoder import quat_to_forward_q15


class ElikoWandImuStream:
    """WandImuStream backed by an Eliko RTLS Server TCP feed.

    Consumes lines from a shared `ElikoClient`, filters to PR_Q (per-tag
    quaternion bursts), and emits one AssembledPacket per line. The wand's
    body-frame forward axis is +Y, so each sample's forward vector is
    q * (0,1,0); the 10 forward vectors are Q15-encoded into the existing
    data_str format consumed by WandClient. Per-sample dt is taken as a fixed
    value from settings (the wand IMU's hardware rate); the packet's
    tag_ts_ms is used as t0.
    """

    _FORWARD_FMT = "forward"

    def __init__(
        self,
        logger: Logger,
        client: ElikoClient,
        settings: ElikoParsingSettings,
        report_type: str,
    ) -> None:
        self._packet_received: Event[Callable[[AssembledPacket], None]] = Event()

        self._logger = logger
        self._client = client
        self._settings = settings
        self._report_type = report_type

        self._line_prefix = f"$PEKIO,{report_type},"

    @property
    def packet_received(self) -> Event[Callable[[AssembledPacket], None]]:
        return self._packet_received

    async def start_async(self) -> None:
        self._client.line_received.subscribe(self._handle_line)
        await self._client.start_async()

    async def stop_async(self) -> None:
        await self._client.stop_async()
        self._client.line_received.unsubscribe(self._handle_line)

    def update(self) -> None:
        return

    def _handle_line(self, line: str) -> None:
        if not line.startswith(self._line_prefix):
            self._logger.trace(f"Eliko non-{self._report_type} line: {line}")
            return

        try:
            packet = self._parse_quat_burst(line)
        except _ParseError as e:
            self._logger.debug(f"Eliko {self._report_type} parse error: {e}. line='{line}'")
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

        return quat_to_forward_q15(
            qx, qy, qz, qw,
            self._settings.body_forward_x,
            self._settings.body_forward_y,
            self._settings.body_forward_z,
        )


class _ParseError(Exception):
    pass
