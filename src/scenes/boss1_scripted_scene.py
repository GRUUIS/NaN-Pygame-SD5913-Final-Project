import pygame
import random
import math
import os
import globals as g
from src.utils.font import get_font
from src.scenes.base_scene import BaseScene
from src.entities.player import Player
from src.entities.bullets import BulletManager
from src.entities.platform import Platform
from src.systems.ui import UIManager, draw_ui_overlay

class Boss1ScriptedScene(BaseScene):
    """
    Boss 1 Scripted Scene (The Hollow Intro)
    
    A scripted encounter where the player is ambushed by The Hollow from off-screen.
    The scene is pitch black, and the player faces an overwhelming attack.
    """
    def __init__(self, game_manager):
        super().__init__(game_manager)
        
        # Entities
        self.player = Player(g.SCREENWIDTH // 2, g.SCREENHEIGHT - 150)
        # One-hit feel from construction time so UI shows 1/1
        self.player.max_health = 1
        self.player.health = 1
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        self._dummy_boss = type('B', (), {'x':-9999,'y':-9999,'width':1,'height':1})()  # prevent None access for player bullets
        self._orig_player_move_speed = g.PLAYER_MOVE_SPEED
        
        # Platforms (Invisible floor)
        ground_h = 40
        self.platforms = [
            Platform(0, g.SCREENHEIGHT - ground_h, g.SCREENWIDTH, ground_h)
        ]
        self.player.on_ground = True # Snap to ground initially
        
        # Script State
        self.timer = 0.0
        self.attack_started = False
        self.game_over_timer = 0.0
        self._is_game_over = False
        self._death_fade_progress = 0.0  # 0.0 to 1.0 for fade to chaos effect
        self._chaos_particles = []  # Particle effect for death chaos
        self._death_transition_started = False  # Track if death SFX/transition played
        self._hit_flash_timer = 0.0  # Screen flash on hit
        
        # Attack Configuration
        self.shard_spawn_timer = 0.0
        self.shard_interval = 0.05 # Very fast spawn
        self.crossfire_timer = 0.0
        self.crossfire_interval = 0.18
        self.aimed_timer = 0.0
        self.aimed_interval = 0.6
        # Boss3 voidfire aimed shots
        self.voidfire_timer = 0.0
        self.voidfire_interval = 0.9
        
        # SFX
        self.sfx_rain = None
        self.sfx_shoot = None
        self.sfx_hit = None
        self.sfx_defeat = None
        try:
            sfx_path = os.path.join('assets', 'sfx')
            self.sfx_rain = pygame.mixer.Sound(os.path.join(sfx_path, 'hollow_rain.wav'))
            self.sfx_shoot = pygame.mixer.Sound(os.path.join(sfx_path, 'hollow_shoot.wav'))
            self.sfx_hit = pygame.mixer.Sound(os.path.join(sfx_path, 'hit.wav'))
            self.sfx_defeat = pygame.mixer.Sound(os.path.join(sfx_path, 'player_defeat.wav'))
            self.sfx_rain.set_volume(0.6)
            self.sfx_shoot.set_volume(0.4)
            self.sfx_hit.set_volume(0.7)
            self.sfx_defeat.set_volume(0.8)
        except Exception as e:
            print(f"SFX Load Error: {e}")

    def enter(self):
        super().enter()
        pygame.mixer.music.stop() # Silence for atmosphere
        self.timer = 0.0
        self.attack_started = False
        self._is_game_over = False
        self._death_fade_progress = 0.0
        self._chaos_particles = []
        self._death_transition_started = False
        self._hit_flash_timer = 0.0
        # One-hit kill feel (redundant guard if reset)
        self.player.max_health = 1
        self.player.health = 1
        # Disable shooting in this intro
        try:
            self.player.can_shoot = lambda: False
        except Exception:
            pass
        # Slow movement using globals with math-based scaling
        self._orig_player_move_speed = g.PLAYER_MOVE_SPEED
        print("Entering Boss 1 Scripted Scene: Pitch Black Ambush")

    def update(self, dt):
        self.timer += dt

        # Death fade transition
        if self._is_game_over:
            # Trigger death SFX and transition on first frame of death
            if not self._death_transition_started:
                self._death_transition_started = True
                # Play hit sound immediately
                if self.sfx_hit:
                    self.sfx_hit.play()
                # Play defeat sound with slight delay for dramatic effect
                if self.sfx_defeat:
                    pygame.time.set_timer(pygame.USEREVENT + 1, 200, 1)  # 200ms delay
                # Trigger screen shake/flash
                self._hit_flash_timer = 0.3  # Flash duration
            
            # Gradually fade to chaos
            self._death_fade_progress = min(1.0, self._death_fade_progress + dt * 0.3)
            
            # Decay hit flash
            if self._hit_flash_timer > 0:
                self._hit_flash_timer -= dt
            
            # Slow down player movement gradually
            self.player.vx *= 0.92
            self.player.vy *= 0.92
            
            # Update chaos particles
            for p in self._chaos_particles:
                p['x'] += p['vx'] * dt
                p['y'] += p['vy'] * dt
                p['life'] -= dt
                p['alpha'] = max(0, min(255, int(p['life'] * 100)))
            self._chaos_particles = [p for p in self._chaos_particles if p['life'] > 0]
            
            # Spawn new chaos particles
            if random.random() < 0.4:
                self._chaos_particles.append({
                    'x': random.uniform(0, g.SCREENWIDTH),
                    'y': random.uniform(0, g.SCREENHEIGHT),
                    'vx': random.uniform(-50, 50),
                    'vy': random.uniform(-50, 50),
                    'life': random.uniform(1.0, 2.5),
                    'alpha': 255,
                    'size': random.randint(2, 8),
                    'color': random.choice([(80, 0, 0), (60, 0, 20), (40, 0, 40), (20, 0, 20)])
                })
            
            self.bullet_manager.update(dt, self.player, None)
            return

        # 1. Update Player (apply heavy slow using a time-varying scale)
        # Scale oscillates slightly but stays very slow (10%~18% of normal)
        slow_scale = 0.10 + 0.08 * max(0.0, math.sin(self.timer * 0.7))
        g.PLAYER_MOVE_SPEED = max(10, int(self._orig_player_move_speed * slow_scale))
        self.player.update(dt, self.platforms)

        # 2. Update Bullets
        self.bullet_manager.update(dt, self.player, None) # No boss entity to hit
        self.bullet_manager.check_collisions(self.player, self._dummy_boss)

        # 3. Scripted Attacks
        if not self.is_game_over():
            # Phase 1: Suspense (0-2s)
            
            # Phase 2: The Attack Begins (2s+)
            if self.timer > 2.0:
                if not self.attack_started:
                    self.attack_started = True
                    # Initial attack sound played once
                    if self.sfx_rain:
                        self.sfx_rain.play()
                    print("The Hollow attacks!")
            
            # Phase 3: Crossfire (4s+) - Lasers from sides
            if self.timer > 4.0:
                self.crossfire_timer += dt
                if self.crossfire_timer >= self.crossfire_interval:
                    self.crossfire_timer = 0.0
                    y = random.randint(g.SCREENHEIGHT - 300, g.SCREENHEIGHT - 50)
                    if random.choice([True, False]):
                        # From Left
                        self.bullet_manager.add_bullet(-50, y, g.BULLET_SPEEDS['laser']*1.7, 0, 'laser', 'boss')
                    else:
                        # From Right
                        self.bullet_manager.add_bullet(g.SCREENWIDTH + 50, y, -g.BULLET_SPEEDS['laser']*1.7, 0, 'laser', 'boss')
                    # Play shoot sound for each crossfire bullet
                    if self.sfx_shoot:
                        self.sfx_shoot.play()
                        
                # Periodic aimed laser burst toward player (telegraph-free)
                self.aimed_timer += dt
                if self.aimed_timer >= self.aimed_interval:
                    self.aimed_timer = 0.0
                    px = self.player.x + self.player.width/2
                    py = self.player.y + self.player.height/2
                    # Fire from offscreen top towards player
                    sx, sy = px + random.uniform(-120,120), -80
                    dx, dy = px - sx, py - sy
                    d = max(1e-3, math.hypot(dx, dy))
                    spd = g.BULLET_SPEEDS['laser'] * 1.2
                    self.bullet_manager.add_bullet(sx, sy, spd*dx/d, spd*dy/d, 'laser', 'boss')
                    # Play shoot sound for aimed shot
                    if self.sfx_shoot:
                        self.sfx_shoot.play()
                        
                # Boss3-style voidfire aimed shots
                self.voidfire_timer += dt
                if self.voidfire_timer >= self.voidfire_interval:
                    self.voidfire_timer = 0.0
                    px = self.player.x + self.player.width/2
                    py = self.player.y + self.player.height/2
                    # spawn from a random edge toward player
                    edge = random.choice(['top','left','right'])
                    if edge == 'top':
                        sx, sy = random.uniform(0, g.SCREENWIDTH), -60
                    elif edge == 'left':
                        sx, sy = -40, random.uniform(20, g.SCREENHEIGHT-20)
                    else:
                        sx, sy = g.SCREENWIDTH + 40, random.uniform(20, g.SCREENHEIGHT-20)
                    dx, dy = px - sx, py - sy
                    d = max(1e-3, math.hypot(dx, dy))
                    spd = g.BULLET_SPEEDS.get('voidfire', 420)
                    self.bullet_manager.add_bullet(sx, sy, spd*dx/d, spd*dy/d, 'voidfire', 'boss')
                    # Play shoot sound for voidfire
                    if self.sfx_shoot:
                        self.sfx_shoot.play()
                        
        # 4. Check Game Over
        if self.player.health <= 0:
            self._is_game_over = True
            self.game_over_timer += dt
            # Wait for player input (Space) to start fade; handled in handle_event

    def draw(self, screen):
        # 1. Pitch Black Background
        screen.fill((0, 0, 0))
        
        # Hit flash effect (red flash on death)
        if self._hit_flash_timer > 0:
            flash_alpha = int((self._hit_flash_timer / 0.3) * 180)  # Fade from 180 to 0
            flash_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
            flash_surf.fill((200, 0, 0, flash_alpha))
            screen.blit(flash_surf, (0, 0))
        
        # 2. Draw Platforms (Optional: barely visible or invisible)
        # For "pitch black" feel, maybe don't draw them, or draw faint outlines
        # pygame.draw.rect(screen, (20, 20, 20), self.platforms[0].rect)
        
        # 3. Draw Player (fade during death)
        if self._is_game_over:
            # Draw player normally but with alpha fade
            temp_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
            self.player.draw(temp_surf)
            # Apply fade to entire player render
            fade_alpha = int(255 * (1.0 - self._death_fade_progress * 0.7))
            temp_surf.set_alpha(fade_alpha)
            screen.blit(temp_surf, (0, 0))
        else:
            self.player.draw(screen)
        
        # 4. Draw Bullets (fade during death)
        if self._is_game_over and self._death_fade_progress > 0.3:
            # Dim bullets as chaos takes over
            for bullet in self.bullet_manager.bullets:
                if bullet.active:
                    alpha = int(255 * (1.0 - self._death_fade_progress * 0.8))
                    bullet_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    color = g.COLORS.get(f'bullet_{bullet.bullet_type}', (255, 100, 100))
                    pygame.draw.circle(bullet_surf, (*color, alpha), (4, 4), 4)
                    screen.blit(bullet_surf, (bullet.x - 4, bullet.y - 4))
        else:
            self.bullet_manager.draw(screen)
        
        # 5. Death chaos particles
        if self._is_game_over:
            for p in self._chaos_particles:
                surf = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*p['color'], p['alpha']), (p['size']//2, p['size']//2), p['size']//2)
                screen.blit(surf, (int(p['x']), int(p['y'])))
            
            # Gradual dark chaos overlay
            chaos_overlay = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
            # Pulsing darkness with red tint
            pulse = abs(math.sin(self.game_over_timer * 2.0))
            darkness = int(self._death_fade_progress * 200)
            red_tint = int(self._death_fade_progress * 60 * pulse)
            chaos_overlay.fill((red_tint, 0, 0, darkness))
            screen.blit(chaos_overlay, (0, 0))
        
        # 6. UI (Health) - only before death fade completes
        if not self._is_game_over or self._death_fade_progress < 0.5:
            self.ui.draw(screen)
            # centralized HUD (player health etc.)
            try:
                draw_ui_overlay(screen, self)
            except Exception:
                pass
        
        # 7. Game Over instruction (small and subtle)
        if self._is_game_over and self._death_fade_progress > 0.6:
            # Small instruction text at bottom center
            text_alpha = min(255, int((self._death_fade_progress - 0.6) * 640))
            small_font = get_font(28)
            instruction = small_font.render("Press SPACE to continue", True, (160, 160, 160))
            instruction.set_alpha(text_alpha)
            # Position at lower center of screen
            y_pos = g.SCREENHEIGHT - 120
            screen.blit(instruction, instruction.get_rect(center=(g.SCREENWIDTH//2, y_pos)))

    def is_game_over(self):
        """Compatibility with run_boss_test loop which expects a callable."""
        return self._is_game_over

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Restore speed then restart
                g.PLAYER_MOVE_SPEED = getattr(self, '_orig_player_move_speed', g.PLAYER_MOVE_SPEED)
                self.enter() # Restart
            if event.key == pygame.K_ESCAPE:
                self.game_manager.change_scene('menu') # Assuming menu exists
        # Handle delayed defeat sound
        if event.type == pygame.USEREVENT + 1:
            if self.sfx_defeat:
                self.sfx_defeat.play()

    def exit(self):
        """Clean up and restore modified globals when exiting the scene"""
        # Restore player move speed to original value
        try:
            original_speed = getattr(self, '_orig_player_move_speed', 100)
            g.PLAYER_MOVE_SPEED = original_speed
            print(f"Boss1 exit: Restored PLAYER_MOVE_SPEED to {original_speed}")
        except Exception as e:
            print(f"Warning: Failed to restore player speed: {e}")
            # Fallback to hardcoded default
            g.PLAYER_MOVE_SPEED = 100
        super().exit()
