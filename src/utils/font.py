"""Compatibility shim for moved font helpers.

The original helper was moved to `combine/font.py` to make lightweight
`combine` scripts self-contained. Keep this shim so imports targeting
`src.utils.font` keep working while the codebase migrates.
"""
try:
    # Prefer the moved helper in combine/ (used by combine runner)
    from combine.font import get_font, draw_text, get_font_path
except Exception:
    # Fall back to minimal in-place implementations to avoid hard failures
    import pygame

    def get_font_path():
        return None

    def get_font(size: int):
        try:
            return pygame.font.Font(None, size)
        except Exception:
            raise

    def draw_text(surface, font, text, color, pos, spacing=0, align='center'):
        glyphs = [font.render(ch, True, color) for ch in text]
        total_width = sum(g.get_width() for g in glyphs) + max(0, (len(glyphs) - 1)) * spacing
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
