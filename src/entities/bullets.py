"""
Bullet System - Projectile Management

Handles bullets for both player and boss, including different bullet types
and collision detection. Uses configuration from globals.py.
"""

#region Imports

import pygame
import math
from typing import List
import globals as g
#endregion Imports


#region Bullet
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
        # Base lifetime; some types override
        self.lifetime = 5.0
        self.homing_target = None
        # For lingering slime pools (do not delete on first hit)
        self.tick_timer = 0.0
        if self.type == 'slime':
            # Slime projectile will travel, then when velocity nearly zero (or hits ground handled elsewhere) we treat as pool.
            self.size = 12
            self.lifetime = g.BOSS2_SLIME_POOL_LIFETIME
            self.pool = False  # becomes True after vertical speed small / touches ground heuristic
        elif self.type == 'slime_spore':
            # Floating spore that ascends briefly, then drops and creates a larger toxic puddle
            self.size = 10
            self.float_time = getattr(g, 'BOSS2_SPORE_FLOAT_TIME', 1.3)
            self.lifetime = self.float_time + g.BOSS2_SLIME_POOL_LIFETIME
            self.ascending = True
            self.pool = False
        else:
            self.pool = False
        
        # Visual properties
        if bullet_type == 'laser':
            self.size = 6
        elif bullet_type == 'void_shard':
            self.size = 7
        elif bullet_type == 'voidfire':
            self.size = 5
        elif bullet_type == 'slime':
            # size already set above (12)
            pass
        else:
            self.size = 4
        
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
        
        # Simple gravity for slime lob to fall
        if self.type == 'slime' and not self.pool:
            self.vy += 250 * dt  # light gravity
        if self.type == 'slime_spore':
            if self.ascending:
                # slow upward drift
                self.vy -= 90 * dt
                self.vx *= 0.98
                self.float_time -= dt
                if self.float_time <= 0:
                    # begin drop
                    self.ascending = False
                    self.vy = 240  # start falling
            else:
                # falling like slime
                self.vy += 220 * dt
            # transform to pool when landed / slowed
            if not self.pool and not self.ascending and (abs(self.vy) < 40 or self.y > g.SCREENHEIGHT - 140):
                self.vx = 0
                self.vy = 0
                self.pool = True
                # enlarge puddle
                self.size = 16
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Improved pooling: only form puddle after descending and reaching ground level
        if self.type == 'slime' and not self.pool:
            ground_top = g.SCREENHEIGHT - getattr(g, 'BOSS2_GROUND_HEIGHT', 78)
            # require downward motion and proximity to ground
            if self.vy > 0 and self.y >= ground_top - self.size*0.4:
                self.vx = 0
                self.vy = 0
                self.pool = True
    
    def is_expired(self) -> bool:
        """Check if bullet should be removed"""
        return (self.lifetime <= 0 or 
                self.x < -50 or self.x > g.SCREENWIDTH + 50 or
                (self.y < -50) or (self.y > g.SCREENHEIGHT + 50 and not self.pool))
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle"""
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, 
                          self.size, self.size)
    
    def draw(self, screen: pygame.Surface):
        """Draw the bullet"""
        color_key = f'bullet_{self.type}'
        color = g.COLORS.get(color_key, g.COLORS['bullet_normal'])
        
        # Helper: radial gradient circle
        def draw_glow(radius, inner_color, outer_alpha=55):
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            for r in range(radius, 0, -1):
                a = int(outer_alpha * (r/ radius)**2)
                c = (*inner_color, a)
                pygame.draw.circle(surf, c, (radius, radius), r)
            screen.blit(surf, (int(self.x - radius), int(self.y - radius)))

        # Draw bullet based on type with improved visuals
        if self.type == 'laser':
            body_rect = (self.x - self.size, self.y - self.size*0.35, self.size*2, self.size*0.7)
            pygame.draw.ellipse(screen, color, body_rect)
            draw_glow(int(self.size*1.4), color, 35)
        elif self.type == 'void_shard':
            # Diamond shape with subtle glow for visibility on dark scenes
            s = self.size
            pts = [
                (int(self.x), int(self.y - s)),
                (int(self.x + s), int(self.y)),
                (int(self.x), int(self.y + s)),
                (int(self.x - s), int(self.y))
            ]
            pygame.draw.polygon(screen, color, pts)
            pygame.draw.polygon(screen, (0,0,0), pts, 1)
            draw_glow(int(self.size*1.8), color, 50)
        elif self.type == 'voidfire':
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
            draw_glow(self.size*2, color, 65)
        elif self.type == 'slime':
            if self.pool:
                # Pulsating toxic puddle with rim
                puddle_w = self.size * 3
                puddle_h = int(self.size * 1.3)
                rect = pygame.Rect(int(self.x - puddle_w/2), int(self.y - puddle_h/2), puddle_w, puddle_h)
                surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                t = pygame.time.get_ticks()*0.003
                base_col = (color[0], color[1], color[2])
                pygame.draw.ellipse(surf, (*base_col, 150), surf.get_rect())
                rim_alpha = int(90 + 40*math.sin(t))
                pygame.draw.ellipse(surf, (30,60,30,rim_alpha), surf.get_rect().inflate(-8,-6), 2)
                screen.blit(surf, rect.topleft)
            else:
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
                draw_glow(int(self.size*1.6), color, 45)
        elif self.type == 'slime_spore':
            if self.pool:
                puddle_w = self.size * 3 + 12
                puddle_h = int(self.size * 1.4)
                rect = pygame.Rect(int(self.x - puddle_w/2), int(self.y - puddle_h/2), puddle_w, puddle_h)
                surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                t = pygame.time.get_ticks()*0.004
                pygame.draw.ellipse(surf, (color[0], color[1], color[2], 180), surf.get_rect())
                rim_alpha = int(120 + 40*math.sin(t))
                pygame.draw.ellipse(surf, (30,80,40,rim_alpha), surf.get_rect().inflate(-10,-8), 2)
                screen.blit(surf, rect.topleft)
            else:
                # floating spore orb with pulsing aura
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
                draw_glow(int(self.size*1.9), color, 60)
        else:
            # Generic player / normal bullet with outline + glow
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(screen, (0,0,0), (int(self.x), int(self.y)), self.size, 1)
            draw_glow(int(self.size*1.4), color, 40)
        
        # Draw collision box in debug mode
        if g.SHOW_COLLISION_BOXES:
            rect = self.get_rect()
            pygame.draw.rect(screen, (255, 0, 255), rect, 1)
#endregion Bullet


#region BulletManager
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
                    if bullet.type == 'slime' and getattr(bullet, 'pool', False):
                        # Damage over time; use tick timer
                        bullet.tick_timer += 1/ g.FPS  # approximate frame dt for tick gating
                        if bullet.tick_timer >= g.BOSS2_SLIME_TICK_INTERVAL:
                            bullet.tick_timer = 0.0
                            player.take_damage(g.BOSS2_SLIME_TICK_DAMAGE)
                        # do not remove pool here
                    elif bullet.type == 'slime_spore' and getattr(bullet, 'pool', False):
                        # Separate, lower DPS for spore pools
                        bullet.tick_timer += 1/ g.FPS
                        interval = getattr(g, 'BOSS2_SPORE_POOL_TICK_INTERVAL', 0.55)
                        if bullet.tick_timer >= interval:
                            bullet.tick_timer = 0.0
                            dmg = getattr(g, 'BOSS2_SPORE_POOL_TICK_DAMAGE', 20)
                            player.take_damage(dmg)
                    else:
                        player.take_damage(bullet.damage)
                        # remove non-pool bullet
                        if bullet in self.bullets:
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
#endregion BulletManager