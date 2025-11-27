"""
梦日记风格 - 画作房解谜关卡
Yume Nikki Style - Painting Room Puzzle

玩家在梦境般的房间中收集6个抽象画作碎片，
收集全部碎片后画作燃烧，角色吸收火焰。
"""

import pygame
import sys
import os
import math
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --------------------------
# 配置
# --------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 32
MAP_WIDTH = 26
MAP_HEIGHT = 18

CHAR_FRAME_WIDTH = 23
CHAR_FRAME_HEIGHT = 36
CHAR_SCALE = 1.5
ANIMATION_SPEED = 0.08

DIRECTION_MAP = {
    'down': 0, 'down_right': 1, 'right': 2, 'up_right': 3,
    'up': 4, 'up_left': 5, 'left': 6, 'down_left': 7,
}

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "Silver.ttf")

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_DREAM = (25, 15, 35)
COLOR_TEXT = (200, 180, 220)


class Character:
    """角色类 - 使用8方向精灵"""
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
        
        self.animation_timer += dt
        if self.is_moving:
            if self.animation_timer >= ANIMATION_SPEED:
                self.animation_timer -= ANIMATION_SPEED
                self.frame_index = (self.frame_index % 8) + 1
        else:
            if self.animation_timer >= ANIMATION_SPEED * 2:
                self.animation_timer = 0
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
    
    def draw(self, surface, offset_x=0, offset_y=0):
        frame = self.frames[self.direction][self.frame_index]
        draw_x = self.x + offset_x - frame.get_width() // 2
        draw_y = self.y + offset_y - frame.get_height() + self.collision_height
        surface.blit(frame, (draw_x, draw_y))


class DreamEffect:
    """梦境视觉效果"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.flash_alpha = 0
        self.flash_color = (255, 255, 255)
        self.screen_shake = 0
        self.shake_intensity = 0
        self.particles = []
        for _ in range(40):
            self.particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(0, self.screen_height),
                'speed': random.uniform(10, 25),
                'size': random.randint(2, 5),
                'alpha': random.randint(30, 80),
                'color': random.choice([
                    (255, 100, 100), (100, 255, 100), (100, 100, 255),
                    (255, 255, 100), (255, 100, 255), (100, 255, 255)
                ])
            })
    
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
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 300 * dt)
        if self.screen_shake > 0:
            self.screen_shake -= dt
        for p in self.particles:
            p['y'] -= p['speed'] * dt
            p['x'] += math.sin(p['y'] * 0.02) * 0.5
            if p['y'] < -10:
                p['y'] = self.screen_height + 10
                p['x'] = random.randint(0, self.screen_width)
    
    def draw(self, surface):
        for p in self.particles:
            ps = pygame.Surface((p['size']*2+2, p['size']*2+2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p['color'], p['alpha']), (p['size']+1, p['size']+1), p['size'])
            surface.blit(ps, (int(p['x']), int(p['y'])))
        
        if self.flash_alpha > 0:
            fs = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            fs.fill((*self.flash_color, int(self.flash_alpha)))
            surface.blit(fs, (0, 0))


class DialogueBox:
    """对话框"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active = False
        self.text = ""
        self.display_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.char_speed = 0.03
        try:
            self.font = pygame.font.Font(FONT_PATH, 24)
        except:
            self.font = pygame.font.Font(None, 24)
    
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
        box_h = 100
        box_rect = pygame.Rect(40, self.screen_height - box_h - 40,
                               self.screen_width - 80, box_h)
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        box_surf.fill((20, 10, 35, 230))
        pygame.draw.rect(box_surf, (150, 100, 50), (0, 0, box_rect.width, box_rect.height), 3)
        surface.blit(box_surf, box_rect.topleft)
        
        for i, line in enumerate(self.display_text.split('\n')):
            text_surf = self.font.render(line, True, COLOR_TEXT)
            surface.blit(text_surf, (box_rect.x + 20, box_rect.y + 15 + i * 28))
        
        if self.char_index >= len(self.text):
            if int(pygame.time.get_ticks() / 500) % 2:
                ind = self.font.render(">>", True, (180, 150, 100))
                surface.blit(ind, (box_rect.right - 50, box_rect.bottom - 30))


class PaintingFragment:
    """画作碎片 - 增强抽象艺术风格"""
    def __init__(self, x, y, fragment_id, color_scheme):
        self.x = x
        self.y = y
        self.fragment_id = fragment_id
        self.color_scheme = color_scheme
        self.collected = False
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.glow_timer = 0
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-30, 30)
        self.surface = self._generate_abstract_art()
    
    def _generate_abstract_art(self):
        size = 56
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        base, accent, highlight = self.color_scheme
        cx, cy = size // 2, size // 2
        
        pattern = self.fragment_id % 6
        
        if pattern == 0:  # 星芒图案
            for i in range(8):
                angle = i * 45
                length = 22 if i % 2 == 0 else 14
                x1 = cx + int(length * math.cos(math.radians(angle)))
                y1 = cy + int(length * math.sin(math.radians(angle)))
                pygame.draw.line(surf, base, (cx, cy), (x1, y1), 3)
            pygame.draw.circle(surf, accent, (cx, cy), 10)
            pygame.draw.circle(surf, highlight, (cx, cy), 5)
            for i in range(12):
                angle = i * 30
                x1 = cx + int(8 * math.cos(math.radians(angle)))
                y1 = cy + int(8 * math.sin(math.radians(angle)))
                pygame.draw.circle(surf, highlight, (x1, y1), 2)
        
        elif pattern == 1:  # 漩涡图案
            for i in range(60):
                angle = i * 18
                dist = 3 + i * 0.35
                x1 = cx + int(dist * math.cos(math.radians(angle)))
                y1 = cy + int(dist * math.sin(math.radians(angle)))
                color_blend = i / 60
                color = (
                    int(base[0] * (1-color_blend) + accent[0] * color_blend),
                    int(base[1] * (1-color_blend) + accent[1] * color_blend),
                    int(base[2] * (1-color_blend) + accent[2] * color_blend)
                )
                pygame.draw.circle(surf, color, (x1, y1), max(1, 4 - i//20))
            pygame.draw.circle(surf, highlight, (cx, cy), 4)
        
        elif pattern == 2:  # 晶体图案
            points = []
            for i in range(6):
                angle = i * 60 - 90
                x1 = cx + int(22 * math.cos(math.radians(angle)))
                y1 = cy + int(22 * math.sin(math.radians(angle)))
                points.append((x1, y1))
            pygame.draw.polygon(surf, base, points)
            inner_points = []
            for i in range(6):
                angle = i * 60 - 60
                x1 = cx + int(12 * math.cos(math.radians(angle)))
                y1 = cy + int(12 * math.sin(math.radians(angle)))
                inner_points.append((x1, y1))
            pygame.draw.polygon(surf, accent, inner_points)
            pygame.draw.circle(surf, highlight, (cx, cy), 6)
            for p in points:
                pygame.draw.line(surf, highlight, (cx, cy), p, 1)
        
        elif pattern == 3:  # 眼睛图案
            pygame.draw.ellipse(surf, base, (cx-22, cy-12, 44, 24))
            pygame.draw.ellipse(surf, accent, (cx-22, cy-12, 44, 24), 2)
            pygame.draw.circle(surf, accent, (cx, cy), 10)
            pygame.draw.circle(surf, (20, 10, 30), (cx, cy), 6)
            pygame.draw.circle(surf, highlight, (cx-2, cy-2), 3)
            pygame.draw.arc(surf, highlight, (cx-18, cy-8, 36, 16), 0.2, 2.9, 2)
        
        elif pattern == 4:  # 火焰图案
            flame_points = [(cx, cy-24), (cx+8, cy-10), (cx+16, cy+8),
                           (cx+10, cy+20), (cx, cy+12), (cx-10, cy+20),
                           (cx-16, cy+8), (cx-8, cy-10)]
            pygame.draw.polygon(surf, base, flame_points)
            inner_flame = [(cx, cy-16), (cx+5, cy-6), (cx+10, cy+4),
                          (cx+6, cy+12), (cx, cy+6), (cx-6, cy+12),
                          (cx-10, cy+4), (cx-5, cy-6)]
            pygame.draw.polygon(surf, accent, inner_flame)
            core_flame = [(cx, cy-8), (cx+3, cy), (cx+5, cy+6),
                         (cx, cy+4), (cx-5, cy+6), (cx-3, cy)]
            pygame.draw.polygon(surf, highlight, core_flame)
        
        else:  # 月相图案
            pygame.draw.circle(surf, base, (cx, cy), 20)
            pygame.draw.circle(surf, (25, 15, 40), (cx+8, cy), 16)
            for i in range(5):
                sx = cx - 12 + random.randint(-3, 3)
                sy = cy - 8 + i * 5 + random.randint(-2, 2)
                pygame.draw.circle(surf, accent, (sx, sy), random.randint(1, 3))
            pygame.draw.circle(surf, highlight, (cx-8, cy-8), 4)
        
        return surf
    
    def update(self, dt):
        self.bob_offset += dt * 2.5
        self.glow_timer += dt
        self.rotation += self.rotation_speed * dt
    
    def is_near(self, char_x, char_y, distance=45):
        dx = char_x - self.x
        dy = char_y - self.y
        return math.sqrt(dx*dx + dy*dy) < distance
    
    def draw(self, surface, offset_x=0, offset_y=0):
        if self.collected:
            return
        
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y + math.sin(self.bob_offset) * 8
        
        # 多层发光效果
        pulse = (math.sin(self.glow_timer * 3) + 1) / 2
        pulse2 = (math.sin(self.glow_timer * 5 + 1) + 1) / 2
        
        # 外层光晕
        glow_size = 45 + pulse * 15
        glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
        for r in range(int(glow_size), 10, -5):
            alpha = int((40 + pulse * 30) * (1 - r/glow_size))
            pygame.draw.circle(glow_surf, (*self.color_scheme[0], alpha),
                              (int(glow_size), int(glow_size)), r)
        surface.blit(glow_surf, (draw_x - glow_size, draw_y - glow_size))
        
        # 内层光晕
        inner_glow = 25 + pulse2 * 8
        inner_surf = pygame.Surface((int(inner_glow*2), int(inner_glow*2)), pygame.SRCALPHA)
        pygame.draw.circle(inner_surf, (*self.color_scheme[1], int(60 + pulse2 * 40)),
                          (int(inner_glow), int(inner_glow)), int(inner_glow))
        surface.blit(inner_surf, (draw_x - inner_glow, draw_y - inner_glow))
        
        # 旋转绘制碎片
        rotated = pygame.transform.rotate(self.surface, self.rotation)
        rot_rect = rotated.get_rect(center=(draw_x, draw_y))
        surface.blit(rotated, rot_rect)


class PaintingCanvas:
    """画布 - 收集6个碎片的地方"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 150
        self.height = 100
        self.slots = [None] * 6
        self.completed = False
        self.glow_timer = 0
        self.shimmer_offset = 0
    
    def add_fragment(self, fragment_id):
        if fragment_id < len(self.slots):
            self.slots[fragment_id] = fragment_id
            if all(slot is not None for slot in self.slots):
                self.completed = True
            return True
        return False
    
    def get_progress(self):
        return sum(1 for s in self.slots if s is not None), len(self.slots)
    
    def update(self, dt):
        self.glow_timer += dt
        self.shimmer_offset += dt * 100
    
    def draw(self, surface, offset_x, offset_y, fragment_surfaces):
        dx = self.x + offset_x
        dy = self.y + offset_y
        
        # 华丽画框
        frame_color1 = (120, 85, 50)
        frame_color2 = (160, 120, 70)
        frame_color3 = (90, 60, 35)
        
        # 外框阴影
        pygame.draw.rect(surface, (30, 20, 15), (dx - 14, dy - 14, self.width + 28, self.height + 28), border_radius=6)
        # 外框
        pygame.draw.rect(surface, frame_color1, (dx - 12, dy - 12, self.width + 24, self.height + 24), border_radius=5)
        # 装饰线
        pygame.draw.rect(surface, frame_color2, (dx - 12, dy - 12, self.width + 24, self.height + 24), 3, border_radius=5)
        # 内框
        pygame.draw.rect(surface, frame_color3, (dx - 4, dy - 4, self.width + 8, self.height + 8), border_radius=2)
        pygame.draw.rect(surface, (200, 160, 100), (dx - 4, dy - 4, self.width + 8, self.height + 8), 2, border_radius=2)
        # 画布背景
        pygame.draw.rect(surface, (40, 28, 50), (dx, dy, self.width, self.height))
        
        # 画框角落装饰
        corner_size = 8
        corners = [(dx - 10, dy - 10), (dx + self.width + 2, dy - 10),
                   (dx - 10, dy + self.height + 2), (dx + self.width + 2, dy + self.height + 2)]
        for cx, cy in corners:
            pygame.draw.rect(surface, frame_color2, (cx, cy, corner_size, corner_size))
            pygame.draw.rect(surface, (220, 180, 120), (cx + 2, cy + 2, corner_size - 4, corner_size - 4))
        
        if self.completed:
            pulse = (math.sin(self.glow_timer * 2) + 1) / 2
            glow = pygame.Surface((self.width + 50, self.height + 50), pygame.SRCALPHA)
            for r in range(40, 5, -5):
                alpha = int((50 + pulse * 60) * (1 - r/40))
                pygame.draw.rect(glow, (255, 180, 80, alpha), (25-r, 25-r, self.width+r*2, self.height+r*2), border_radius=r//2)
            surface.blit(glow, (dx - 25, dy - 25))
        
        # 3x2 格子排列6个碎片
        slot_w, slot_h = self.width // 3, self.height // 2
        for i, slot in enumerate(self.slots):
            sx = dx + (i % 3) * slot_w
            sy = dy + (i // 3) * slot_h
            if slot is not None and slot < len(fragment_surfaces):
                scaled = pygame.transform.scale(fragment_surfaces[slot], (slot_w - 4, slot_h - 4))
                surface.blit(scaled, (sx + 2, sy + 2))
            else:
                # 空槽位装饰
                pygame.draw.rect(surface, (55, 40, 65), (sx + 3, sy + 3, slot_w - 6, slot_h - 6), 1)
                # 闪烁效果
                shimmer = int((math.sin(self.shimmer_offset * 0.05 + i) + 1) * 15)
                pygame.draw.rect(surface, (70 + shimmer, 50 + shimmer, 80 + shimmer),
                               (sx + 6, sy + 6, slot_w - 12, slot_h - 12), 1)


class BurningEffect:
    """燃烧特效"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.active = False
        self.timer = 0
        self.duration = 4.0
        self.flames = []
        self.complete = False
    
    def start(self):
        self.active = True
        self.timer = 0
        self.complete = False
        for _ in range(80):
            self.flames.append({
                'x': self.x + random.uniform(0, self.width),
                'y': self.y + random.uniform(0, self.height),
                'vx': random.uniform(-30, 30),
                'vy': random.uniform(-120, -60),
                'size': random.uniform(12, 30),
                'life': random.uniform(0.5, 1.2),
                'max_life': random.uniform(0.5, 1.2),
                'hue': random.uniform(0, 1)
            })
    
    def update(self, dt):
        if not self.active:
            return
        
        self.timer += dt
        
        for flame in self.flames[:]:
            flame['x'] += flame['vx'] * dt
            flame['y'] += flame['vy'] * dt
            flame['vy'] -= 80 * dt
            flame['life'] -= dt
            flame['size'] *= 0.97
            
            if flame['life'] <= 0:
                self.flames.remove(flame)
                if self.timer < self.duration * 0.7:
                    self.flames.append({
                        'x': self.x + random.uniform(0, self.width),
                        'y': self.y + random.uniform(self.height * 0.3, self.height),
                        'vx': random.uniform(-40, 40),
                        'vy': random.uniform(-150, -80),
                        'size': random.uniform(15, 35),
                        'life': random.uniform(0.5, 1.0),
                        'max_life': random.uniform(0.5, 1.0),
                        'hue': random.uniform(0, 1)
                    })
        
        if self.timer >= self.duration:
            self.complete = True
            self.active = False
    
    def draw(self, surface, offset_x, offset_y):
        if not self.active and not self.flames:
            return
        
        for flame in self.flames:
            fx = flame['x'] + offset_x
            fy = flame['y'] + offset_y
            life_ratio = max(0, flame['life'] / flame['max_life'])
            
            if flame['hue'] < 0.4:
                color = (255, int(220 * life_ratio), 50)
            elif flame['hue'] < 0.7:
                color = (255, int(140 * life_ratio), 30)
            else:
                color = (255, int(80 * life_ratio), int(60 * life_ratio))
            
            size = max(2, int(flame['size']))
            flame_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            alpha = int(220 * life_ratio)
            pygame.draw.circle(flame_surf, (*color, alpha), (size, size), size)
            surface.blit(flame_surf, (fx - size, fy - size))


class AbsorptionEffect:
    """吸收特效"""
    def __init__(self):
        self.active = False
        self.timer = 0
        self.duration = 3.0
        self.particles = []
        self.glow_intensity = 0
        self.complete = False
        self.source_x = 0
        self.source_y = 0
    
    def start(self, source_x, source_y, target_x, target_y):
        self.active = True
        self.timer = 0
        self.complete = False
        self.source_x = source_x
        self.source_y = source_y
        self.glow_intensity = 0
        
        for _ in range(60):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(50, 150)
            self.particles.append({
                'x': source_x + math.cos(angle) * dist,
                'y': source_y + math.sin(angle) * dist,
                'size': random.uniform(8, 20),
                'speed': random.uniform(150, 280),
                'color': random.choice([
                    (255, 200, 80), (255, 150, 50), (255, 100, 30), (255, 220, 120)
                ]),
                'absorbed': False
            })
    
    def update(self, dt, target_x, target_y):
        if not self.active:
            return
        
        self.timer += dt
        absorbed = 0
        
        for p in self.particles:
            if p['absorbed']:
                absorbed += 1
                continue
            
            dx = target_x - p['x']
            dy = target_y - p['y']
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < 30:
                p['absorbed'] = True
                absorbed += 1
                self.glow_intensity = min(255, self.glow_intensity + 15)
            else:
                speed = p['speed'] * (1 + self.timer * 0.7)
                p['x'] += (dx / dist) * speed * dt
                p['y'] += (dy / dist) * speed * dt
                p['size'] *= 0.995
        
        if absorbed >= len(self.particles) * 0.9:
            self.complete = True
        
        if self.complete:
            self.glow_intensity = max(0, self.glow_intensity - 120 * dt)
            if self.glow_intensity <= 0:
                self.active = False
    
    def draw(self, surface, offset_x, offset_y, char_x, char_y):
        if not self.active:
            return
        
        for p in self.particles:
            if p['absorbed']:
                continue
            px = p['x'] + offset_x
            py = p['y'] + offset_y
            size = max(2, int(p['size']))
            ps = pygame.Surface((size*3, size*3), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p['color'], 180), (size*3//2, size*3//2), size)
            pygame.draw.circle(ps, (255, 255, 200, 220), (size*3//2, size*3//2), size//2)
            surface.blit(ps, (px - size*3//2, py - size*3//2))
        
        if self.glow_intensity > 0:
            cx = char_x + offset_x
            cy = char_y + offset_y
            pulse = (math.sin(self.timer * 10) + 1) / 2
            glow_size = 60 + pulse * 30
            glow = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
            for r in range(int(glow_size), 10, -5):
                alpha = int(self.glow_intensity * (1 - r/glow_size) * 0.6)
                pygame.draw.circle(glow, (255, 180, 80, alpha), (int(glow_size), int(glow_size)), r)
            surface.blit(glow, (cx - glow_size, cy - glow_size - 15))


class PaintingRoomPuzzle:
    """画作房谜题主类"""
    def __init__(self, screen=None):
        pygame.init()
        pygame.mixer.init()
        
        if screen is not None:
            self.screen = screen
            self.owns_screen = False
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.owns_screen = True
        
        pygame.display.set_caption("Dream Diary - Painting Room")
        self.clock = pygame.time.Clock()
        
        # 计算居中偏移
        self.map_pixel_width = MAP_WIDTH * TILE_SIZE
        self.map_pixel_height = MAP_HEIGHT * TILE_SIZE
        self.offset_x = (SCREEN_WIDTH - self.map_pixel_width) // 2
        self.offset_y = (SCREEN_HEIGHT - self.map_pixel_height) // 2
        
        self._generate_map()
        
        sprite_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "8Direction_TopDown_Character Sprites_ByBossNelNel", "SpriteSheet.png"
        )
        
        spawn_x = 13 * TILE_SIZE + TILE_SIZE // 2
        spawn_y = 14 * TILE_SIZE + TILE_SIZE // 2
        self.character = Character(sprite_path, spawn_x, spawn_y)
        
        self.dialogue = DialogueBox(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.dream_effect = DreamEffect(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        self._create_fragments_and_canvas()
        
        self.game_complete = False
        self.burning_started = False
        self.burn_delay_timer = 0
        
        self.dialogue.show("Welcome to the Painting Room...\nCollect 6 fragments of the shattered masterpiece.")
    
    def _generate_map(self):
        self.collision_map = []
        
        for y in range(MAP_HEIGHT):
            row = []
            for x in range(MAP_WIDTH):
                if x <= 1 or x >= MAP_WIDTH-2 or y <= 1 or y >= MAP_HEIGHT-2:
                    row.append(1)
                else:
                    row.append(0)
            self.collision_map.append(row)
        
        # 装饰柱子
        pillars = [(6, 5), (19, 5), (6, 12), (19, 12)]
        for px, py in pillars:
            if 0 <= py < MAP_HEIGHT and 0 <= px < MAP_WIDTH:
                self.collision_map[py][px] = 1
        
        # 渲染地图
        self.map_surface = pygame.Surface((self.map_pixel_width, self.map_pixel_height))
        self.map_surface.fill(COLOR_DREAM)
        
        # 渐变地板
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if self.collision_map[y][x] == 1:
                    # 墙壁渐变
                    wall_base = 45 + int(10 * math.sin(x * 0.3 + y * 0.2))
                    pygame.draw.rect(self.map_surface, (wall_base + 15, wall_base, wall_base + 20), rect)
                    pygame.draw.rect(self.map_surface, (wall_base + 5, wall_base - 5, wall_base + 10), rect, 1)
                    # 墙壁纹理
                    if (x + y) % 3 == 0:
                        pygame.draw.line(self.map_surface, (wall_base + 25, wall_base + 10, wall_base + 30),
                                       (x * TILE_SIZE + 8, y * TILE_SIZE + 8),
                                       (x * TILE_SIZE + 24, y * TILE_SIZE + 24), 1)
                else:
                    # 地板棋盘格渐变
                    dist_center = math.sqrt((x - MAP_WIDTH/2)**2 + (y - MAP_HEIGHT/2)**2)
                    darken = min(15, int(dist_center * 0.8))
                    if (x + y) % 2 == 0:
                        color = (38 - darken, 28 - darken, 50 - darken)
                    else:
                        color = (32 - darken, 22 - darken, 44 - darken)
                    pygame.draw.rect(self.map_surface, color, rect)
                    
                    # 地板装饰线
                    if x % 4 == 0 and y % 4 == 0:
                        pygame.draw.circle(self.map_surface, (45, 35, 60),
                                         (x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2), 3)
        
        # 绘制装饰柱子
        for px, py in pillars:
            if 0 <= py < MAP_HEIGHT and 0 <= px < MAP_WIDTH:
                rect = pygame.Rect(px * TILE_SIZE, py * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                # 柱子底座
                pygame.draw.rect(self.map_surface, (50, 35, 60), (px * TILE_SIZE - 2, py * TILE_SIZE - 2, TILE_SIZE + 4, TILE_SIZE + 4))
                # 柱子主体
                pygame.draw.rect(self.map_surface, (75, 55, 90), rect)
                pygame.draw.rect(self.map_surface, (95, 75, 110), rect, 2)
                # 柱子高光
                pygame.draw.line(self.map_surface, (110, 90, 130),
                               (px * TILE_SIZE + 4, py * TILE_SIZE + 4),
                               (px * TILE_SIZE + 4, py * TILE_SIZE + TILE_SIZE - 4), 2)
                # 柱子顶部装饰
                pygame.draw.rect(self.map_surface, (100, 80, 120),
                               (px * TILE_SIZE + 4, py * TILE_SIZE + 2, TILE_SIZE - 8, 4))
    
    def _create_fragments_and_canvas(self):
        # 6个碎片的配色方案 (基色, 强调色, 高光色)
        color_schemes = [
            ((255, 100, 120), (200, 50, 70), (255, 200, 210)),    # 红
            ((100, 255, 130), (50, 200, 80), (200, 255, 220)),    # 绿
            ((100, 130, 255), (50, 80, 200), (200, 210, 255)),    # 蓝
            ((255, 220, 100), (220, 180, 50), (255, 250, 200)),   # 金
            ((220, 130, 255), (180, 80, 220), (240, 200, 255)),   # 紫
            ((130, 255, 255), (80, 220, 220), (200, 255, 255)),   # 青
        ]
        
        # 6个碎片位置 (分布在房间各处)
        positions = [
            (4 * TILE_SIZE, 4 * TILE_SIZE),       # 左上
            (21 * TILE_SIZE, 4 * TILE_SIZE),      # 右上
            (4 * TILE_SIZE, 13 * TILE_SIZE),      # 左下
            (21 * TILE_SIZE, 13 * TILE_SIZE),     # 右下
            (12 * TILE_SIZE, 4 * TILE_SIZE),      # 上中
            (12 * TILE_SIZE, 13 * TILE_SIZE),     # 下中
        ]
        
        self.fragments = []
        for i, (pos, colors) in enumerate(zip(positions, color_schemes)):
            frag = PaintingFragment(pos[0], pos[1], i, colors)
            self.fragments.append(frag)
        
        # 画布居中
        self.canvas = PaintingCanvas(13 * TILE_SIZE - 75, 7 * TILE_SIZE)
        self.burning_effect = BurningEffect(self.canvas.x, self.canvas.y, 150, 100)
        self.absorption_effect = AbsorptionEffect()
        self.flying_fragments = []
    
    def check_collision(self, x, y, w, h):
        left = int(x // TILE_SIZE)
        right = int((x + w) // TILE_SIZE)
        top = int(y // TILE_SIZE)
        bottom = int((y + h) // TILE_SIZE)
        
        for ty in range(max(0, top), min(MAP_HEIGHT, bottom + 1)):
            for tx in range(max(0, left), min(MAP_WIDTH, right + 1)):
                if self.collision_map[ty][tx] == 1:
                    return True
        return False
    
    def run(self):
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        if self.dialogue.active:
                            self.dialogue.skip()
                        else:
                            self._try_collect()
                    elif event.key == pygame.K_c:
                        if not self.dialogue.active:
                            self._try_collect()
            
            if not self.dialogue.active and not self.absorption_effect.active:
                keys = pygame.key.get_pressed()
                dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
                dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
                self.character.update(dt, dx, dy, self.check_collision)
            
            self.dialogue.update(dt)
            self.dream_effect.update(dt)
            self.canvas.update(dt)
            for frag in self.fragments:
                frag.update(dt)
            
            self._update_flying_fragments(dt)
            
            # 燃烧延迟
            if self.burning_started and not self.burning_effect.active and not self.burning_effect.complete:
                self.burn_delay_timer += dt
                if self.burn_delay_timer >= 1.5:
                    self.burning_effect.start()
                    self.dream_effect.shake(1.5, 12)
            
            if self.burning_effect.active:
                self.burning_effect.update(dt)
                if self.burning_effect.complete and not self.absorption_effect.active:
                    self.absorption_effect.start(
                        self.canvas.x + 75, self.canvas.y + 50,
                        self.character.x, self.character.y
                    )
            
            if self.absorption_effect.active:
                self.absorption_effect.update(dt, self.character.x, self.character.y)
                if self.absorption_effect.complete and not self.game_complete:
                    self.game_complete = True
                    self.dialogue.show("The flames of creation flow into your soul...\n\n[FIRE SOUL] acquired!")
            
            self._render()
            pygame.display.flip()
        
        if self.owns_screen:
            pygame.quit()
        
        return self.game_complete
    
    def _try_collect(self):
        if self.burning_effect.active or self.absorption_effect.active:
            return
        
        for frag in self.fragments:
            if not frag.collected and frag.is_near(self.character.x, self.character.y):
                frag.collected = True
                self.dream_effect.flash((255, 200, 100), 120)
                
                self.flying_fragments.append({
                    'surface': frag.surface.copy(),
                    'x': frag.x,
                    'y': frag.y,
                    'start_x': frag.x,
                    'start_y': frag.y,
                    'target_x': self.canvas.x + 75,
                    'target_y': self.canvas.y + 50,
                    'fragment_id': frag.fragment_id,
                    'timer': 0,
                    'duration': 0.9
                })
                return
    
    def _update_flying_fragments(self, dt):
        for flying in self.flying_fragments[:]:
            flying['timer'] += dt
            t = min(1.0, flying['timer'] / flying['duration'])
            ease = t * t * (3 - 2 * t)
            
            flying['x'] = flying['start_x'] + (flying['target_x'] - flying['start_x']) * ease
            flying['y'] = flying['start_y'] + (flying['target_y'] - flying['start_y']) * ease
            
            if t >= 1.0:
                self.canvas.add_fragment(flying['fragment_id'])
                self.flying_fragments.remove(flying)
                
                if self.canvas.completed and not self.burning_started:
                    self.burning_started = True
                    self.burn_delay_timer = 0
                    self.dialogue.show("The painting is complete!\nIt begins to burn with an otherworldly fire...")
    
    def _render(self):
        shake_x, shake_y = self.dream_effect.get_shake_offset()
        
        # 计算总偏移 (居中 + 震动)
        total_offset_x = self.offset_x + shake_x
        total_offset_y = self.offset_y + shake_y
        
        # 绘制背景
        self.screen.fill((12, 8, 20))
        
        # 背景装饰光晕
        bg_glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        for r in range(300, 50, -20):
            alpha = max(0, 15 - r // 25)
            pygame.draw.circle(bg_glow, (40, 25, 60, alpha), (center_x, center_y), r)
        self.screen.blit(bg_glow, (0, 0))
        
        # 地图居中绘制
        self.screen.blit(self.map_surface, (total_offset_x, total_offset_y))
        
        if not self.burning_effect.complete:
            frag_surfs = [f.surface for f in self.fragments]
            self.canvas.draw(self.screen, total_offset_x, total_offset_y, frag_surfs)
        
        for frag in self.fragments:
            frag.draw(self.screen, total_offset_x, total_offset_y)
        
        for flying in self.flying_fragments:
            fx = flying['x'] + total_offset_x
            fy = flying['y'] + total_offset_y
            t = flying['timer'] / flying['duration']
            scale = 1.0 - t * 0.3
            # 飞行轨迹光效
            trail_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*flying['surface'].get_at((28, 28))[:3], 100), (10, 10), 8)
            self.screen.blit(trail_surf, (fx - 10, fy - 10))
            # 碎片本体
            scaled = pygame.transform.scale(flying['surface'], (int(56*scale), int(56*scale)))
            rot_angle = t * 360
            rotated = pygame.transform.rotate(scaled, rot_angle)
            rect = rotated.get_rect(center=(fx, fy))
            self.screen.blit(rotated, rect)
        
        self.burning_effect.draw(self.screen, total_offset_x, total_offset_y)
        self.character.draw(self.screen, total_offset_x, total_offset_y)
        self.absorption_effect.draw(self.screen, total_offset_x, total_offset_y, self.character.x, self.character.y)
        
        if not self.dialogue.active and not self.burning_effect.active:
            for frag in self.fragments:
                if not frag.collected and frag.is_near(self.character.x, self.character.y, 60):
                    try:
                        font = pygame.font.Font(FONT_PATH, 18)
                    except:
                        font = pygame.font.Font(None, 18)
                    hint = font.render("Press SPACE to collect", True, (255, 220, 150))
                    hx = frag.x + total_offset_x - hint.get_width() // 2
                    hy = frag.y + total_offset_y - 60
                    bg = pygame.Surface((hint.get_width() + 14, hint.get_height() + 8), pygame.SRCALPHA)
                    bg.fill((0, 0, 0, 180))
                    pygame.draw.rect(bg, (100, 80, 60), (0, 0, bg.get_width(), bg.get_height()), 1)
                    self.screen.blit(bg, (hx - 7, hy - 4))
                    self.screen.blit(hint, (hx, hy))
        
        self.dream_effect.draw(self.screen)
        
        try:
            font = pygame.font.Font(FONT_PATH, 24)
            small = pygame.font.Font(FONT_PATH, 18)
        except:
            font = pygame.font.Font(None, 24)
            small = pygame.font.Font(None, 18)
        
        title = font.render("~ The Painting Room ~", True, (180, 140, 100))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 15))
        
        collected, total = self.canvas.get_progress()
        progress = small.render(f"Fragments: {collected}/{total}", True, (160, 140, 120))
        self.screen.blit(progress, (20, 20))
        
        if self.game_complete:
            status = font.render("[FIRE SOUL] Absorbed", True, (255, 180, 80))
            self.screen.blit(status, (SCREEN_WIDTH//2 - status.get_width()//2, SCREEN_HEIGHT - 50))
        
        self.dialogue.draw(self.screen)


def run_painting_room(screen=None):
    game = PaintingRoomPuzzle(screen)
    return game.run()


if __name__ == "__main__":
    result = run_painting_room()
    print(f"Game completed: {result}")
