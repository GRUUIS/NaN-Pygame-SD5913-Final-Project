"""SlothBattleScene

Dedicated battle scene for Boss #2 - The Sloth.

Differences from generic `BossBattleScene`:
  - Ground-focused arena: wide flat ground with a few low ledges so player must reposition
  - No vertical spike waves (emphasis on horizontal zoning via slime trail & pools)
  - Creepy forest / cave background (placeholder gradient if image missing)
  - Automatically sets the Sloth's ground height so it truly crawls.

Assets expected (optional):
  assets/backgrounds/boss_sloth_forest.png  (provide your own later)

If missing, a dark green-to-black vertical gradient is rendered.
"""
from __future__ import annotations
import pygame, os, random
import globals as g
from .player import Player
from .boss_sloth import TheSloth
from .bullets import BulletManager
from .platform import Platform
from ..systems.ui import UIManager, TextPopup


class SlothBattleScene:
    def __init__(self):
        self.player = Player(g.SCREENWIDTH//2, g.SCREENHEIGHT - 200)
        self.boss = TheSloth(g.SCREENWIDTH*0.25, 0)
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        self._shown_entry = False
        self._shown_victory = False
        self._last_boss_health = getattr(self.boss, 'health', 0)

        ground_h = 78
        ground_top = g.SCREENHEIGHT - ground_h
        # Platforms: small bumps to reposition & avoid stacking trail infinitely
        self.platforms = [
            Platform(0, ground_top, g.SCREENWIDTH, ground_h),
            Platform(int(g.SCREENWIDTH*0.28), ground_top-60, 140, 18),
            Platform(int(g.SCREENWIDTH*0.60), ground_top-72, 160, 20),
        ]
        # Snap boss to ground
        self.boss.set_ground(ground_top)

        # Background
        self.background = self._load_background()

    # --- Internal helpers ---
    def _load_background(self):
        path = os.path.join('assets','backgrounds','boss_sloth_forest.png')
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert()
            except Exception:
                return None
        return None

    def _draw_background(self, screen: pygame.Surface):
        """Render parallax eerie forest with layered silhouettes.
        If a custom bitmap background exists it scrolls slowly; otherwise build layers procedurally:
          - Sky gradient (dark mossy)
          - Far tree silhouettes (low contrast)
          - Mid tree trunks + sparse branches
          - Foreground bush / thorn shapes
        Layers scroll at different speeds for depth."""
        if self.background:
            t = pygame.time.get_ticks()*0.02
            ox = int(t) % self.background.get_width()
            screen.blit(self.background, (-ox,0))
            screen.blit(self.background, (-ox + self.background.get_width(),0))
            return
        w,h = g.SCREENWIDTH, g.SCREENHEIGHT
        # Sky gradient cache per frame (cheap enough once)
        sky = pygame.Surface((w,h))
        top_col = (8,18,12)
        bot_col = (12,60,38)
        for y in range(h):
            k = y / h
            col = (
                int(top_col[0] + (bot_col[0]-top_col[0])*k),
                int(top_col[1] + (bot_col[1]-top_col[1])*k),
                int(top_col[2] + (bot_col[2]-top_col[2])*k)
            )
            pygame.draw.line(sky, col, (0,y), (w,y))
        screen.blit(sky,(0,0))
        rng = random.Random(0)  # deterministic layout each frame
        t = pygame.time.get_ticks()/1000.0
        # Far layer trees
        far = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(28):
            base_x = (i * 140 + int(t*8)) % (w+140) - 70
            trunk_h = rng.randint(int(h*0.45), int(h*0.7))
            trunk_w = rng.randint(10,18)
            alpha = 55
            pygame.draw.rect(far, (20,40,28,alpha), (base_x, h-trunk_h, trunk_w, trunk_h))
        screen.blit(far,(0,0))
        # Mid layer
        mid = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(18):
            base_x = (i * 200 + int(t*24)) % (w+200) - 100
            trunk_h = rng.randint(int(h*0.5), int(h*0.78))
            trunk_w = rng.randint(26,38)
            pygame.draw.rect(mid, (26,60,40,130), (base_x, h-trunk_h, trunk_w, trunk_h))
            # Simple branch triangles
            for b in range(3):
                by = h-trunk_h + rng.randint(20, trunk_h-60)
                dir = -1 if b%2==0 else 1
                length = rng.randint(50,100)
                pygame.draw.polygon(mid, (26,60,40,110), [
                    (base_x + (trunk_w//2), by),
                    (base_x + (trunk_w//2)+dir*length, by-12),
                    (base_x + (trunk_w//2), by+10)
                ])
        screen.blit(mid,(0,0))
        # Foreground bushes
        fg = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(22):
            bx = (i*120 + int(t*40)) % (w+120) - 60
            by = h - 90 + rng.randint(-8,18)
            rad = rng.randint(40,70)
            pygame.draw.ellipse(fg, (14,50,30,200), (bx, by, rad*2, rad))
        screen.blit(fg,(0,0))
        # Subtle fog overlay
        fog = pygame.Surface((w,h), pygame.SRCALPHA)
        fog.fill((30,50,40,35))
        screen.blit(fog,(0,0))

    # --- Public API ---
    def update(self, dt: float):
        if not self.is_game_over():
            self.player.update(dt, self.platforms)
            self.boss.update(dt, self.player, self.bullet_manager)
            self.bullet_manager.update(dt, self.player, self.boss)
            self.bullet_manager.check_collisions(self.player, self.boss)
            self.ui.update(dt)
            if not self._shown_entry:
                self._shown_entry = True
                def anchor(): return (self.boss.x + self.boss.width/2, self.boss.y)
                self.ui.add(TextPopup(getattr(self.boss,'entry_line','Time... stalls.'), anchor, duration=3.0, bg=(12,12,12)))
            # Player shooting (reuse normal bullet style for now)
            if self.player.mouse_pressed and self.player.can_shoot():
                info = self.player.shoot()
                if info:
                    x,y,dx,dy = info
                    speed = g.BULLET_SPEEDS['player']
                    self.bullet_manager.add_bullet(x,y,dx*speed,dy*speed,'player','player')
            # Debug health prints
            if g.DEBUG_MODE and self._last_boss_health != self.boss.health:
                print(f"Boss health: {self.boss.health}/{self.boss.max_health}")
                self._last_boss_health = self.boss.health

    def draw(self, screen: pygame.Surface):
        self._draw_background(screen)
        for p in self.platforms:
            p.draw(screen)
        # Draw player after trail so player is visible; trail drawn inside boss.draw
        self.boss.draw(screen)
        self.player.draw(screen)
        self.bullet_manager.draw(screen)
        self.ui.draw(screen)
        if g.SHOW_DEBUG_INFO:
            self._draw_debug(screen)

    def _draw_debug(self, screen: pygame.Surface):
        font = pygame.font.Font(None, 18)
        lines = [
            f"Player HP {int(self.player.health)}/{int(self.player.max_health)} vx={self.player.vx:.1f}",
            f"Boss HP {int(self.boss.health)}/{int(self.boss.max_health)} State={self.boss.current_state.__class__.__name__}",
            f"Trail segs: {len(self.boss.trail_segments)}"
        ]
        for i,l in enumerate(lines):
            screen.blit(font.render(l,True,(220,230,220)), (8, g.SCREENHEIGHT-120 + i*20))

    def is_game_over(self):
        over = self.player.health <=0 or self.boss.health <=0
        if over and not self._shown_victory and self.boss.health<=0:
            self._shown_victory = True
            def anchor(): return (self.player.x + self.player.width/2, self.player.y)
            self.ui.add(TextPopup(getattr(self.boss,'defeat_line','Keep walking.'), anchor, duration=3.2, bg=(12,12,12)))
        return over

    def reset_battle(self):
        # re-init while keeping same scene layout
        ground_top = self.platforms[0].y
        self.player = Player(g.SCREENWIDTH//2, g.SCREENHEIGHT - 200)
        self.boss = TheSloth(g.SCREENWIDTH*0.25, 0)
        self.boss.set_ground(ground_top)
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        self._shown_entry = False
        self._shown_victory = False
        self._last_boss_health = self.boss.health
