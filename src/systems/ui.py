"""
Lightweight UI system for battle scene text popups and announcements.

Provides anchored speech bubbles and centered announcements with simple
fade-in/fade-out and lifetime.
"""

#region Imports
import pygame
import globals as g
#endregion Imports


class TextPopup:
    """A small text bubble that can be anchored to a world position/entity."""
    def __init__(self, text: str, pos_fn, duration: float = 2.5,
                 fade: float = 0.3, color=(255, 255, 255), bg=(0, 0, 0),
                 padding: int = 6):
        """
        pos_fn: callable -> (x, y) in screen space each frame (anchor center).
        duration: total life time in seconds.
        fade: fade-in and fade-out time in seconds.
        """
        self.text = text
        self.pos_fn = pos_fn
        self.duration = max(0.1, duration)
        self.fade = max(0.05, fade)
        self.color = color
        self.bg = bg
        self.padding = padding
        self.elapsed = 0.0
        self.font = pygame.font.Font(None, 28)

    def update(self, dt: float):
        self.elapsed += dt

    def is_alive(self) -> bool:
        return self.elapsed < self.duration

    def draw(self, screen: pygame.Surface):
        # Compute alpha based on fade in/out
        t = self.elapsed
        a = 1.0
        if t < self.fade:
            a = max(0.0, min(1.0, t / self.fade))
        elif t > self.duration - self.fade:
            a = max(0.0, min(1.0, (self.duration - t) / self.fade))

        # Render text surface
        txt = self.font.render(self.text, True, self.color)
        rect = txt.get_rect()
        rect.inflate_ip(self.padding * 2, self.padding * 2)

        # Anchor position
        x, y = self.pos_fn()
        rect.center = (int(x), int(y - 40))  # above anchor

        # Draw background with alpha by drawing onto temporary surface
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg_col = (*self.bg, int(180 * a))
        pygame.draw.rect(surf, bg_col, surf.get_rect(), border_radius=6)
        # small pointer triangle
        tri = pygame.Surface((12, 8), pygame.SRCALPHA)
        pygame.draw.polygon(tri, bg_col, [(0, 0), (12, 0), (6, 8)])
        # Blit
        screen.blit(surf, rect.topleft)
        # triangle below bubble
        screen.blit(tri, (rect.centerx - 6, rect.bottom - 1))

        # Draw text with alpha
        txt_surf = txt.copy()
        txt_surf.set_alpha(int(255 * a))
        screen.blit(txt_surf, (rect.left + self.padding, rect.top + self.padding))


class Announcement:
    """Centered announcement banner."""
    def __init__(self, text: str, duration: float = 2.5, fade: float = 0.4,
                 color=(255, 255, 255), bg=(0, 0, 0)):
        self.text = text
        self.duration = duration
        self.fade = fade
        self.color = color
        self.bg = bg
        self.elapsed = 0.0
        self.font = pygame.font.Font(None, 36)

    def update(self, dt: float):
        self.elapsed += dt

    def is_alive(self) -> bool:
        return self.elapsed < self.duration

    def draw(self, screen: pygame.Surface):
        t = self.elapsed
        a = 1.0
        if t < self.fade:
            a = max(0.0, min(1.0, t / self.fade))
        elif t > self.duration - self.fade:
            a = max(0.0, min(1.0, (self.duration - t) / self.fade))

        txt = self.font.render(self.text, True, self.color)
        rect = txt.get_rect()
        rect.inflate_ip(20, 12)
        rect.center = (g.SCREENWIDTH // 2, int(g.SCREENHEIGHT * 0.22))

        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg_col = (*self.bg, int(160 * a))
        pygame.draw.rect(surf, bg_col, surf.get_rect(), border_radius=8)
        screen.blit(surf, rect.topleft)

        txt_surf = txt.copy()
        txt_surf.set_alpha(int(255 * a))
        screen.blit(txt_surf, (rect.left + 10, rect.top + 6))


class UIManager:
    """Manages transient UI elements like text popups/announcements."""
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def update(self, dt: float):
        for it in self.items:
            it.update(dt)
        self.items = [it for it in self.items if it.is_alive()]

    def draw(self, screen: pygame.Surface):
        for it in self.items:
            it.draw(screen)
