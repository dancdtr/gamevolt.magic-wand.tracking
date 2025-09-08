from PIL import Image
from PIL.Image import Image as PILImage


def recolour_region_by_threshold(
    image: PILImage,
    color: tuple[int, int, int] | tuple[int, int, int, int],
    thresh: int,
    select_above: bool = True,  # True = p > thresh, False = p <= thresh
) -> PILImage:
    """
    Replace only the selected luminance region with a solid color.
    - rgba: black-on-white icon image (any RGBA works)
    - color: RGB(A) fill color for the selected region (e.g., (0, 200, 0))
    - thresh: 0..255 threshold in luminance space
    - select: "above" (bright/background) or "below" (dark/icon)

    Returns a new RGBA image where selected pixels are colored, others preserved.
    """
    src = image.convert("RGBA")
    gray = src.convert("L")

    if select_above:
        # select bright pixels (background) → recolor background
        mask = gray.point(lambda p: 255 if p > thresh else 0)
    else:
        # select dark pixels (icon) → recolor icon
        mask = gray.point(lambda p: 255 if p <= thresh else 0)

    # solid color layer
    if len(color) == 3:
        color = (*color, 255)
    fill = Image.new("RGBA", src.size, color)

    # Where mask==255 take from fill; else keep original
    return Image.composite(fill, src, mask)
