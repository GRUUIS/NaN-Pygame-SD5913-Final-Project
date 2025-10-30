"""
Bullet System - Projectile Management

Handles bullets for both player and boss, including different bullet types
and collision detection. Uses configuration from globals.py.
"""

import pygame
import math
from typing import List
import globals as g


class Bullet:
    """Bullet projectile for both player and boss"""
    def __init__(self, x: float, y: float, vx: float, vy: float, bullet_type: str, source: str):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.type = bullet_type
        self.source = source  # 'player' or 'boss'
        self.damage = g.BULLET_DAMAGE[bullet_type]
        self.lifetime = 5.0
        self.homing_target = None
        
        # Visual properties
        self.size = 4 if bullet_type != 'laser' else 6
        
    def update(self, dt: float, target=None):
        """Update bullet position and behavior"""
        self.lifetime -= dt
        
        # Homing behavior
        if self.type == 'homing' and target:
            # Calculate direction to target
            dx = (target.x + target.width/2) - self.x
            dy = (target.y + target.height/2) - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0:
                # Homing strength
                homing_strength = 200 * dt
                self.vx += (dx / distance) * homing_strength
                self.vy += (dy / distance) * homing_strength
                
                # Limit speed
                speed = math.sqrt(self.vx*self.vx + self.vy*self.vy)
                max_speed = g.BULLET_SPEEDS['homing']
                if speed > max_speed:
                    self.vx = (self.vx / speed) * max_speed
                    self.vy = (self.vy / speed) * max_speed
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
    
    def is_expired(self) -> bool:
        """Check if bullet should be removed"""
        return (self.lifetime <= 0 or 
                self.x < -50 or self.x > g.SCREENWIDTH + 50 or
                self.y < -50 or self.y > g.SCREENHEIGHT + 50)
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle"""
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, 
                          self.size, self.size)
    
    def draw(self, screen: pygame.Surface):
        """Draw the bullet"""
        color_key = f'bullet_{self.type}'
        color = g.COLORS.get(color_key, g.COLORS['bullet_normal'])
        
        # Draw bullet based on type
        if self.type == 'laser':
            # Elongated shape for laser
            pygame.draw.ellipse(screen, color, 
                              (self.x - self.size, self.y - self.size//2, 
                               self.size*2, self.size))
        else:
            # Circular bullets
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
        
        # Draw collision box in debug mode
        if g.SHOW_COLLISION_BOXES:
            rect = self.get_rect()
            pygame.draw.rect(screen, (255, 0, 255), rect, 1)


class BulletManager:
    """Manages all bullets in the scene"""
    def __init__(self):
        self.bullets: List[Bullet] = []
    
    def add_bullet(self, x: float, y: float, vx: float, vy: float, 
                   bullet_type: str, source: str):
        """Add a new bullet"""
        self.bullets.append(Bullet(x, y, vx, vy, bullet_type, source))
    
    def update(self, dt: float, player, boss):
        """Update all bullets"""
        # Update bullet positions and behavior
        for bullet in self.bullets[:]:  # Copy list to avoid modification issues
            if bullet.source == 'boss' and bullet.type == 'homing':
                bullet.update(dt, player)
            else:
                bullet.update(dt)
        
        # Remove expired bullets
        self.bullets = [b for b in self.bullets if not b.is_expired()]
    
    def check_collisions(self, player, boss):
        """Check bullet collisions with player and boss"""
        for bullet in self.bullets[:]:
            bullet_rect = bullet.get_rect()
            
            # Boss bullets hitting player
            if bullet.source == 'boss':
                player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
                if bullet_rect.colliderect(player_rect):
                    player.take_damage(bullet.damage)
                    self.bullets.remove(bullet)
            
            # Player bullets hitting boss
            elif bullet.source == 'player':
                boss_rect = pygame.Rect(boss.x, boss.y, boss.width, boss.height)
                if bullet_rect.colliderect(boss_rect):
                    boss.take_damage(bullet.damage)
                    self.bullets.remove(bullet)
    
    def draw(self, screen: pygame.Surface):
        """Draw all bullets"""
        for bullet in self.bullets:
            bullet.draw(screen)