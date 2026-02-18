from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FillerResult:
    """
    Result of attempting to consume a segment as filler.

    consumed:
      - False => cannot be consumed; caller should fail the window (for required-step mismatch)
      - True  => segment was consumed; caller should advance the segment index

    is_absorbed:
      - True  => counts as "absorbed jitter" (not filler); contributes to absorbed metrics
      - False => true filler; contributes to filler_duration

    group_idx:
      - for absorbed jitter, which group to credit into
      - for true filler, usually None (or you can set it if you want bookkeeping)
    """

    consumed: bool
    is_absorbed: bool
    duration_s: float
    distance: float
    group_idx: int | None = None
    adj: int | None = None  # optional debug info
