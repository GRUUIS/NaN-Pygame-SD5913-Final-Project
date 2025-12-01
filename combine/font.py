"""Font helper moved for `combine` runner compatibility.

This file is a direct move of `src/utils/font.py` so that lightweight
`combine` scripts can use font helpers without importing from `src`.
"""
import os
import pygame

_FONT_PATHS = [
    os.path.join('assets', 'art', 'Silver.ttf'),
    os.path.join('assets', 'art', 'silver.ttf'),
    os.path.join('assets', 'art', 'Silver.TTF'),
    # Also look for fonts in common asset locations
    os.path.join('assets', 'fonts', 'Silver.ttf'),
    os.path.join('assets', 'fonts', 'silver.ttf'),
    os.path.join('assets', 'Silver.ttf'),
    # Also look in the combine/docs folder in case the font was placed there
    os.path.join('combine', 'docs', 'Silver.ttf'),
    os.path.join('combine', 'docs', 'silver.ttf'),
]


def _find_font_path():
    # Check common explicit locations first
    for p in _FONT_PATHS:
        if os.path.exists(p):
            return p

    # If not found, walk the assets directory looking for a file that
    # contains 'silver' in the filename (case-insensitive) and has a
    # typical font extension. This helps when the font was placed in
    # a different subfolder (e.g. assets/fonts/, assets/art/, etc.).
    assets_dir = 'assets'
    if os.path.exists(assets_dir):
        for root, dirs, files in os.walk(assets_dir):
            for fname in files:
                lower = fname.lower()
                if 'silver' in lower and (lower.endswith('.ttf') or lower.endswith('.otf')):
                    return os.path.join(root, fname)

    return None


def get_font_path():
    """Return the path to the Silver.ttf if found, otherwise None."""
    return _find_font_path()


def get_font(size: int):
    """Return a pygame Font of the requested size. Prefer Silver.ttf if present.

    Falls back to pygame's default font if Silver.ttf is not found or fails to load.
    """
    font_path = _find_font_path()
    try:
        if font_path:
            return pygame.font.Font(font_path, size)
    except Exception:
        # fall through to default
        pass
    return pygame.font.Font(None, size)


def draw_text(surface, font, text, color, pos, spacing=0, align='center'):
    """Draw text with custom letter spacing.

    Args:
        surface: pygame.Surface to draw onto
        font: pygame.Font instance
        text: string
        color: color tuple
        pos: (x, y) position. Interpreted as center if align=='center', or topleft if 'topleft'.
        spacing: extra pixels between glyphs (can be negative)
        align: 'center' or 'topleft'
    """
    # Pre-render each glyph to measure widths
    glyphs = [font.render(ch, True, color) for ch in text]
    widths = [g.get_width() for g in glyphs]
    total_width = sum(widths) + max(0, (len(glyphs) - 1)) * spacing
    height = max((g.get_height() for g in glyphs), default=font.get_height())

    if align == 'center':
        start_x = int(pos[0] - total_width // 2)
        y = int(pos[1] - height // 2)
    else:
        start_x = int(pos[0])
        y = int(pos[1])

    x = start_x
    for gsurf in glyphs:
        surface.blit(gsurf, (x, y))
        x += gsurf.get_width() + spacing
