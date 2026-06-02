from __future__ import annotations

import math
import struct
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.data.assembled_packet import AssembledPacket
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings
from wand.streaming.eliko_single_anchor.eliko_single_anchor_client import ElikoSingleAnchorClient
from wand.streaming.quat_forward_encoder import quat_to_forward_q15


class ElikoSingleAnchorWandImuStream:
    """WandImuStream backed by a single Eliko anchor over USB serial.

    Consumes raw PR lines from an `ElikoSingleAnchorClient`. Each PR sample is
    a 6-byte SFLP word packing 3 IEEE-754 half-floats (x, y, z) of a unit
    quaternion; w is recovered as sqrt(1 - x^2 - y^2 - z^2) per the STM
    `sflp2q` algorithm. Forward vectors are derived and Q15-encoded into the
    same `data_str` format `WandClient` already consumes.

    Anchor timestamps are emitted as a hex tick counter; we treat them as ms
    for `t0_ms` (consistent with the RTLS PR_Q path which uses `tag_ts_ms`).
    Per-sample dt is taken from settings (IMU hardware rate).
    """

    _LINE_PREFIX = "$PEKIO,PR,"
    _FORWARD_FMT = "forward"

    def __init__(
        self,
        logger: Logger,
        client: ElikoSingleAnchorClient,
        settings: ElikoParsingSettings,
    ) -> None:
        self._packet_received: Event[Callable[[AssembledPacket], None]] = Event()

        self._logger = logger
        self._client = client
        self._settings = settings

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
        if not line.startswith(self._LINE_PREFIX):
            self._logger.trace(f"Eliko single-anchor non-PR line: {line}")
            return

        try:
            packet = self._parse_pr_burst(line)
        except _ParseError as e:
            self._logger.debug(f"Eliko single-anchor PR parse error: {e}. line='{line}'")
            return

        self._packet_received.invoke(packet)

    def _parse_pr_burst(self, line: str) -> AssembledPacket:
        fields = line.split(",")
        # $PEKIO,PR,seq,anchor_id,tag_id,pr_type,ts_hex,raw0,...,raw(N-1)
        nsamp = self._settings.nsamp_per_packet
        expected = 7 + nsamp
        if len(fields) < expected:
            raise _ParseError(f"expected >= {expected} fields, got {len(fields)}")

        try:
            seq = int(fields[2])
            tag_hex = self._normalise_id(fields[4])
            t0_ms = int(fields[6], 16)
        except ValueError as e:
            raise _ParseError(f"header parse: {e}")

        forward_q15 = [self._raw_word_to_forward_q15(fields[7 + i]) for i in range(nsamp)]
        data_str = ";".join(f"{fx},{fy},{fz}" for (fx, fy, fz) in forward_q15)

        return AssembledPacket(
            seq=seq,
            t0_ms=t0_ms,
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

    def _raw_word_to_forward_q15(self, raw_field: str) -> tuple[int, int, int]:
        qx, qy, qz, qw = self._sflp_word_to_quat(raw_field)
        return quat_to_forward_q15(
            qx, qy, qz, qw,
            self._settings.body_forward_x,
            self._settings.body_forward_y,
            self._settings.body_forward_z,
        )

    @staticmethod
    def _sflp_word_to_quat(raw_field: str) -> tuple[float, float, float, float]:
        s = raw_field.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        if len(s) != 12:
            raise _ParseError(f"SFLP word must be 12 hex chars, got {len(s)}: {raw_field!r}")
        try:
            b = bytes.fromhex(s)
        except ValueError as e:
            raise _ParseError(f"SFLP hex decode: {e}")

        # Hex written MSB-first; pair-up to (x, y, z) of unit quat.
        try:
            x = struct.unpack(">e", b[0:2])[0]
            y = struct.unpack(">e", b[2:4])[0]
            z = struct.unpack(">e", b[4:6])[0]
        except struct.error as e:
            raise _ParseError(f"SFLP half decode: {e}")

        sumsq = x * x + y * y + z * z
        if sumsq > 1.0:
            n = math.sqrt(sumsq)
            x /= n
            y /= n
            z /= n
            sumsq = 1.0
        w = math.sqrt(1.0 - sumsq)
        return (x, y, z, w)


class _ParseError(Exception):
    pass
