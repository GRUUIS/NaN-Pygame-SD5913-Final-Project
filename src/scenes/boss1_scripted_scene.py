import pygame
import random
import math
import os
import globals as g
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
        # defeat UI stays simple
        
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
        try:
            sfx_path = os.path.join('assets', 'sfx')
            self.sfx_rain = pygame.mixer.Sound(os.path.join(sfx_path, 'hollow_rain.wav'))
            self.sfx_shoot = pygame.mixer.Sound(os.path.join(sfx_path, 'hollow_shoot.wav'))
            self.sfx_rain.set_volume(0.6)
            self.sfx_shoot.set_volume(0.4)
        except Exception as e:
            print(f"SFX Load Error: {e}")

    def enter(self):
        super().enter()
        pygame.mixer.music.stop() # Silence for atmosphere
        self.timer = 0.0
        self.attack_started = False
        self._is_game_over = False
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

        # Freeze player movement after death
        if self._is_game_over:
            # Keep bullets animating briefly, but player stops reacting
            self.player.vx = 0.0
            self.player.vy = 0.0
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
                    if self.sfx_shoot: self.sfx_shoot.play()
                    print("The Hollow attacks!")
                # Note: Void shard rain and aimed shards disabled for black scene
            
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
                        
        # 4. Check Game Over
        if self.player.health <= 0:
            self._is_game_over = True
            self.game_over_timer += dt
            # Wait for player input (Space) to start fade; handled in handle_event

    def draw(self, screen):
        # 1. Pitch Black Background
        screen.fill((0, 0, 0))
        
        # 2. Draw Platforms (Optional: barely visible or invisible)
        # For "pitch black" feel, maybe don't draw them, or draw faint outlines
        # pygame.draw.rect(screen, (20, 20, 20), self.platforms[0].rect)
        
        # 3. Draw Player
        self.player.draw(screen)
        # No extra defeated glow; keep original minimal look
        
        # 4. Draw Bullets
        self.bullet_manager.draw(screen)
        
        # 5. UI (Health)
        self.ui.draw(screen)
        # centralized HUD (player health etc.)
        try:
            draw_ui_overlay(screen, self)
        except Exception:
            pass
        
        # 6. Game Over Text (original simple UI)
        if self._is_game_over:
            font = pygame.font.Font(None, 72)
            text = font.render("YOU DIED", True, (150, 0, 0))
            rect = text.get_rect(center=(g.SCREENWIDTH//2, g.SCREENHEIGHT//2))
            screen.blit(text, rect)

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

    def exit(self):
        # Restore any globals we modified
        try:
            g.PLAYER_MOVE_SPEED = getattr(self, '_orig_player_move_speed', g.PLAYER_MOVE_SPEED)
        except Exception:
            pass
        # No color overrides to restore
