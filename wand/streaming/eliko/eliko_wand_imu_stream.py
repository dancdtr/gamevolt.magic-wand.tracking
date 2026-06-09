from __future__ import annotations

from gamevolt.logging import Logger
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings
from wand.streaming.eliko.eliko_wand_imu_stream_base import ElikoParseError, ElikoWandImuStreamBase
from wand.streaming.wand_line_source import WandLineSource


class ElikoWandImuStream(ElikoWandImuStreamBase):
    """WandImuStream for the Eliko RTLS Server PR_Q line format.

    Each line is `$PEKIO,<report>,seq,anchor_sn,tag_sn,tag_ts_ms,q0,...,q(N-1)`
    where each sample is the text quad `qx;qy;qz;qw`. Body-frame forward is
    +Y; the base encodes `q*(0,1,0)` to Q15 into the existing data_str so
    WandClient consumes RTLS and single-anchor sources identically.
    """

    _SAMPLE_FIELD_OFFSET = 6

    def __init__(
        self,
        logger: Logger,
        client: WandLineSource,
        settings: ElikoParsingSettings,
        report_type: str,
    ) -> None:
        super().__init__(
            logger=logger,
            client=client,
            settings=settings,
            line_prefix=f"$PEKIO,{report_type},",
        )
        self._report_type = report_type

    def _parse_header(self, fields: list[str]) -> tuple[int, str, int]:
        try:
            seq = int(fields[2])
            tag_hex = self._normalise_id(fields[4])
            t0_ms = int(fields[5])
        except ValueError as e:
            raise ElikoParseError(f"header parse: {e}") from e
        return seq, tag_hex, t0_ms

    def _decode_sample_quat(self, field: str) -> tuple[float, float, float, float]:
        parts = field.split(";")
        if len(parts) != 4:
            raise ElikoParseError(f"quat must have 4 components, got {len(parts)}: {field!r}")
        try:
            return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
        except ValueError as e:
            raise ElikoParseError(f"quat parse: {e}") from e
