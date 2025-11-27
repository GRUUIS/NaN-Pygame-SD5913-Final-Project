"""
Mirror Room Puzzle Scene - Yume Nikki Style
A surreal dream room filled with mirrors.
Player must solve the puzzle to break the mirror and obtain the Pencil effect.
"""

import pygame
import sys
import os
import math
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --------------------------
# Configuration
# --------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 32
MAP_WIDTH = 20
MAP_HEIGHT = 15

CHAR_FRAME_WIDTH = 23
CHAR_FRAME_HEIGHT = 36
CHAR_SCALE = 1.5
ANIMATION_SPEED = 0.2

DIRECTION_MAP = {
    'down': 0, 'down_right': 1, 'right': 2, 'up_right': 3,
    'up': 4, 'up_left': 5, 'left': 6, 'down_left': 7,
}

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "Silver.ttf")
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "yume_nikki")
TILES_DIR = os.path.join(ASSET_DIR, "tiles")
SPRITES_DIR = os.path.join(ASSET_DIR, "sprites")

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_DREAM = (15, 15, 25)
COLOR_TEXT = (200, 200, 220)
COLOR_MIRROR = (180, 200, 220)


class Character:
    def __init__(self, sprite_path: str, x: float, y: float):
        self.x = x
        self.y = y
        self.speed = 120.0
        self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
        self.frames = self._load_frames()
        self.direction = 'down'
        self.is_moving = False
        self.frame_index = 0
        self.animation_timer = 0.0
        self.collision_width = 16
        self.collision_height = 12
    
    def _load_frames(self) -> dict:
        frames = {}
        for dir_name, row in DIRECTION_MAP.items():
            frames[dir_name] = []
            for col in range(9):
                rect = pygame.Rect(col * CHAR_FRAME_WIDTH, row * CHAR_FRAME_HEIGHT,
                                   CHAR_FRAME_WIDTH, CHAR_FRAME_HEIGHT)
                frame = self.sprite_sheet.subsurface(rect)
                scaled = pygame.transform.scale(frame,
                    (int(CHAR_FRAME_WIDTH * CHAR_SCALE), int(CHAR_FRAME_HEIGHT * CHAR_SCALE)))
                frames[dir_name].append(scaled)
        return frames
    
    def update(self, dt: float, dx: float, dy: float, collision_check=None):
        if dx != 0 or dy != 0:
            self.is_moving = True
            self.direction = self._get_direction(dx, dy)
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071
            new_x = self.x + dx * self.speed * dt
            new_y = self.y + dy * self.speed * dt
            if collision_check:
                if not collision_check(new_x, self.y, self.collision_width, self.collision_height):
                    self.x = new_x
                if not collision_check(self.x, new_y, self.collision_width, self.collision_height):
                    self.y = new_y
            else:
                self.x, self.y = new_x, new_y
        else:
            self.is_moving = False
        
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= ANIMATION_SPEED:
                self.animation_timer = 0
                self.frame_index = (self.frame_index % 8) + 1
        else:
            self.frame_index = 0
    
    def _get_direction(self, dx, dy):
        if dx > 0 and dy > 0: return 'down_right'
        elif dx < 0 and dy > 0: return 'down_left'
        elif dx > 0 and dy < 0: return 'up_right'
        elif dx < 0 and dy < 0: return 'up_left'
        elif dx > 0: return 'right'
        elif dx < 0: return 'left'
        elif dy > 0: return 'down'
        return 'up'
    
    def draw(self, surface, camera_x=0, camera_y=0):
        frame = self.frames[self.direction][self.frame_index]
        draw_x = self.x - camera_x - frame.get_width() // 2
        draw_y = self.y - camera_y - frame.get_height() + self.collision_height
        surface.blit(frame, (draw_x, draw_y))
    
    def get_reflection_direction(self):
        """Get the mirrored direction for reflection"""
        reflection_map = {
            'down': 'down', 'up': 'up',
            'left': 'right', 'right': 'left',
            'down_left': 'down_right', 'down_right': 'down_left',
            'up_left': 'up_right', 'up_right': 'up_left',
        }
        return reflection_map.get(self.direction, self.direction)
    
    def draw_reflection(self, surface, mirror_x, camera_x=0, camera_y=0, alpha=150):
        """Draw a mirrored reflection of the character"""
        reflected_dir = self.get_reflection_direction()
        frame = self.frames[reflected_dir][self.frame_index]
        
        # Flip horizontally
        flipped = pygame.transform.flip(frame, True, False)
        
        # Calculate reflection position (mirrored across the mirror's x position)
        char_screen_x = self.x - camera_x
        distance_to_mirror = mirror_x - char_screen_x
        reflected_x = mirror_x + distance_to_mirror - flipped.get_width() // 2
        
        draw_y = self.y - camera_y - flipped.get_height() + self.collision_height
        
        # Apply transparency
        reflection_surf = flipped.copy()
        reflection_surf.set_alpha(alpha)
        
        # Tint slightly blue for mirror effect
        tint_surf = pygame.Surface(reflection_surf.get_size(), pygame.SRCALPHA)
        tint_surf.fill((100, 150, 200, 30))
        reflection_surf.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
        surface.blit(reflection_surf, (reflected_x, draw_y))


class DreamEffect:
    def __init__(self, screen_width=1280, screen_height=720):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.static_timer = 0
        self.static_intensity = 0
        self.flash_alpha = 0
        self.flash_color = (255, 255, 255)
        self.screen_shake = 0
        self.shake_intensity = 0
        self.particles = []
        # Dust particles floating in the room
        for _ in range(20):
            self.particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(0, self.screen_height),
                'speed': random.uniform(5, 15),
                'size': random.randint(1, 2),
                'alpha': random.randint(30, 80),
                'color': (200, 210, 230)
            })
    
    def trigger_static(self, duration=0.5):
        self.static_timer = duration
        self.static_intensity = 255
    
    def flash(self, color, alpha):
        self.flash_color = color
        self.flash_alpha = alpha
    
    def shake(self, duration=0.3, intensity=5):
        self.screen_shake = duration
        self.shake_intensity = intensity
    
    def get_shake_offset(self):
        if self.screen_shake > 0:
            return (random.uniform(-self.shake_intensity, self.shake_intensity),
                    random.uniform(-self.shake_intensity, self.shake_intensity))
        return (0, 0)
    
    def update(self, dt):
        if self.static_timer > 0:
            self.static_timer -= dt
            self.static_intensity = int(255 * (self.static_timer / 0.5))
        else:
            self.static_intensity = 0
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 300 * dt)
        if self.screen_shake > 0:
            self.screen_shake -= dt
        for p in self.particles:
            p['y'] -= p['speed'] * dt
            p['x'] += math.sin(p['y'] * 0.01) * 0.3
            if p['y'] < -10:
                p['y'] = self.screen_height + 10
                p['x'] = random.randint(0, self.screen_width)
    
    def draw(self, surface):
        for p in self.particles:
            ps = pygame.Surface((p['size']*2+2, p['size']*2+2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p['color'], p['alpha']), (p['size']+1, p['size']+1), p['size'])
            surface.blit(ps, (int(p['x']), int(p['y'])))
        
        if self.static_intensity > 0:
            ss = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            surf_w, surf_h = surface.get_size()
            for _ in range(int(800 * self.static_intensity / 255)):
                x, y = random.randint(0, surf_w-1), random.randint(0, surf_h-1)
                gray = random.randint(100, 255)
                pygame.draw.rect(ss, (gray, gray, gray, min(255, self.static_intensity)), (x, y, 2, 2))
            surface.blit(ss, (0, 0))
        
        if self.flash_alpha > 0:
            fs = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            fs.fill((*self.flash_color, int(self.flash_alpha)))
            surface.blit(fs, (0, 0))
        
        # Vignette effect
        surf_w, surf_h = surface.get_size()
        vignette = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for i in range(60):
            alpha = int(100 * (1 - i / 60))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (i, i, surf_w-i*2, surf_h-i*2), 1)
        surface.blit(vignette, (0, 0))


class DialogueBox:
    def __init__(self):
        self.active = False
        self.text = ""
        self.display_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.char_speed = 0.02
        try:
            self.font = pygame.font.Font(FONT_PATH, 26)
        except:
            self.font = pygame.font.Font(None, 26)
    
    def show(self, text):
        self.active = True
        self.text = text
        self.display_text = ""
        self.char_index = 0
    
    def update(self, dt):
        if self.active and self.char_index < len(self.text):
            self.char_timer += dt
            if self.char_timer >= self.char_speed:
                self.char_timer = 0
                self.display_text += self.text[self.char_index]
                self.char_index += 1
    
    def skip(self):
        if self.char_index < len(self.text):
            self.display_text = self.text
            self.char_index = len(self.text)
        else:
            self.active = False
    
    def draw(self, surface):
        if not self.active:
            return
        box_h = 110
        surf_w, surf_h = surface.get_size()
        box_rect = pygame.Rect(30, surf_h - box_h - 30, surf_w - 60, box_h)
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        box_surf.fill((10, 10, 20, 240))
        pygame.draw.rect(box_surf, (100, 120, 150), (0, 0, box_rect.width, box_rect.height), 3)
        surface.blit(box_surf, box_rect.topleft)
        
        for i, line in enumerate(self.display_text.split('\n')):
            text_surf = self.font.render(line, True, COLOR_TEXT)
            surface.blit(text_surf, (box_rect.x + 20, box_rect.y + 15 + i * 28))
        
        if self.char_index >= len(self.text):
            if int(pygame.time.get_ticks() / 500) % 2:
                ind = self.font.render(">>", True, (150, 170, 200))
                surface.blit(ind, (box_rect.right - 45, box_rect.bottom - 30))


# ==================== MIRROR CLASSES ====================

class MirrorShard:
    """A single shard of broken mirror that flies away"""
    def __init__(self, x, y, vx, vy, size, rotation_speed):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = rotation_speed
        self.alpha = 255
        self.gravity = 200
        self.life = 1.0
        self.points = self._generate_points()
    
    def _generate_points(self):
        """Generate random shard shape"""
        points = []
        num_points = random.randint(3, 5)
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi + random.uniform(-0.3, 0.3)
            dist = self.size * random.uniform(0.5, 1.0)
            points.append((math.cos(angle) * dist, math.sin(angle) * dist))
        return points
    
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.rotation += self.rotation_speed * dt
        self.life -= dt * 0.8
        self.alpha = max(0, int(255 * self.life))
        return self.life > 0
    
    def draw(self, surface, camera_x, camera_y):
        if self.alpha <= 0:
            return
        
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Rotate points
        rotated = []
        rad = math.radians(self.rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        for px, py in self.points:
            rx = px * cos_r - py * sin_r + draw_x
            ry = px * sin_r + py * cos_r + draw_y
            rotated.append((rx, ry))
        
        # Draw shard with reflection effect
        if len(rotated) >= 3:
            # Glass color with transparency
            surf_w, surf_h = surface.get_size()
            shard_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            pygame.draw.polygon(shard_surf, (200, 220, 255, self.alpha), rotated)
            # Highlight
            pygame.draw.polygon(shard_surf, (255, 255, 255, self.alpha // 2), rotated, 1)
            surface.blit(shard_surf, (0, 0))


class Mirror:
    """A mirror that can be broken to reveal an item"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.broken = False
        self.breaking = False
        self.break_timer = 0
        self.shards = []
        self.crack_progress = 0
        self.cracks = []
        self.shimmer_timer = 0
        self.highlight = False
        self.distortion_timer = 0
        
        # Generate crack lines (will be revealed progressively)
        self._generate_cracks()
    
    def _generate_cracks(self):
        """Generate crack patterns"""
        center_x = self.width // 2
        center_y = self.height // 2
        
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(30, min(self.width, self.height) * 0.4)
            points = [(center_x, center_y)]
            x, y = center_x, center_y
            segments = random.randint(3, 6)
            for i in range(segments):
                # Add some randomness to the crack direction
                angle += random.uniform(-0.5, 0.5)
                seg_len = length / segments * random.uniform(0.8, 1.2)
                x += math.cos(angle) * seg_len
                y += math.sin(angle) * seg_len
                points.append((x, y))
            self.cracks.append(points)
    
    def start_breaking(self):
        """Start the mirror breaking animation"""
        if not self.broken and not self.breaking:
            self.breaking = True
            self.break_timer = 0
    
    def add_crack(self):
        """Add visible crack (called when puzzle progress is made)"""
        self.crack_progress = min(1.0, self.crack_progress + 0.25)
    
    def update(self, dt):
        self.shimmer_timer += dt
        self.distortion_timer += dt
        
        if self.breaking:
            self.break_timer += dt
            
            # Generate shards during breaking animation
            if self.break_timer < 0.5:
                if random.random() < dt * 50:
                    cx = self.x + self.width // 2
                    cy = self.y + self.height // 2
                    sx = cx + random.uniform(-self.width//2, self.width//2)
                    sy = cy + random.uniform(-self.height//2, self.height//2)
                    vx = random.uniform(-200, 200)
                    vy = random.uniform(-300, -100)
                    size = random.uniform(8, 25)
                    rot_speed = random.uniform(-400, 400)
                    self.shards.append(MirrorShard(sx, sy, vx, vy, size, rot_speed))
            
            if self.break_timer >= 0.5:
                self.breaking = False
                self.broken = True
        
        # Update shards
        self.shards = [s for s in self.shards if s.update(dt)]
    
    def draw(self, surface, camera_x, camera_y, character=None):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.broken:
            # Draw broken frame only
            self._draw_frame(surface, draw_x, draw_y, broken=True)
            # Draw remaining shards
            for shard in self.shards:
                shard.draw(surface, camera_x, camera_y)
            return
        
        # Draw mirror frame
        self._draw_frame(surface, draw_x, draw_y)
        
        # Draw mirror surface
        mirror_surf = pygame.Surface((self.width - 16, self.height - 16), pygame.SRCALPHA)
        
        # Base mirror color with gradient
        for y in range(self.height - 16):
            gradient = int(180 + 40 * (y / (self.height - 16)))
            g_r = min(255, gradient)
            g_g = min(255, gradient + 20)
            g_b = min(255, gradient + 40)
            pygame.draw.line(mirror_surf, (g_r, g_g, g_b, 200),
                           (0, y), (self.width - 16, y))
        
        # Shimmer effect
        shimmer_x = int((math.sin(self.shimmer_timer * 2) + 1) * (self.width - 20) / 2)
        pygame.draw.line(mirror_surf, (255, 255, 255, 100),
                        (shimmer_x, 0), (shimmer_x + 10, self.height - 16), 3)
        
        # Draw reflection of character if nearby
        if character:
            char_screen_x = character.x - camera_x
            mirror_center_x = draw_x + self.width // 2
            
            # Only show reflection if character is in front of mirror
            if abs(char_screen_x - mirror_center_x) < 150:
                character.draw_reflection(surface, mirror_center_x, camera_x, camera_y, 120)
        
        # Draw cracks if any
        if self.crack_progress > 0:
            crack_surf = pygame.Surface((self.width - 16, self.height - 16), pygame.SRCALPHA)
            num_cracks = int(len(self.cracks) * self.crack_progress)
            for i, crack in enumerate(self.cracks[:num_cracks]):
                for j in range(len(crack) - 1):
                    pygame.draw.line(crack_surf, (255, 255, 255, 200),
                                   crack[j], crack[j+1], 2)
                    # Dark line for depth
                    pygame.draw.line(crack_surf, (50, 50, 70, 150),
                                   (crack[j][0]+1, crack[j][1]+1),
                                   (crack[j+1][0]+1, crack[j+1][1]+1), 1)
            mirror_surf.blit(crack_surf, (0, 0))
        
        # Distortion effect during breaking
        if self.breaking:
            distort = int(10 * (1 - self.break_timer / 0.5))
            if distort > 0:
                for _ in range(5):
                    ox = random.randint(-distort, distort)
                    oy = random.randint(-distort, distort)
                    mirror_surf.scroll(ox, oy)
        
        surface.blit(mirror_surf, (draw_x + 8, draw_y + 8))
        
        # Draw shards
        for shard in self.shards:
            shard.draw(surface, camera_x, camera_y)
        
        # Highlight effect
        if self.highlight and not self.breaking:
            hl_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(hl_surf, (255, 255, 255, 30), (0, 0, self.width, self.height))
            surface.blit(hl_surf, (draw_x, draw_y))
    
    def _draw_frame(self, surface, draw_x, draw_y, broken=False):
        """Draw ornate mirror frame"""
        # Outer frame
        frame_color = (80, 70, 60) if not broken else (50, 45, 40)
        pygame.draw.rect(surface, frame_color, (draw_x, draw_y, self.width, self.height))
        
        # Inner frame details
        inner_color = (60, 50, 45) if not broken else (40, 35, 30)
        pygame.draw.rect(surface, inner_color, (draw_x + 4, draw_y + 4, self.width - 8, self.height - 8))
        
        # Frame border
        border_color = (100, 90, 80) if not broken else (70, 60, 50)
        pygame.draw.rect(surface, border_color, (draw_x, draw_y, self.width, self.height), 3)
        pygame.draw.rect(surface, (40, 35, 30), (draw_x + 6, draw_y + 6, self.width - 12, self.height - 12), 2)
        
        # Corner decorations
        corners = [(draw_x + 3, draw_y + 3), (draw_x + self.width - 12, draw_y + 3),
                   (draw_x + 3, draw_y + self.height - 12), (draw_x + self.width - 12, draw_y + self.height - 12)]
        for cx, cy in corners:
            pygame.draw.circle(surface, (120, 100, 80) if not broken else (80, 70, 60), (cx + 4, cy + 4), 5)


class ReflectionPuzzle:
    """Puzzle: Match your reflection's position by standing in specific spots"""
    def __init__(self, mirror, target_positions):
        self.mirror = mirror
        self.target_positions = target_positions  # [(x, y), ...]
        self.current_target = 0
        self.solved = False
        self.progress = 0
        self.stand_timer = 0
        self.required_time = 1.5  # Seconds to stand in position
        self.glow_timer = 0
    
    def update(self, dt, char_x, char_y):
        if self.solved:
            return None
        
        self.glow_timer += dt
        
        target_x, target_y = self.target_positions[self.current_target]
        distance = math.sqrt((char_x - target_x)**2 + (char_y - target_y)**2)
        
        if distance < 30:
            self.stand_timer += dt
            if self.stand_timer >= self.required_time:
                self.current_target += 1
                self.stand_timer = 0
                self.mirror.add_crack()
                
                if self.current_target >= len(self.target_positions):
                    self.solved = True
                    return "solved"
                return "progress"
        else:
            self.stand_timer = max(0, self.stand_timer - dt * 0.5)
        
        return None
    
    def draw(self, surface, camera_x, camera_y):
        if self.solved:
            return
        
        # Draw target positions
        for i, (tx, ty) in enumerate(self.target_positions):
            draw_x = tx - camera_x
            draw_y = ty - camera_y
            
            if i < self.current_target:
                # Completed - green check
                color = (100, 255, 100, 100)
            elif i == self.current_target:
                # Current target - pulsing
                pulse = (math.sin(self.glow_timer * 4) + 1) / 2
                alpha = int(100 + pulse * 100)
                color = (255, 200, 100, alpha)
                
                # Draw progress ring
                if self.stand_timer > 0:
                    progress_angle = (self.stand_timer / self.required_time) * 360
                    self._draw_progress_ring(surface, draw_x, draw_y, progress_angle)
            else:
                # Future - dim
                color = (150, 150, 180, 50)
            
            # Draw marker
            marker_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(marker_surf, color, (30, 30), 25, 3)
            
            # Draw symbol in center
            if i == self.current_target:
                try:
                    font = pygame.font.Font(FONT_PATH, 20)
                except:
                    font = pygame.font.Font(None, 20)
                text = font.render("◈", True, color[:3])
                marker_surf.blit(text, (30 - text.get_width()//2, 30 - text.get_height()//2))
            
            surface.blit(marker_surf, (draw_x - 30, draw_y - 30))
    
    def _draw_progress_ring(self, surface, x, y, angle):
        """Draw a progress ring showing stand time"""
        ring_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
        center = (35, 35)
        
        # Draw arc
        rect = pygame.Rect(5, 5, 60, 60)
        start_angle = math.radians(-90)
        end_angle = math.radians(-90 + angle)
        
        # Draw segments
        segments = int(angle / 10) + 1
        for i in range(segments):
            seg_start = start_angle + (end_angle - start_angle) * i / segments
            seg_end = start_angle + (end_angle - start_angle) * (i + 1) / segments
            
            x1 = center[0] + 28 * math.cos(seg_start)
            y1 = center[1] + 28 * math.sin(seg_start)
            x2 = center[0] + 28 * math.cos(seg_end)
            y2 = center[1] + 28 * math.sin(seg_end)
            
            pygame.draw.line(ring_surf, (100, 255, 150, 200), (x1, y1), (x2, y2), 4)
        
        surface.blit(ring_surf, (x - 35, y - 35))


class PencilItem:
    """The Pencil item that appears after breaking the mirror"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visible = False
        self.collected = False
        self.bob_timer = 0
        self.glow_timer = 0
        self.appear_timer = 0
        self.appear_alpha = 0
        
        # Absorption effect
        self.absorbing = False
        self.absorb_timer = 0
        self.absorb_particles = []
        self.absorb_target_x = 0
        self.absorb_target_y = 0
    
    def appear(self):
        """Make the pencil appear (called when mirror breaks)"""
        self.visible = True
        self.appear_timer = 0
    
    def start_absorb(self, target_x, target_y):
        """Start absorption animation towards the character"""
        self.absorbing = True
        self.absorb_timer = 0
        self.absorb_target_x = target_x
        self.absorb_target_y = target_y
        
        # Create absorption particles
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(30, 80)
            speed = random.uniform(100, 200)
            self.absorb_particles.append({
                'x': self.x + math.cos(angle) * dist,
                'y': self.y + math.sin(angle) * dist,
                'speed': speed,
                'size': random.randint(2, 5),
                'color': random.choice([
                    (255, 200, 100),  # Gold
                    (255, 255, 200),  # White
                    (200, 180, 255),  # Light purple
                ])
            })
    
    def update(self, dt):
        if not self.visible:
            return
        
        self.bob_timer += dt
        self.glow_timer += dt
        
        # Appear animation
        if self.appear_timer < 1.0:
            self.appear_timer += dt
            self.appear_alpha = min(255, int(self.appear_timer * 255))
        
        # Absorption animation
        if self.absorbing:
            self.absorb_timer += dt
            
            # Move particles towards target
            for p in self.absorb_particles:
                dx = self.absorb_target_x - p['x']
                dy = self.absorb_target_y - p['y']
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 5:
                    p['x'] += (dx / dist) * p['speed'] * dt * (1 + self.absorb_timer)
                    p['y'] += (dy / dist) * p['speed'] * dt * (1 + self.absorb_timer)
            
            # Move pencil towards target
            if self.absorb_timer < 1.0:
                progress = self.absorb_timer
                self.x += (self.absorb_target_x - self.x) * progress * dt * 5
                self.y += (self.absorb_target_y - self.y) * progress * dt * 5
            
            if self.absorb_timer >= 1.0:
                self.collected = True
                self.visible = False
    
    def draw(self, surface, camera_x, camera_y):
        if not self.visible:
            return
        
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y + math.sin(self.bob_timer * 3) * 5
        
        # Draw glow
        pulse = (math.sin(self.glow_timer * 4) + 1) / 2
        glow_size = 40 + pulse * 20
        glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
        for r in range(int(glow_size), 0, -2):
            alpha = int(60 * (1 - r / glow_size) * (self.appear_alpha / 255))
            pygame.draw.circle(glow_surf, (255, 220, 100, alpha),
                             (int(glow_size), int(glow_size)), r)
        surface.blit(glow_surf, (draw_x - glow_size + 8, draw_y - glow_size + 20))
        
        # Draw pencil shape
        pencil_surf = pygame.Surface((20, 50), pygame.SRCALPHA)
        
        # Pencil body (yellow)
        body_alpha = self.appear_alpha
        pygame.draw.rect(pencil_surf, (255, 200, 50, body_alpha), (4, 10, 12, 30))
        
        # Pencil tip (wood + graphite)
        pygame.draw.polygon(pencil_surf, (200, 150, 100, body_alpha), 
                          [(4, 40), (16, 40), (10, 50)])
        pygame.draw.polygon(pencil_surf, (50, 50, 50, body_alpha),
                          [(7, 45), (13, 45), (10, 50)])
        
        # Eraser
        pygame.draw.rect(pencil_surf, (255, 150, 150, body_alpha), (4, 5, 12, 8))
        
        # Metal band
        pygame.draw.rect(pencil_surf, (180, 180, 180, body_alpha), (4, 8, 12, 4))
        
        # Highlight
        pygame.draw.line(pencil_surf, (255, 255, 200, body_alpha // 2), (6, 12), (6, 38), 2)
        
        surface.blit(pencil_surf, (draw_x - 2, draw_y))
        
        # Draw absorption particles
        if self.absorbing:
            for p in self.absorb_particles:
                px = p['x'] - camera_x
                py = p['y'] - camera_y
                alpha = max(0, int(255 * (1 - self.absorb_timer)))
                ps = pygame.Surface((p['size']*2+2, p['size']*2+2), pygame.SRCALPHA)
                pygame.draw.circle(ps, (*p['color'], alpha), (p['size']+1, p['size']+1), p['size'])
                surface.blit(ps, (int(px) - p['size'], int(py) - p['size']))
        
        # Draw "collect" hint if nearby and not absorbing
        if not self.absorbing and self.appear_alpha >= 255:
            try:
                font = pygame.font.Font(FONT_PATH, 18)
            except:
                font = pygame.font.Font(None, 18)
            hint = font.render("Press SPACE", True, (255, 220, 100))
            surface.blit(hint, (draw_x - hint.get_width()//2 + 8, draw_y - 25))


class MirrorRoomPuzzle:
    def __init__(self, screen=None):
        pygame.init()
        pygame.mixer.init()
        
        if screen is not None:
            self.screen = screen
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dream Diary - Mirror Room")
        self.clock = pygame.time.Clock()
        
        self._generate_map()
        
        sprite_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "8Direction_TopDown_Character Sprites_ByBossNelNel", "SpriteSheet.png"
        )
        
        spawn_x = 10 * TILE_SIZE + TILE_SIZE // 2
        spawn_y = 12 * TILE_SIZE
        self.character = Character(sprite_path, spawn_x, spawn_y)
        
        self.camera_x = 0
        self.camera_y = 0
        
        screen_w, screen_h = self.screen.get_size()
        self.dialogue = DialogueBox()
        self.dream_effect = DreamEffect(screen_w, screen_h)
        
        self._create_puzzle()
        
        self.game_complete = False
        self.effect_obtained = False
        
        self.dream_effect.trigger_static(0.8)
        self.dialogue.show("A room of mirrors...\nThe reflections seem... wrong.\n\nFind where you belong.")
    
    def _generate_map(self):
        """Generate the mirror room map"""
        self.map_data = []
        self.collision_map = []
        
        # Create a dark, reflective room
        for y in range(MAP_HEIGHT):
            row = []
            collision_row = []
            for x in range(MAP_WIDTH):
                # Walls
                if x == 0 or x == MAP_WIDTH-1 or y == 0 or y == MAP_HEIGHT-1:
                    row.append('wall')
                    collision_row.append(1)
                elif x == 1 or x == MAP_WIDTH-2 or y == 1 or y == MAP_HEIGHT-2:
                    row.append('wall_inner')
                    collision_row.append(1)
                else:
                    # Checkered floor
                    if (x + y) % 2 == 0:
                        row.append('floor_dark')
                    else:
                        row.append('floor_light')
                    collision_row.append(0)
            self.map_data.append(row)
            self.collision_map.append(collision_row)
        
        # Create map surface
        self.map_surface = pygame.Surface((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
        self.map_surface.fill(COLOR_DREAM)
        
        tile_colors = {
            'wall': (30, 25, 35),
            'wall_inner': (40, 35, 50),
            'floor_dark': (20, 18, 25),
            'floor_light': (25, 23, 32),
        }
        
        for y, row in enumerate(self.map_data):
            for x, tile_name in enumerate(row):
                color = tile_colors.get(tile_name, (30, 30, 30))
                pygame.draw.rect(self.map_surface, color,
                               (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                
                # Add subtle grid lines
                pygame.draw.rect(self.map_surface, (40, 35, 50),
                               (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)
    
    def _create_puzzle(self):
        """Create the mirror and puzzle"""
        # Main mirror in the center-top of the room
        mirror_x = MAP_WIDTH // 2 * TILE_SIZE - 60
        mirror_y = 3 * TILE_SIZE
        self.mirror = Mirror(mirror_x, mirror_y, 120, 160)
        
        # Block collision where mirror is
        for mx in range(mirror_x // TILE_SIZE, (mirror_x + 120) // TILE_SIZE + 1):
            for my in range(mirror_y // TILE_SIZE, (mirror_y + 160) // TILE_SIZE + 1):
                if 0 <= mx < MAP_WIDTH and 0 <= my < MAP_HEIGHT:
                    self.collision_map[my][mx] = 1
        
        # Reflection puzzle: stand in specific positions
        # Make sure all positions are accessible (not blocked by mirror or walls)
        target_positions = [
            (5 * TILE_SIZE, 8 * TILE_SIZE),      # Left side
            (15 * TILE_SIZE, 8 * TILE_SIZE),     # Right side  
            (10 * TILE_SIZE, 11 * TILE_SIZE),    # Center bottom
            (8 * TILE_SIZE, 6 * TILE_SIZE),      # Left front (away from mirror)
        ]
        self.puzzle = ReflectionPuzzle(self.mirror, target_positions)
        
        # Pencil item (will appear at the center of the mirror after it breaks)
        pencil_x = mirror_x + self.mirror.width // 2
        pencil_y = mirror_y + self.mirror.height // 2
        self.pencil = PencilItem(pencil_x, pencil_y)
        
        # Store mirror collision area to clear when broken
        self.mirror_collision_tiles = []
        for mx in range(mirror_x // TILE_SIZE, (mirror_x + 120) // TILE_SIZE + 1):
            for my in range(mirror_y // TILE_SIZE, (mirror_y + 160) // TILE_SIZE + 1):
                if 0 <= mx < MAP_WIDTH and 0 <= my < MAP_HEIGHT:
                    self.mirror_collision_tiles.append((mx, my))
        
        # Decorative small mirrors on walls
        self.small_mirrors = [
            pygame.Rect(3 * TILE_SIZE, 5 * TILE_SIZE, 32, 48),
            pygame.Rect(3 * TILE_SIZE, 9 * TILE_SIZE, 32, 48),
            pygame.Rect((MAP_WIDTH - 4) * TILE_SIZE, 5 * TILE_SIZE, 32, 48),
            pygame.Rect((MAP_WIDTH - 4) * TILE_SIZE, 9 * TILE_SIZE, 32, 48),
        ]
    
    def check_collision(self, x, y, width, height):
        check_points = [(x, y), (x - width//2, y), (x + width//2, y),
                       (x, y - height//2), (x, y + height//2)]
        
        for px, py in check_points:
            tile_x, tile_y = int(px // TILE_SIZE), int(py // TILE_SIZE)
            if tile_x < 0 or tile_x >= MAP_WIDTH or tile_y < 0 or tile_y >= MAP_HEIGHT:
                return True
            if self.collision_map[tile_y][tile_x] == 1:
                return True
        return False
    
    def update_camera(self):
        # Center the map on screen since it's smaller than the screen
        map_pixel_width = MAP_WIDTH * TILE_SIZE
        map_pixel_height = MAP_HEIGHT * TILE_SIZE
        screen_w, screen_h = self.screen.get_size()
        
        # If map is smaller than screen, center it
        if map_pixel_width < screen_w:
            self.camera_x = -(screen_w - map_pixel_width) // 2
        else:
            target_x = self.character.x - screen_w // 2
            max_x = map_pixel_width - screen_w
            target_x = max(0, min(target_x, max_x))
            self.camera_x += (target_x - self.camera_x) * 0.1
        
        if map_pixel_height < screen_h:
            self.camera_y = -(screen_h - map_pixel_height) // 2
        else:
            target_y = self.character.y - screen_h // 2
            max_y = map_pixel_height - screen_h
            target_y = max(0, min(target_y, max_y))
            self.camera_y += (target_y - self.camera_y) * 0.1
    
    def handle_interaction(self):
        char_x, char_y = self.character.x, self.character.y
        
        # Check if near pencil
        if self.pencil.visible and not self.pencil.absorbing and not self.pencil.collected:
            dx = char_x - self.pencil.x
            dy = char_y - self.pencil.y
            if math.sqrt(dx*dx + dy*dy) < 50:
                self.pencil.start_absorb(char_x, char_y)
                self.dream_effect.flash((255, 220, 100), 150)
                self.dream_effect.shake(0.4, 6)
                return
        
        # Check if near mirror
        mirror_center_x = self.mirror.x + self.mirror.width // 2
        mirror_center_y = self.mirror.y + self.mirror.height // 2
        dx = char_x - mirror_center_x
        dy = char_y - mirror_center_y
        if math.sqrt(dx*dx + dy*dy) < 100 and not self.mirror.broken:
            self.dialogue.show("A tall mirror stands before you.\nYour reflection stares back... expectantly.\n\nFind the marked positions in the room.")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if self.dialogue.active:
                        self.dialogue.skip()
                    else:
                        self.handle_interaction()
                
                if event.key == pygame.K_e:
                    if self.effect_obtained:
                        self.dialogue.show("Effect: [PENCIL]\nThe power to draw your own path.")
                    else:
                        self.dialogue.show("No effects yet.\nSolve the mirror puzzle!")
        
        return True
    
    def update(self, dt):
        if self.game_complete:
            self.dialogue.update(dt)
            self.dream_effect.update(dt)
            return
        
        # Character movement
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
        
        self.character.update(dt, dx, dy, self.check_collision)
        self.update_camera()
        
        # Update mirror
        self.mirror.update(dt)
        
        # Update puzzle
        if not self.puzzle.solved and not self.mirror.broken:
            result = self.puzzle.update(dt, self.character.x, self.character.y)
            if result == "solved":
                self.dialogue.show("The mirror begins to crack...\nYour reflection smiles.")
                self.mirror.start_breaking()
                self.dream_effect.flash((200, 220, 255), 150)
                self.dream_effect.shake(0.5, 8)
            elif result == "progress":
                self.dialogue.show(f"Position aligned... ({self.puzzle.current_target}/{len(self.puzzle.target_positions)})")
                self.dream_effect.flash((150, 200, 255), 80)
                self.dream_effect.shake(0.2, 3)
        
        # Show pencil when mirror breaks and clear collision
        if self.mirror.broken and not self.pencil.visible:
            # Clear mirror collision so player can reach the pencil
            for mx, my in self.mirror_collision_tiles:
                self.collision_map[my][mx] = 0
            self.pencil.appear()
            self.dialogue.show("Behind the shattered glass...\nA pencil, glowing with dream energy!")
        
        # Update pencil
        self.pencil.update(dt)
        
        # Check if pencil was collected
        if self.pencil.collected and not self.effect_obtained:
            self.effect_obtained = True
            self.dialogue.show("Obtained [PENCIL] effect!\n\nThe power to draw your own path...")
            self.dream_effect.flash((255, 255, 200), 200)
            self.game_complete = True
        
        # Update mirror highlight
        mirror_center_x = self.mirror.x + self.mirror.width // 2
        dx = self.character.x - mirror_center_x
        dy = self.character.y - (self.mirror.y + self.mirror.height)
        self.mirror.highlight = math.sqrt(dx*dx + dy*dy) < 80
        
        self.dialogue.update(dt)
        self.dream_effect.update(dt)
    
    def draw(self):
        shake_x, shake_y = self.dream_effect.get_shake_offset()
        self.screen.fill(COLOR_DREAM)
        
        # Draw map
        self.screen.blit(self.map_surface, (-self.camera_x + shake_x, -self.camera_y + shake_y))
        
        # Draw small decorative mirrors
        for rect in self.small_mirrors:
            self._draw_small_mirror(rect, shake_x, shake_y)
        
        # Draw puzzle markers
        self.puzzle.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw main mirror
        self.mirror.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y, self.character)
        
        # Draw pencil
        self.pencil.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw character
        self.character.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw effects
        self.dream_effect.draw(self.screen)
        
        # Draw UI
        self._draw_ui()
        
        # Draw dialogue
        self.dialogue.draw(self.screen)
        
        pygame.display.flip()
    
    def _draw_small_mirror(self, rect, shake_x, shake_y):
        """Draw a small decorative wall mirror"""
        draw_x = rect.x - self.camera_x + shake_x
        draw_y = rect.y - self.camera_y + shake_y
        
        # Frame
        pygame.draw.rect(self.screen, (70, 60, 50), (draw_x - 2, draw_y - 2, rect.width + 4, rect.height + 4))
        
        # Mirror surface
        mirror_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for y in range(rect.height):
            gradient = int(150 + 50 * (y / rect.height))
            pygame.draw.line(mirror_surf, (gradient, gradient + 10, gradient + 20, 180),
                           (0, y), (rect.width, y))
        self.screen.blit(mirror_surf, (draw_x, draw_y))
    
    def _draw_ui(self):
        try:
            font = pygame.font.Font(FONT_PATH, 24)
            small_font = pygame.font.Font(FONT_PATH, 18)
        except:
            font = pygame.font.Font(None, 24)
            small_font = pygame.font.Font(None, 18)
        
        # Room title
        ui_bg = pygame.Surface((180, 50), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 100))
        self.screen.blit(ui_bg, (5, 5))
        
        title = font.render("MIRROR ROOM", True, (180, 200, 220))
        self.screen.blit(title, (15, 12))
        
        # Progress indicator
        if not self.puzzle.solved:
            progress_text = f"Positions: {self.puzzle.current_target}/{len(self.puzzle.target_positions)}"
            progress = small_font.render(progress_text, True, (150, 170, 200))
            self.screen.blit(progress, (15, 35))
        
        # Controls hint
        hint_text = "WASD/Arrows: Move | SPACE: Interact | E: Effects"
        hint = small_font.render(hint_text, True, (100, 100, 120))
        screen_w, screen_h = self.screen.get_size()
        self.screen.blit(hint, (10, screen_h - 25))
        
        # Effect indicator
        effect_x = screen_w - 60
        if self.effect_obtained:
            pygame.draw.circle(self.screen, (255, 200, 100), (effect_x, 25), 15)
            pygame.draw.circle(self.screen, (255, 255, 200), (effect_x, 25), 10)
            label = small_font.render("✏", True, (80, 60, 40))
            self.screen.blit(label, (effect_x - label.get_width()//2, 18))
        else:
            pygame.draw.circle(self.screen, (50, 50, 60), (effect_x, 25), 15)
            pygame.draw.circle(self.screen, (40, 40, 50), (effect_x, 25), 12, 2)
        
        # Game complete overlay
        if self.game_complete and self.effect_obtained:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            alpha = min(150, int(pygame.time.get_ticks() % 3000 / 15))
            overlay.fill((255, 255, 255, alpha))
            self.screen.blit(overlay, (0, 0))
            
            try:
                big_font = pygame.font.Font(FONT_PATH, 48)
            except:
                big_font = pygame.font.Font(None, 48)
            text = big_font.render("Mirror Cleared", True, (50, 50, 80))
            rect = text.get_rect(center=(screen_w // 2, screen_h // 2))
            self.screen.blit(text, rect)
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    game = MirrorRoomPuzzle()
    game.run()


if __name__ == "__main__":
    main()
