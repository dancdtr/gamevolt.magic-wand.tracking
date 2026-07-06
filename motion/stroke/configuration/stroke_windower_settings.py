from gamevolt.configuration.appsetting import appsetting


@appsetting
class StrokeWindowerSettings:
    """Windows the rotation stream into candidate strokes (see stroke_windower.py)."""

    min_points: int = 8  # strokes with fewer samples are noise and are dropped silently
    # Trailing cap on an open stroke: only the most recent span is kept, so a wand that
    # wanders without ever settling can't grow the stroke unbounded. 0 disables.
    max_open_duration_s: float = 8.0
