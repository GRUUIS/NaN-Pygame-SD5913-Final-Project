"""SlothBattleScene

Dedicated battle scene for Boss #2 - The Sloth.

Differences from generic `BossBattleScene`:
  - Ground-focused arena: wide flat ground with a few low ledges so player must reposition
  - No vertical spike waves (emphasis on horizontal zoning via slime trail & pools)
  - Creepy forest / cave background (placeholder gradient if image missing)
  - Automatically sets the Sloth's ground height so it truly crawls.

Assets expected (optional):
  assets/backgrounds/boss_sloth_forest.png  (provide your own later)

If missing, a dark green-to-black vertical gradient is rendered.
"""
from __future__ import annotations
import pygame, os, random, math
import globals as g
from .player import Player
from .boss_sloth import TheSloth
from .bullets import BulletManager
from .platform import Platform
from ..systems.ui import UIManager, TextPopup, draw_ui_overlay, draw_game_over_screen


class SlothBattleScene:
    def __init__(self):
        self.player = Player(g.SCREENWIDTH//2, g.SCREENHEIGHT - 200)
        self.boss = TheSloth(g.SCREENWIDTH*0.25, 0)
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        # Inject UI into boss for dialogue
        self.boss.ui = self.ui
        self._shown_entry = False
        self._shown_victory = False
        self._last_boss_health = getattr(self.boss, 'health', 0)
        # Transition states
        self._victory_transition = False
        self._defeat_shown = False
        self._transition_timer = 0.0
        self._dandelion_particles = []
        self._wind_trails = []
        self._light_specks = []
        self._bgm_fading = False
        self._boss_death_location = None
        self._boss_defeated = False
        self._death_marker_particles = []
        self._death_marker_time = 0.0

        ground_h = 78
        ground_top = g.SCREENHEIGHT - ground_h
        # Platforms: extended lengths for better mobility during Sloth battle
        self.platforms = [
            Platform(0, ground_top, g.SCREENWIDTH, ground_h),
            Platform(int(g.SCREENWIDTH*0.22), ground_top-100, 240, 18),
            Platform(int(g.SCREENWIDTH*0.55), ground_top-120, 280, 20),
        ]
        # Snap boss to ground
        self.boss.set_ground(ground_top)

        # Background
        self.background = self._load_background()

        # BGM
        try:
            bgm_path = os.path.join('assets', 'sfx', 'Boss_Sloth_Lurid_Delusion.mp3')
            pygame.mixer.music.load(bgm_path)
            try:
                pygame.mixer.music.set_volume(getattr(g, 'music_volume', 0.2))
            except Exception:
                try:
                    pygame.mixer.music.set_volume(0.2)
                except Exception:
                    pass
            pygame.mixer.music.play(-1) # Loop
        except Exception as e:
            print(f"Failed to load Sloth BGM: {e}")
        
        # Load SFX
        self.defeat_sfx = None
        self.victory_sfx = None
        self.dandelion_sfx = None
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
            self.dandelion_sfx = pygame.mixer.Sound(os.path.join('assets', 'sfx', 'dandelion_float.wav'))
            self.dandelion_sfx.set_volume(0.5)
        except Exception:
            pass

    # --- Internal helpers ---
    def _load_background(self):
        path = os.path.join('assets','backgrounds','boss_sloth_forest.png')
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert()
            except Exception:
                return None
        return None

    def _draw_background(self, screen: pygame.Surface):
        """High-velocity eerie forest: multi-layer parallax + drifting fog + color pulse.

        Layers:
          1. Pulsing gradient sky (slow hue shift)
          2. Distant trees (fast horizontal drift)
          3. Mid trees with branch silhouettes (accelerated parallax)
          4. Foreground thorns/bushes (very fast scroll for speed sensation)
          5. Multi band fog + occasional flash silhouettes
        All procedural so it matches the Sloth's unsettling, fast crawl style.
        """
        w,h = g.SCREENWIDTH, g.SCREENHEIGHT
        time_ms = pygame.time.get_ticks()
        t = time_ms / 1000.0
        # Sky gradient with subtle pulsating hue
        sky = pygame.Surface((w,h))
        pulse = (math.sin(t*0.6)+1)/2  # 0..1
        top_col = (
            int(6 + 12*pulse),
            int(14 + 24*pulse),
            int(10 + 18*pulse)
        )
        bot_col = (
            int(16 + 30*pulse),
            int(48 + 42*pulse),
            int(36 + 34*pulse)
        )
        for y in range(h):
            k = y / h
            col = (
                int(top_col[0] + (bot_col[0]-top_col[0])*k),
                int(top_col[1] + (bot_col[1]-top_col[1])*k),
                int(top_col[2] + (bot_col[2]-top_col[2])*k)
            )
            pygame.draw.line(sky, col, (0,y), (w,y))
        screen.blit(sky,(0,0))

        rng = random.Random(0)  # deterministic layout base
        # Parallax speed multipliers (higher than previous for "flying" feel)
        far_speed = 110
        mid_speed = 210
        fg_speed = 360
        # FAR layer (thin silhouettes)
        far = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(34):
            base_x = (i * 150 - int(t*far_speed)) % (w+150) - 75
            trunk_h = rng.randint(int(h*0.40), int(h*0.68))
            trunk_w = rng.randint(8,16)
            alpha = 50
            pygame.draw.rect(far, (18,38,26,alpha), (base_x, h-trunk_h, trunk_w, trunk_h))
        screen.blit(far,(0,0))
        # MID layer (branchy)
        mid = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(26):
            base_x = (i * 180 - int(t*mid_speed)) % (w+180) - 90
            trunk_h = rng.randint(int(h*0.50), int(h*0.78))
            trunk_w = rng.randint(24,36)
            color = (26,60,40,140)
            pygame.draw.rect(mid, color, (base_x, h-trunk_h, trunk_w, trunk_h))
            # Branch shards
            branch_count = 4
            for b in range(branch_count):
                by = h-trunk_h + rng.randint(28, trunk_h-40)
                dir = -1 if b%2==0 else 1
                length = rng.randint(60,120)
                pygame.draw.polygon(mid, (26,60,42,120), [
                    (base_x + trunk_w//2, by),
                    (base_x + trunk_w//2 + dir*length, by - rng.randint(8,18)),
                    (base_x + trunk_w//2, by + rng.randint(6,14))
                ])
        screen.blit(mid,(0,0))
        # FOREGROUND fast bushes / thorns
        fg = pygame.Surface((w,h), pygame.SRCALPHA)
        for i in range(40):
            bx = (i*100 - int(t*fg_speed)) % (w+100) - 50
            by = h - rng.randint(70,110)
            rad_x = rng.randint(50,90)
            rad_y = rng.randint(30,60)
            pygame.draw.ellipse(fg, (16,46,32,210), (bx, by, rad_x*2, rad_y))
        screen.blit(fg,(0,0))
        # Layered fog bands drifting opposite direction for depth
        fog = pygame.Surface((w,h), pygame.SRCALPHA)
        for band in range(5):
            band_h = h//6
            y0 = band * band_h + int(math.sin(t*0.8 + band)*6)
            fog_alpha = int(28 + 18*math.sin(t*1.2 + band*0.7))
            pygame.draw.rect(fog, (40,60,50,fog_alpha), (0,y0, w, band_h))
        screen.blit(fog,(0,0))
        # Flash silhouettes (rare): brief dark vertical streaks to add tension
        if int(t*4) % 7 == 0:  # periodic condition
            streaks = pygame.Surface((w,h), pygame.SRCALPHA)
            for _ in range(6):
                sx = random.randint(0,w)
                sh = random.randint(int(h*0.3), int(h*0.7))
                pygame.draw.rect(streaks, (10,20,14,90), (sx, h-sh, 6, sh))
            screen.blit(streaks,(0,0))

    # --- Public API ---
    def update(self, dt: float):
        self._last_dt = dt  # Store for transitions
        
        # Handle victory transition
        if self._victory_transition:
            self._transition_timer += dt
            self._update_dandelion_particles(dt)
            self._update_wind_trails(dt)
            self._update_light_specks(dt)
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
            self.player.update(dt, self.platforms)
            self.boss.update(dt, self.player, self.bullet_manager)
            self.bullet_manager.update(dt, self.player, self.boss)
            self.bullet_manager.check_collisions(self.player, self.boss)
            self.ui.update(dt)
            if not self._shown_entry:
                self._shown_entry = True
                def anchor(): return (self.boss.x + self.boss.width/2, self.boss.y)
                self.ui.add(TextPopup(getattr(self.boss,'entry_line','Time... stalls.'), anchor, duration=3.0, bg=(12,12,12)))
            # Player shooting (reuse normal bullet style for now)
            if self.player.mouse_pressed and self.player.can_shoot():
                info = self.player.shoot()
                if info:
                    x,y,dx,dy = info
                    speed = g.BULLET_SPEEDS['player']
                    self.bullet_manager.add_bullet(x,y,dx*speed,dy*speed,'player','player')
            
            # Check for boss defeat - store location
            if self.boss.health <= 0 and not self._boss_defeated and not self._victory_transition:
                if hasattr(self.boss, 'fully_defeated') and self.boss.fully_defeated:
                    self._boss_defeated = True
                    self._boss_death_location = (self.boss.x + self.boss.width/2, self.boss.y + self.boss.height/2)
                    self._spawn_death_marker()
                elif not hasattr(self.boss, 'fully_defeated'):
                    self._boss_defeated = True
                    self._boss_death_location = (self.boss.x + self.boss.width/2, self.boss.y + self.boss.height/2)
                    self._spawn_death_marker()
            
            # Check proximity to trigger dandelion transition
            if self._boss_defeated and self._boss_death_location and not self._victory_transition:
                self._death_marker_time += dt
                self._update_death_marker(dt)
                
                px = self.player.x + self.player.width/2
                py = self.player.y + self.player.height/2
                bx, by = self._boss_death_location
                distance = ((px - bx)**2 + (py - by)**2)**0.5
                
                if distance < 120:
                    self._victory_transition = True
                    self._transition_timer = 0.0
                    self._bgm_fading = True
                    if self.victory_sfx:
                        self.victory_sfx.play()
                    if self.dandelion_sfx:
                        self.dandelion_sfx.play()
                    self._spawn_dandelions()
            
            # Debug health prints
            if g.DEBUG_MODE and self._last_boss_health != self.boss.health:
                print(f"Boss health: {self.boss.health}/{self.boss.max_health}")
                self._last_boss_health = self.boss.health
    
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
            # SPACE key: continue after victory (handled by main.py CLI runner)

    def draw(self, screen: pygame.Surface):
        self._draw_background(screen)
        for p in self.platforms:
            p.draw(screen)
        # Draw player after trail so player is visible; trail drawn inside boss.draw
        self.boss.draw(screen)
        self.player.draw(screen)
        self.bullet_manager.draw(screen)
        self.ui.draw(screen)
        try:
            draw_ui_overlay(screen, self)
        except Exception:
            pass
        
        # Draw death marker indicator (before victory transition)
        if self._boss_defeated and not self._victory_transition and self._boss_death_location:
            import math
            bx, by = self._boss_death_location
            pulse = (math.sin(self._death_marker_time * 2.5) + 1) / 2
            
            # Soft glowing bubble with green/yellow tint
            bubble_radius = int(55 + 12 * pulse)
            bubble_surf = pygame.Surface((bubble_radius*2, bubble_radius*2), pygame.SRCALPHA)
            bubble_alpha = int(70 + 35 * pulse)
            pygame.draw.circle(bubble_surf, (200, 240, 180, bubble_alpha), 
                             (bubble_radius, bubble_radius), bubble_radius)
            pygame.draw.circle(bubble_surf, (220, 250, 200, bubble_alpha + 40), 
                             (bubble_radius, bubble_radius), bubble_radius, 3)
            screen.blit(bubble_surf, (int(bx - bubble_radius), int(by - bubble_radius)))
            
            # Draw floating dandelion wisps
            for p in self._death_marker_particles:
                # Wisp with slight glow
                wisp_surf = pygame.Surface((int(p['size']*4), int(p['size']*4)), pygame.SRCALPHA)
                glow_size = int(p['size'] * 2)
                particle_alpha = int(p['alpha'] * (0.7 + 0.3 * pulse))
                # Outer glow
                pygame.draw.circle(wisp_surf, (*p['color'], particle_alpha // 3),
                                 (glow_size, glow_size), glow_size)
                # Inner core
                pygame.draw.circle(wisp_surf, (*p['color'], particle_alpha),
                                 (glow_size, glow_size), int(p['size']))
                screen.blit(wisp_surf, (int(p['x'] - glow_size), int(p['y'] - glow_size)))
        
        # Victory transition: elaborate dandelion float escape
        if self._victory_transition:
            import math
            
            # Phase 1: Wind trails (0s+)
            for t in self._wind_trails:
                if t['alpha'] > 0:
                    end_x = t['x'] + math.cos(t['vy'] * 0.01) * t['length']
                    end_y = t['y'] + math.sin(t['vx'] * 0.01) * t['length'] * 0.3
                    pygame.draw.line(screen, (220, 240, 200, int(t['alpha'])), 
                                   (int(t['x']), int(t['y'])),
                                   (int(end_x), int(end_y)), 2)
            
            # Phase 2: Light specks (0s+)
            for s in self._light_specks:
                if s['alpha'] > 0:
                    surf = pygame.Surface((int(s['size']*2), int(s['size']*2)), pygame.SRCALPHA)
                    glow_alpha = max(0, min(255, int(s['alpha'])))
                    pygame.draw.circle(surf, (255, 250, 200, glow_alpha), 
                                     (int(s['size']), int(s['size'])), int(s['size']))
                    screen.blit(surf, (int(s['x']), int(s['y'])))
            
            # Phase 3: Dandelion seeds with detailed rendering (0s+)
            for p in self._dandelion_particles:
                if p['alpha'] > 0:
                    # Draw seed body
                    surf = pygame.Surface((int(p['size']*3), int(p['size']*3)), pygame.SRCALPHA)
                    center = int(p['size']*1.5)
                    
                    # Seed center
                    pygame.draw.circle(surf, (240, 235, 200, int(p['alpha'])), 
                                     (center, center), int(p['size']))
                    
                    # Parachute filaments
                    import random
                    random.seed(int(p['x'] + p['y']))
                    for i in range(8):
                        angle = (i / 8) * 6.28 + p['rotation'] * 0.01
                        length = p['size'] * 2.5
                        end_x = center + math.cos(angle) * length
                        end_y = center + math.sin(angle) * length * 0.6
                        pygame.draw.line(surf, (255, 255, 230, int(p['alpha'] * 0.7)),
                                       (center, center), (int(end_x), int(end_y)), 1)
                        # Tip of filament
                        pygame.draw.circle(surf, (255, 255, 220, int(p['alpha'] * 0.8)),
                                         (int(end_x), int(end_y)), 1)
                    
                    # Rotate and blit
                    rotated = pygame.transform.rotate(surf, p['rotation'])
                    screen.blit(rotated, (int(p['x'] - rotated.get_width()/2), 
                                        int(p['y'] - rotated.get_height()/2)))
            
            # Phase 4: Player floats upward (0.5s+)
            if self._transition_timer > 0.5:
                # Gentle swaying motion
                sway_x = math.sin(self._transition_timer * 3) * 20
                self.player.x += sway_x * getattr(self, '_last_dt', 0.016)
                self.player.y -= 120 * getattr(self, '_last_dt', 0.016)
                
                # Motion trail
                trail_surf = pygame.Surface((self.player.width, self.player.height), pygame.SRCALPHA)
                trail_surf.fill((150, 200, 150, 60))
                screen.blit(trail_surf, (int(self.player.x), int(self.player.y + 15)))
            
            # Phase 5: Sky gradient shift (1.5s+)
            if self._transition_timer > 1.5:
                gradient_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                progress = min(1.0, (self._transition_timer - 1.5) / 2.0)
                
                # Warm sunset colors
                for y in range(g.SCREENHEIGHT):
                    ratio = y / g.SCREENHEIGHT
                    r = int(180 + 75 * progress * (1 - ratio))
                    g_val = int(140 + 110 * progress * (1 - ratio))
                    b = int(100 + 155 * progress * ratio)
                    alpha = int(120 * progress)
                    pygame.draw.line(gradient_surf, (r, g_val, b, alpha), 
                                   (0, y), (g.SCREENWIDTH, y))
                
                screen.blit(gradient_surf, (0, 0))
            
            # Phase 6: Golden hour glow particles (2s+)
            if self._transition_timer > 2.0:
                glow_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                import random
                random.seed(int(self._transition_timer * 10))
                for _ in range(30):
                    x = random.randint(0, g.SCREENWIDTH)
                    y = random.randint(0, g.SCREENHEIGHT)
                    size = random.uniform(2, 5)
                    alpha = int(random.uniform(80, 150))
                    pygame.draw.circle(glow_surf, (255, 240, 180, alpha), (x, y), int(size))
                screen.blit(glow_surf, (0, 0))
            
            # Phase 7: Fade to warm white (3.5s+)
            fade_start = 3.5
            if self._transition_timer > fade_start:
                alpha = min(255, int((self._transition_timer - fade_start) * 130))
                fade_overlay = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT))
                fade_overlay.fill((255, 250, 235))
                fade_overlay.set_alpha(alpha)
                screen.blit(fade_overlay, (0, 0))
                
                # Sunburst rays
                if alpha < 200:
                    rays_surf = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT), pygame.SRCALPHA)
                    for ray in range(16):
                        angle = (ray / 16) * 6.28 + self._transition_timer * 0.3
                        end_x = g.SCREENWIDTH // 2 + math.cos(angle) * g.SCREENWIDTH * 1.5
                        end_y = g.SCREENHEIGHT // 2 + math.sin(angle) * g.SCREENHEIGHT * 1.5
                        ray_alpha = int((200 - alpha) * 0.4)
                        pygame.draw.line(rays_surf, (255, 245, 200, ray_alpha),
                                       (g.SCREENWIDTH // 2, g.SCREENHEIGHT // 2),
                                       (int(end_x), int(end_y)), 4)
                    screen.blit(rays_surf, (0, 0))
        
        # Draw game over screen on top of all effects
        if self.is_game_over():
            try:
                draw_game_over_screen(screen, self)
            except Exception:
                pass
        
        if g.SHOW_DEBUG_INFO:
            self._draw_debug_info(screen)

    def _draw_debug_info(self, screen: pygame.Surface):
        """Draw debug information overlay"""
        font = pygame.font.Font(None, 24)
        y_offset = 10
        debug_lines = [
            f"Player HP: {self.player.health}/{self.player.max_health}",
            f"Boss HP: {self.boss.health}/{self.boss.max_health}",
            f"Player Pos: ({int(self.player.x)}, {int(self.player.y)})",
            f"Boss Pos: ({int(self.boss.x)}, {int(self.boss.y)})",
            f"Victory State: {self._victory_triggered}"
        ]
        for line in debug_lines:
            text = font.render(line, True, (255, 255, 0))
            screen.blit(text, (10, y_offset))
            y_offset += 25

    def _spawn_dandelions(self):
        """Create dandelion particles around player"""
        import random
        px, py = self.player.x + self.player.width/2, self.player.y + self.player.height/2
        # Main dandelion cluster
        for _ in range(40):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(40, 120)
            self._dandelion_particles.append({
                'x': px + random.uniform(-30, 30),
                'y': py + random.uniform(-30, 30),
                'vx': speed * 0.3 * random.choice([-1, 1]),
                'vy': -speed,
                'size': random.uniform(3, 10),
                'alpha': 255,
                'rotation': random.uniform(0, 360),
                'spin': random.uniform(-2, 2)
            })
        # Spawn light specks
        for _ in range(60):
            self._light_specks.append({
                'x': random.uniform(0, g.SCREENWIDTH),
                'y': random.uniform(0, g.SCREENHEIGHT),
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(-60, -20),
                'size': random.uniform(1, 3),
                'alpha': random.randint(100, 255),
                'twinkle': random.uniform(0, 6.28)
            })
    
    def _spawn_death_marker(self):
        """Create dandelion-themed marker at boss death location"""
        if not self._boss_death_location:
            return
        import random
        bx, by = self._boss_death_location
        
        # Gentle dandelion wisps floating upward
        for _ in range(25):
            angle = random.uniform(0, 6.28)
            radius = random.uniform(5, 35)
            self._death_marker_particles.append({
                'x': bx,
                'y': by,
                'float_offset': random.uniform(0, 6.28),
                'float_speed': random.uniform(0.8, 1.5),
                'drift_radius': radius,
                'drift_angle': angle,
                'size': random.uniform(2, 6),
                'alpha': random.randint(200, 255),
                'color': random.choice([(240, 250, 220), (230, 245, 210), (250, 255, 230), (220, 240, 200)])
            })
    
    def _update_death_marker(self, dt):
        """Animate dandelion wisps floating gently upward"""
        import math
        if not self._boss_death_location:
            return
        
        bx, by = self._boss_death_location
        
        for p in self._death_marker_particles:
            p['float_offset'] += p['float_speed'] * dt
            # Gentle upward float with horizontal drift
            float_y = -20 * math.sin(p['float_offset'])
            drift_x = math.cos(self._death_marker_time * 0.5 + p['drift_angle']) * p['drift_radius']
            drift_y = math.sin(self._death_marker_time * 0.5 + p['drift_angle']) * p['drift_radius'] * 0.5
            
            p['x'] = bx + drift_x
            p['y'] = by + drift_y + float_y
    
    def _update_dandelion_particles(self, dt):
        """Update dandelion particle positions with wind effect"""
        import math
        for p in self._dandelion_particles:
            # Wind sway
            wind_x = math.sin(self._transition_timer * 2 + p['y'] * 0.01) * 30
            p['x'] += (p['vx'] + wind_x) * dt
            p['y'] += p['vy'] * dt
            p['rotation'] += p['spin']
            p['alpha'] = max(0, p['alpha'] - 40 * dt)
            
            # Spawn wind trail
            if len(self._wind_trails) < 100 and p['alpha'] > 100:
                import random
                if random.random() < 0.3:
                    self._wind_trails.append({
                        'x': p['x'],
                        'y': p['y'],
                        'vx': p['vx'] * 0.5,
                        'vy': p['vy'] * 0.5,
                        'length': random.uniform(10, 30),
                        'alpha': 150
                    })
        
        self._dandelion_particles = [p for p in self._dandelion_particles if p['alpha'] > 0]
    
    def _update_wind_trails(self, dt):
        """Update wind trail streaks"""
        for t in self._wind_trails:
            t['x'] += t['vx'] * dt
            t['y'] += t['vy'] * dt
            t['alpha'] = max(0, t['alpha'] - 100 * dt)
        self._wind_trails = [t for t in self._wind_trails if t['alpha'] > 0]
    
    def _update_light_specks(self, dt):
        """Update floating light particles"""
        import math
        for s in self._light_specks:
            s['x'] += s['vx'] * dt
            s['y'] += s['vy'] * dt
            s['twinkle'] += 3 * dt
            s['alpha'] = int(200 + 55 * math.sin(s['twinkle']))
            
            # Wrap around screen
            if s['y'] < -10:
                s['y'] = g.SCREENHEIGHT + 10
            if s['x'] < -10:
                s['x'] = g.SCREENWIDTH + 10
            elif s['x'] > g.SCREENWIDTH + 10:
                s['x'] = -10

    def is_game_over(self):
        if self.player.health <= 0:
            return True
        # Only game over when victory transition starts (player approached boss)
        if self._victory_transition:
            return True
        return False

    def reset_battle(self):
        # re-init while keeping same scene layout
        # Platform objects store position in rect; use rect.y instead of non-existent .y
        ground_top = self.platforms[0].rect.y
        self.player = Player(g.SCREENWIDTH//2, g.SCREENHEIGHT - 200)
        self.boss = TheSloth(g.SCREENWIDTH*0.25, 0)
        self.boss.set_ground(ground_top)
        self.bullet_manager = BulletManager()
        self.ui = UIManager()
        # Inject UI into boss for dialogue
        self.boss.ui = self.ui
        self._shown_entry = False
        self._shown_victory = False
        self._last_boss_health = self.boss.health
