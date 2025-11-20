"""
Player Entity - 2D Platformer Character

Handles player physics, input, combat, and rendering.
Uses configuration from globals.py.
"""

#region Imports

import pygame
import math
import os
from typing import List, Tuple
import globals as g
from src.utils.sprite_loader import load_animation_strip
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
        self.mouse_pressed_right = False

        # Animation State
        self.animations = {}
        self.current_anim = 'idle'
        self.facing_right = True
        self.frame_index = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.1  # 10 FPS

        # Load Sprites
        try:
            sprite_dir = os.path.join('assets', 'sprites', 'Blue_witch')
            self.animations['idle'] = load_animation_strip(os.path.join(sprite_dir, 'B_witch_idle.png'))
            self.animations['run'] = load_animation_strip(os.path.join(sprite_dir, 'B_witch_run.png'))
            self.animations['attack'] = load_animation_strip(os.path.join(sprite_dir, 'B_witch_attack.png'))
            self.animations['take_damage'] = load_animation_strip(os.path.join(sprite_dir, 'B_witch_take_damage.png'))
            self.animations['death'] = load_animation_strip(os.path.join(sprite_dir, 'B_witch_death.png'))
            self.animations['charge'] = load_animation_strip(os.path.join(sprite_dir, 'B_witch_charge.png'))
            
            # Fallback if loading fails or returns empty
            if not self.animations.get('idle'):
                 s = pygame.Surface((self.width, self.height))
                 s.fill(g.COLORS['player'])
                 self.animations['idle'] = [s]
                 
        except Exception as e:
            print(f"Failed to load player sprites: {e}")
            # Fallback
            s = pygame.Surface((self.width, self.height))
            s.fill(g.COLORS['player'])
            self.animations = {'idle': [s]}

        # SFX
        try:
            sfx_path = os.path.join('assets', 'sfx', 'Attack_alienshoot1.wav')
            self.shoot_sfx = pygame.mixer.Sound(sfx_path)
            self.shoot_sfx.set_volume(0.4)
        except Exception as e:
            print(f"Failed to load player SFX: {e}")
            self.shoot_sfx = None
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
        buttons = pygame.mouse.get_pressed()
        self.mouse_pressed = buttons[0]
        self.mouse_pressed_right = buttons[2]
        
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
        
        # Animation Logic
        if self.vx > 0:
            self.facing_right = True
        elif self.vx < 0:
            self.facing_right = False
            
        # Determine animation state
        target_anim = 'idle'
        if abs(self.vx) > 10: # Threshold for movement
            target_anim = 'run'
            
        if target_anim != self.current_anim:
            self.current_anim = target_anim
            self.frame_index = 0
            self.anim_timer = 0.0
            
        # Advance frame
        self.anim_timer += dt
        frames = self.animations.get(self.current_anim, self.animations.get('idle', []))
        if not frames: frames = [] # Should be handled by fallback
        
        if frames and self.anim_timer >= self.anim_speed:
            self.anim_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(frames)
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
        
        if self.shoot_sfx:
            self.shoot_sfx.play()

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

    def shoot_voidfire(self) -> Tuple[float, float, float, float]:
        """Fire a Voidfire projectile towards mouse; separate cooldown for clarity."""
        if not self.can_shoot():
            return None

        # Slightly longer cooldown for voidfire for balance
        self.attack_cooldown = max(g.PLAYER_ATTACK_COOLDOWN, 0.6)

        if self.shoot_sfx:
            self.shoot_sfx.play()

        dx = self.mouse_pos[0] - (self.x + self.width/2)
        dy = self.mouse_pos[1] - (self.y + self.height/2)
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            dx /= distance
            dy /= distance
            return (self.x + self.width/2, self.y + self.height/2, dx, dy)
        return None
    
    def take_damage(self, damage: float):
        """Take damage with invincibility frames"""
        if self.invincible_time <= 0:
            self.health -= damage
            self.invincible_time = g.PLAYER_INVINCIBLE_DURATION
            if self.health <= 0:
                self.health = 0
    #endregion Combat
    
    #region Rendering
    def draw(self, screen: pygame.Surface):
        """Draw the player"""
        # Get current frame
        frames = self.animations.get(self.current_anim, self.animations.get('idle', []))
        
        if not frames:
            # Fallback
            pygame.draw.rect(screen, g.COLORS['player'], (int(self.x), int(self.y), self.width, self.height))
            return

        idx = self.frame_index % len(frames)
        image = frames[idx]
        
        # Flip if facing left (Blue witch sprites face right by default usually, let's assume right)
        # Actually, let's check the sprites. Usually sprites face right.
        # If facing_right is False, we flip.
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
            
        # Draw centered on hitbox bottom
        rect = image.get_rect()
        rect.midbottom = (self.x + self.width // 2, self.y + self.height)
        
        # Flashing effect during invincibility
        if self.invincible_time > 0:
            if int(self.invincible_time * 10) % 2:
                # Draw white silhouette or just skip drawing to flash
                mask = pygame.mask.from_surface(image)
                white_surf = mask.to_surface(setcolor=(255, 255, 255, 128), unsetcolor=(0,0,0,0))
                screen.blit(white_surf, rect)
            else:
                screen.blit(image, rect)
        else:
            screen.blit(image, rect)
        
        # Draw collision box in debug mode
        if g.SHOW_COLLISION_BOXES:
            pygame.draw.rect(screen, (255, 255, 0), 
                           (int(self.x), int(self.y), self.width, self.height), 1)
    #endregion Rendering
