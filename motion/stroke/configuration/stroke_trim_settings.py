from gamevolt.configuration.appsetting import appsetting


@appsetting
class StrokeTrimSettings:
    """Trims a straight run at one end of a stroke before $1 matching and the snapshot
    overlay. Used for both the 'approach' lead-in (rest/centre into the glyph start, e.g.
    the SW diagonal into the base of an R) and the 'reset' tail (glyph end back toward
    rest/centre). The corner detection is end-agnostic; see stroke_trimmer.py."""

    enabled: bool
    angle_deg: float  # heading deviation from the run direction that marks the glyph edge (a corner)
    min_trim_fraction: float  # ignore trims smaller than this fraction of the path (no real run)
    max_trim_fraction: float  # never trim more than this fraction of the path (safety clamp)
    resample_count: int  # points to arc-length resample to for stable corner detection
