"""
Boss Battle Scene - Integrated 2D Platformer with Boss Fight

This module combines all entities into a complete boss battle experience.
Uses modular components from separate files and globals.py configuration.
"""

import pygame
import globals as g
from .player import Player
from .boss import Perfectionist
from .bullets import BulletManager
from .platform import Platform


class BossBattleScene:
    """
    Complete boss battle scene with integrated platformer mechanics
    """
    def __init__(self):
        # Initialize entities
        self.player = Player(g.SCREENWIDTH // 2, g.SCREENHEIGHT - 150)
        self.boss = Perfectionist(g.SCREENWIDTH // 2, 100)
        self.bullet_manager = BulletManager()
        
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
    
    def update(self, dt: float):
        """Update the entire battle scene"""
        if not self.is_game_over():
            # Update entities
            self.player.update(dt, self.platforms)
            self.boss.update(dt, self.player, self.bullet_manager)
            
            # Handle player shooting
            if self.player.mouse_pressed and self.player.can_shoot():
                bullet_info = self.player.shoot()
                if bullet_info:
                    x, y, dx, dy = bullet_info
                    speed = g.BULLET_SPEEDS['player']
                    self.bullet_manager.add_bullet(x, y, dx * speed, dy * speed, 'player', 'player')
                    
                    # Debug: 显示射击信息
                    if g.DEBUG_MODE:
                        print(f"Player shot: pos=({x:.1f}, {y:.1f}), dir=({dx:.2f}, {dy:.2f})")
            
            # Update bullets
            self.bullet_manager.update(dt, self.player, self.boss)
            
            # Check bullet collisions
            self.bullet_manager.check_collisions(self.player, self.boss)
            
            # Debug: 显示生命值变化
            if g.DEBUG_MODE and hasattr(self, '_last_boss_health'):
                if self._last_boss_health != self.boss.health:
                    print(f"Boss health: {self.boss.health}/{self.boss.max_health}")
                    self._last_boss_health = self.boss.health
            elif g.DEBUG_MODE:
                self._last_boss_health = self.boss.health
    
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
        
        # Draw debug information
        if g.SHOW_DEBUG_INFO:
            self._draw_debug_info(screen)
    
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
    
    def is_game_over(self) -> bool:
        """Check if battle is over"""
        return self.player.health <= 0 or self.boss.health <= 0
    
    def reset_battle(self):
        """Reset the battle to initial state"""
        # Reset player
        self.player = Player(g.SCREENWIDTH // 2, g.SCREENHEIGHT - 150)
        
        # Reset boss
        self.boss = Perfectionist(g.SCREENWIDTH // 2, 100)
        
        # Clear bullets
        self.bullet_manager = BulletManager()
        
        # Debug message
        if g.DEBUG_MODE:
            print("Battle reset! Player and Boss restored to full health.")
    
    def get_battle_result(self) -> str:
        """Get the result of the battle"""
        if not self.is_game_over():
            return "ongoing"
        elif self.player.health <= 0:
            return "defeat"
        elif self.boss.health <= 0:
            return "victory"
        else:
            return "unknown"