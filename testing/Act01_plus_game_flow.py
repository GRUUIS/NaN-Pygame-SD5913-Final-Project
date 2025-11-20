"""
游戏流程管理器 - Act 01 完整版
整合游戏的多个场景：初始菜单 -> 镜像对称解谜场景 -> 梦境过渡 -> 战斗场景

场景流程：
1. combine/game.py 的菜单界面（初始界面）
2. 镜像对称解谜场景：玩家需要破坏房间的对称性
3. testing/dream_transition_scene.py 的梦境过渡场景（剧情衔接）
4. combine/game.py 的 map01 场景（战斗场景）

解谜逻辑：
- 房间被镜子分为左右两部分，一切都是对称的
- 玩家需要：
  1. 推动左侧椅子至右侧桌子旁（破坏左右对称）
  2. 打开显示器（现实显示乱码，镜中显示完美报告）
  3. 拿起断铅笔放到右侧书架（破坏上下对称）
- 完成后镜中房间崩坏，出现箱子，获得破损画笔
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


def run_mirror_puzzle_scene(screen):
    """
    镜像对称解谜场景
    
    场景逻辑：
    1. 左侧为原始地图，右侧为程序生成的镜像地图
    2. 初始中间有空气墙，解谜完成后消失
    3. 右侧镜像会根据解谜进度发生变化（打破对称）
    """
    from src.tiled_loader import load_map, draw_map
    import xml.etree.ElementTree as ET
    
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
    
    # 地图尺寸
    single_map_width = m.get('width', 0)
    single_map_height = m.get('height', 0)
    
    # 绘图参数
    tile_draw_size = 64
    scale = tile_draw_size / float(TILE_SIZE)
    single_target_w = tile_draw_size * single_map_width
    total_target_w = single_target_w * 2
    target_h = tile_draw_size * single_map_height
    
    offset_y = (SCREEN_HEIGHT - target_h) // 2
    offset_x = 0
    
    # 加载字体
    try:
        game_font = pygame.font.Font(str(FONT_PATH), 16)
        hint_font = pygame.font.Font(str(FONT_PATH), 20)
    except Exception:
        game_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 16)
        hint_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 20)
    
    # 构建 tile 属性
    tile_props = {}
    for ts in m.get('tilesets', []):
        firstgid = ts.get('firstgid', 0)
        for t in ts.get('tiles', []) or []:
            local_id = t.get('id')
            props = {}
            for p in t.get('properties', []) or []:
                props[p.get('name')] = p.get('value')
            tile_props[firstgid + int(local_id)] = props
            
    # 解析 TSX
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
    
    def is_truthy(v):
        return v in (True, 'true', 'True', 1, '1')
    
    # 提取对象和碰撞
    collision_tiles = []
    interactive_objects = []
    door_objects = []
    
    # 关键解谜对象的坐标（如果在地图中找不到名字，使用默认坐标）
    # 假设：椅子(10,12), 显示器(15,10), 铅笔(15,11), 书架(22,14)
    puzzle_coords = {
        'chair': (10, 12),
        'monitor': (15, 10),
        'pencil': (15, 11),
        'shelf': (22, 14)
    }
    
    for layer in m.get('layers', []):
        if layer.get('type') != 'tilelayer':
            continue
        data = layer.get('data', [])
        lname = layer.get('name') or ''
        
        for idx, raw_gid in enumerate(data):
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0:
                continue
            tx = idx % single_map_width
            ty = idx // single_map_width
            props = tile_props.get(gid, {})
            
            # 碰撞体（左侧）
            if is_truthy(props.get('collidable')):
                rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                collision_tiles.append((tx, ty, rect))
            
            # 交互对象
            if is_truthy(props.get('interactive')) or lname == 'door':
                obj_type = props.get('type', 'unknown')
                obj_name = props.get('name', 'unknown')
                
                # 尝试识别关键对象
                if (tx, ty) == puzzle_coords['chair']: obj_name = 'chair'
                elif (tx, ty) == puzzle_coords['monitor']: obj_name = 'monitor'
                elif (tx, ty) == puzzle_coords['pencil']: obj_name = 'pencil'
                elif (tx, ty) == puzzle_coords['shelf']: obj_name = 'shelf'
                
                if lname == 'door' and (tx, ty) in [(21, 12), (21, 13)]:
                    door_objects.append({
                        'rect': pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                        'name': 'door'
                    })
                elif is_truthy(props.get('interactive')):
                    interactive_objects.append({
                        'rect': pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                        'prompt': props.get('prompt', 'interact'),
                        'name': obj_name,
                        'tx': tx, 'ty': ty
                    })

    # 玩家设置
    USER_DEFAULT_SPAWN = (16, 14)
    player_x = USER_DEFAULT_SPAWN[0] * TILE_SIZE
    player_y = USER_DEFAULT_SPAWN[1] * TILE_SIZE
    player_speed_pixels = 140
    
    # 角色尺寸
    player_scale_on_tile = 1.1
    player_map_h = max(1, int(round(TILE_SIZE * player_scale_on_tile)))
    player_map_w = max(1, int(round(player_map_h * (23.0 / 36.0))))
    player_bbox_w = int(player_map_w * 0.7)
    player_bbox_h = int(player_map_h * 0.5)
    player_bbox_xoff = (player_map_w - player_bbox_w) // 2
    player_bbox_yoff = player_map_h - player_bbox_h
    
    SPRITE_ASPECT = 23.0 / 36.0
    player_draw_h = int(round(player_map_h * scale))
    player_draw_w = int(round(player_draw_h * SPRITE_ASPECT))
    player_draw_xoff = (tile_draw_size - player_draw_w) // 2
    player_draw_yoff = (tile_draw_size - player_draw_h) // 2
    
    # 加载角色动画
    sprite_path = ASSETS_PATH / "8Direction_TopDown_Character Sprites_ByBossNelNel" / "SpriteSheet.png"
    player_animations = {}
    try:
        sprite_sheet = pygame.image.load(str(sprite_path)).convert_alpha()
        directions = ['down', 'down_left', 'left', 'up_left', 'up', 'up_right', 'right', 'down_right']
        SPRITE_W, SPRITE_H = 23, 36
        for row, direction in enumerate(directions):
            player_animations[direction] = {'idle': None, 'walk': []}
            idle_sprite = sprite_sheet.subsurface(pygame.Rect(0, row * SPRITE_H, SPRITE_W, SPRITE_H))
            if 'right' in direction: idle_sprite = pygame.transform.flip(idle_sprite, True, False)
            player_animations[direction]['idle'] = pygame.transform.scale(idle_sprite, (player_draw_w, player_draw_h))
            for col in range(1, 9):
                walk_sprite = sprite_sheet.subsurface(pygame.Rect(col * SPRITE_W, row * SPRITE_H, SPRITE_W, SPRITE_H))
                if 'right' in direction: walk_sprite = pygame.transform.flip(walk_sprite, True, False)
                player_animations[direction]['walk'].append(pygame.transform.scale(walk_sprite, (player_draw_w, player_draw_h)))
        player_img = player_animations['down']['idle']
    except Exception:
        player_img = pygame.Surface((player_draw_w, player_draw_h))
        player_img.fill((0, 255, 0))
    
    # 动画状态
    player_direction = 'down'
    player_moving = False
    anim_frame = 0
    anim_timer = 0
    ANIM_FPS = 8
    FRAME_DURATION = 1.0 / ANIM_FPS
    
    # 相机
    ACTIVITY_H = 400
    activity_top = (SCREEN_HEIGHT - ACTIVITY_H) // 2
    activity_rect = pygame.Rect(0, activity_top, SCREEN_WIDTH, ACTIVITY_H)
    camera_x = 0
    max_scroll = max(0, total_target_w - SCREEN_WIDTH)
    camera_smooth = 8.0
    
    # 解谜状态
    puzzle_state = {
        'chair_moved': False,
        'monitor_clicked': False,
        'pencil_placed': False,
        'puzzle_solved': False
    }
    
    hints = []
    hint_timer = 0
    def add_hint(text, duration=3.0):
        nonlocal hints, hint_timer
        hints = [text]
        hint_timer = duration
    
    add_hint("房间中间有一面镜子...一切都是对称的", 4.0)
    
    # 绘制气泡
    def draw_bubble(text, map_x, map_y):
        sx = int(round(map_x * scale)) + offset_x - int(round(camera_x))
        sy = int(round(map_y * scale)) + offset_y
        text_surf = game_font.render(text, True, (0, 0, 0))
        bubble_center_x = sx + (tile_draw_size // 2)
        bubble_rect = text_surf.get_rect(center=(bubble_center_x, sy - 18))
        bubble_rect.inflate_ip(10, 8)
        pygame.draw.rect(screen, (255, 255, 200), bubble_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), bubble_rect, 1, border_radius=5)
        screen.blit(text_surf, text_surf.get_rect(center=bubble_rect.center))
    
    # 动态生成右侧镜像房间
    def render_mirror_room(surface, state):
        surface.fill((0,0,0,0)) # 清空
        
        # 遍历所有层
        for layer in m.get('layers', []):
            if layer.get('type') != 'tilelayer': continue
            data = layer.get('data', [])
            
            for idx, raw_gid in enumerate(data):
                gid = raw_gid & 0x1FFFFFFF
                if gid == 0: continue
                
                tx = idx % single_map_width
                ty = idx // single_map_width
                
                # 镜像坐标：总宽度 2*W，镜像位置 = 2*W - 1 - tx
                # 但我们是在一个单独的 surface 上画右侧，所以 x = W - 1 - tx
                mirror_tx = single_map_width - 1 - tx
                
                # 检查解谜状态，决定是否绘制该瓦片
                # 1. 椅子：如果椅子移动了，镜像中的椅子消失
                if state['chair_moved'] and (tx, ty) == puzzle_coords['chair']:
                    continue
                
                # 2. 显示器：如果点击了，显示器变黑（这里简单处理为不画，或者画一个黑色矩形）
                if state['monitor_clicked'] and (tx, ty) == puzzle_coords['monitor']:
                    # 可以选择画一个黑色矩形代替
                    rect = pygame.Rect(mirror_tx * tile_draw_size, ty * tile_draw_size, tile_draw_size, tile_draw_size)
                    pygame.draw.rect(surface, (0,0,0), rect)
                    continue
                
                # 3. 书架：如果放了铅笔，书架变箱子（这里简单处理为画一个金色矩形）
                if state['pencil_placed'] and (tx, ty) == puzzle_coords['shelf']:
                    rect = pygame.Rect(mirror_tx * tile_draw_size, ty * tile_draw_size, tile_draw_size, tile_draw_size)
                    pygame.draw.rect(surface, (255,215,0), rect) # 金色箱子
                    continue
                
                # 绘制镜像瓦片
                tile_surf = tiles_by_gid.get(gid)
                if tile_surf:
                    # 水平翻转瓦片图像以保持几何对称
                    flipped_tile = pygame.transform.flip(tile_surf, True, False)
                    scaled_tile = pygame.transform.scale(flipped_tile, (tile_draw_size, tile_draw_size))
                    surface.blit(scaled_tile, (mirror_tx * tile_draw_size, ty * tile_draw_size))

    # 预渲染左侧房间
    left_room_surf = pygame.Surface((single_target_w, target_h), pygame.SRCALPHA)
    m_bg = dict(m)
    draw_map(left_room_surf, m_bg, tiles_by_gid, scale=scale)
    
    # 右侧房间表面（动态更新）
    right_room_surf = pygame.Surface((single_target_w, target_h), pygame.SRCALPHA)
    render_mirror_room(right_room_surf, puzzle_state)
    
    # 碰撞检测
    def check_collision(new_x, new_y):
        pr = pygame.Rect(int(new_x + player_bbox_xoff), int(new_y + player_bbox_yoff), player_bbox_w, player_bbox_h)
        
        # 边界
        if new_x < 0 or new_y < 0 or new_x + player_bbox_w > (single_map_width * TILE_SIZE * 2) or new_y + player_bbox_h > (single_map_height * TILE_SIZE):
            # print("Collision: Boundary")
            return True
            
        # 中间空气墙
        if not puzzle_state['puzzle_solved']:
            mid_x = single_map_width * TILE_SIZE
            if pr.right > mid_x:
                # print(f"Collision: Invisible Wall at {mid_x}")
                return True
            
        # 瓦片碰撞（左侧 + 右侧镜像）
        for tx, ty, rect in collision_tiles:
            # 左侧原始碰撞
            if pr.colliderect(rect): return True
            # 右侧镜像碰撞
            mirror_tx = single_map_width * 2 - 1 - tx
            mirror_rect = pygame.Rect(mirror_tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if pr.colliderect(mirror_rect): return True
            
        return False

    # 主循环
    clock = pygame.time.Clock()
    running = True
    
    while running:
        screen.fill((0, 0, 0))
        dt = clock.tick(60) / 1000.0
        
        if hint_timer > 0:
            hint_timer -= dt
            if hint_timer <= 0: hints = []
            
        # 绘制房间
        screen.blit(left_room_surf, (offset_x - int(camera_x), offset_y))
        screen.blit(right_room_surf, (offset_x + single_target_w - int(camera_x), offset_y))
        
        # 玩家移动
        keys = pygame.key.get_pressed()
        new_x, new_y = player_x, player_y
        move_delta = player_speed_pixels * dt
        dx, dy = 0, 0
        
        if keys[pygame.K_w]: new_y -= move_delta; dy = -1
        if keys[pygame.K_s]: new_y += move_delta; dy = 1
        if keys[pygame.K_a]: new_x -= move_delta; dx = -1
        if keys[pygame.K_d]: new_x += move_delta; dx = 1
        
        player_moving = (dx != 0 or dy != 0)
        if player_moving:
            if dy < 0: player_direction = 'up'
            elif dy > 0: player_direction = 'down'
            if dx < 0: player_direction = 'left'
            elif dx > 0: player_direction = 'right'
            
            anim_timer += dt
            if anim_timer >= FRAME_DURATION:
                anim_frame = (anim_frame + 1) % 8
                anim_timer = 0
            player_img = player_animations[player_direction]['walk'][anim_frame]
        else:
            player_img = player_animations[player_direction]['idle']
            
        if not check_collision(new_x, new_y):
            player_x, player_y = new_x, new_y
            
        # 相机跟随
        player_screen_x = int(player_x * scale) + offset_x
        target_cam_x = player_screen_x - SCREEN_WIDTH // 2
        target_cam_x = max(0, min(max_scroll, target_cam_x))
        camera_x += (target_cam_x - camera_x) * 0.1
        
        # 绘制玩家
        draw_x = int(player_x * scale) + offset_x - int(camera_x) + player_draw_xoff
        draw_y = int(player_y * scale) + offset_y + player_draw_yoff
        screen.blit(player_img, (draw_x, draw_y))
        
        # 交互检测
        player_rect = pygame.Rect(player_x, player_y, TILE_SIZE, TILE_SIZE)
        current_obj = None
        
        for obj in interactive_objects:
            if player_rect.colliderect(obj['rect'].inflate(10, 10)):
                current_obj = obj
                draw_bubble(obj['prompt'], obj['rect'].x, obj['rect'].y)
                break
                
        for door in door_objects:
            if player_rect.colliderect(door['rect'].inflate(10, 10)):
                if puzzle_state['puzzle_solved']:
                    draw_bubble("右键离开", door['rect'].x, door['rect'].y)
                    if pygame.mouse.get_pressed()[2]: return 'next'
                else:
                    draw_bubble("门锁住了", door['rect'].x, door['rect'].y)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return 'quit'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if current_obj:
                    name = current_obj['name']
                    changed = False
                    
                    if name == 'chair' and not puzzle_state['chair_moved']:
                        puzzle_state['chair_moved'] = True
                        add_hint("镜子里的椅子消失了！", 3.0)
                        changed = True
                    elif name == 'monitor' and not puzzle_state['monitor_clicked']:
                        puzzle_state['monitor_clicked'] = True
                        add_hint("镜子里的屏幕黑了！", 3.0)
                        changed = True
                    elif name == 'shelf' and not puzzle_state['pencil_placed']: # 简化：直接点书架
                        puzzle_state['pencil_placed'] = True
                        add_hint("镜子里的书架变成了箱子！", 3.0)
                        changed = True
                        
                    if changed:
                        render_mirror_room(right_room_surf, puzzle_state)
                        if all([puzzle_state['chair_moved'], puzzle_state['monitor_clicked'], puzzle_state['pencil_placed']]):
                            puzzle_state['puzzle_solved'] = True
                            add_hint("对称被打破！门已打开", 4.0)
                            
        # UI
        if hints:
            text = hint_font.render(hints[0], True, (255, 255, 255))
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 50))
            
        pygame.display.flip()
        
    return 'quit'


def run_puzzle_scene(screen):
    """
    运行解谜场景（基于 new_third_puzzle.py 的逻辑）
    返回：'next' 表示完成解谜并触发门，'quit' 表示退出游戏
    """
    from src.tiled_loader import load_map, draw_map
    import xml.etree.ElementTree as ET
    
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
        if lname == 'door':
            door_objects.append(layer)
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
    USER_DEFAULT_SPAWN = (16, 15)
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
        directions = ['down', 'down_left', 'left', 'up_left', 'up', 'up_right', 'right', 'down_right']
        
        for row, direction in enumerate(directions):
            player_animations[direction] = {
                'idle': None,
                'walk': []
            }
            # 第一列是idle
            idle_sprite = sprite_sheet.subsurface(pygame.Rect(0, row * SPRITE_H, SPRITE_W, SPRITE_H))
            # 右侧方向需要水平翻转
            if 'right' in direction:
                idle_sprite = pygame.transform.flip(idle_sprite, True, False)
            player_animations[direction]['idle'] = pygame.transform.scale(idle_sprite, (player_draw_w, player_draw_h))
            
            # 第2-9列是行走动画（8帧）
            for col in range(1, 9):
                walk_sprite = sprite_sheet.subsurface(pygame.Rect(col * SPRITE_W, row * SPRITE_H, SPRITE_W, SPRITE_H))
                # 右侧方向需要水平翻转
                if 'right' in direction:
                    walk_sprite = pygame.transform.flip(walk_sprite, True, False)
                scaled_sprite = pygame.transform.scale(walk_sprite, (player_draw_w, player_draw_h))
                player_animations[direction]['walk'].append(scaled_sprite)
        
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
    ANIM_FPS = 8  # 每秒8帧
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
    
    # 主循环
    clock = pygame.time.Clock()
    running = True
    print("Starting game loop")
    
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
                draw_bubble("Right-click to open", door["rect"].x, door["rect"].y, camera_x, offset_x, offset_y)
                break
        
        # 检查普通交互
        if not current_door:
            for obj in interactive_objects:
                if player_bbox_rect.colliderect(obj["rect"].inflate(10, 10)):
                    current_interactive = obj
                    draw_bubble(obj["prompt"], obj["rect"].x, obj["rect"].y, camera_x, offset_x, offset_y)
                    break
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            # 右键交互
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # 门交互：跳转到下一场景
                if current_door:
                    print(f"玩家触发门交互，跳转到下一场景")
                    return 'next'
                
                # 普通交互
                if current_interactive:
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
                    
                    print(f"与【{current_interactive['name']}】交互")
        
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
    
    # 第二阶段：运行镜像对称解谜场景
    print("进入镜像对称解谜场景...")
    puzzle_result = run_mirror_puzzle_scene(screen)
    
    if puzzle_result == 'quit':
        pygame.quit()
        return
    
    # 第三阶段：梦境过渡场景
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
    
    # 第四阶段：跳转到战斗场景（map01）
    if puzzle_result == 'next':
        print("进入战斗场景...")
        try:
            from src.systems.inventory import Inventory
            inv = Inventory()
        except Exception:
            inv = None
        
        try:
            from src.scenes.map01_scene import run as run_map01
            run_map01(screen, inventory=inv)
        except Exception as e:
            print('Failed to run map01 scene:', e)
    
    pygame.quit()


if __name__ == '__main__':
    main()
