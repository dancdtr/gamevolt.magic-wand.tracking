# spells/matching/preprocess/segment_compressor.py
from __future__ import annotations

from collections.abc import Sequence

from motion.gesture.gesture_segment import GestureSegment


class SegmentCompressor:
    """
    Merge consecutive segments with the same direction_type.

    - duration_s and path_length are summed
    - net_dx/net_dy are summed
    - mean_speed is recomputed from (total_path / total_dur)
    - avg_vec_x/avg_vec_y are set to 0.0 for the merged segment
    """

    def compress(self, segments: Sequence[GestureSegment]) -> list[GestureSegment]:
        if not segments:
            return []

        out: list[GestureSegment] = []
        cur = segments[0]

        for seg in segments[1:]:
            if seg.direction_type == cur.direction_type:
                total_dur = cur.duration_s + seg.duration_s
                total_path = cur.path_length + seg.path_length

                cur = type(cur)(
                    start_ts_ms=cur.start_ts_ms,
                    end_ts_ms=seg.end_ts_ms,
                    duration_s=total_dur,
                    sample_count=cur.sample_count + seg.sample_count,
                    direction_type=cur.direction_type,
                    avg_vec_x=0.0,
                    avg_vec_y=0.0,
                    net_dx=cur.net_dx + seg.net_dx,
                    net_dy=cur.net_dy + seg.net_dy,
                    mean_speed=(total_path / total_dur) if total_dur > 0 else 0.0,
                    path_length=total_path,
                )
            else:
                out.append(cur)
                cur = seg

        out.append(cur)
        return out
