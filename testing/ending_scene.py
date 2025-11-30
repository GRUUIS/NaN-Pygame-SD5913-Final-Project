"""
结局场景 - 黎明觉醒
Ending Scene - Dawn Awakening

使用 new_third_puzzle.py 的地图和角色系统
小女孩从床上醒来，窗外阳光明媚，一切都是新的开始。
"""

import pygame
import sys
import os
import math
import random
from pathlib import Path

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tiled_loader import load_map, draw_map

# --------------------------
# 配置
# --------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# 资源路径
ASSETS_PATH = Path("assets")
MAP_PATH = ASSETS_PATH / "tilemaps" / "test puzzle scene.tmj"
FONT_PATH = ASSETS_PATH / "Silver.ttf"

# 角色精灵路径
GIRL_SPRITE_PATH = ASSETS_PATH / "8Direction_TopDown_Character Sprites_ByBossNelNel" / "SpriteSheet.png"
GIRL_FRAME_WIDTH = 23
GIRL_FRAME_HEIGHT = 36
GIRL_SCALE = 2.0  # 稍微放大一点
GIRL_ANIMATION_SPEED = 0.1

# 8方向映射
DIRECTION_TO_ROW = {
    'down': 0, 'down_right': 1, 'right': 2, 'up_right': 3,
    'up': 4, 'up_left': 5, 'left': 6, 'down_left': 7
}

# 结算文本
ENDING_TEXT = """When you open your eyes, sunlight has already crept onto the windowsill.

As if nothing had ever happened.

You walk to the mirror.

The reflection smiles back, calm and steady.

It's you—

the you who has finally stepped out of the dark.

Outside, a bird begins to sing.

And in that moment, you understand:

Dawn does not mean the end.

It is only—

a new beginning."""


class Character:
    """8方向角色类"""
    def __init__(self, x: float, y: float, scale: float = 1.0):
        self.x = x
        self.y = y
        self.map_scale = scale  # 地图缩放
        self.speed = 100.0
        self.direction = 'down'
        self.is_moving = False
        self.frame_index = 0
        self.animation_timer = 0.0
        self.frames = self._load_frames()
        
    def _load_frames(self):
        """加载8方向动画帧"""
        frames = {}
        try:
            sprite_sheet = pygame.image.load(str(GIRL_SPRITE_PATH)).convert_alpha()
            
            directions = ['down', 'down_right', 'right', 'up_right', 'up', 'up_left', 'left', 'down_left']
            row_height = 36
            
            for row, direction in enumerate(directions):
                frames[direction] = []
                for col in range(9):  # 9列：idle + 8 walk
                    x = col * GIRL_FRAME_WIDTH
                    y = row * row_height
                    
                    if x + GIRL_FRAME_WIDTH <= sprite_sheet.get_width() and y + GIRL_FRAME_HEIGHT <= sprite_sheet.get_height():
                        frame = sprite_sheet.subsurface(pygame.Rect(x, y, GIRL_FRAME_WIDTH, GIRL_FRAME_HEIGHT))
                        scaled_w = int(GIRL_FRAME_WIDTH * GIRL_SCALE)
                        scaled_h = int(GIRL_FRAME_HEIGHT * GIRL_SCALE)
                        scaled = pygame.transform.scale(frame, (scaled_w, scaled_h))
                        frames[direction].append(scaled)
                
                if not frames[direction]:
                    placeholder = pygame.Surface((int(GIRL_FRAME_WIDTH * GIRL_SCALE), 
                                                 int(GIRL_FRAME_HEIGHT * GIRL_SCALE)), pygame.SRCALPHA)
                    pygame.draw.circle(placeholder, (255, 200, 150), 
                                     (int(GIRL_FRAME_WIDTH * GIRL_SCALE // 2), 
                                      int(GIRL_FRAME_HEIGHT * GIRL_SCALE // 2)), 10)
                    frames[direction] = [placeholder]
            
            return frames
        except Exception as e:
            print(f"Warning: Could not load sprite sheet: {e}")
            placeholder = pygame.Surface((int(GIRL_FRAME_WIDTH * GIRL_SCALE), 
                                         int(GIRL_FRAME_HEIGHT * GIRL_SCALE)), pygame.SRCALPHA)
            pygame.draw.circle(placeholder, (255, 200, 150), 
                             (int(GIRL_FRAME_WIDTH * GIRL_SCALE // 2), 
                              int(GIRL_FRAME_HEIGHT * GIRL_SCALE // 2)), 10)
            return {d: [placeholder] for d in ['down', 'down_left', 'left', 'up_left', 'up', 'up_right', 'right', 'down_right']}
    
    def _get_direction_from_input(self, dx, dy):
        """根据输入获取8方向"""
        if dx == 0 and dy == 0:
            return self.direction
        
        if dx > 0 and dy > 0:
            return 'down_right'
        elif dx < 0 and dy > 0:
            return 'down_left'
        elif dx > 0 and dy < 0:
            return 'up_right'
        elif dx < 0 and dy < 0:
            return 'up_left'
        elif dx > 0:
            return 'right'
        elif dx < 0:
            return 'left'
        elif dy > 0:
            return 'down'
        else:
            return 'up'
    
    def update(self, dt: float, dx: float = 0, dy: float = 0, collision_check=None):
        if dx != 0 or dy != 0:
            self.is_moving = True
            self.direction = self._get_direction_from_input(dx, dy)
            
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071
            
            new_x = self.x + dx * self.speed * dt
            new_y = self.y + dy * self.speed * dt
            
            if collision_check:
                if not collision_check(new_x, self.y):
                    self.x = new_x
                if not collision_check(self.x, new_y):
                    self.y = new_y
            else:
                self.x = new_x
                self.y = new_y
            
            # 更新动画
            self.animation_timer += dt
            if self.animation_timer >= GIRL_ANIMATION_SPEED:
                self.animation_timer = 0
                frames = self.frames.get(self.direction, [])
                if len(frames) > 1:
                    self.frame_index = ((self.frame_index) % (len(frames) - 1)) + 1
        else:
            self.is_moving = False
            self.frame_index = 0  # idle帧
    
    def draw(self, screen: pygame.Surface, offset_x: float, offset_y: float, camera_x: float = 0):
        frames = self.frames.get(self.direction, [])
        if frames:
            idx = min(self.frame_index, len(frames) - 1)
            sprite = frames[idx]
            
            # 计算屏幕位置
            screen_x = int(self.x * self.map_scale) + offset_x - int(camera_x)
            screen_y = int(self.y * self.map_scale) + offset_y
            
            # 居中绘制
            draw_x = screen_x - sprite.get_width() // 2 + 32  # 偏移到瓦片中心
            draw_y = screen_y - sprite.get_height() // 2 + 32
            
            screen.blit(sprite, (draw_x, draw_y))


class SunlightEffect:
    """阳光效果 - 覆盖整个场景"""
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.time = 0
        self.particles = []
        
        # 创建飘浮的尘埃粒子
        for _ in range(40):
            self.particles.append({
                'x': random.randint(0, screen_width),
                'y': random.randint(0, screen_height),
                'size': random.uniform(1, 3),
                'speed_x': random.uniform(-0.3, 0.3),
                'speed_y': random.uniform(-0.2, 0.2),
                'alpha': random.randint(80, 180),
                'phase': random.uniform(0, math.pi * 2)
            })
    
    def update(self, dt):
        self.time += dt
        
        for p in self.particles:
            p['x'] += p['speed_x'] + math.sin(self.time + p['phase']) * 0.5
            p['y'] += p['speed_y'] + math.cos(self.time * 0.5 + p['phase']) * 0.3
            
            if p['x'] < 0:
                p['x'] = self.width
            elif p['x'] > self.width:
                p['x'] = 0
            if p['y'] < 0:
                p['y'] = self.height
            elif p['y'] > self.height:
                p['y'] = 0
    
    def draw(self, screen, intensity=1.0):
        # 温暖的阳光色调覆盖
        warm_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        warm_alpha = int(30 * intensity)
        warm_overlay.fill((255, 240, 200, warm_alpha))
        screen.blit(warm_overlay, (0, 0))
        
        # 光线从右上角照入
        ray_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for i in range(5):
            angle = math.radians(-30 + i * 10 + math.sin(self.time * 0.5) * 3)
            start_x = self.width - 100
            start_y = 50 + i * 30
            length = 1000
            
            end_x = start_x + math.cos(angle) * length
            end_y = start_y + math.sin(angle) * length
            
            for w in range(80, 0, -10):
                alpha = int(15 * intensity * (w / 80))
                pygame.draw.line(ray_surface, (255, 250, 220, alpha),
                               (start_x, start_y), (end_x, end_y), w)
        
        screen.blit(ray_surface, (0, 0))
        
        # 绘制尘埃粒子
        for p in self.particles:
            glow_alpha = int(p['alpha'] * intensity * (0.7 + 0.3 * math.sin(self.time * 2 + p['phase'])))
            glow_surf = pygame.Surface((int(p['size'] * 4), int(p['size'] * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 220, glow_alpha), 
                             (int(p['size'] * 2), int(p['size'] * 2)), int(p['size']))
            screen.blit(glow_surf, (p['x'] - p['size'] * 2, p['y'] - p['size'] * 2))


class TextDisplay:
    """文字显示效果"""
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.lines = ENDING_TEXT.strip().split('\n')
        self.current_line = 0
        self.char_index = 0
        self.displayed_text = []
        self.timer = 0
        self.char_delay = 0.04
        self.line_delay = 0.6
        self.waiting = False
        self.wait_timer = 0
        self.complete = False
        self.fade_alpha = 0
        self.show_final = False
        self.started = False
        
        try:
            self.font = pygame.font.Font(str(FONT_PATH), 28)
            self.title_font = pygame.font.Font(str(FONT_PATH), 48)
            self.hint_font = pygame.font.Font(str(FONT_PATH), 20)
        except:
            self.font = pygame.font.Font(None, 28)
            self.title_font = pygame.font.Font(None, 48)
            self.hint_font = pygame.font.Font(None, 20)
    
    def start(self):
        self.started = True
    
    def update(self, dt):
        if not self.started:
            return
            
        if self.complete:
            if self.show_final:
                self.fade_alpha = min(255, self.fade_alpha + dt * 100)
            return
            
        if self.waiting:
            self.wait_timer += dt
            if self.wait_timer >= self.line_delay:
                self.waiting = False
                self.wait_timer = 0
            return
        
        self.timer += dt
        if self.timer >= self.char_delay:
            self.timer = 0
            
            if self.current_line < len(self.lines):
                line = self.lines[self.current_line]
                
                if self.char_index < len(line):
                    self.char_index += 1
                    
                    if len(self.displayed_text) <= self.current_line:
                        self.displayed_text.append('')
                    self.displayed_text[self.current_line] = line[:self.char_index]
                else:
                    self.current_line += 1
                    self.char_index = 0
                    self.waiting = True
            else:
                self.complete = True
    
    def show_final_message(self):
        self.show_final = True
    
    def draw(self, screen):
        if not self.started:
            return
            
        # 半透明背景
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))
        
        # 绘制文字
        y_offset = 60
        line_height = 36
        
        for i, line in enumerate(self.displayed_text):
            if line.strip():
                if "a new beginning" in line.lower():
                    color = (255, 220, 150)
                elif "dawn" in line.lower():
                    color = (255, 200, 100)
                elif "it's you" in line.lower():
                    color = (255, 230, 180)
                else:
                    color = (255, 255, 255)
                
                text_surface = self.font.render(line, True, color)
                x = (self.width - text_surface.get_width()) // 2
                screen.blit(text_surface, (x, y_offset + i * line_height))
        
        # 最终标题
        if self.show_final and self.fade_alpha > 0:
            title = self.title_font.render("~ THE END ~", True, (255, 220, 150))
            title.set_alpha(int(self.fade_alpha))
            screen.blit(title, ((self.width - title.get_width()) // 2, self.height - 120))
            
            subtitle = self.font.render("Thank you for playing", True, (200, 200, 200))
            subtitle.set_alpha(int(self.fade_alpha))
            screen.blit(subtitle, ((self.width - subtitle.get_width()) // 2, self.height - 70))
            
            hint = self.hint_font.render("Press SPACE to continue...", True, (150, 150, 150))
            hint.set_alpha(int(self.fade_alpha))
            screen.blit(hint, ((self.width - hint.get_width()) // 2, self.height - 30))


class EndingScene:
    """结局场景主类"""
    def __init__(self, screen=None):
        pygame.init()
        try:
            pygame.mixer.init()
        except:
            pass
        
        if screen is not None:
            self.screen = screen
            self.owns_screen = False
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.owns_screen = True
        
        pygame.display.set_caption("Dream Diary - Dawn")
        self.clock = pygame.time.Clock()
        
        # 加载地图
        self._load_map()
        
        # 创建角色（在床边位置）
        spawn_x = 16 * self.tile_size  # 床旁边
        spawn_y = 15 * self.tile_size
        self.character = Character(spawn_x, spawn_y, self.scale)
        
        # 特效
        self.sunlight = SunlightEffect(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.text_display = TextDisplay(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 状态
        self.phase = 'exploring'  # exploring, text, end
        self.phase_timer = 0
        self.sunlight_intensity = 0.3
        self.fade_in = 0
        self.ending_complete = False
        self.can_move = True
        
        # 相机
        self.camera_x = 0
        self.max_scroll = max(0, self.target_w - SCREEN_WIDTH)
        
        # 字体
        try:
            self.font = pygame.font.Font(str(FONT_PATH), 24)
        except:
            self.font = pygame.font.Font(None, 24)
    
    def _load_map(self):
        """加载TMJ地图"""
        try:
            self.m, self.tiles_by_gid, self.tileset_meta = load_map(str(MAP_PATH))
            self.tile_size = self.m.get('tilewidth', 32)
        except Exception as e:
            print(f"地图加载失败：{e}")
            # 创建空白地图
            self.m = {'width': 20, 'height': 15, 'tilewidth': 32, 'tileheight': 32, 'layers': []}
            self.tiles_by_gid = {}
            self.tileset_meta = {}
            self.tile_size = 32
        
        # 计算缩放
        map_pixel_w = self.m.get('width', 0) * self.tile_size
        map_pixel_h = self.m.get('height', 0) * self.tile_size
        
        self.tile_draw_size = 64
        self.scale = self.tile_draw_size / float(self.tile_size)
        self.target_w = self.tile_draw_size * self.m.get('width', 0)
        self.target_h = self.tile_draw_size * self.m.get('height', 0)
        
        self.offset_x = (SCREEN_WIDTH - self.target_w) // 2
        self.offset_y = (SCREEN_HEIGHT - self.target_h) // 2
        
        # 构建碰撞信息
        self._build_collision()
    
    def _build_collision(self):
        """构建碰撞数据"""
        self.collision_tiles = []
        
        # 从地图属性中提取碰撞
        tile_props = {}
        for ts in self.m.get('tilesets', []):
            firstgid = ts.get('firstgid', 0)
            for t in ts.get('tiles', []) or []:
                local_id = t.get('id')
                props = {}
                for p in t.get('properties', []) or []:
                    props[p.get('name')] = p.get('value')
                tile_props[firstgid + int(local_id)] = props
        
        width = self.m.get('width', 0)
        
        def is_truthy(v):
            return v in (True, 'true', 'True', 1, '1')
        
        for layer in self.m.get('layers', []):
            if layer.get('type') != 'tilelayer':
                continue
            
            data = layer.get('data', [])
            for idx, raw_gid in enumerate(data):
                gid = raw_gid & 0x1FFFFFFF
                if gid == 0:
                    continue
                
                tx = idx % width
                ty = idx // width
                props = tile_props.get(gid, {})
                
                if is_truthy(props.get('collidable')):
                    self.collision_tiles.append((tx, ty))
        
        # 手动覆盖可通行区域
        OVERRIDE_NON_COLLIDABLE = {(15, 14), (16, 14), (17, 14)}
        self.collision_tiles = [(tx, ty) for tx, ty in self.collision_tiles 
                                if (tx, ty) not in OVERRIDE_NON_COLLIDABLE]
        
        self.blocked_coords = set(self.collision_tiles)
    
    def check_collision(self, new_x, new_y):
        """碰撞检测"""
        # 简化的碰撞检测
        tx = int(new_x // self.tile_size)
        ty = int(new_y // self.tile_size)
        
        # 检查周围的格子
        for ox in range(-1, 2):
            for oy in range(-1, 2):
                if (tx + ox, ty + oy) in self.blocked_coords:
                    # 计算实际碰撞
                    tile_rect = pygame.Rect((tx + ox) * self.tile_size, (ty + oy) * self.tile_size,
                                           self.tile_size, self.tile_size)
                    player_rect = pygame.Rect(new_x + 8, new_y + 8, 16, 16)
                    if player_rect.colliderect(tile_rect):
                        return True
        
        # 检查地图边界
        if new_x < 0 or new_y < 0:
            return True
        if new_x > self.m.get('width', 0) * self.tile_size - 16:
            return True
        if new_y > self.m.get('height', 0) * self.tile_size - 16:
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
                        if self.phase == 'exploring':
                            # 开始结局文字
                            self.phase = 'text'
                            self.can_move = False
                            self.text_display.start()
                        elif self.phase == 'end' and self.text_display.show_final:
                            running = False
            
            self._update(dt)
            self._render()
            pygame.display.flip()
        
        if self.owns_screen:
            pygame.quit()
        
        return True
    
    def _update(self, dt):
        self.phase_timer += dt
        self.fade_in = min(1.0, self.fade_in + dt * 0.5)
        
        # 更新阳光
        self.sunlight.update(dt)
        self.sunlight_intensity = min(1.0, self.sunlight_intensity + dt * 0.05)
        
        # 玩家移动
        if self.can_move:
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            self.character.update(dt, dx, dy, self.check_collision)
        else:
            self.character.update(dt, 0, 0)
        
        # 更新相机
        player_screen_x = int(self.character.x * self.scale) + self.offset_x
        desired_camera_x = self.camera_x
        
        activity_left = SCREEN_WIDTH * 0.3
        activity_right = SCREEN_WIDTH * 0.7
        
        player_rel_x = player_screen_x - self.camera_x
        if player_rel_x < activity_left:
            desired_camera_x = self.camera_x - (activity_left - player_rel_x)
        elif player_rel_x > activity_right:
            desired_camera_x = self.camera_x + (player_rel_x - activity_right)
        
        desired_camera_x = max(0, min(self.max_scroll, desired_camera_x))
        self.camera_x += (desired_camera_x - self.camera_x) * min(1.0, 8.0 * dt)
        
        # 更新文字
        if self.phase == 'text':
            self.text_display.update(dt)
            if self.text_display.complete and not self.ending_complete:
                self.ending_complete = True
                self.phase = 'end'
                self.phase_timer = 0
        
        elif self.phase == 'end':
            self.text_display.update(dt)
            if self.phase_timer > 1.5:
                self.text_display.show_final_message()
    
    def _render(self):
        # 黑色背景
        self.screen.fill((0, 0, 0))
        
        # 绘制地图背景
        try:
            off_surface = pygame.Surface((self.target_w, self.target_h), pygame.SRCALPHA)
            draw_map(off_surface, self.m, self.tiles_by_gid, scale=self.scale)
            self.screen.blit(off_surface, (self.offset_x - int(self.camera_x), self.offset_y))
        except Exception as e:
            pass
        
        # 绘制角色
        self.character.draw(self.screen, self.offset_x, self.offset_y, self.camera_x)
        
        # 绘制阳光效果
        self.sunlight.draw(self.screen, self.sunlight_intensity)
        
        # 淡入效果
        if self.fade_in < 1.0:
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(int(255 * (1.0 - self.fade_in)))
            self.screen.blit(fade_surface, (0, 0))
        
        # 探索阶段的提示
        if self.phase == 'exploring':
            hint = self.font.render("Press SPACE when ready to see the ending...", True, (200, 200, 200))
            hint_bg = pygame.Surface((hint.get_width() + 20, hint.get_height() + 10), pygame.SRCALPHA)
            hint_bg.fill((0, 0, 0, 150))
            self.screen.blit(hint_bg, (SCREEN_WIDTH // 2 - hint.get_width() // 2 - 10, SCREEN_HEIGHT - 50))
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 45))
        
        # 绘制文字显示
        if self.phase in ('text', 'end'):
            self.text_display.draw(self.screen)


def run_ending_scene(screen=None):
    """运行结局场景"""
    scene = EndingScene(screen)
    return scene.run()


if __name__ == "__main__":
    result = run_ending_scene()
    print(f"Ending complete: {result}")
