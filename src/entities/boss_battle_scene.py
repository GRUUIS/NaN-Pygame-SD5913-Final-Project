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
from .boss_the_hollow import TheHollow
from .boss_sloth import TheSloth
from .bullets import BulletManager
from .platform import Platform
from ..systems.ui import UIManager, TextPopup, Announcement, draw_ui_overlay, draw_game_over_screen
#endregion Imports


class BossBattleScene:
    """
    Complete boss battle scene with integrated platformer mechanics
    """
    def __init__(self, boss_type: str = 'hollow'):
        #region Initialization
        # Initialize entities
        self.player = Player(g.SCREENWIDTH // 2, g.SCREENHEIGHT - 150)
        self._boss_type = boss_type.lower() if boss_type else 'hollow'
        self.boss = self._create_boss()
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        self._shown_victory = False
        self._shown_entry = False
        # Transition states
        self._victory_transition = False
        self._defeat_shown = False
        self._transition_timer = 0.0
        self._earthquake_timer = 0.0
        self._void_particles = []
        self._falling_platforms = []
        self._bgm_fading = False
        self._boss_death_location = None  # Store where boss died
        self._boss_defeated = False  # Track if boss is defeated but transition not started
        self._death_marker_particles = []  # Visual indicator at death location
        self._death_marker_time = 0.0
        self._player_wants_exit = False  # Track if player pressed space to exit after victory
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
                try:
                    pygame.mixer.music.set_volume(getattr(g, 'music_volume', 0.2))
                except Exception:
                    try:
                        pygame.mixer.music.set_volume(0.2)
                    except Exception:
                        pass
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Failed to load BGM: {e}")
        
        # Load SFX
        self.defeat_sfx = None
        self.victory_sfx = None
        self.earthquake_sfx = None
        self.fade_sfx = None
        try:
            self.defeat_sfx = pygame.mixer.Sound(os.path.join('assets', 'sfx', 'player_defeat.wav'))
            self.defeat_sfx.set_volume(0.5)
        except Exception:
            pass
        try:
            self.victory_sfx = pygame.mixer.Sound(os.path.join('assets', 'sfx', 'victory_fanfare.wav'))
            self.victory_sfx.set_volume(0.6)
        except Exception:
            pass
        try:
            self.earthquake_sfx = pygame.mixer.Sound(os.path.join('assets', 'sfx', 'earthquake_rumble.wav'))
            self.earthquake_sfx.set_volume(0.7)
        except Exception:
            pass
        try:
            self.fade_sfx = pygame.mixer.Sound(os.path.join('assets', 'sfx', 'white_fade.wav'))
            self.fade_sfx.set_volume(0.5)
        except Exception:
            pass
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
            b = TheHollow(x, y)
            b.ui = getattr(self, 'ui', None)
            return b
        # default to TheHollow
        b = TheHollow(x, y)
        b.ui = getattr(self, 'ui', None)
        return b
    
    #region Update Loop
    def update(self, dt: float):
        """Update the entire battle scene"""
        self._last_dt = dt  # Store for transition effects
        # Handle victory transition
        if self._victory_transition:
            self._transition_timer += dt
            if isinstance(self.boss, TheHollow):
                self._earthquake_timer += dt
                self._update_void_particles(dt)
            # Fade out BGM
            if self._bgm_fading:
                current_volume = pygame.mixer.music.get_volume()
                new_volume = max(0, current_volume - 0.3 * dt)
                pygame.mixer.music.set_volume(new_volume)
                if new_volume <= 0:
                    pygame.mixer.music.stop()
                    self._bgm_fading = False
            return
        
        # Handle defeat
        if self.player.health <= 0 and not self._defeat_shown:
            self._defeat_shown = True
            if self.defeat_sfx:
                self.defeat_sfx.play()
            return
        
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
            
            # Check for boss defeat - store location, let player explore
            if self.boss.health <= 0 and not self._boss_defeated and not self._victory_transition:
                if hasattr(self.boss, 'fully_defeated') and self.boss.fully_defeated:
                    self._boss_defeated = True
                    self._boss_death_location = (self.boss.x + self.boss.width/2, self.boss.y + self.boss.height/2)
                    self._spawn_death_marker()
                elif not hasattr(self.boss, 'fully_defeated'):
                    self._boss_defeated = True
                    self._boss_death_location = (self.boss.x + self.boss.width/2, self.boss.y + self.boss.height/2)
                    self._spawn_death_marker()
            
            # Check proximity to boss death location to trigger transition
            if self._boss_defeated and self._boss_death_location and not self._victory_transition:
                self._death_marker_time += dt
                self._update_death_marker(dt)
                
                px = self.player.x + self.player.width/2
                py = self.player.y + self.player.height/2
                bx, by = self._boss_death_location
                distance = ((px - bx)**2 + (py - by)**2)**0.5
                
                if distance < 120:  # Player approaches within ~120 pixels
                    self._victory_transition = True
                    self._transition_timer = 0.0
                    self._bgm_fading = True
                    if self.victory_sfx:
                        self.victory_sfx.play()
                    if isinstance(self.boss, TheHollow):
                        if self.earthquake_sfx:
                            self.earthquake_sfx.play()
                        self._earthquake_timer = 0.0
                        self._spawn_void_particles()
                    else:
                        self._spawn_void_particles()

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
    
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.KEYDOWN:
            # R key: restart battle (for defeat)
            if event.key == pygame.K_r and self.is_game_over():
                # Only allow restart on defeat
                if self.player.health <= 0:
                    # Reset battle
                    self.reset_battle()
                    # Restart BGM
                    try:
                        pygame.mixer.music.play(-1)
                        pygame.mixer.music.set_volume(getattr(g, 'music_volume', 0.2))
                    except Exception:
                        pass
                    # Clear transition states
                    self._victory_transition = False
                    self._defeat_shown = False
                    self._transition_timer = 0.0
                    self._boss_defeated = False
                    self._boss_death_location = None
                    self._death_marker_particles = []
                    self._bgm_fading = False
                    self._player_wants_exit = False
            # SPACE key: exit after victory
            elif event.key == pygame.K_SPACE:
                # Check if boss is defeated (victory condition)
                if self.is_game_over() and self.boss.health <= 0:
                    self._player_wants_exit = True
    
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
        # Draw centralized HUD (player/boss bars, meters, footer)
        try:
            draw_ui_overlay(screen, self)
        except Exception:
            pass
        
        # Draw death marker indicator (before victory transition)
        if self._boss_defeated and not self._victory_transition and self._boss_death_location:
            import math
            bx, by = self._boss_death_location
            pulse = (math.sin(self._death_marker_time * 3) + 1) / 2
            
            # Pulsing bubble background
            bubble_radius = int(50 + 15 * pulse)
            bubble_surf = pygame.Surface((bubble_radius*2, bubble_radius*2), pygame.SRCALPHA)
            bubble_alpha = int(80 + 40 * pulse)
            pygame.draw.circle(bubble_surf, (100, 80, 140, bubble_alpha), 
                             (bubble_radius, bubble_radius), bubble_radius)
            pygame.draw.circle(bubble_surf, (120, 100, 160, bubble_alpha + 30), 
                             (bubble_radius, bubble_radius), bubble_radius, 3)
            screen.blit(bubble_surf, (int(bx - bubble_radius), int(by - bubble_radius)))
            
            # Draw orbiting particles
            for p in self._death_marker_particles:
                particle_surf = pygame.Surface((int(p['size']*2), int(p['size']*2)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*p['color'], int(p['alpha'] * (0.6 + 0.4 * pulse))),
                                 (int(p['size']), int(p['size'])), int(p['size']))
                screen.blit(particle_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        # Victory transition overlay for Hollow (elaborate void descent)
        if self._victory_transition and isinstance(self.boss, TheHollow):
            # Phase 1: Earthquake (0-2s)
            shake_intensity = max(0, 1.0 - self._earthquake_timer / 2.0)
            if shake_intensity > 0:
                import random
                shake_x = random.uniform(-10 * shake_intensity, 10 * shake_intensity)
                shake_y = random.uniform(-10 * shake_intensity, 10 * shake_intensity)
                temp_surf = screen.copy()
                screen.fill((0, 0, 0))
                screen.blit(temp_surf, (int(shake_x), int(shake_y)))
            
            # Phase 2: Void particles swirling (0.5s+)
            if self._transition_timer > 0.5:
                for p in self._void_particles:
                    # Draw particle trail
                    for i in range(3):
                        trail_alpha = int(p['alpha'] * (0.3 - i * 0.1))
                        if trail_alpha > 0:
                            trail_x = p['x'] - p['vx'] * i * 0.05
                            trail_y = p['y'] - p['vy'] * i * 0.05
                            surf = pygame.Surface((int(p['size']*1.5), int(p['size']*1.5)), pygame.SRCALPHA)
                            pygame.draw.circle(surf, (*p['color'], trail_alpha), 
                                             (int(p['size']*0.75), int(p['size']*0.75)), int(p['size']))
                            screen.blit(surf, (int(trail_x), int(trail_y)))
            
            # Phase 3: Platform crumbling effect (1s+)
            if self._transition_timer > 1.0 and not self._falling_platforms:
                import random
                for platform in self.platforms[1:]:  # Skip ground
                    for x in range(platform.rect.left, platform.rect.right, 20):
                        self._falling_platforms.append({
                            'x': x,
                            'y': platform.rect.top,
                            'vy': random.uniform(50, 150),
                            'rotation': random.uniform(-2, 2),
                            'alpha': 255
                        })
            
            # Draw falling platforms
            for chunk in self._falling_platforms:
                chunk['y'] += chunk['vy'] * getattr(self, '_last_dt', 0.016)
                chunk['vy'] += 300 * getattr(self, '_last_dt', 0.016)  # Gravity
                chunk['rotation'] += 2 * getattr(self, '_last_dt', 0.016)
                chunk['alpha'] = max(0, chunk['alpha'] - 100 * getattr(self, '_last_dt', 0.016))
                
                if chunk['alpha'] > 0:
                    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
                    color = (100, 100, 100, int(chunk['alpha']))
                    pygame.draw.rect(surf, color, surf.get_rect())
                    rotated = pygame.transform.rotate(surf, chunk['rotation'] * 30)
                    screen.blit(rotated, (int(chunk['x']), int(chunk['y'])))
            
            # Phase 4: Player spiraling descent (1.5s+)
            if self._transition_timer > 1.5:
                # Spiral motion
                import math
                spiral_offset_x = math.sin(self._transition_timer * 4) * 60
                self.player.x += spiral_offset_x * getattr(self, '_last_dt', 0.016)
                self.player.y += 180 * getattr(self, '_last_dt', 0.016)
                
                # Draw motion blur
                blur_surf = pygame.Surface((self.player.width, self.player.height), pygame.SRCALPHA)
                blur_surf.fill((100, 150, 255, 80))
                screen.blit(blur_surf, (int(self.player.x), int(self.player.y - 20)))
            
            # Phase 5: Void vortex background (2s+)
            if self._transition_timer > 2.0:
                import math
                vortex_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                center_x, center_y = g.SCREENWIDTH // 2, g.SCREENHEIGHT // 2
                
                for ring in range(8):
                    radius = 50 + ring * 80 + (self._transition_timer - 2.0) * 100
                    segments = 24 + ring * 4
                    for seg in range(segments):
                        angle = (seg / segments) * math.pi * 2 + self._transition_timer * 2
                        x = center_x + math.cos(angle) * radius
                        y = center_y + math.sin(angle) * radius
                        alpha = max(0, 120 - ring * 15)
                        pygame.draw.circle(vortex_surf, (10, 10, 30, alpha), (int(x), int(y)), 3)
                
                screen.blit(vortex_surf, (0, 0))
            
            # Phase 6: White fade liberation (3.5s+) - Transition to ethereal realm
            fade_start = 3.5
            if self._transition_timer > fade_start:
                fade_progress = min(1.0, (self._transition_timer - fade_start) / 2.0)
                
                # Gentle white fade (not harsh)
                alpha = int(fade_progress * 220)
                fade_overlay = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT))
                fade_overlay.fill((255, 255, 255))
                fade_overlay.set_alpha(alpha)
                screen.blit(fade_overlay, (0, 0))
                
                # Expanding light rays with soft fade
                if fade_progress < 0.8:
                    import math
                    rays_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                    num_rays = 16
                    for ray in range(num_rays):
                        angle = (ray / num_rays) * math.pi * 2 + self._transition_timer * 0.3
                        # Rays expand outward
                        ray_length = g.SCREENWIDTH * (0.5 + fade_progress * 1.5)
                        end_x = g.SCREENWIDTH // 2 + math.cos(angle) * ray_length
                        end_y = g.SCREENHEIGHT // 2 + math.sin(angle) * ray_length
                        ray_alpha = int((1 - fade_progress) * 120)
                        # Gradient rays (thicker at center)
                        for thickness in range(4, 0, -1):
                            t_alpha = ray_alpha // (5 - thickness)
                            pygame.draw.line(rays_surf, (255, 250, 240, t_alpha),
                                           (g.SCREENWIDTH // 2, g.SCREENHEIGHT // 2),
                                           (int(end_x), int(end_y)), thickness)
                    screen.blit(rays_surf, (0, 0))
                
                # Void dissolving into light particles (continuity from Phase 5)
                if fade_progress < 0.6:
                    dissolve_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                    import random
                    # Dynamic seed for variation
                    random.seed(int(self._transition_timer * 10))
                    for _ in range(int(80 * (1 - fade_progress))):
                        px = random.randint(0, g.SCREENWIDTH)
                        py = random.randint(0, g.SCREENHEIGHT)
                        p_size = random.uniform(2, 6)
                        # Void colors fading to white
                        base_color = random.choice([(40, 40, 80), (50, 50, 100), (30, 30, 60)])
                        fade_to_white = fade_progress * 0.8
                        final_color = tuple(int(c + (255 - c) * fade_to_white) for c in base_color)
                        p_alpha = int(random.uniform(60, 150) * (1 - fade_progress))
                        pygame.draw.circle(dissolve_surf, (*final_color, p_alpha), (px, py), int(p_size))
                    screen.blit(dissolve_surf, (0, 0))
                
                if self._transition_timer > fade_start + 0.8 and self.fade_sfx and not getattr(self, '_fade_played', False):
                    self.fade_sfx.play()
                    self._fade_played = True
            
            # Phase 7: Waking from dream (5.5s+) - Ethereal pixel realm dissolve
            dream_start = 5.5
            if self._transition_timer > dream_start:
                import math
                import random
                wake_progress = min(1.0, (self._transition_timer - dream_start) / 4.0)
                
                # Soft pastel gradient background - ethereal sky
                dawn_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT))
                for y in range(0, g.SCREENHEIGHT, 2):
                    ratio = y / g.SCREENHEIGHT
                    # Lavender-to-cream gradient with subtle shimmer
                    shimmer = math.sin(self._transition_timer * 1.5 + ratio * math.pi) * 10
                    r = int(210 + 45 * ratio * wake_progress + shimmer)
                    g_val = int(190 + 65 * ratio * wake_progress + shimmer * 0.7)
                    b = int(230 - 50 * ratio * wake_progress + shimmer * 0.5)
                    pygame.draw.line(dawn_surf, (r, g_val, b), (0, y), (g.SCREENWIDTH, y), 2)
                dawn_surf.set_alpha(int(200 * wake_progress))
                screen.blit(dawn_surf, (0, 0))
                
                # Dynamic pixelated dissolve - world fragmenting
                if wake_progress < 0.75:
                    dissolve_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                    pixel_size = int(3 + wake_progress * 15)
                    # Dynamic pattern each frame
                    random.seed(int(self._transition_timer * 30))
                    density = int(200 * (1 - wake_progress * 0.7))
                    for i in range(density):
                        x = random.randint(0, g.SCREENWIDTH // pixel_size) * pixel_size
                        y = random.randint(0, g.SCREENHEIGHT // pixel_size) * pixel_size
                        fade_chance = random.random()
                        # Progressive fade based on position and time
                        spatial_fade = (x / g.SCREENWIDTH + y / g.SCREENHEIGHT) / 2
                        if fade_chance < wake_progress + spatial_fade * 0.3:
                            pixel_colors = [(245, 235, 255), (235, 225, 250), (255, 245, 255), (225, 215, 245)]
                            p_color = random.choice(pixel_colors)
                            p_alpha = int(random.uniform(70, 160) * (1 - wake_progress))
                            pygame.draw.rect(dissolve_surf, (*p_color, p_alpha), 
                                           (x, y, pixel_size, pixel_size))
                    screen.blit(dissolve_surf, (0, 0))
                
                # Floating memory fragments - more organic motion
                fragment_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                num_fragments = int(30 - 20 * wake_progress)
                random.seed(100)  # Consistent positions
                for i in range(max(6, num_fragments)):
                    # Vertical rising with horizontal wave
                    base_y = ((i * 60 + self._transition_timer * 20) % (g.SCREENHEIGHT + 120)) - 60
                    base_x = (i * 79) % g.SCREENWIDTH
                    wave_x = math.sin(self._transition_timer * 0.6 + i * 0.4) * 40
                    wave_y = math.cos(self._transition_timer * 0.4 + i * 0.6) * 15
                    
                    frag_x = int(base_x + wave_x)
                    frag_y = int(base_y - wake_progress * 120 + wave_y)
                    
                    # Varied shapes with rotation
                    shape_type = i % 4
                    size = int(10 + (i % 6) * 4)
                    rotation = self._transition_timer * 20 + i * 30
                    frag_alpha = int(140 * (1 - wake_progress) * (1 - min(1.0, base_y / g.SCREENHEIGHT)))
                    
                    if frag_alpha > 10:
                        if shape_type == 0:
                            # Rotating square
                            angle_rad = math.radians(rotation)
                            half = size // 2
                            corners = [
                                (frag_x + math.cos(angle_rad + i*math.pi/2) * half,
                                 frag_y + math.sin(angle_rad + i*math.pi/2) * half)
                                for i in range(4)
                            ]
                            pygame.draw.polygon(fragment_surf, (205, 185, 225, frag_alpha), corners)
                        elif shape_type == 1:
                            # Pulsing diamond
                            pulse = 1 + 0.2 * math.sin(self._transition_timer * 2 + i)
                            points = [(frag_x, frag_y - int(size*pulse)//2), 
                                     (frag_x + int(size*pulse)//2, frag_y),
                                     (frag_x, frag_y + int(size*pulse)//2),
                                     (frag_x - int(size*pulse)//2, frag_y)]
                            pygame.draw.polygon(fragment_surf, (215, 195, 235, frag_alpha), points)
                        elif shape_type == 2:
                            # Glowing cross
                            glow_size = int(size * 1.3)
                            pygame.draw.line(fragment_surf, (225, 205, 245, frag_alpha // 2),
                                           (frag_x - glow_size//2, frag_y), (frag_x + glow_size//2, frag_y), 3)
                            pygame.draw.line(fragment_surf, (225, 205, 245, frag_alpha // 2),
                                           (frag_x, frag_y - glow_size//2), (frag_x, frag_y + glow_size//2), 3)
                            pygame.draw.line(fragment_surf, (235, 215, 250, frag_alpha),
                                           (frag_x - size//2, frag_y), (frag_x + size//2, frag_y), 1)
                            pygame.draw.line(fragment_surf, (235, 215, 250, frag_alpha),
                                           (frag_x, frag_y - size//2), (frag_x, frag_y + size//2), 1)
                        else:
                            # Hollow circle
                            pygame.draw.circle(fragment_surf, (215, 195, 235, frag_alpha), 
                                             (frag_x, frag_y), size // 2, 2)
                
                screen.blit(fragment_surf, (0, 0))
                
                # Enhanced light motes - volumetric feeling
                mote_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                random.seed(int(self._transition_timer * 25))
                num_motes = int(50 + 30 * wake_progress)
                for _ in range(num_motes):
                    mx = random.randint(0, g.SCREENWIDTH)
                    my = random.randint(0, g.SCREENHEIGHT)
                    # Gentle downward drift with horizontal sway
                    my_offset = int(self._transition_timer * 12 + random.random() * 80) % (g.SCREENHEIGHT + 40)
                    mx_sway = int(math.sin(self._transition_timer + my * 0.01) * 15)
                    my = (my + my_offset) % g.SCREENHEIGHT
                    mx = (mx + mx_sway) % g.SCREENWIDTH
                    
                    mote_size = random.uniform(1.5, 4)
                    # Organic twinkling
                    twinkle = (math.sin(self._transition_timer * 3.5 + mx * 0.015 + my * 0.01) * 0.4 + 0.6)
                    mote_alpha = int(random.uniform(120, 220) * twinkle * wake_progress)
                    # Warm ethereal glow
                    mote_colors = [(255, 250, 235), (250, 245, 225), (255, 248, 230), (245, 242, 220)]
                    m_color = random.choice(mote_colors)
                    # Soft glow halo
                    pygame.draw.circle(mote_surf, (*m_color, mote_alpha // 3), (mx, my), int(mote_size * 2))
                    pygame.draw.circle(mote_surf, (*m_color, mote_alpha), (mx, my), int(mote_size))
                
                screen.blit(mote_surf, (0, 0))
                
                # Soft radial vignette - consciousness focusing
                if wake_progress > 0.35:
                    vignette_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                    center_x, center_y = g.SCREENWIDTH // 2, g.SCREENHEIGHT // 2
                    max_dist = math.sqrt(center_x**2 + center_y**2)
                    vignette_strength = (wake_progress - 0.35) / 0.65
                    
                    # Multi-ring soft vignette
                    for ring in range(10):
                        radius = int(max_dist * (0.3 + ring * 0.08))
                        ring_alpha = int(25 * ring * vignette_strength)
                        if ring_alpha > 0:
                            pygame.draw.circle(vignette_surf, (255, 252, 248, ring_alpha),
                                             (center_x, center_y), radius, max(2, 18 - ring * 2))
                    
                    screen.blit(vignette_surf, (0, 0))
                
                # Final fade to bright white (awakening) at 70%+
                if wake_progress > 0.7:
                    awaken_alpha = int((wake_progress - 0.7) / 0.3 * 255)
                    awaken_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT))
                    awaken_surf.fill((255, 255, 250))
                    awaken_surf.set_alpha(awaken_alpha)
                    screen.blit(awaken_surf, (0, 0))
        
        # Draw game over screen on top of all effects
        if self.is_game_over():
            try:
                draw_game_over_screen(screen, self)
            except Exception:
                pass
        
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
        if self.player.health <= 0:
            return True
        # Only game over when victory transition starts (player approached boss)
        if self._victory_transition:
            return True
        return False

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
    
    def player_wants_to_exit(self) -> bool:
        """Check if player pressed space to exit after victory"""
        return self._player_wants_exit
    
    def _spawn_void_particles(self):
        """Create swirling void particles for Hollow transition"""
        import random
        import math
        for _ in range(80):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(100, 400)
            self._void_particles.append({
                'x': g.SCREENWIDTH // 2 + math.cos(angle) * distance,
                'y': g.SCREENHEIGHT // 2 + math.sin(angle) * distance,
                'vx': math.cos(angle) * random.uniform(-100, -50),
                'vy': math.sin(angle) * random.uniform(-100, -50),
                'size': random.uniform(2, 6),
                'alpha': random.randint(150, 255),
                'color': random.choice([(20, 20, 40), (30, 30, 60), (10, 10, 20), (40, 40, 80)])
            })
    
    def _spawn_death_marker(self):
        """Create pulsing marker at boss death location"""
        if not self._boss_death_location:
            return
        import random
        bx, by = self._boss_death_location
        
        if isinstance(self.boss, TheHollow):
            # Void-themed: dark purple swirling particles
            for _ in range(30):
                angle = random.uniform(0, 6.28)
                radius = random.uniform(5, 40)
                self._death_marker_particles.append({
                    'x': bx,
                    'y': by,
                    'orbit_radius': radius,
                    'orbit_angle': angle,
                    'orbit_speed': random.uniform(1.5, 3.0),
                    'size': random.uniform(2, 5),
                    'alpha': random.randint(180, 255),
                    'color': random.choice([(80, 60, 120), (60, 40, 100), (100, 80, 140), (50, 30, 90)])
                })
        else:
            # Generic void particles for other bosses
            for _ in range(30):
                angle = random.uniform(0, 6.28)
                radius = random.uniform(5, 40)
                self._death_marker_particles.append({
                    'x': bx,
                    'y': by,
                    'orbit_radius': radius,
                    'orbit_angle': angle,
                    'orbit_speed': random.uniform(1.5, 3.0),
                    'size': random.uniform(2, 5),
                    'alpha': random.randint(180, 255),
                    'color': random.choice([(80, 60, 120), (60, 40, 100), (100, 80, 140), (50, 30, 90)])
                })
    
    def _update_death_marker(self, dt):
        """Animate death marker particles in orbit"""
        import math
        if not self._boss_death_location:
            return
        
        bx, by = self._boss_death_location
        pulse = (math.sin(self._death_marker_time * 3) + 1) / 2  # 0..1
        
        for p in self._death_marker_particles:
            p['orbit_angle'] += p['orbit_speed'] * dt
            # Pulsing orbit radius
            current_radius = p['orbit_radius'] * (0.8 + 0.4 * pulse)
            p['x'] = bx + math.cos(p['orbit_angle']) * current_radius
            p['y'] = by + math.sin(p['orbit_angle']) * current_radius
    
    def _update_void_particles(self, dt):
        """Update void particle swirl toward center"""
        import math
        center_x, center_y = g.SCREENWIDTH // 2, g.SCREENHEIGHT // 2
        for p in self._void_particles:
            # Pull toward center with spiral
            dx = center_x - p['x']
            dy = center_y - p['y']
            dist = max(1, math.hypot(dx, dy))
            
            # Spiral force
            angle = math.atan2(dy, dx)
            spiral_angle = angle + math.pi / 4
            pull_strength = 200
            
            p['vx'] = math.cos(spiral_angle) * pull_strength
            p['vy'] = math.sin(spiral_angle) * pull_strength
            
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            
            # Fade near center
            if dist < 100:
                p['alpha'] = max(0, p['alpha'] - 300 * dt)
            
            # Regenerate at edges
            if dist > 600 or p['alpha'] <= 0:
                import random
                angle = random.uniform(0, math.pi * 2)
                distance = 500
                p['x'] = g.SCREENWIDTH // 2 + math.cos(angle) * distance
                p['y'] = g.SCREENHEIGHT // 2 + math.sin(angle) * distance
                p['alpha'] = random.randint(150, 255)

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