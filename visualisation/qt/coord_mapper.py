from __future__ import annotations

from visualisation.coordinate_mode import CoordinateMode


def map_trail_point(
    nx: float,
    ny: float,
    w: int,
    h: int,
    *,
    coords_mode: CoordinateMode,
    y_up: bool,
    clip: bool,
    margin: int,
) -> tuple[float, float]:
    """Map a trail coordinate into widget pixels.

    Maps into a centred *square* region (side = the smaller widget dimension) so equal
    x/y motion renders undistorted regardless of the pane's aspect ratio — a circular
    flourish stays circular on a wide or tall pane.
    """
    m = max(0, margin)
    side = max(1, min(w, h) - 2 * m)
    # Centre the square region within the (possibly non-square) widget.
    ox = (w - side) / 2.0
    oy = (h - side) / 2.0

    if coords_mode is CoordinateMode.CENTRED:
        if clip:
            nx = max(-1.0, min(1.0, nx))
            ny = max(-1.0, min(1.0, ny))
        x = ox + ((nx + 1.0) * 0.5) * (side - 1)
        v = (1.0 - (ny + 1.0) * 0.5) if y_up else ((ny + 1.0) * 0.5)
        return x, oy + v * (side - 1)

    if coords_mode is CoordinateMode.UNIT:
        if clip:
            nx = max(0.0, min(1.0, nx))
            ny = max(0.0, min(1.0, ny))
        x = ox + nx * (side - 1)
        v = (1.0 - ny) if y_up else ny
        return x, oy + v * (side - 1)

    raise ValueError(f"Unknown coords_mode: '{coords_mode}'")


def map_normalized_point(
    px: float,
    py: float,
    w: int,
    h: int,
    *,
    margin: int,
    y_up: bool,
) -> tuple[float, float]:
    """Map a $1-normalised point (centroid at origin, longest axis ~1, so ~[-0.5, 0.5])
    into a centred square inside the widget."""
    m = max(0, margin)
    side = max(1, min(w, h) - 2 * m)
    cx = w / 2.0
    cy = h / 2.0
    x = cx + px * side
    y = cy - py * side if y_up else cy + py * side
    return x, y
