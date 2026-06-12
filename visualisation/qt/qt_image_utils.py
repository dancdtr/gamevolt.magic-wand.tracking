from __future__ import annotations

from PIL.Image import Image as PILImage
from PySide6.QtGui import QImage, QPixmap


def pil_to_qpixmap(image: PILImage) -> QPixmap:
    """Convert a PIL image to a QPixmap (RGBA, copy-safe)."""
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimage = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
    # fromImage copies the pixel data, so it's safe once `data` is GC'd.
    return QPixmap.fromImage(qimage.copy())
