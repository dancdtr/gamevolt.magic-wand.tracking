from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.data.assembled_packet import AssembledPacket
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings
from wand.streaming.quat_forward_encoder import quat_to_forward_q15
from wand.streaming.wand_line_source import WandLineSource


class ElikoParseError(Exception):
    """Raised by parsing helpers on malformed Eliko-format lines."""


class ElikoWandImuStreamBase(ABC):
    """Shared shape for WandImuStreams that consume Eliko-format PEKIO lines.

    Owns: client lifecycle, prefix-based filtering, AssembledPacket assembly,
    forward-vector Q15 encoding. Subclasses declare per-deployment specifics:
    line prefix, sample-field offset, header field layout, per-sample quat
    decoding (PR_Q text vs PR SFLP word).
    """

    _FORWARD_FMT = "forward"
    _SAMPLE_FIELD_OFFSET: int = 0

    def __init__(
        self,
        logger: Logger,
        client: WandLineSource,
        settings: ElikoParsingSettings,
        line_prefix: str,
    ) -> None:
        self._packet_received: Event[Callable[[AssembledPacket], None]] = Event()

        self._logger = logger
        self._client = client
        self._settings = settings
        self._line_prefix = line_prefix

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

    @abstractmethod
    def _parse_header(self, fields: list[str]) -> tuple[int, str, int]:
        """Return (seq, tag_hex, t0_ms) from the comma-split fields."""

    @abstractmethod
    def _decode_sample_quat(self, field: str) -> tuple[float, float, float, float]:
        """Decode one per-sample field into (qx, qy, qz, qw)."""

    def _handle_line(self, line: str) -> None:
        if not line.startswith(self._line_prefix):
            self._logger.trace(f"Eliko non-matching line ({self._line_prefix!r}): {line}")
            return

        try:
            packet = self._parse_burst(line)
        except ElikoParseError as e:
            self._logger.debug(f"Eliko parse error ({self._line_prefix!r}): {e}. line='{line}'")
            return

        self._packet_received.invoke(packet)

    def _parse_burst(self, line: str) -> AssembledPacket:
        fields = line.split(",")
        nsamp = self._settings.nsamp_per_packet
        offset = self._SAMPLE_FIELD_OFFSET
        expected = offset + nsamp
        if len(fields) < expected:
            raise ElikoParseError(f"expected >= {expected} fields, got {len(fields)}")

        seq, tag_hex, t0_ms = self._parse_header(fields)

        forward_q15 = [self._sample_to_forward_q15(fields[offset + i]) for i in range(nsamp)]
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

    def _sample_to_forward_q15(self, field: str) -> tuple[int, int, int]:
        qx, qy, qz, qw = self._decode_sample_quat(field)
        return quat_to_forward_q15(
            qx, qy, qz, qw,
            self._settings.body_forward_x,
            self._settings.body_forward_y,
            self._settings.body_forward_z,
        )

    @staticmethod
    def _normalise_id(raw: str) -> str:
        s = raw.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        return s.upper()
