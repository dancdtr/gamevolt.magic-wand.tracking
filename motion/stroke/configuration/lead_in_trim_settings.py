from gamevolt.configuration.appsetting import appsetting


@appsetting
class LeadInTrimSettings:
    """Trims the straight 'approach' run people draw moving from their rest/centre
    orientation to where the actual glyph begins (e.g. the SW diagonal into the base
    of an R). Trimmed before $1 matching and the snapshot overlay."""

    enabled: bool
    angle_deg: float  # heading deviation from the approach direction that marks the glyph start (a corner)
    min_trim_fraction: float  # ignore trims smaller than this fraction of the path (no real lead-in)
    max_trim_fraction: float  # never trim more than this fraction of the path (safety clamp)
    resample_count: int  # points to arc-length resample to for stable corner detection
