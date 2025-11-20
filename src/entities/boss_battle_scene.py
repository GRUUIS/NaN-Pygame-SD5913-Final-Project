"""
Boss Battle Scene - Integrated 2D Platformer with Boss Fight

This module combines all entities into a complete boss battle experience.
Uses modular components from separate files and globals.py configuration.
"""

#region Imports

import pygame
import random
import globals as g
import os
from .player import Player
from .boss import Perfectionist
from .boss_the_hollow import TheHollow
from .boss_sloth import TheSloth
from .bullets import BulletManager
from .platform import Platform
from ..systems.ui import UIManager, TextPopup, Announcement
#endregion Imports


class BossBattleScene:
    """
    Complete boss battle scene with integrated platformer mechanics
    """
    def __init__(self, boss_type: str = 'perfectionist'):
        #region Initialization
        # Initialize entities
        self.player = Player(g.SCREENWIDTH // 2, g.SCREENHEIGHT - 150)
        self._boss_type = boss_type.lower() if boss_type else 'perfectionist'
        self.boss = self._create_boss()
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        self._shown_victory = False
        self._shown_entry = False
        # Idle penalty tracking
        self._idle_timer = 0.0
        self._idle_spawn_timer = 0.0
        # Restore full horizontal play width
        self.play_left = 0
        self.play_right = g.SCREENWIDTH

        ground_h = 70
        ground_top = g.SCREENHEIGHT - ground_h
        # New layout: tiers closer to ground to improve reachability
        lower_y = ground_top - 110
        middle_y = ground_top - 190
        upper_y = ground_top - 260

        self.platforms = [
            Platform(0, ground_top, g.SCREENWIDTH, ground_h),
            # Lower tier (reachable from ground)
            Platform(100, lower_y, 240, 20),
            Platform(g.SCREENWIDTH - 340, lower_y, 240, 20),
            # Middle tier (reachable from lower)
            Platform(g.SCREENWIDTH // 2 - 110, middle_y, 220, 20),
            # Upper side ledges (reachable from middle)
            Platform(60, upper_y, 160, 20),
            Platform(g.SCREENWIDTH - 220, upper_y, 160, 20),
        ]

        # Spike system state
        self.spikes_active = []  # list of rects
        self.spike_timer = 0.0
        self.spike_wave_elapsed = 0.0
        self.spike_wave_active = False

        # Background image (deep cave)
        try:
            bg_path = os.path.join('assets', 'backgrounds', 'boss_hollow_cave.png')
            self.background = pygame.image.load(bg_path).convert()
        except Exception:
            self.background = None
        
        # BGM
        try:
            bgm_file = None
            if self._boss_type in ('sloth','the_sloth','boss2','b0ss','snail'):
                bgm_file = 'Boss_Sloth_Lurid_Delusion.mp3'
            elif self._boss_type in ('procrastinator', 'procrastination', 'hollow', 'the_hollow', 'nihilism'):
                bgm_file = 'Boss_Hollow_Spiritwatcher.mp3'
            
            if bgm_file:
                bgm_path = os.path.join('assets', 'sfx', bgm_file)
                pygame.mixer.music.load(bgm_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Failed to load BGM: {e}")
        #endregion Initialization

    def _create_boss(self):
        x = g.SCREENWIDTH // 2
        y = 100
        if self._boss_type in ('sloth','the_sloth','boss2','b0ss','snail'):
            b = TheSloth(x, y)
            # inject ui reference for dialogue popups
            b.ui = getattr(self, 'ui', None)
            return b
        if self._boss_type in ('procrastinator', 'procrastination', 'hollow', 'the_hollow', 'nihilism'):
            return TheHollow(x, y)
        # default
        return Perfectionist(x, y)
    
    #region Update Loop
    def update(self, dt: float):
        """Update the entire battle scene"""
        if not self.is_game_over():
            # Update entities
            # Full width movement
            self.player.update(dt, self.platforms)
            # Spike wave logic (restrict movement)
            self._update_spikes(dt)
            self._handle_spike_collisions(block_player=True)
            self.boss.update(dt, self.player, self.bullet_manager)
            self.ui.update(dt)

            # Pre-fight announcement once
            if not self._shown_entry:
                self._shown_entry = True
                # Anchor popup near boss
                def boss_anchor():
                    return (self.boss.x + self.boss.width/2, self.boss.y)
                self.ui.add(TextPopup(getattr(self.boss, 'entry_line', "You think words can scare me away?"), boss_anchor, duration=3.2, bg=(10,10,10)))
            
            # Handle player shooting
            if self.player.mouse_pressed and self.player.can_shoot():
                # In The Hollow battle, left click uses Voidfire instead of normal bullets
                use_voidfire = isinstance(self.boss, TheHollow)
                if use_voidfire:
                    bullet_info = self.player.shoot_voidfire()
                    if bullet_info:
                        x, y, dx, dy = bullet_info
                        speed = g.BULLET_SPEEDS['voidfire']
                        self.bullet_manager.add_bullet(x, y, dx * speed, dy * speed, 'voidfire', 'player')
                        if g.DEBUG_MODE:
                            print(f"Voidfire: pos=({x:.1f}, {y:.1f}), dir=({dx:.2f}, {dy:.2f})")
                else:
                    bullet_info = self.player.shoot()
                    if bullet_info:
                        x, y, dx, dy = bullet_info
                        speed = g.BULLET_SPEEDS['player']
                        self.bullet_manager.add_bullet(x, y, dx * speed, dy * speed, 'player', 'player')
                        if g.DEBUG_MODE:
                            print(f"Player shot: pos=({x:.1f}, {y:.1f}), dir=({dx:.2f}, {dy:.2f})")
            
            # Update bullets
            self.bullet_manager.update(dt, self.player, self.boss)
            
            # Check bullet collisions
            self.bullet_manager.check_collisions(self.player, self.boss)

            # Idle penalty: spawn void shards above player if idle too long (escalating)
            moving = abs(self.player.vx) > 10 or not self.player.on_ground
            if moving:
                self._idle_timer = 0.0
                self._idle_spawn_timer = 0.0
            else:
                self._idle_timer += dt
                if g.PLAYER_IDLE_HEALTH_DRAIN > 0 and self._idle_timer >= g.PLAYER_IDLE_THRESHOLD:
                    # continuous drain while idle beyond threshold
                    self.player.take_damage(g.PLAYER_IDLE_HEALTH_DRAIN * dt)
                if self._idle_timer >= g.PLAYER_IDLE_THRESHOLD:
                    self._idle_spawn_timer += dt
                    if self._idle_spawn_timer >= g.PLAYER_IDLE_SHARD_INTERVAL:
                        self._idle_spawn_timer = 0.0
                        px = self.player.x + self.player.width/2
                        # Escalate with idle time: more shards and faster
                        over = max(0.0, self._idle_timer - g.PLAYER_IDLE_THRESHOLD)
                        severity = min(4, 1 + int(over // 1.2))  # 1..4 shards per tick
                        speed_scale = min(1.8, 1.0 + over * 0.15)
                        for i in range(severity):
                            x = max(20, min(g.SCREENWIDTH - 20, random.gauss(px, 50 + 10*severity)))
                            y = -10
                            vy = g.BULLET_SPEEDS['void_shard'] * speed_scale
                            vx = random.uniform(-20 - 10*severity, 20 + 10*severity)
                            self.bullet_manager.add_bullet(x, y, vx, vy, 'void_shard', 'boss')
            
            # Debug: Show health changes
            if g.DEBUG_MODE and hasattr(self, '_last_boss_health'):
                if self._last_boss_health != self.boss.health:
                    print(f"Boss health: {self.boss.health}/{self.boss.max_health}")
                    self._last_boss_health = self.boss.health
            elif g.DEBUG_MODE:
                self._last_boss_health = self.boss.health
    #endregion Update Loop
    
    #region Draw
    def draw(self, screen: pygame.Surface):
        """Draw the entire battle scene"""
        # Draw background (parallax-lite) or solid color fallback
        if getattr(self, 'background', None) is not None:
            # Simple vertical scroll to suggest infinite descent
            t = pygame.time.get_ticks() * 0.02
            offset_y = int(t) % self.background.get_height()
            # Tile vertically to fake infinite
            screen.blit(self.background, (0, -offset_y))
            screen.blit(self.background, (0, -offset_y + self.background.get_height()))
        else:
            screen.fill(g.COLORS['background'])
        
        # Draw platforms
        for platform in self.platforms:
            platform.draw(screen)
        
        # Draw entities
        self.player.draw(screen)
        self.boss.draw(screen)
        self.bullet_manager.draw(screen)
        self.ui.draw(screen)
        
        # Draw active spikes
        if self.spikes_active:
            flash_phase = (pygame.time.get_ticks() / 100.0) % 2.0
            pre_spawn = self.spike_wave_active and self.spike_wave_elapsed < self._preflash_time()
            for r, top in self.spikes_active:
                # Pre-flash: alternate bright/dim to warn
                if pre_spawn:
                    if flash_phase < 1.0:
                        color = (120, 120, 130)
                    else:
                        color = (40, 40, 50)
                else:
                    color = (15, 15, 20) if top else (20, 15, 25)
                pygame.draw.rect(screen, color, r)
                tip_w = r.width
                tip_h = 12
                if top:
                    pygame.draw.polygon(screen, (8,8,12), [(r.left, r.bottom), (r.left+tip_w//2, r.bottom+tip_h), (r.right, r.bottom)])
                else:
                    pygame.draw.polygon(screen, (8,8,12), [(r.left, r.top), (r.left+tip_w//2, r.top - tip_h), (r.right, r.top)])

        # Draw debug information
        if g.SHOW_DEBUG_INFO:
            self._draw_debug_info(screen)
    #endregion Draw
    
    #region Debug/Helpers
    def _draw_debug_info(self, screen: pygame.Surface):
        """Draw debug information on screen"""
        font = pygame.font.Font(None, 20)
        debug_y = g.SCREENHEIGHT - 150
        
        debug_info = [
            f"Player: HP={self.player.health}/{self.player.max_health} Pos=({self.player.x:.0f},{self.player.y:.0f})",
            f"Boss: HP={self.boss.health}/{self.boss.max_health} Phase={self.boss.phase}",
            f"Boss State: {self.boss.current_state.__class__.__name__}",
            f"Bullets: {len(self.bullet_manager.bullets)} active",
            f"Player on ground: {self.player.on_ground}"
        ]
        
        for i, info in enumerate(debug_info):
            text = font.render(info, True, g.COLORS['ui_text'])
            screen.blit(text, (10, debug_y + i * 22))
    #endregion Debug/Helpers
    
    #region Game State & Reset
    def is_game_over(self) -> bool:
        """Check if battle is over"""
        over = self.player.health <= 0 or self.boss.health <= 0
        # Trigger victory popup once
        if not self._shown_victory and over and self.boss.health <= 0:
            self._shown_victory = True
            def player_anchor():
                return (self.player.x + self.player.width/2, self.player.y)
            self.ui.add(TextPopup(getattr(self.boss, 'defeat_line', "This is not a threat-it's my process"), player_anchor, duration=3.0, bg=(10,10,10)))
        return over

    def reset_battle(self):
        """Reset the battle maintaining the same boss type and clear bullets."""
        self.player = Player(g.SCREENWIDTH // 2, g.SCREENHEIGHT - 150)
        self.boss = self._create_boss()
        self.bullet_manager = BulletManager()

        if g.DEBUG_MODE:
            print("Battle reset! Player and Boss restored to full health.")

    def get_battle_result(self) -> str:
        """Get the result of the battle: victory/defeat/ongoing."""
        if not self.is_game_over():
            return "ongoing"
        return "victory" if self.boss.health <= 0 else "defeat"

    #region Spike System
    def _current_spike_interval(self):
        if getattr(self.boss, 'phase', 1) == 1:
            return getattr(g, 'HOLLOW_SPIKE_INTERVAL_P1', 6.0)
        elif self.boss.phase == 2:
            return getattr(g, 'HOLLOW_SPIKE_INTERVAL_P2', 4.5)
        else:
            return getattr(g, 'HOLLOW_SPIKE_INTERVAL_P3', 3.2)

    def _preflash_time(self):
        return 0.8  # seconds of warning before becoming solid

    def _update_spikes(self, dt: float):
        self.spike_timer += dt
        interval = self._current_spike_interval()
        if not self.spike_wave_active and self.spike_timer >= interval:
            self.spike_wave_active = True
            self.spike_wave_elapsed = 0.0
            self.spike_timer = 0.0
            self._spawn_spike_wave()
        if self.spike_wave_active:
            self.spike_wave_elapsed += dt
            duration = getattr(g, 'HOLLOW_SPIKE_DURATION', 3.0)
            if self.spike_wave_elapsed >= duration:
                self.spike_wave_active = False
                self.spikes_active.clear()

    def _spawn_spike_wave(self):
        self.spikes_active.clear()
        gap_min = getattr(g, 'HOLLOW_SPIKE_GAP_MIN', 90)
        gap_max = getattr(g, 'HOLLOW_SPIKE_GAP_MAX', 140)
        spike_w = getattr(g, 'HOLLOW_SPIKE_WIDTH', 28)
        top_h = getattr(g, 'HOLLOW_SPIKE_TOP_HEIGHT', 260)
        bottom_h = getattr(g, 'HOLLOW_SPIKE_BOTTOM_HEIGHT', 320)
        x = 0
        # Guarantee at least one gap near player x
        player_x = self.player.x + self.player.width/2
        gap_center = player_x
        gap_size = random.randint(gap_min, gap_max)
        gap_left = max(0, int(gap_center - gap_size/2))
        gap_right = min(g.SCREENWIDTH, int(gap_center + gap_size/2))
        while x < g.SCREENWIDTH:
            # If in gap region skip placing spikes
            if x + spike_w <= gap_left or x >= gap_right:
                # choose top or bottom spike pattern alternation
                place_top = random.random() < 0.5
                if place_top:
                    rect = pygame.Rect(x, 0, spike_w, top_h)
                    self.spikes_active.append((rect, True))
                else:
                    rect = pygame.Rect(x, g.SCREENHEIGHT - bottom_h, spike_w, bottom_h)
                    self.spikes_active.append((rect, False))
            x += spike_w

    def _handle_spike_collisions(self, block_player: bool = False):
        if not self.spike_wave_active:
            return
        solid = self.spike_wave_elapsed >= self._preflash_time()
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        dmg = getattr(g, 'HOLLOW_SPIKE_DAMAGE', 18) * (1/ g.FPS)
        for r, _ in self.spikes_active:
            if player_rect.colliderect(r):
                if solid:
                    # Damage
                    self.player.take_damage(dmg)
                    if block_player:
                        # Simple resolution: push player out horizontally based on center
                        if player_rect.centerx < r.centerx:
                            self.player.x = r.left - self.player.width - 1
                        else:
                            self.player.x = r.right + 1
                # If not solid yet (pre-flash) we do not block, only warn visually
    #endregion Spike System
    #endregion Game State & Reset