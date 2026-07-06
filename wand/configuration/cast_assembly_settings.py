from gamevolt.configuration.appsetting import appsetting


@appsetting
class CastAssemblySettings:
    """Segment buffering + recognition-gated commit (see wand/cast_assembler.py).

    Makes segmentation forgiving (corner over-pauses merge, clean glyphs commit at a
    micro-pause) without loosening the score gates a cast must clear.
    """

    enabled: bool = True

    # Extra $1 accuracy bar for committing at a transient PAUSED (on top of the normal
    # scoring gates). No sustained still confirms intent there, so the match must be
    # unambiguous. Committing at HOLDING uses the normal gates only.
    soft_commit_accuracy: float = 0.60

    # Most recent segments considered for suffix joins. Bounds the buffer and the
    # per-event recognition cost.
    max_join_segments: int = 3

    # Segments older than this (vs the newest sample) fall out of the buffer — they can
    # no longer be part of the same cast.
    max_segment_age_s: float = 5.0

    # After a successful commit, trailing motion that dies at the next STOPPED within
    # this window is dropped silently instead of surfacing as a miscast (no fail streak,
    # no reject flash) — it's the wand being lowered, not an attempt.
    post_commit_suppression_s: float = 1.5
