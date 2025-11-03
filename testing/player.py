"""
Player Entity - 2D Platformer Character (testing copy)

This is a copy of `src/entities/player.py` placed in `testing/` for experimentation.
Do not import this from production code unless intentionally switching imports in tests.
"""

#region Imports

import pygame
import math
from typing import List, Tuple
import globals as g
#endregion Imports


class Player:
    """
    2D Platformer Player with physics and combat abilities
    """
    def __init__(self, x: float, y: float):
        #region Init/State
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.width = g.PLAYER_SIZE
        self.height = g.PLAYER_SIZE
        self.on_ground = False
        
        # Health and combat
        self.max_health = g.PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.attack_cooldown = 0.0
        self.invincible_time = 0.0
        
        # Input state
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = (0, 0)
        self.mouse_pressed = False
    # Held tool (testing only)
    self.held_tool = None
        #endregion Init/State
    
    #region Update & Physics
    def update(self, dt: float, platforms: List):
        """Update player physics and state"""
        # Update timers
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.invincible_time = max(0, self.invincible_time - dt)
        
        # Handle input
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()[0]
        
        # Horizontal movement
        if self.keys[pygame.K_a] or self.keys[pygame.K_LEFT]:
            self.vx = -g.PLAYER_MOVE_SPEED
        elif self.keys[pygame.K_d] or self.keys[pygame.K_RIGHT]:
            self.vx = g.PLAYER_MOVE_SPEED
        else:
            if self.on_ground:
                self.vx *= g.GROUND_FRICTION
            else:
                self.vx *= g.AIR_RESISTANCE
        
        # Jumping
        if (self.keys[pygame.K_SPACE] or self.keys[pygame.K_w] or self.keys[pygame.K_UP]) and self.on_ground:
            self.vy = -g.JUMP_STRENGTH
            self.on_ground = False
        
        # Apply gravity
        if not self.on_ground:
            self.vy += g.GRAVITY * dt
            if self.vy > g.MAX_FALL_SPEED:
                self.vy = g.MAX_FALL_SPEED
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Platform collision
        self.handle_platform_collision(platforms)
        
        # Keep player in screen bounds
        self.x = max(0, min(g.SCREENWIDTH - self.width, self.x))
        if self.y > g.SCREENHEIGHT:
            self.take_damage(20)  # Fall damage
            self.y = g.SCREENHEIGHT - 100  # Reset position
    #endregion Update & Physics
    
    #region Collisions
    def handle_platform_collision(self, platforms: List):
        """Handle collision with platforms"""
        from .platform import Platform  # Local import to avoid circular imports
        
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = False
        
        for platform in platforms:
            if player_rect.colliderect(platform.rect):
                # Landing on top of platform
                if self.vy > 0 and self.y < platform.rect.top:
                    self.y = platform.rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                # Hitting platform from below
                elif self.vy < 0 and self.y > platform.rect.bottom:
                    self.y = platform.rect.bottom
                    self.vy = 0
                # Hitting platform from side
                else:
                    if self.vx > 0:  # Moving right
                        self.x = platform.rect.left - self.width
                    else:  # Moving left
                        self.x = platform.rect.right
                    self.vx = 0
    #endregion Collisions
    
    #region Combat
    def can_shoot(self) -> bool:
        """Check if player can shoot"""
        return self.attack_cooldown <= 0
    
    def shoot(self) -> Tuple[float, float, float, float]:
        """Shoot towards mouse position, return bullet info"""
        if not self.can_shoot():
            return None
            
        self.attack_cooldown = g.PLAYER_ATTACK_COOLDOWN
        
        # Calculate direction to mouse
        dx = self.mouse_pos[0] - (self.x + self.width/2)
        dy = self.mouse_pos[1] - (self.y + self.height/2)
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Return bullet spawn position and direction
            return (self.x + self.width/2, self.y + self.height/2, dx, dy)
        
        return None
    
    def take_damage(self, damage: float):
        """Take damage with invincibility frames"""
        if self.invincible_time <= 0:
            self.health -= damage
            self.invincible_time = g.PLAYER_INVINCIBLE_DURATION
            if self.health <= 0:
                self.health = 0
    #region Tool handling (testing helpers)
    def hold_tool(self, tool):
        """Assign a tool to the player's hands (testing helper)."""
        self.held_tool = tool

    def drop_tool(self):
        """Remove the currently held tool and return it, or None if none held."""
        t = getattr(self, 'held_tool', None)
        self.held_tool = None
        return t
    #endregion Tool handling
    #endregion Combat
    
    #region Rendering
    def draw(self, screen: pygame.Surface):
        """Draw the player"""
        # Choose color based on state
        if self.invincible_time > 0:
            # Flashing effect during invincibility
            if int(self.invincible_time * 10) % 2:
                color = g.COLORS['player_invincible']
            else:
                color = g.COLORS['player']
        elif not self.on_ground:
            color = g.COLORS['player_jumping']
        else:
            color = g.COLORS['player']
        
        pygame.draw.rect(screen, color, (int(self.x), int(self.y), self.width, self.height))
        
        # Draw collision box in debug mode
        if g.SHOW_COLLISION_BOXES:
            pygame.draw.rect(screen, (255, 255, 0), 
                           (int(self.x), int(self.y), self.width, self.height), 1)
    #endregion Rendering
