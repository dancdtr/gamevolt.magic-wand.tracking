from __future__ import annotations

import math
import struct

from gamevolt.logging import Logger
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings
from wand.streaming.eliko.eliko_wand_imu_stream_base import ElikoParseError, ElikoWandImuStreamBase
from wand.streaming.wand_line_source import WandLineSource


class ElikoSingleAnchorWandImuStream(ElikoWandImuStreamBase):
    """WandImuStream for the single-anchor PR line format over USB serial.

    Each line is `$PEKIO,PR,seq,anchor_id,tag_id,pr_type,ts_hex,raw0,...,raw(N-1)`.
    Each raw sample is a 6-byte SFLP word packing 3 IEEE-754 half-floats
    (x, y, z) of a unit quaternion; w is recovered as
    sqrt(1 - x^2 - y^2 - z^2) per the STM `sflp2q` algorithm.

    Anchor timestamps are emitted as a hex tick counter; treated as ms for
    `t0_ms` (consistent with the RTLS PR_Q `tag_ts_ms`). Per-sample dt is
    taken from settings (IMU hardware rate, not derived from packet ts).
    """

    _LINE_PREFIX = "$PEKIO,PR,"
    _SAMPLE_FIELD_OFFSET = 7

    def __init__(
        self,
        logger: Logger,
        client: WandLineSource,
        settings: ElikoParsingSettings,
    ) -> None:
        super().__init__(
            logger=logger,
            client=client,
            settings=settings,
            line_prefix=self._LINE_PREFIX,
        )

    def _parse_header(self, fields: list[str]) -> tuple[int, str, int]:
        try:
            seq = int(fields[2])
            tag_hex = self._normalise_id(fields[4])
            t0_ms = int(fields[6], 16)
        except ValueError as e:
            raise ElikoParseError(f"header parse: {e}") from e
        return seq, tag_hex, t0_ms

    def _decode_sample_quat(self, field: str) -> tuple[float, float, float, float]:
        return self._sflp_word_to_quat(field)

    @staticmethod
    def _sflp_word_to_quat(raw_field: str) -> tuple[float, float, float, float]:
        s = raw_field.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        if len(s) != 12:
            raise ElikoParseError(f"SFLP word must be 12 hex chars, got {len(s)}: {raw_field!r}")
        try:
            b = bytes.fromhex(s)
        except ValueError as e:
            raise ElikoParseError(f"SFLP hex decode: {e}") from e

        try:
            x = struct.unpack(">e", b[0:2])[0]
            y = struct.unpack(">e", b[2:4])[0]
            z = struct.unpack(">e", b[4:6])[0]
        except struct.error as e:
            raise ElikoParseError(f"SFLP half decode: {e}") from e

        sumsq = x * x + y * y + z * z
        if sumsq > 1.0:
            n = math.sqrt(sumsq)
            x /= n
            y /= n
            z /= n
            sumsq = 1.0
        w = math.sqrt(1.0 - sumsq)
        return (x, y, z, w)
