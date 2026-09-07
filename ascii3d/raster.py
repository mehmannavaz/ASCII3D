"""Render ASCII text frames as PNG images (needs Pillow).

Shared by :mod:`ascii3d.rotation` (animated GIF export) and
:mod:`ascii3d.vlm` (vision model input): drawing a character grid
with a monospaced font so an ASCII frame can leave the terminal.
"""

from __future__ import annotations

__all__ = ['load_font', 'text_to_image', 'text_to_png', 'text_to_png_bytes']

_MONO_FONTS = (
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
    '/usr/share/fonts/truetype/freefont/FreeMono.ttf',
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
)


def load_font(size: int = 14):
    """Load a monospaced font for rendering (Pillow).

    Tries a list of common monospaced fonts and falls back to
    Pillow's built-in bitmap font.

    Args:
        size: Glyph size in pixels.

    Returns:
        An ``ImageFont`` instance.

    Raises:
        ImportError: If Pillow is not installed.
    """
    from PIL import ImageFont
    for path in _MONO_FONTS:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, ImportError):
            continue
    return ImageFont.load_default()


def _metrics(font, size: int) -> tuple[int, int]:
    """Character advance and line height for *font*."""
    try:
        bbox = font.getbbox('M')
        advance = max(1, bbox[2] - bbox[0])
    except AttributeError:  # pragma: no cover - bitmap font fallback
        advance = 6
    line_height = int(size * 1.25)
    return advance, max(line_height, size)


def text_to_image(text: str, font_size: int = 14,
                  background=(12, 12, 12), foreground=(220, 220, 210),
                  pad: int | None = None):
    """Draw *text* onto a new Pillow image.

    Args:
        text: The ASCII frame (rows separated by newlines).
        font_size: Glyph size in pixels.
        background: RGB background colour.
        foreground: RGB stroke colour.
        pad: Blank border in pixels (default: one glyph).

    Returns:
        A ``PIL.Image.Image``.

    Raises:
        ImportError: If Pillow is not installed.
    """
    from PIL import Image, ImageDraw
    font = load_font(font_size)
    advance, line_height = _metrics(font, font_size)
    if pad is None:
        pad = font_size
    lines = text.split('\n')
    width = max((len(line) for line in lines), default=0) * advance \
        + 2 * pad
    height = len(lines) * line_height + 2 * pad
    image = Image.new('RGB', (width, height), background)
    draw = ImageDraw.Draw(image)
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            if ch != ' ':
                draw.text((pad + c * advance, pad + r * line_height), ch,
                          fill=foreground, font=font)
    return image


def text_to_png(text: str, path: str, font_size: int = 14,
                background=(12, 12, 12), foreground=(220, 220, 210)
                ) -> str:
    """Draw *text* to a PNG file.

    Args:
        text: The ASCII frame.
        path: Output file path.
        font_size: Glyph size in pixels.
        background: RGB background colour.
        foreground: RGB stroke colour.

    Returns:
        The *path* written.
    """
    text_to_image(text, font_size, background, foreground).save(path)
    return path


def text_to_png_bytes(text: str, font_size: int = 14,
                      background=(12, 12, 12),
                      foreground=(220, 220, 210)) -> bytes:
    """Draw *text* to PNG bytes (in memory).

    Args:
        text: The ASCII frame.
        font_size: Glyph size in pixels.
        background: RGB background colour.
        foreground: RGB stroke colour.

    Returns:
        The PNG file as bytes.
    """
    import io
    buffer = io.BytesIO()
    text_to_image(text, font_size, background, foreground).save(
        buffer, format='PNG')
    return buffer.getvalue()
