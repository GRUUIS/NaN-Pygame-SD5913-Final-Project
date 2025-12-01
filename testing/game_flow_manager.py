"""
游戏流程管理器
整合游戏的多个场景：初始菜单 -> 解谜场景 -> 梦境解谜 -> 梦境过渡 -> Boss1剧情战 -> Map01探索 -> 镜子房间 -> Boss2 -> 画作房 -> Boss3

场景流程：
1. combine/game.py 的菜单界面（初始界面）
2. testing/new_third_puzzle.py 的解谜场景
3. testing/first_dream_puzzle.py 的梦境解谜场景（4个谜题）
4. testing/dream_transition_scene.py 的梦境过渡场景（主角转换为小女巫）
5. src/scenes/boss1_scripted_scene.py 的 Boss1 剧情战斗场景（玩家被秒杀）
6. testing/map01_final.py 的 Map01 探索场景
7. testing/mirror_room_puzzle.py 的镜子房间谜题
8. src/entities/sloth_battle_scene.py 的 Boss2 战斗场景 (The Sloth)
9. testing/painting_room_puzzle.py 的画作房谜题
10. src/entities/boss_battle_scene.py 的 Boss3 战斗场景 (The Hollow - 最终BOSS)

按 Z 键可以跳过任何关卡。
在解谜场景中，玩家走到门前（坐标 21,12 和 21,13）右键点击可跳转到梦境场景。
"""

import pygame
import sys
from pathlib import Path
import os

# 确保项目根目录在 sys.path 中
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import globals as g
from combine.meun import Meun


def run_puzzle_scene(screen):
    """
    运行解谜场景（基于 new_third_puzzle.py 的逻辑）
    返回：'next' 表示完成解谜并触发门，'quit' 表示退出游戏
    """
    from src.tiled_loader import load_map, draw_map
    import xml.etree.ElementTree as ET
    import random
    
    # 屏幕设置
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # 资源路径
    ASSETS_PATH = Path("assets")
    MAP_PATH = ASSETS_PATH / "tilemaps" / "test puzzle scene.tmj"
    FONT_PATH = ASSETS_PATH / "Silver.ttf"
    
    # 加载 TMJ
    try:
        m, tiles_by_gid, tileset_meta = load_map(str(MAP_PATH))
        TILE_SIZE = m.get('tilewidth', 32)
    except Exception as e:
        print(f"地图加载失败：{e}")
        return 'quit'
    
    # 计算缩放
    map_pixel_w = m.get('width', 0) * TILE_SIZE
    map_pixel_h = m.get('height', 0) * TILE_SIZE
    tile_draw_size = 64
    scale = tile_draw_size / float(TILE_SIZE)
    target_w = tile_draw_size * m.get('width', 0)
    target_h = tile_draw_size * m.get('height', 0)
    offset_x = (SCREEN_WIDTH - target_w) // 2
    offset_y = (SCREEN_HEIGHT - target_h) // 2
    
    # 加载字体
    try:
        game_font = pygame.font.Font(str(FONT_PATH), 16)
    except Exception:
        game_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 16)
    
    # 构建 tile 属性映射
    tile_props = {}
    for ts in m.get('tilesets', []):
        firstgid = ts.get('firstgid', 0)
        for t in ts.get('tiles', []) or []:
            local_id = t.get('id')
            props = {}
            for p in t.get('properties', []) or []:
                props[p.get('name')] = p.get('value')
            tile_props[firstgid + int(local_id)] = props
    
    # 解析 TSX 文件中的属性
    for fg, meta in (tileset_meta or {}).items():
        tsx_path = meta.get('tsx_path')
        if tsx_path and os.path.exists(tsx_path):
            try:
                tree = ET.parse(tsx_path)
                root = tree.getroot()
                for tile in root.findall('tile'):
                    tid = int(tile.attrib.get('id', 0))
                    props = {}
                    props_elem = tile.find('properties')
                    if props_elem is not None:
                        for prop in props_elem.findall('property'):
                            name = prop.attrib.get('name')
                            val = prop.attrib.get('value')
                            if val is None:
                                val = prop.text
                            props[name] = val
                    if props:
                        tile_props[fg + tid] = {**tile_props.get(fg + tid, {}), **props}
            except Exception:
                pass
    
    width = m.get('width', 0)
    
    def is_truthy(v):
        return v in (True, 'true', 'True', 1, '1')
    
    # 构建碰撞和交互对象
    background_layers = []
    foreground_layer = None
    interactive_objects = []
    collision_tiles = []
    door_objects = []  # 门的特殊交互对象
    
    collidable_gids = {gid for gid, props in tile_props.items() if is_truthy(props.get('collidable'))}
    
    for layer in m.get('layers', []):
        if layer.get('type') != 'tilelayer':
            continue
        lname = (layer.get('name') or '')
        if lname == 'foreground_furniture':
            foreground_layer = layer
        else:
            background_layers.append(layer)
        
        data = layer.get('data', [])
        layer_off_x = int(layer.get('offsetx', 0) or 0)
        layer_off_y = int(layer.get('offsety', 0) or 0)
        
        for idx, raw_gid in enumerate(data):
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0:
                continue
            tx = idx % width
            ty = idx // width
            props = tile_props.get(gid, {})
            
            # 检查是否是门的位置（21,12 或 21,13）
            if lname == 'door' and (tx, ty) in [(21, 12), (21, 13)]:
                door_objects.append({
                    'rect': pygame.Rect(tx * TILE_SIZE + layer_off_x, ty * TILE_SIZE + layer_off_y, TILE_SIZE, TILE_SIZE),
                    'tx': tx,
                    'ty': ty,
                    'name': 'exit_door'
                })
            
            if is_truthy(props.get('interactive')):
                interactive_objects.append({
                    'rect': pygame.Rect(tx * TILE_SIZE + layer_off_x, ty * TILE_SIZE + layer_off_y, TILE_SIZE, TILE_SIZE),
                    'prompt': props.get('prompt', 'check'),
                    'sound_path': props.get('click_sound'),
                    'name': props.get('name', 'unknown'),
                    'type': props.get('type', '')
                })
            
            if is_truthy(props.get('collidable')):
                collision_tiles.append((tx, ty, pygame.Rect(tx * TILE_SIZE + layer_off_x, ty * TILE_SIZE + layer_off_y, TILE_SIZE, TILE_SIZE)))
    
    # 手动覆盖：特定格子设为不可碰撞（包括门的下半部分位置）
    OVERRIDE_NON_COLLIDABLE = {(15, 14), (16, 14), (17, 14), (21, 13)}
    if collision_tiles:
        filtered = []
        for tx, ty, rect in collision_tiles:
            if (tx, ty) in OVERRIDE_NON_COLLIDABLE:
                continue
            filtered.append((tx, ty, rect))
        collision_tiles = filtered
    
    blocked_coords = {(tx, ty) for tx, ty, _r in collision_tiles}
    
    # 玩家初始位置
    USER_DEFAULT_SPAWN = (15, 14)
    sx, sy = USER_DEFAULT_SPAWN
    player_x = sx * TILE_SIZE
    player_y = sy * TILE_SIZE
    
    # 玩家参数
    player_speed_pixels = 140
    # 角色精灵是 23×36，瓦片是 32×32
    # 让角色高度约等于瓦片大小，宽度按比例
    player_scale_on_tile = 1.1  # 角色稍微比瓦片高一点（36/32 ≈ 1.125）
    player_map_h = max(1, int(round(TILE_SIZE * player_scale_on_tile)))
    player_map_w = max(1, int(round(player_map_h * (23.0 / 36.0))))  # 保持 23:36 比例
    player_bbox_w = int(player_map_w * 0.7)  # 碰撞盒稍小一些，避免卡墙
    player_bbox_h = int(player_map_h * 0.5)  # 碰撞盒在下半部分
    player_bbox_xoff = (player_map_w - player_bbox_w) // 2
    player_bbox_yoff = player_map_h - player_bbox_h
    
    # 保持精灵宽高比 23:36
    SPRITE_ASPECT = 23.0 / 36.0
    player_draw_h = int(round(player_map_h * scale))
    player_draw_w = int(round(player_draw_h * SPRITE_ASPECT))
    player_draw_xoff = (tile_draw_size - player_draw_w) // 2
    player_draw_yoff = (tile_draw_size - player_draw_h) // 2
    
    # 加载角色精灵图动画系统
    sprite_path = ASSETS_PATH / "8Direction_TopDown_Character Sprites_ByBossNelNel" / "SpriteSheet.png"
    player_animations = {}  # 存储所有方向的动画帧
    SPRITE_W, SPRITE_H = 23, 36
    
    try:
        sprite_sheet = pygame.image.load(str(sprite_path)).convert_alpha()
        # 8个方向：下、左下、左、左上、上、右上、右、右下
        # 精灵图中的行顺序 - 实际上精灵图中是右方向，左方向需要翻转
        directions = ['down', 'down_right', 'right', 'up_right', 'up', 'up_left', 'left', 'down_left']
        
        # 需要翻转的方向映射（左侧方向使用右侧方向的翻转）
        # 精灵图本身包含右方向，左方向需要翻转右方向获得
        flip_mapping = {
            'left': 'right',
            'up_left': 'up_right', 
            'down_left': 'down_right'
        }
        
        # 先加载不需要翻转的方向
        for row, direction in enumerate(directions):
            if direction in flip_mapping:
                continue  # 稍后处理需要翻转的方向
            
            player_animations[direction] = {
                'idle': None,
                'walk': []
            }
            # 第一列是idle
            idle_sprite = sprite_sheet.subsurface(pygame.Rect(0, row * SPRITE_H, SPRITE_W, SPRITE_H))
            player_animations[direction]['idle'] = pygame.transform.scale(idle_sprite, (player_draw_w, player_draw_h))
            
            # 第2-9列是行走动画（8帧）
            for col in range(1, 9):
                walk_sprite = sprite_sheet.subsurface(pygame.Rect(col * SPRITE_W, row * SPRITE_H, SPRITE_W, SPRITE_H))
                scaled_sprite = pygame.transform.scale(walk_sprite, (player_draw_w, player_draw_h))
                player_animations[direction]['walk'].append(scaled_sprite)
        
        # 处理需要翻转的方向（左侧方向通过翻转右侧方向获得）
        for flip_dir, source_dir in flip_mapping.items():
            player_animations[flip_dir] = {
                'idle': pygame.transform.flip(player_animations[source_dir]['idle'], True, False),
                'walk': [pygame.transform.flip(frame, True, False) for frame in player_animations[source_dir]['walk']]
            }
        
        player_img = player_animations['down']['idle']  # 默认朝下静止
    except Exception as e:
        print(f"无法加载角色精灵图: {e}，使用默认方块")
        player_img = pygame.Surface((player_draw_w, player_draw_h), pygame.SRCALPHA)
        player_img.fill((0, 255, 0))
        player_animations = None
    
    # 动画状态
    player_direction = 'down'  # 当前朝向
    player_moving = False  # 是否在移动
    anim_frame = 0  # 当前动画帧
    anim_timer = 0  # 动画计时器
    ANIM_FPS = 12  # 每秒12帧，更流畅的动画
    FRAME_DURATION = 1.0 / ANIM_FPS
    
    # 相机设置
    ACTIVITY_H = 400
    activity_top = (SCREEN_HEIGHT - ACTIVITY_H) // 2
    activity_rect = pygame.Rect(0, activity_top, SCREEN_WIDTH, ACTIVITY_H)
    camera_x = 0
    max_scroll = max(0, target_w - SCREEN_WIDTH)
    camera_smooth = 8.0
    
    # 碰撞检测
    def check_collision(new_x, new_y):
        pr = pygame.Rect(int(new_x + player_bbox_xoff), int(new_y + player_bbox_yoff), player_bbox_w, player_bbox_h)
        
        # 检查空白区域
        left = pr.left
        right = pr.right - 1
        top = pr.top
        bottom = pr.bottom - 1
        min_tx = left // TILE_SIZE
        max_tx = right // TILE_SIZE
        min_ty = top // TILE_SIZE
        max_ty = bottom // TILE_SIZE
        map_h = m.get('height', 0)
        
        for ty in range(min_ty, max_ty + 1):
            for tx in range(min_tx, max_tx + 1):
                if tx < 0 or ty < 0 or tx >= width or ty >= map_h:
                    return True
                idx = ty * width + tx
                tile_has = False
                for L in m.get('layers', []):
                    if L.get('type') != 'tilelayer':
                        continue
                    data = L.get('data', [])
                    raw = data[idx]
                    gid = raw & 0x1FFFFFFF
                    if gid != 0:
                        tile_has = True
                        break
                if not tile_has:
                    return True
        
        # 检查碰撞瓦片
        for tx, ty, tile_rect in collision_tiles:
            if pr.colliderect(tile_rect):
                return True
        return False
    
    # 绘制气泡
    def draw_bubble(text, map_x, map_y, cam_x, off_x, off_y):
        sx = int(round(map_x * scale)) + off_x - int(round(cam_x))
        sy = int(round(map_y * scale)) + off_y
        text_surf = game_font.render(text, True, (0, 0, 0))
        bubble_center_x = sx + (tile_draw_size // 2)
        bubble_rect = text_surf.get_rect(center=(bubble_center_x, sy - 18))
        bubble_rect.inflate_ip(10, 8)
        pygame.draw.rect(screen, (255, 255, 200), bubble_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), bubble_rect, 1, border_radius=5)
        screen.blit(text_surf, text_surf.get_rect(center=bubble_rect.center))
    
    # ========== 收集系统 ==========
    import math
    
    # 可收集物品定义（物品名称 -> 描述文本、颜色）
    collectible_items = {
        'item1': {'name': 'Strange Object', 'desc': 'It feels... familiar somehow.', 'collected': False, 'color': (100, 200, 255)},
        'item2': {'name': 'Old Photograph', 'desc': 'The faces are blurred... who are they?', 'collected': False, 'color': (255, 200, 100)},
        'item3': {'name': 'Faded Letter', 'desc': 'The ink has faded... but something remains.', 'collected': False, 'color': (255, 255, 150)},
    }
    collected_items = []
    ITEMS_REQUIRED = 3  # 需要收集的物品数量才能开门
    door_unlocked = False
    
    # 收集动画粒子系统
    class CollectParticle:
        def __init__(self, x, y, target_x, target_y, color):
            self.x = x
            self.y = y
            self.start_x = x
            self.start_y = y
            self.target_x = target_x
            self.target_y = target_y
            self.color = color
            self.progress = 0.0
            self.speed = 2.5  # 飞行速度
            self.active = True
            self.glow_timer = 0
            self.particles = []  # 拖尾粒子
            
        def update(self, dt, new_target_x, new_target_y):
            if not self.active:
                return
            # 更新目标位置（跟踪角色）
            self.target_x = new_target_x
            self.target_y = new_target_y
            
            self.progress += dt * self.speed
            self.glow_timer += dt
            
            # 贝塞尔曲线运动（有弧度的飞行）
            t = min(self.progress, 1.0)
            # 控制点在起点和终点之间上方
            ctrl_x = (self.start_x + self.target_x) / 2
            ctrl_y = min(self.start_y, self.target_y) - 80
            
            # 二次贝塞尔曲线
            self.x = (1-t)**2 * self.start_x + 2*(1-t)*t * ctrl_x + t**2 * self.target_x
            self.y = (1-t)**2 * self.start_y + 2*(1-t)*t * ctrl_y + t**2 * self.target_y
            
            # 添加拖尾粒子
            if random.random() < 0.3:
                self.particles.append({
                    'x': self.x + random.uniform(-5, 5),
                    'y': self.y + random.uniform(-5, 5),
                    'alpha': 200,
                    'size': random.uniform(3, 8)
                })
            
            # 更新拖尾粒子
            for p in self.particles:
                p['alpha'] -= 300 * dt
                p['size'] -= 5 * dt
            self.particles = [p for p in self.particles if p['alpha'] > 0 and p['size'] > 0]
            
            if self.progress >= 1.0:
                self.active = False
        
        def draw(self, surface):
            if not self.active:
                return
            
            # 绘制拖尾
            for p in self.particles:
                color_with_alpha = (*self.color, int(p['alpha']))
                glow = pygame.Surface((int(p['size']*4), int(p['size']*4)), pygame.SRCALPHA)
                pygame.draw.circle(glow, color_with_alpha, (int(p['size']*2), int(p['size']*2)), int(p['size']))
                surface.blit(glow, (p['x'] - p['size']*2, p['y'] - p['size']*2))
            
            # 绘制主光球
            pulse = (math.sin(self.glow_timer * 10) + 1) / 2
            glow_size = 25 + pulse * 10
            
            # 外层光晕
            glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
            for r in range(int(glow_size), 0, -2):
                alpha = int(100 * (1 - r / glow_size))
                pygame.draw.circle(glow_surf, (*self.color, alpha), 
                                 (int(glow_size), int(glow_size)), r)
            surface.blit(glow_surf, (self.x - glow_size, self.y - glow_size))
            
            # 内核
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), 8)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 6)
    
    # 收集动画列表
    collect_animations = []
    
    # 吸收特效（当物品飞到角色身上时）
    class AbsorbEffect:
        def __init__(self, x, y, color):
            self.x = x
            self.y = y
            self.color = color
            self.timer = 0
            self.duration = 0.5
            self.active = True
            self.rings = []
            for i in range(3):
                self.rings.append({'radius': 5, 'alpha': 255, 'delay': i * 0.1})
        
        def update(self, dt):
            self.timer += dt
            for ring in self.rings:
                if self.timer > ring['delay']:
                    ring['radius'] += 150 * dt
                    ring['alpha'] = max(0, 255 - ring['radius'] * 4)
            if self.timer >= self.duration:
                self.active = False
        
        def draw(self, surface):
            for ring in self.rings:
                if ring['alpha'] > 0:
                    surf = pygame.Surface((int(ring['radius']*2+4), int(ring['radius']*2+4)), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (*self.color, int(ring['alpha'])), 
                                     (int(ring['radius']+2), int(ring['radius']+2)), int(ring['radius']), 3)
                    surface.blit(surf, (self.x - ring['radius'] - 2, self.y - ring['radius'] - 2))
    
    absorb_effects = []
    
    # 为可交互物品添加发光效果计时器
    for obj in interactive_objects:
        obj['glow_timer'] = random.uniform(0, math.pi * 2)
    
    # 手动指定收集物品位置（只选择可到达的位置）
    collectible_positions = {
        'item1': (17, 15),    # First item position
        'item2': (22, 14),    # Second item position  
        'item3': (24, 14),    # Third item position (main position with glow effect)
    }
    
    # 扩展触发范围（额外的触发位置，但不显示特效）
    extended_trigger_positions = {
        'item3': [(24, 15)],  # (24, 15) 也可以触发 item3，但不显示发光特效
    }
    
    # 将指定位置的交互物品映射到收集物品
    item_mapping = {}  # id(obj) -> item_key
    glow_positions = {}  # item_key -> (tx, ty) 只有这个位置显示发光特效
    
    for obj in interactive_objects:
        tx = obj['rect'].x // TILE_SIZE
        ty = obj['rect'].y // TILE_SIZE
        
        # 检查主要位置
        for item_key, (target_tx, target_ty) in collectible_positions.items():
            if tx == target_tx and ty == target_ty:
                item_mapping[id(obj)] = item_key
                obj['is_collectible'] = True
                obj['item_key'] = item_key
                obj['show_glow'] = True  # 主要位置显示发光
                glow_positions[item_key] = (tx, ty)
                break
        
        # 检查扩展触发位置
        for item_key, extra_positions in extended_trigger_positions.items():
            for (ext_tx, ext_ty) in extra_positions:
                if tx == ext_tx and ty == ext_ty:
                    item_mapping[id(obj)] = item_key
                    obj['is_collectible'] = True
                    obj['item_key'] = item_key
                    obj['show_glow'] = False  # 扩展位置不显示发光
                    break
    
    # ========== 对话框系统 ==========
    class DialogueBox:
        def __init__(self, font_path):
            self.active = False
            self.text = ""
            self.display_text = ""
            self.char_index = 0
            self.char_timer = 0
            self.char_speed = 0.03
            self.display_time = 0
            self.auto_close_time = 3.0  # 3秒后自动关闭
            try:
                self.font = pygame.font.Font(str(font_path), 28)
                self.small_font = pygame.font.Font(str(font_path), 20)
            except:
                self.font = pygame.font.Font(None, 28)
                self.small_font = pygame.font.Font(None, 20)
        
        def show(self, text):
            self.active = True
            self.text = text
            self.display_text = ""
            self.char_index = 0
            self.char_timer = 0
            self.display_time = 0
        
        def update(self, dt):
            if not self.active:
                return
            if self.char_index < len(self.text):
                self.char_timer += dt
                if self.char_timer >= self.char_speed:
                    self.char_timer = 0
                    self.display_text += self.text[self.char_index]
                    self.char_index += 1
            else:
                self.display_time += dt
                if self.display_time >= self.auto_close_time:
                    self.active = False
        
        def skip(self):
            if self.char_index < len(self.text):
                self.display_text = self.text
                self.char_index = len(self.text)
            else:
                self.active = False
        
        def draw(self, surface):
            if not self.active:
                return
            sw, sh = surface.get_size()
            box_h = 120
            box_w = sw - 100
            box_x = 50
            box_y = sh - box_h - 40
            
            # 绘制对话框背景
            box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box_surf.fill((20, 15, 30, 230))
            pygame.draw.rect(box_surf, (150, 130, 180), (0, 0, box_w, box_h), 3, border_radius=8)
            surface.blit(box_surf, (box_x, box_y))
            
            # 绘制文本
            lines = self.display_text.split('\n')
            for i, line in enumerate(lines):
                text_surf = self.font.render(line, True, (255, 255, 255))
                surface.blit(text_surf, (box_x + 20, box_y + 15 + i * 32))
            
            # 绘制继续提示
            if self.char_index >= len(self.text):
                if int(pygame.time.get_ticks() / 500) % 2:
                    hint = self.small_font.render("Press SPACE to continue...", True, (180, 180, 200))
                    surface.blit(hint, (box_x + box_w - hint.get_width() - 20, box_y + box_h - 30))
    
    dialogue = DialogueBox(FONT_PATH)
    
    # 显示开场提示
    dialogue.show("I feel like I forgot something...\nIs everything as it should be?")
    
    # 主循环
    clock = pygame.time.Clock()
    running = True
    current_interactive = None
    current_door = None
    
    while running:
        screen.fill((0, 0, 0))
        
        # 绘制背景
        try:
            m_bg = dict(m)
            m_bg['layers'] = [layer for layer in m.get('layers', []) if (layer.get('name') or '') != 'foreground_furniture']
            off_bg = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            draw_map(off_bg, m_bg, tiles_by_gid, scale=scale)
            screen.blit(off_bg, (offset_x - int(round(camera_x)), offset_y))
        except Exception:
            pass
        
        # 处理玩家移动
        dt = clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()
        new_x, new_y = player_x, player_y
        move_delta = player_speed_pixels * dt
        
        # 检测移动方向
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_y -= move_delta
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_y += move_delta
            dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            new_x -= move_delta
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            new_x += move_delta
            dx = 1
        
        # 判断是否在移动
        player_moving = (dx != 0 or dy != 0)
        
        # 根据移动方向确定朝向
        if player_moving and player_animations:
            if dy < 0 and dx == 0:
                player_direction = 'up'
            elif dy > 0 and dx == 0:
                player_direction = 'down'
            elif dx < 0 and dy == 0:
                player_direction = 'left'
            elif dx > 0 and dy == 0:
                player_direction = 'right'
            elif dy < 0 and dx < 0:
                player_direction = 'up_left'
            elif dy < 0 and dx > 0:
                player_direction = 'up_right'
            elif dy > 0 and dx < 0:
                player_direction = 'down_left'
            elif dy > 0 and dx > 0:
                player_direction = 'down_right'
        
        # 更新动画
        if player_animations:
            if player_moving:
                anim_timer += dt
                if anim_timer >= FRAME_DURATION:
                    anim_frame = (anim_frame + 1) % 8
                    anim_timer = 0
                player_img = player_animations[player_direction]['walk'][anim_frame]
            else:
                anim_frame = 0
                anim_timer = 0
                player_img = player_animations[player_direction]['idle']
        
        if not check_collision(new_x, new_y):
            player_x, player_y = new_x, new_y
        
        # 相机跟随
        player_screen_x_nocam = int(round(player_x * scale)) + offset_x
        player_screen_y = int(round(player_y * scale)) + offset_y
        player_screen_x_rel = player_screen_x_nocam - camera_x
        desired_camera_x = camera_x
        
        if player_screen_x_rel < activity_rect.left:
            desired_camera_x = camera_x - (activity_rect.left - player_screen_x_rel)
        elif player_screen_x_rel > activity_rect.right:
            desired_camera_x = camera_x + (player_screen_x_rel - activity_rect.right)
        
        desired_camera_x = max(0, min(max_scroll, desired_camera_x))
        lerp_t = max(0.0, min(1.0, camera_smooth * dt))
        camera_x = camera_x + (desired_camera_x - camera_x) * lerp_t
        
        # ===== 绘制可收集物品的发光效果 =====
        for obj in interactive_objects:
            item_key = item_mapping.get(id(obj))
            # 只有标记了 show_glow 且物品未收集时才显示发光效果
            if item_key and not collectible_items[item_key]['collected'] and obj.get('show_glow', False):
                # 更新发光计时器
                obj['glow_timer'] += dt * 3
                
                # 计算物品屏幕位置
                obj_screen_x = int(round(obj['rect'].x * scale)) + offset_x - int(round(camera_x))
                obj_screen_y = int(round(obj['rect'].y * scale)) + offset_y
                
                # 绘制脉动发光效果
                pulse = (math.sin(obj['glow_timer']) + 1) / 2
                glow_size = 30 + pulse * 15
                item_color = collectible_items[item_key]['color']
                
                glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
                for r in range(int(glow_size), 0, -3):
                    alpha = int(80 * (1 - r / glow_size) * (0.5 + pulse * 0.5))
                    pygame.draw.circle(glow_surf, (*item_color, alpha), 
                                     (int(glow_size), int(glow_size)), r)
                screen.blit(glow_surf, (obj_screen_x + tile_draw_size//2 - glow_size, 
                                       obj_screen_y + tile_draw_size//2 - glow_size))
                
                # 绘制小星星粒子
                for i in range(3):
                    angle = obj['glow_timer'] * 2 + i * (math.pi * 2 / 3)
                    star_dist = 20 + pulse * 8
                    star_x = obj_screen_x + tile_draw_size//2 + math.cos(angle) * star_dist
                    star_y = obj_screen_y + tile_draw_size//2 + math.sin(angle) * star_dist
                    star_alpha = int(150 + pulse * 100)
                    star_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    pygame.draw.circle(star_surf, (*item_color, star_alpha), (4, 4), 3)
                    screen.blit(star_surf, (star_x - 4, star_y - 4))
        
        # 绘制玩家
        screen_x = int(round(player_x * scale)) + offset_x - int(round(camera_x))
        screen_y = int(round(player_y * scale)) + offset_y
        draw_x = screen_x + player_draw_xoff
        draw_y = screen_y + player_draw_yoff
        screen.blit(player_img, (draw_x, draw_y))
        
        # 绘制前景
        if foreground_layer:
            try:
                m_fg = {
                    'tilewidth': m.get('tilewidth'),
                    'tileheight': m.get('tileheight'),
                    'width': m.get('width'),
                    'height': m.get('height'),
                    'layers': [foreground_layer]
                }
                off_fg = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                draw_map(off_fg, m_fg, tiles_by_gid, scale=scale)
                screen.blit(off_fg, (offset_x - int(round(camera_x)), offset_y))
            except Exception:
                pass
        
        # 检测交互
        player_bbox_rect = pygame.Rect(int(player_x + player_bbox_xoff), int(player_y + player_bbox_yoff), player_bbox_w, player_bbox_h)
        current_interactive = None
        current_door = None
        
        # 检查门交互
        for door in door_objects:
            if player_bbox_rect.colliderect(door["rect"].inflate(10, 10)):
                current_door = door
                if door_unlocked:
                    draw_bubble("SPACE: Enter", door["rect"].x, door["rect"].y, camera_x, offset_x, offset_y)
                else:
                    draw_bubble(f"Locked ({len(collected_items)}/{ITEMS_REQUIRED})", door["rect"].x, door["rect"].y, camera_x, offset_x, offset_y)
                break
        
        # 检查普通交互
        if not current_door:
            for obj in interactive_objects:
                if player_bbox_rect.colliderect(obj["rect"].inflate(10, 10)):
                    current_interactive = obj
                    # 检查是否已收集
                    item_key = item_mapping.get(id(obj))
                    if item_key and collectible_items.get(item_key, {}).get('collected'):
                        draw_bubble("(Collected)", obj["rect"].x, obj["rect"].y, camera_x, offset_x, offset_y)
                    elif item_key:
                        # 可收集物品显示特殊提示
                        draw_bubble("SPACE: Collect", obj["rect"].x, obj["rect"].y, camera_x, offset_x, offset_y)
                    else:
                        draw_bubble("SPACE: Check", obj["rect"].x, obj["rect"].y, camera_x, offset_x, offset_y)
                    break
        
        # 绘制收集进度UI
        try:
            ui_font = pygame.font.Font(str(FONT_PATH), 24)
            ui_small = pygame.font.Font(str(FONT_PATH), 18)
        except:
            ui_font = pygame.font.Font(None, 24)
            ui_small = pygame.font.Font(None, 18)
        
        # 收集进度背景
        ui_bg = pygame.Surface((200, 80), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 150))
        screen.blit(ui_bg, (10, 10))
        
        # 标题
        title = ui_font.render("Collected Items", True, (255, 220, 150))
        screen.blit(title, (20, 15))
        
        # 进度条
        progress = len(collected_items) / ITEMS_REQUIRED
        bar_w, bar_h = 160, 15
        pygame.draw.rect(screen, (50, 50, 60), (20, 45, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(screen, (100, 200, 100) if progress >= 1.0 else (200, 150, 50), 
                        (20, 45, int(bar_w * min(progress, 1.0)), bar_h), border_radius=3)
        
        # 进度文本
        progress_text = ui_small.render(f"{len(collected_items)} / {ITEMS_REQUIRED}", True, (255, 255, 255))
        screen.blit(progress_text, (20 + bar_w//2 - progress_text.get_width()//2, 65))
        
        # ===== 更新和绘制收集动画 =====
        # 计算玩家中心位置（用于动画跟踪）
        player_center_x = draw_x + player_draw_w // 2
        player_center_y = draw_y + player_draw_h // 2
        
        # 更新收集动画
        for anim in collect_animations:
            anim.update(dt, player_center_x, player_center_y)
            # 当动画完成时，创建吸收特效
            if not anim.active:
                absorb_effects.append(AbsorbEffect(player_center_x, player_center_y, anim.color))
        collect_animations[:] = [a for a in collect_animations if a.active]
        
        # 更新吸收特效
        for effect in absorb_effects:
            effect.update(dt)
        absorb_effects[:] = [e for e in absorb_effects if e.active]
        
        # 绘制收集动画
        for anim in collect_animations:
            anim.draw(screen)
        
        # 绘制吸收特效
        for effect in absorb_effects:
            effect.draw(screen)
        
        # 更新对话框
        dialogue.update(dt)
        dialogue.draw(screen)
        
        # 定义交互处理函数
        def handle_interaction():
            nonlocal door_unlocked, collected_items
            
            # 如果对话框激活，按空格跳过/关闭
            if dialogue.active:
                dialogue.skip()
                return
            
            # 门交互
            if current_door:
                if door_unlocked:
                    print(f"玩家触发门交互，跳转到下一场景")
                    return 'next_scene'
                else:
                    remaining = ITEMS_REQUIRED - len(collected_items)
                    dialogue.show(f"The door is locked!\nYou need to find {remaining} more item(s) to unlock it.")
                return
            
            # 普通物品交互
            if current_interactive:
                # 播放音效
                sound_path = current_interactive.get("sound_path")
                resolved = None
                if sound_path:
                    if os.path.isabs(sound_path) and os.path.exists(sound_path):
                        resolved = sound_path
                    else:
                        cand = ASSETS_PATH / sound_path
                        if cand.exists():
                            resolved = str(cand)
                        else:
                            cand2 = ASSETS_PATH / 'sounds' / sound_path
                            if cand2.exists():
                                resolved = str(cand2)
                if resolved:
                    try:
                        pygame.mixer.Sound(resolved).play()
                    except Exception as e:
                        print(f"音效播放失败：{e}")
                else:
                    default_click = ASSETS_PATH / 'sounds' / 'click.wav'
                    if default_click.exists():
                        try:
                            pygame.mixer.Sound(str(default_click)).play()
                        except Exception:
                            pass
                
                # 检查是否可收集
                item_key = item_mapping.get(id(current_interactive))
                if item_key and not collectible_items[item_key]['collected']:
                    # 收集物品
                    collectible_items[item_key]['collected'] = True
                    collected_items.append(item_key)
                    item_info = collectible_items[item_key]
                    
                    # 创建收集动画（物品飞向角色）
                    obj_screen_x = int(round(current_interactive['rect'].x * scale)) + offset_x - int(round(camera_x)) + tile_draw_size//2
                    obj_screen_y = int(round(current_interactive['rect'].y * scale)) + offset_y + tile_draw_size//2
                    player_center_x = draw_x + player_draw_w // 2
                    player_center_y = draw_y + player_draw_h // 2
                    
                    collect_anim = CollectParticle(obj_screen_x, obj_screen_y, 
                                                   player_center_x, player_center_y,
                                                   item_info['color'])
                    collect_animations.append(collect_anim)
                    
                    # 显示收集提示
                    dialogue.show(f"Found: {item_info['name']}!\n{item_info['desc']}\n\n[{len(collected_items)}/{ITEMS_REQUIRED} items collected]")
                    
                    # 检查是否收集足够
                    if len(collected_items) >= ITEMS_REQUIRED:
                        door_unlocked = True
                        # 延迟显示开门提示会在下次交互时显示
                    
                    print(f"收集物品: {item_info['name']} ({len(collected_items)}/{ITEMS_REQUIRED})")
                elif item_key and collectible_items[item_key]['collected']:
                    # 已经收集过
                    dialogue.show(f"You already checked this.\nNothing else here...")
                else:
                    # 普通交互（无收集物品）
                    dialogue.show(f"Examining: {current_interactive['name']}...\nJust an ordinary object.")
                
                print(f"与【{current_interactive['name']}】交互")
            return None
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            # Z 键跳过关卡 (仅开发者模式)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                if getattr(g, 'DEVELOPER_MODE', False):
                    print("跳过关卡...")
                    return 'next'
            
            # 空格键交互
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                result = handle_interaction()
                if result == 'next_scene':
                    return 'next'
            
            # 右键交互
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                result = handle_interaction()
                if result == 'next_scene':
                    return 'next'
        
        pygame.display.flip()
    
    return 'quit'


def main():
    """主入口：管理游戏流程"""
    pygame.init()
    screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
    pygame.display.set_caption('NaN Game - 游戏流程')
    
    # 第一阶段：显示初始菜单
    meun = Meun(screen)
    choice = meun.run()
    
    if choice != 'start':
        pygame.quit()
        return
    
    # 第二阶段：运行解谜场景
    print("进入解谜场景...")
    puzzle_result = run_puzzle_scene(screen)
    
    if puzzle_result == 'quit':
        pygame.quit()
        return
    
    # 第三阶段：梦日记风格解谜关卡（4个谜题）
    if puzzle_result == 'next':
        print("进入梦境解谜关卡...")
        try:
            from testing.first_dream_puzzle import run_dream_puzzle
            dream_puzzle_result = run_dream_puzzle(screen)
            
            if dream_puzzle_result == 'quit':
                pygame.quit()
                return
        except Exception as e:
            print(f'梦境解谜关卡加载失败: {e}')
            dream_puzzle_result = 'next'  # 失败则跳过
    
    # 第四阶段：梦境过渡场景（小女巫转换）
    if puzzle_result == 'next':
        print("解谜完成，进入梦境过渡...")
        try:
            from testing.dream_transition_scene import run_dream_transition
            dream_result = run_dream_transition(screen)
            
            if dream_result == 'quit':
                pygame.quit()
                return
        except Exception as e:
            print(f'梦境场景加载失败: {e}')
            dream_result = 'next'  # 失败则跳过梦境场景
    
    # 第五阶段：Boss1 剧情战斗场景（The Hollow Intro - 玩家被秒杀）
    if puzzle_result == 'next':
        print("进入 Boss1 剧情战斗场景 (The Hollow - 初遇)...")
        
        try:
            from src.scenes.boss1_scripted_scene import Boss1ScriptedScene
            
            boss_scene = Boss1ScriptedScene(game_manager=None)
            if hasattr(boss_scene, 'enter'):
                try:
                    boss_scene.enter()
                except Exception:
                    pass
            
            pygame.display.set_caption("Boss1 - The First Attack")
            clock = pygame.time.Clock()
            boss_running = True
            
            while boss_running:
                dt = clock.tick(g.FPS) / 1000.0
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        boss_running = False
                        pygame.quit()
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            boss_running = False
                        # Z 键跳过关卡 (仅开发者模式)
                        elif event.key == pygame.K_z:
                            if getattr(g, 'DEVELOPER_MODE', False):
                                boss_running = False
                        elif event.key == pygame.K_SPACE:
                            # 死亡后按空格继续
                            is_over = hasattr(boss_scene, 'is_game_over') and boss_scene.is_game_over()
                            if is_over:
                                boss_running = False
                    
                    try:
                        boss_scene.handle_event(event)
                    except Exception:
                        pass
                
                try:
                    boss_scene.update(dt)
                except Exception:
                    pass
                
                try:
                    boss_scene.draw(screen)
                except Exception:
                    pass
                
                pygame.display.flip()
            
            # 退出Boss1场景时恢复玩家速度
            if hasattr(boss_scene, 'exit'):
                try:
                    boss_scene.exit()
                except Exception:
                    pass
                
        except Exception as e:
            import traceback
            print(f'Boss1 场景加载失败: {e}')
            traceback.print_exc()
    
    # 第六阶段：Map01 探索场景
    if puzzle_result == 'next':
        print("进入 Map01 探索场景...")
        try:
            from testing.map01_final import run as run_map01
            map01_result = run_map01(screen)
            
            if map01_result == 'quit':
                pygame.quit()
                return
        except Exception as e:
            import traceback
            print(f'Map01 场景加载失败: {e}')
            traceback.print_exc()
            map01_result = 'next'  # 失败则跳过
    
    # 第七阶段：镜子房间谜题
    if puzzle_result == 'next':
        print("进入镜子房间...")
        try:
            from testing.mirror_room_puzzle import run_mirror_room
            mirror_result = run_mirror_room(screen)
            
            if mirror_result == 'quit':
                pygame.quit()
                return
        except Exception as e:
            import traceback
            print(f'镜子房间加载失败: {e}')
            traceback.print_exc()
            mirror_result = 'next'  # 失败则跳过
    
    # 第八阶段：Boss2 战斗场景 (The Sloth)
    if puzzle_result == 'next':
        print("进入 Boss2 战斗场景 (The Sloth)...")
        try:
            from src.entities.sloth_battle_scene import SlothBattleScene
            
            boss_scene = SlothBattleScene()
            if hasattr(boss_scene, 'enter'):
                try:
                    boss_scene.enter()
                except Exception:
                    pass
            
            pygame.display.set_caption("Boss Battle - The Sloth")
            clock = pygame.time.Clock()
            boss_running = True
            
            while boss_running:
                dt = clock.tick(g.FPS) / 1000.0
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        boss_running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            boss_running = False
                        # Z 键跳过关卡 (仅开发者模式)
                        elif event.key == pygame.K_z:
                            if getattr(g, 'DEVELOPER_MODE', False):
                                boss_running = False
                        elif event.key == pygame.K_r:
                            # 重置战斗
                            if hasattr(boss_scene, 'is_game_over') and callable(boss_scene.is_game_over) and not boss_scene.is_game_over():
                                if hasattr(boss_scene, 'reset_battle') and callable(boss_scene.reset_battle):
                                    boss_scene.reset_battle()
                                elif hasattr(boss_scene, 'enter') and callable(boss_scene.enter):
                                    boss_scene.enter()
                        elif event.key == pygame.K_SPACE:
                            # 胜利后按空格退出
                            boss = getattr(boss_scene, 'boss', None)
                            is_over = hasattr(boss_scene, 'is_game_over') and boss_scene.is_game_over()
                            victory = False
                            if boss is not None and hasattr(boss, 'health'):
                                victory = getattr(boss, 'health', 1) <= 0
                            else:
                                victory = is_over and boss is None
                            if is_over and victory:
                                boss_running = False
                    
                    try:
                        boss_scene.handle_event(event)
                    except Exception:
                        pass
                
                try:
                    boss_scene.update(dt)
                except Exception:
                    pass
                
                try:
                    boss_scene.draw(screen)
                except Exception:
                    pass
                
                pygame.display.flip()
                
                # 检查是否胜利
                boss = getattr(boss_scene, 'boss', None)
                if boss is not None and hasattr(boss, 'health') and boss.health <= 0:
                    # 胜利，等待玩家按空格
                    pass
                    
        except Exception as e:
            import traceback
            print(f'Boss2 场景加载失败: {e}')
            traceback.print_exc()
    
    # 第九阶段：画作房谜题
    if puzzle_result == 'next':
        print("进入画作房谜题...")
        try:
            from testing.painting_room_puzzle import run_painting_room
            painting_result = run_painting_room(screen)
            
            if painting_result == 'quit':
                pygame.quit()
                return
        except Exception as e:
            import traceback
            print(f'画作房谜题加载失败: {e}')
            traceback.print_exc()
    
    # 第十阶段：Boss3 最终战斗场景 (The Hollow)
    if puzzle_result == 'next':
        print("进入最终 Boss3 战斗场景 (The Hollow)...")
        try:
            from src.entities.boss_battle_scene import BossBattleScene
            
            boss_scene = BossBattleScene(boss_type='hollow')
            if hasattr(boss_scene, 'enter'):
                try:
                    boss_scene.enter()
                except Exception:
                    pass
            
            pygame.display.set_caption("Final Boss Battle - The Hollow")
            clock = pygame.time.Clock()
            boss_running = True
            
            while boss_running:
                dt = clock.tick(g.FPS) / 1000.0
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        boss_running = False
                        pygame.quit()
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            boss_running = False
                        # Z 键跳过关卡 (仅开发者模式)
                        elif event.key == pygame.K_z:
                            if getattr(g, 'DEVELOPER_MODE', False):
                                boss_running = False
                        # R 键重新开始战斗
                        elif event.key == pygame.K_r:
                            is_over = hasattr(boss_scene, 'is_game_over') and boss_scene.is_game_over()
                            if is_over:
                                # 重新初始化 Boss3 场景
                                if hasattr(boss_scene, 'exit'):
                                    try:
                                        boss_scene.exit()
                                    except Exception:
                                        pass
                                boss_scene = BossBattleScene(boss_type='hollow')
                                if hasattr(boss_scene, 'enter'):
                                    try:
                                        boss_scene.enter()
                                    except Exception:
                                        pass
                    
                    try:
                        boss_scene.handle_event(event)
                    except Exception:
                        pass
                
                try:
                    boss_scene.update(dt)
                except Exception:
                    pass
                
                try:
                    boss_scene.draw(screen)
                except Exception:
                    pass
                
                pygame.display.flip()
            
            # 退出Boss3场景
            if hasattr(boss_scene, 'exit'):
                try:
                    boss_scene.exit()
                except Exception:
                    pass
                    
        except Exception as e:
            import traceback
            print(f'Boss3 场景加载失败: {e}')
            traceback.print_exc()
    
    print("所有关卡完成！恭喜通关！")
    pygame.quit()


if __name__ == '__main__':
    main()
