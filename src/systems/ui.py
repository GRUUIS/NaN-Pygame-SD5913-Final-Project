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


# ---------------------------------------------------------------------------
# Additional HUD rendering utilities (health/meter overlay + game over)
# These live here so the game can import a single `src.systems.ui` module
# ---------------------------------------------------------------------------


def _draw_shadow_box(screen, rect, alpha=160, radius=10):
    shadow = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, alpha), shadow.get_rect(), border_radius=radius)
    screen.blit(shadow, rect.topleft)


def draw_health_bar(screen, current, maximum, x, y, width, height, label, icon=None, icon_color=(255, 255, 255)):
    """Draw a compact health bar with label and numeric readout."""
    font = pygame.font.Font(None, 18)
    maximum = max(1.0, float(maximum))
    current = max(0.0, float(current))
    pct = max(0.0, min(1.0, current / maximum))

    if pct > 0.6:
        color = g.COLORS.get('ui_health_high', (50, 255, 50))
    elif pct > 0.3:
        color = g.COLORS.get('ui_health_medium', (255, 255, 50))
    else:
        color = g.COLORS.get('ui_health_low', (255, 50, 50))

    # subtle background
    pygame.draw.rect(screen, (28, 28, 28), (x - 2, y - 2, width + 4, height + 4), border_radius=4)
    # filled portion
    fill_w = int(width * pct)
    if fill_w > 0:
        pygame.draw.rect(screen, color, (x, y, fill_w, height), border_radius=3)
    # remaining
    if fill_w < width:
        pygame.draw.rect(screen, (56, 56, 56), (x + fill_w, y, width - fill_w, height), border_radius=3)

    pygame.draw.rect(screen, g.COLORS.get('ui_text', (255, 255, 255)), (x, y, width, height), 2, border_radius=4)

    label_surf = font.render(str(label), True, g.COLORS.get('ui_text', (255, 255, 255)))
    value_surf = font.render(f"{int(current)}/{int(maximum)}", True, g.COLORS.get('ui_text', (255, 255, 255)))
    label_x = x + 6
    if icon:
        pygame.draw.circle(screen, icon_color, (x - 10, y + height // 2), height // 2 + 4)
        icon_surf = font.render(icon, True, (0, 0, 0))
        icon_rect = icon_surf.get_rect(center=(x - 10, y + height // 2))
        screen.blit(icon_surf, icon_rect)
        label_x = x + 10
    screen.blit(label_surf, (label_x, y - 22))
    screen.blit(value_surf, (x + width - value_surf.get_width() - 6, y - 22))


def draw_meter_bar(screen, current, maximum, x, y, width, height, label,
                   color_high=(120, 200, 120), color_mid=(230, 180, 80), color_low=(220, 120, 120)):
    font = pygame.font.Font(None, 18)
    maximum = max(1.0, float(maximum) if maximum else 1.0)
    pct = max(0.0, min(1.0, float(current) / float(maximum))) if maximum else 0.0

    if pct > 0.6:
        color = color_high
    elif pct > 0.3:
        color = color_mid
    else:
        color = color_low

    pygame.draw.rect(screen, (28, 28, 28), (x - 2, y - 2, width + 4, height + 4), border_radius=4)
    pygame.draw.rect(screen, color, (x, y, int(width * pct), height), border_radius=3)
    pygame.draw.rect(screen, (56, 56, 56), (x + int(width * pct), y, width - int(width * pct), height), border_radius=3)
    pygame.draw.rect(screen, g.COLORS.get('ui_text', (255, 255, 255)), (x, y, width, height), 2, border_radius=4)

    label_surf = font.render(str(label), True, g.COLORS.get('ui_text', (255, 255, 255)))
    screen.blit(label_surf, (x + 6, y - 18))


def draw_game_over_screen(screen, boss_scene):
    overlay = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), flags=pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    title_font = pygame.font.Font(None, 72)
    small_font = pygame.font.Font(None, 36)

    # Check if player defeated or boss defeated
    player_defeated = getattr(boss_scene, 'player', None) and boss_scene.player.health <= 0
    boss_defeated = getattr(boss_scene, 'boss', None) and boss_scene.boss.health <= 0
    
    if player_defeated:
        title = title_font.render("DEFEAT", True, g.COLORS.get('ui_health_low'))
        sub_text = "Press R to restart"
    elif boss_defeated:
        title = title_font.render("VICTORY!", True, g.COLORS.get('ui_health_high'))
        sub_text = "Press SPACE to continue"
    else:
        title = title_font.render("GAME OVER", True, g.COLORS.get('ui_text'))
        sub_text = "Press R to restart"

    screen.blit(title, title.get_rect(center=(g.SCREENWIDTH // 2, g.SCREENHEIGHT // 2 - 20)))
    sub = small_font.render(sub_text, True, g.COLORS.get('ui_text'))
    screen.blit(sub, sub.get_rect(center=(g.SCREENWIDTH // 2, g.SCREENHEIGHT // 2 + 40)))


def _format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02}:{seconds % 60:02}"


def _draw_status_pill(screen, text, pos, color):
    font = pygame.font.Font(None, 24)
    surf = font.render(text, True, (10, 10, 10))
    padding = 10
    pill = pygame.Surface((surf.get_width() + padding * 2, surf.get_height() + 8), pygame.SRCALPHA)
    pygame.draw.rect(pill, color, pill.get_rect(), border_radius=12)
    pill.blit(surf, (padding, 4))
    screen.blit(pill, pill.get_rect(midtop=pos))


def draw_ui_overlay(screen, boss_scene):
    """Stylized HUD overlay for all boss scenes."""
    margin = 28
    bar_height = 24

    # Player pane (top-left)
    if getattr(boss_scene, 'player', None):
        pane_width = 320
        pane_rect = pygame.Rect(14, 14, pane_width, 90)
        _draw_shadow_box(screen, pane_rect, alpha=180, radius=12)
        draw_health_bar(
            screen,
            boss_scene.player.health,
            boss_scene.player.max_health,
            pane_rect.x + 40,
            pane_rect.y + 30,
            pane_width - 60,
            bar_height,
            "Aria",
            icon="P",
            icon_color=(80, 180, 255)
        )

    # Boss pane (top-center)
    boss = getattr(boss_scene, 'boss', None)
    if boss:
        pane_width = 600
        pane_rect = pygame.Rect((g.SCREENWIDTH - pane_width) // 2, 14, pane_width, 110)
        _draw_shadow_box(screen, pane_rect, alpha=180, radius=18)

        boss_name = getattr(boss, 'display_name', None) or getattr(boss, 'name', '') or boss.__class__.__name__
        title_font = pygame.font.Font(None, 32)
        title = title_font.render(str(boss_name).replace('_', ' '), True, (230, 230, 230))
        screen.blit(title, (pane_rect.x + 20, pane_rect.y + 6))

        draw_health_bar(
            screen,
            boss.health,
            boss.max_health,
            pane_rect.x + 20,
            pane_rect.y + 42,
            pane_width - 40,
            bar_height,
            "Boss",
            icon="B",
            icon_color=(220, 120, 120)
        )

        meter_y = pane_rect.y + 42 + bar_height + 18
        meters = []
        if hasattr(boss, 'stress') and hasattr(boss, 'max_stress'):
            # Only show stress meter if boss is alive
            if boss.health > 0:
                meters.append((boss.stress, boss.max_stress, "Stress", (220, 120, 120)))
        if hasattr(boss, 'deadline_left') and hasattr(boss, 'deadline_total'):
            meters.append((boss.deadline_left, boss.deadline_total, "Deadline", (120, 200, 180)))
        meter_width = (pane_width - 60)
        for idx, (curr, maximum, label, color) in enumerate(meters):
            draw_meter_bar(screen, curr, max(0.01, maximum), pane_rect.x + 30, meter_y + idx * 22, meter_width, 16, f"{label}", color_high=color)

        # Status pill (phase/enrage etc.)
        if hasattr(boss, 'phase'):
            pill_color = (200, 120, 255) if getattr(boss, 'enraged', False) else (140, 200, 255)
            _draw_status_pill(screen, f"Phase {getattr(boss, 'phase', 1)}", (pane_rect.centerx, pane_rect.bottom - 16), pill_color)

    # Bottom reading (controls + timers + debug info)
    footer_height = 52
    footer_rect = pygame.Rect(0, g.SCREENHEIGHT - footer_height, g.SCREENWIDTH, footer_height)
    _draw_shadow_box(screen, footer_rect, alpha=200, radius=0)
    font = pygame.font.Font(None, 24)
    controls = "WASD move  |  SPACE jump  |  LMB Voidfire  |  RMB Phase Blink  |  R restart  |  ESC exit"
    screen.blit(font.render(controls, True, (230, 230, 230)), (40, g.SCREENHEIGHT - footer_height + 12))

    # Right-aligned runtime info
    info_font = pygame.font.Font(None, 22)
    runtime = _format_time(getattr(boss_scene, 'elapsed_time', pygame.time.get_ticks() / 1000))
    fps = int(pygame.time.Clock().get_fps()) if pygame.time.get_ticks() > 0 else g.FPS
    info_text = f"{runtime}  |  {fps:02d} FPS"
    info_surf = info_font.render(info_text, True, (200, 200, 200))
    screen.blit(info_surf, info_surf.get_rect(bottomright=(g.SCREENWIDTH - 40, g.SCREENHEIGHT - 12)))

    # Debug text intentionally removed per latest UI direction.

