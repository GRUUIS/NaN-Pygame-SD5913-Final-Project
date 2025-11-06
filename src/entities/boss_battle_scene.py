"""
Boss Battle Scene - Integrated 2D Platformer with Boss Fight

This module combines all entities into a complete boss battle experience.
Uses modular components from separate files and globals.py configuration.
"""

#region Imports

import pygame
import random
import globals as g
from .player import Player
from .boss import Perfectionist
from .boss_the_hollow import TheHollow
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
        
        # Create platforms for 2D platformer gameplay
        self.platforms = [
            # Ground
            Platform(0, g.SCREENHEIGHT - 50, g.SCREENWIDTH, 50),
            # Platforms for movement
            Platform(100, g.SCREENHEIGHT - 200, 200, 20),
            Platform(g.SCREENWIDTH - 300, g.SCREENHEIGHT - 200, 200, 20),
            Platform(g.SCREENWIDTH // 2 - 100, g.SCREENHEIGHT - 350, 200, 20),
            Platform(50, g.SCREENHEIGHT - 450, 150, 20),
            Platform(g.SCREENWIDTH - 200, g.SCREENHEIGHT - 450, 150, 20),
        ]
        #endregion Initialization

    def _create_boss(self):
        x = g.SCREENWIDTH // 2
        y = 100
        if self._boss_type in ('procrastinator', 'procrastination', 'hollow', 'the_hollow', 'nihilism'):
            return TheHollow(x, y)
        # default
        return Perfectionist(x, y)
    
    #region Update Loop
    def update(self, dt: float):
        """Update the entire battle scene"""
        if not self.is_game_over():
            # Update entities
            self.player.update(dt, self.platforms)
            self.boss.update(dt, self.player, self.bullet_manager)
            self.ui.update(dt)

            # Pre-fight announcement once
            if not self._shown_entry:
                self._shown_entry = True
                # Anchor popup near boss
                def boss_anchor():
                    return (self.boss.x + self.boss.width/2, self.boss.y)
                self.ui.add(TextPopup(getattr(self.boss, 'entry_line', "You think words can scare me away?"), boss_anchor, duration=3.0, bg=(10,10,10)))
            
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
        # Clear screen
        screen.fill(g.COLORS['background'])
        
        # Draw platforms
        for platform in self.platforms:
            platform.draw(screen)
        
        # Draw entities
        self.player.draw(screen)
        self.boss.draw(screen)
        self.bullet_manager.draw(screen)
        self.ui.draw(screen)
        
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
    #endregion Game State & Reset