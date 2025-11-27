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
import pygame, os, random, math
import globals as g
from .player import Player
from .boss_sloth import TheSloth
from .bullets import BulletManager
from .platform import Platform
from ..systems.ui import UIManager, TextPopup, draw_ui_overlay, draw_game_over_screen


class SlothBattleScene:
    def __init__(self):
        self.player = Player(g.SCREENWIDTH//2, g.SCREENHEIGHT - 200)
        self.boss = TheSloth(g.SCREENWIDTH*0.25, 0)
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        # Inject UI into boss for dialogue
        self.boss.ui = self.ui
        self._shown_entry = False
        self._shown_victory = False
        self._last_boss_health = getattr(self.boss, 'health', 0)

        ground_h = 78
        ground_top = g.SCREENHEIGHT - ground_h
        # Platforms: restore elevated ledges for repositioning & trail management
        self.platforms = [
            Platform(0, ground_top, g.SCREENWIDTH, ground_h),
            Platform(int(g.SCREENWIDTH*0.28), ground_top-100, 140, 18),
            Platform(int(g.SCREENWIDTH*0.60), ground_top-120, 160, 20),
        ]
        # Snap boss to ground
        self.boss.set_ground(ground_top)

        # Background
        self.background = self._load_background()

        # BGM
        try:
            bgm_path = os.path.join('assets', 'sfx', 'Boss_Sloth_Lurid_Delusion.mp3')
            pygame.mixer.music.load(bgm_path)
            try:
                pygame.mixer.music.set_volume(getattr(g, 'music_volume', 0.2))
            except Exception:
                try:
                    pygame.mixer.music.set_volume(0.2)
                except Exception:
                    pass
            pygame.mixer.music.play(-1) # Loop
        except Exception as e:
            print(f"Failed to load Sloth BGM: {e}")

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
        """High-velocity eerie forest: multi-layer parallax + drifting fog + color pulse.

        Layers:
          1. Pulsing gradient sky (slow hue shift)
          2. Distant trees (fast horizontal drift)
          3. Mid trees with branch silhouettes (accelerated parallax)
          4. Foreground thorns/bushes (very fast scroll for speed sensation)
          5. Multi band fog + occasional flash silhouettes
        All procedural so it matches the Sloth's unsettling, fast crawl style.
        """
        w,h = g.SCREENWIDTH, g.SCREENHEIGHT
        time_ms = pygame.time.get_ticks()
        t = time_ms / 1000.0
        # Sky gradient with subtle pulsating hue
        sky = pygame.Surface((w,h))
        pulse = (math.sin(t*0.6)+1)/2  # 0..1
        top_col = (
            int(6 + 12*pulse),
            int(14 + 24*pulse),
            int(10 + 18*pulse)
        )
        bot_col = (
            int(16 + 30*pulse),
            int(48 + 42*pulse),
            int(36 + 34*pulse)
        )
        for y in range(h):
            k = y / h
            col = (
                int(top_col[0] + (bot_col[0]-top_col[0])*k),
                int(top_col[1] + (bot_col[1]-top_col[1])*k),
                int(top_col[2] + (bot_col[2]-top_col[2])*k)
            )
            pygame.draw.line(sky, col, (0,y), (w,y))
        screen.blit(sky,(0,0))

        rng = random.Random(0)  # deterministic layout base
        # Parallax speed multipliers (higher than previous for "flying" feel)
        far_speed = 110
        mid_speed = 210
        fg_speed = 360
        # FAR layer (thin silhouettes)
        far = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(34):
            base_x = (i * 150 - int(t*far_speed)) % (w+150) - 75
            trunk_h = rng.randint(int(h*0.40), int(h*0.68))
            trunk_w = rng.randint(8,16)
            alpha = 50
            pygame.draw.rect(far, (18,38,26,alpha), (base_x, h-trunk_h, trunk_w, trunk_h))
        screen.blit(far,(0,0))
        # MID layer (branchy)
        mid = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(26):
            base_x = (i * 180 - int(t*mid_speed)) % (w+180) - 90
            trunk_h = rng.randint(int(h*0.50), int(h*0.78))
            trunk_w = rng.randint(24,36)
            color = (26,60,40,140)
            pygame.draw.rect(mid, color, (base_x, h-trunk_h, trunk_w, trunk_h))
            # Branch shards
            branch_count = 4
            for b in range(branch_count):
                by = h-trunk_h + rng.randint(28, trunk_h-40)
                dir = -1 if b%2==0 else 1
                length = rng.randint(60,120)
                pygame.draw.polygon(mid, (26,60,42,120), [
                    (base_x + trunk_w//2, by),
                    (base_x + trunk_w//2 + dir*length, by - rng.randint(8,18)),
                    (base_x + trunk_w//2, by + rng.randint(6,14))
                ])
        screen.blit(mid,(0,0))
        # FOREGROUND fast bushes / thorns
        fg = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(40):
            bx = (i*100 - int(t*fg_speed)) % (w+100) - 50
            by = h - rng.randint(70,110)
            rad_x = rng.randint(50,90)
            rad_y = rng.randint(30,60)
            pygame.draw.ellipse(fg, (16,46,32,210), (bx, by, rad_x*2, rad_y))
        screen.blit(fg,(0,0))
        # Layered fog bands drifting opposite direction for depth
        fog = pygame.Surface((w,h), pygame.SRCALPHA)
        for band in range(5):
            band_h = h//6
            y0 = band * band_h + int(math.sin(t*0.8 + band)*6)
            fog_alpha = int(28 + 18*math.sin(t*1.2 + band*0.7))
            pygame.draw.rect(fog, (40,60,50,fog_alpha), (0,y0, w, band_h))
        screen.blit(fog,(0,0))
        # Flash silhouettes (rare): brief dark vertical streaks to add tension
        if int(t*4) % 7 == 0:  # periodic condition
            streaks = pygame.Surface((w,h), pygame.SRCALPHA)
            for _ in range(6):
                sx = random.randint(0,w)
                sh = random.randint(int(h*0.3), int(h*0.7))
                pygame.draw.rect(streaks, (10,20,14,90), (sx, h-sh, 6, sh))
            screen.blit(streaks,(0,0))

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
        try:
            draw_ui_overlay(screen, self)
        except Exception:
            pass
        if self.is_game_over():
            try:
                draw_game_over_screen(screen, self)
            except Exception:
                pass
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
        if self.player.health <= 0:
            return True
        if self.boss.health <= 0:
            # Wait for boss to finish fading animation/dialogue
            if hasattr(self.boss, 'fully_defeated') and not self.boss.fully_defeated:
                return False
            return True
        return False

    def reset_battle(self):
        # re-init while keeping same scene layout
        # Platform objects store position in rect; use rect.y instead of non-existent .y
        ground_top = self.platforms[0].rect.y
        self.player = Player(g.SCREENWIDTH//2, g.SCREENHEIGHT - 200)
        self.boss = TheSloth(g.SCREENWIDTH*0.25, 0)
        self.boss.set_ground(ground_top)
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        # Inject UI into boss for dialogue
        self.boss.ui = self.ui
        self._shown_entry = False
        self._shown_victory = False
        self._last_boss_health = self.boss.health
