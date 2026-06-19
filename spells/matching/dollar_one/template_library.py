"""Build a DollarOneRecognizer from the SVG templates in spells/templates/.

Spike-stage source resolution: templates dir is resolved relative to this module.
When bundling (PyInstaller), switch to gamevolt.io.utils.bundled_path.
"""

from __future__ import annotations

from pathlib import Path

from gamevolt.logging import Logger
from spells.matching.dollar_one.dollar_one_recognizer import DollarOneRecognizer, PathTemplate, prepare
from spells.matching.dollar_one.svg_template_loader import load_svg_points


def templates_dir() -> Path:
    # spells/matching/dollar_one/template_library.py -> parents[2] == spells/
    return Path(__file__).resolve().parents[2] / "templates"


def load_default_library(
    logger: Logger, allowed_labels: set[str] | None = None, n: int = 64
) -> DollarOneRecognizer:
    """Build a recognizer from the template SVGs.

    `allowed_labels` (upper-cased spell labels) restricts the library to those templates —
    pass the union of zone-mapped spells to skip glyphs no zone can ever cast. None = load all.
    """
    directory = templates_dir()
    templates: list[PathTemplate] = []

    for svg in sorted(directory.glob("*.svg")):
        label = svg.stem.upper()
        if allowed_labels is not None and label not in allowed_labels:
            logger.info(f"$1 template skipped (no zone): {label} ({svg.name})")
            continue
        try:
            points = load_svg_points(svg)
        except Exception as exc:  # malformed SVG should not kill startup
            logger.warning(f"$1: failed to load template {svg.name}: {exc}")
            continue
        templates.append(PathTemplate(label=label, points=prepare(points, n)))
        logger.info(f"$1 template loaded: {label} ({svg.name})")

    if not templates:
        logger.warning(f"$1: no templates found in {directory}")

    return DollarOneRecognizer(templates, n)
