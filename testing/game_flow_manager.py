"""
游戏流程管理器
整合游戏的多个场景：初始菜单 -> 解谜场景 -> 第二场景

场景流程：
1. combine/game.py 的菜单界面（初始界面）
2. testing/new_third_puzzle.py 的解谜场景
3. combine/game.py 的 map01 场景（第二界面）

在解谜场景中，玩家走到门前（坐标 21,12 和 21,13）右键点击可跳转到下一场景。
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
    USER_DEFAULT_SPAWN = (16, 15)
    sx, sy = USER_DEFAULT_SPAWN
    player_x = sx * TILE_SIZE
    player_y = sy * TILE_SIZE
    
    # 玩家参数
    player_speed_pixels = 140
    player_scale_on_tile = 0.6
    player_map_w = max(1, int(round(TILE_SIZE * player_scale_on_tile)))
    player_map_h = max(1, int(round(TILE_SIZE * player_scale_on_tile)))
    player_bbox_w = player_map_w
    player_bbox_h = player_map_h
    player_bbox_xoff = (TILE_SIZE - player_bbox_w) // 2
    player_bbox_yoff = (TILE_SIZE - player_bbox_h)
    
    player_draw_w = int(round(player_map_w * scale))
    player_draw_h = int(round(player_map_h * scale))
    player_draw_xoff = (tile_draw_size - player_draw_w) // 2
    player_draw_yoff = (tile_draw_size - player_draw_h) // 2
    
    player_img = pygame.Surface((player_draw_w, player_draw_h), pygame.SRCALPHA)
    player_img.fill((0, 255, 0))
    
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
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_y -= move_delta
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_y += move_delta
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            new_x -= move_delta
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            new_x += move_delta
        
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
    
    # 第二阶段：运行解谜场景
    print("进入解谜场景...")
    puzzle_result = run_puzzle_scene(screen)
    
    if puzzle_result == 'quit':
        pygame.quit()
        return
    
    # 第三阶段：跳转到第二场景（map01）
    if puzzle_result == 'next':
        print("解谜完成，进入第二场景...")
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
