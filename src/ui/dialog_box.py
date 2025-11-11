"""Simple dialogue box UI component.

Provides a pixel-art-friendly dialog box that uses a UI image if available
and scales it using nearest-neighbour (integer scaling) to avoid blur.

API:
    DialogBox(pos, size, image_name=None, scale=2)
    .set_text(text)
    .open()/close()/toggle()
    .draw(surface)

The module prefers `Silver.ttf` for the font via src.utils.font.get_font.
If the requested UI image is not found, a rounded rect fallback is drawn.
"""
from __future__ import annotations

import os
import pygame
from typing import Optional, Tuple

from src.utils.font import get_font


class DialogBox:
    def __init__(self, pos: Tuple[int, int], size: Tuple[int, int], image_name: Optional[str] = None, scale: int = 2):
        """Create a dialog box.

        Args:
            pos: top-left position (x,y) on screen
            size: (width, height) target size in pixels
            image_name: filename to search for in assets (optional)
            scale: integer scale to apply to the source image (nearest neighbour)
        """
        self.x, self.y = pos
        self.w, self.h = size
        self.visible = False
        self.text = ""
        self.padding = 8
        self.scale = max(1, int(scale))

        self._bg_surf: Optional[pygame.Surface] = None
        self._load_background(image_name)

        # default font size: make it readable relative to box height
        font_size = max(12, int(self.h * 0.18))
        try:
            self.font = get_font(font_size)
        except Exception:
            self.font = pygame.font.Font(None, font_size)

        # text color as RGB tuple
        self.text_color: Tuple[int, int, int] = (255, 255, 255)

    def _find_image_path(self, image_name: Optional[str]) -> Optional[str]:
        if not image_name:
            return None
        candidates = [
            os.path.join('assets', image_name),
            os.path.join('assets', 'ui', image_name),
            os.path.join('assets', 'art', image_name),
            os.path.join('assets', 'sprites', 'ui', image_name),
            os.path.join('assets', 'sprites', image_name),
            os.path.join('combine', 'docs', image_name),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p

        # recursive search fallback
        assets_dir = 'assets'
        if os.path.exists(assets_dir):
            for root, dirs, files in os.walk(assets_dir):
                for fname in files:
                    if fname.lower() == image_name.lower():
                        return os.path.join(root, fname)
        return None

    def _load_background(self, image_name: Optional[str]):
        path = self._find_image_path(image_name)
        if path is None:
            # fallback: create translucent dark rounded rect
            surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 160))
            self._bg_surf = surf
            return

        try:
            img = pygame.image.load(path).convert_alpha()
        except Exception:
            # fallback to rect
            surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 160))
            self._bg_surf = surf
            return

        iw, ih = img.get_size()
        # Prefer integer scaling factors to preserve pixel-art crispness
        scale_x = max(1, self.w // iw)
        scale_y = max(1, self.h // ih)
        scale = min(scale_x, scale_y)
        new_w = iw * scale
        new_h = ih * scale
        try:
            img2 = pygame.transform.scale(img, (new_w, new_h))
        except Exception:
            img2 = img

        # center the bg image inside the requested box
        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ox = (self.w - new_w) // 2
        oy = (self.h - new_h) // 2
        surf.blit(img2, (ox, oy))
        self._bg_surf = surf

    def set_text(self, text: str):
        self.text = str(text)

    def open(self):
        self.visible = True

    def close(self):
        self.visible = False

    def toggle(self):
        self.visible = not self.visible

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        # draw background
        if self._bg_surf:
            surface.blit(self._bg_surf, (self.x, self.y))
        else:
            # fallback box
            rect = pygame.Rect(self.x, self.y, self.w, self.h)
            pygame.draw.rect(surface, (0, 0, 0, 200), rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        # text wrap simple: split on spaces to fill lines
        if not self.text:
            return
        max_w = self.w - self.padding * 2
        words = self.text.split(' ')
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip() if cur else w
            tw = self.font.size(test)[0]
            if tw <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

        # draw lines centered horizontally and vertically within the box
        max_lines = 10
        lines = lines[:max_lines]
        line_h = self.font.get_height()
        total_h = line_h * len(lines)
        start_y = self.y + self.padding + max(0, (self.h - self.padding * 2 - total_h) // 2)
        for i, line in enumerate(lines):
            rendered = self.font.render(line, True, self.text_color)
            tx = self.x + max(0, (self.w - rendered.get_width()) // 2)
            ty = start_y + i * line_h
            surface.blit(rendered, (tx, ty))
