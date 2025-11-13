import pygame
import sys
from pathlib import Path
# Ensure repository root is on sys.path so `src` imports work when running this script directly
ROOT = Path(__file__).resolve().parent.parent
import os
import sys as _sys
if str(ROOT) not in _sys.path:
    _sys.path.insert(0, str(ROOT))
from src.tiled_loader import load_map, draw_map, extract_collision_rects

# 命令行参数：允许覆盖出生格与瓦片绘制尺寸，以及 dry-run（只打印选择，不打开窗口）
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--spawn-x', type=int, help='手动设置玩家出生格的 tile x 坐标（以 tile 为单位）')
parser.add_argument('--spawn-y', type=int, help='手动设置玩家出生格的 tile y 坐标（以 tile 为单位）')
parser.add_argument('--tile-draw-size', type=int, help='强制每个瓦片在屏幕上的像素尺寸（例如 64）')
parser.add_argument('--dry-run', action='store_true', help='只计算并打印出生格/缩放信息，然后退出（不打开窗口）')
args = parser.parse_args()

# 初始化 pygame（如果不是 dry-run）
if not getattr(args, 'dry_run', False):
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        # 有些环境下 mixer 初始化会失败（例如无音频设备），继续也行
        pass

# 屏幕设置：使用 1280x720 作为首选视图（与项目要求一致）
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = None
if not getattr(args, 'dry_run', False):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("解谜场景 - 第三关")

# 资源路径
ASSETS_PATH = Path("assets")
MAP_PATH = ASSETS_PATH / "tilemaps" / "test puzzle scene.tmj"
print(f"Using TMJ map {MAP_PATH}")
TILESET_IMAGE = ASSETS_PATH / "tilemaps" / "test scene2.png"
FONT_PATH = ASSETS_PATH / "Silver.ttf"  # 字体路径

# 加载 TMJ（使用项目自带的 JSON loader）
try:
    m, tiles_by_gid, tileset_meta = load_map(str(MAP_PATH))
    TILE_SIZE = m.get('tilewidth', 32)
except Exception as e:
    import traceback
    print(f"地图加载失败（使用 load_map）：{e}")
    traceback.print_exc()
    sys.exit(1)

# 计算地图像素大小与渲染缩放因子
map_pixel_w = m.get('width', 0) * TILE_SIZE
map_pixel_h = m.get('height', 0) * TILE_SIZE
# 缩放到窗口（保持长宽比，整体缩放）
float_scale = min(SCREEN_WIDTH / max(1, map_pixel_w), SCREEN_HEIGHT / max(1, map_pixel_h))
float_scale = float(float_scale)
# 为避免四舍五入导致的像素错位，我们使用整数的每瓦片绘制尺寸（像素）。
# 默认固定为 64（以便测试 64x64 效果），除非通过命令行参数 --tile-draw-size 覆盖。
if getattr(args, 'tile_draw_size', None):
    tile_draw_size = int(args.tile_draw_size)
else:
    tile_draw_size = 64
# 使用整像素瓦片尺寸重新计算实际 scale（精确比例）
scale = tile_draw_size / float(TILE_SIZE)
target_w = tile_draw_size * m.get('width', 0)
target_h = tile_draw_size * m.get('height', 0)
# 计算将缩放后的地图居中到窗口的偏移
offset_x = (SCREEN_WIDTH - target_w) // 2
offset_y = (SCREEN_HEIGHT - target_h) // 2
print(f"map size = {map_pixel_w}x{map_pixel_h}, window = {SCREEN_WIDTH}x{SCREEN_HEIGHT}, float_scale = {float_scale:.3f}, tile_draw_size = {tile_draw_size}, scale = {scale:.3f}, target = {target_w}x{target_h}, offset = {offset_x},{offset_y}")

if not getattr(args, 'dry_run', False):
    # 加载字体（优先使用Silver.ttf，失败则 fallback 到系统字体）
    try:
        game_font = pygame.font.Font(str(FONT_PATH), 16)  # 字体大小16
    except Exception:
        print(f"警告：未找到 {FONT_PATH}，使用系统默认字体")
        game_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 16)

    # 加载角色（绿色方块，可替换为图片）
    # 玩家尺寸随缩放调整，取整
    player_w = tile_draw_size
    player_h = tile_draw_size
    player_img = pygame.Surface((player_w, player_h), pygame.SRCALPHA)
    player_img.fill((0, 255, 0))  # 绿色代表角色
else:
    # dry-run 时不创建 pygame 资源，设置占位变量
    game_font = None
    player_img = None

# 图层分离：背景、前景、交互物体、碰撞瓦片（基于 load_map 返回的 JSON 结构）
background_layers = []
foreground_layer = None
interactive_objects = []
collision_tiles = []

# 构建 gid -> 属性 的映射（来自 tilesets[].tiles[].properties）
tile_props = {}
for ts in m.get('tilesets', []):
    firstgid = ts.get('firstgid', 0)
    for t in ts.get('tiles', []) or []:
        local_id = t.get('id')
        props = {}
        for p in t.get('properties', []) or []:
            props[p.get('name')] = p.get('value')
        tile_props[firstgid + int(local_id)] = props

# 补充：有些 tile 的 properties 存在于外部 .tsx 文件中（而非 TMJ），
# 所以额外解析 load_map 返回的 tileset_meta 中的 tsx_path，
# 将 tsx 中的 <tile><properties> 合并进 tile_props（覆盖/补充）。
try:
    import xml.etree.ElementTree as ET
    import os as _os
    for fg, meta in (tileset_meta or {}).items():
        tsx_path = meta.get('tsx_path')
        if not tsx_path or not _os.path.exists(tsx_path):
            continue
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
                        # Tiled may store value in 'value' attribute or as text
                        val = prop.attrib.get('value')
                        if val is None:
                            val = prop.text
                        props[name] = val
                if props:
                    tile_props[fg + tid] = props
        except Exception as _e:
            print(f"Warning: failed to parse TSX {tsx_path} properties: {_e}")
except Exception:
    pass

width = m.get('width', 0)
# normalize truthy checker (used several places)
def is_truthy(v):
    return v in (True, 'true', 'True', 1, '1')

# build a quick set of gids that are marked collidable (so we can test spawn tiles by gid)
collidable_gids = {gid for gid, props in tile_props.items() if is_truthy(props.get('collidable'))}
bed_spawn = None
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
        # properties from Tiled may be booleans, numbers or strings like "true"/"1"; normalize
        def is_truthy(v):
            return v in (True, 'true', 'True', 1, '1')
        if is_truthy(props.get('interactive')):
            interactive_objects.append({
                'rect': pygame.Rect(tx * TILE_SIZE + layer_off_x, ty * TILE_SIZE + layer_off_y, TILE_SIZE, TILE_SIZE),
                'prompt': props.get('prompt', 'check'),
                'sound_path': props.get('click_sound'),
                'name': props.get('name', 'unknown'),
                'type': props.get('type', '')
            })
        if is_truthy(props.get('collidable')):
            collision_tiles.append(pygame.Rect(tx * TILE_SIZE + layer_off_x, ty * TILE_SIZE + layer_off_y, TILE_SIZE, TILE_SIZE))
        # 记录 bed 图层的第一个非零瓦片作为床位置（用于出生点）
        if lname == 'bed' and bed_spawn is None:
            # find first tile in this layer that is non-zero
            for jdx, rv in enumerate(data):
                if (rv & 0x1FFFFFFF) != 0:
                    bx = jdx % width
                    by = jdx // width
                    bed_spawn = (bx, by)
                    break
# 玩家初始位置（可调整）
# 如果找到了床 (bed_spawn)，出生在床右侧（或最近的空位）
def find_spawn_near(bx, by, width, collidable_gids):
    # Prefer the right side of the bed. First try the immediate right tile unconditionally
    # (if it's inside the map). If it's out of bounds, fall back to searching nearby tiles.
    # After forcing immediate right, try increasing right offsets first, then down/up, then lefts.
    immediate_right_x = bx + 1
    if 0 <= immediate_right_x < width and 0 <= by < m.get('height', 0):
        return immediate_right_x, by

    offsets = [
        (2, 0), (3, 0), (4, 0),
        (0, 1), (0, -1),
        (1, 0),
        (-1, 0), (-2, 0), (-3, 0)
    ]
    max_h = m.get('height', 0)
    for ox, oy in offsets:
        sx = bx + ox
        sy = by + oy
        if sx < 0 or sy < 0 or sx >= width or sy >= max_h:
            continue
        idx = sy * width + sx
        # check every tilelayer at this index; if any layer places a collidable gid here, it's not a valid spawn
        blocked = False
        for L in m.get('layers', []):
            if L.get('type') != 'tilelayer':
                continue
            data = L.get('data', [])
            raw = data[idx]
            gid = raw & 0x1FFFFFFF
            if gid == 0:
                continue
            if gid in collidable_gids:
                blocked = True
                break
        if not blocked:
            return sx, sy
    # fallback: return original bed tile (will overlap but prevents None)
    return bx, by

player_x, player_y = TILE_SIZE * 5, TILE_SIZE * 5
if bed_spawn:
    # find the bed layer data to test emptiness
    bed_layer = None
    for L in m.get('layers', []):
        if (L.get('name') or '') == 'bed' and L.get('type') == 'tilelayer':
            bed_layer = L
            break
    if bed_layer:
        # 如果用户通过参数传入 spawn 坐标，优先使用（以 tile 单位）
        if getattr(args, 'spawn_x', None) is not None and getattr(args, 'spawn_y', None) is not None:
            sx = int(args.spawn_x)
            sy = int(args.spawn_y)
            print(f"使用命令行提供的出生格: ({sx},{sy})")
        else:
            # pass width and collidable_gids to find_spawn_near (new signature)
            sx, sy = find_spawn_near(bed_spawn[0], bed_spawn[1], width, collidable_gids)
        player_x = sx * TILE_SIZE
        player_y = sy * TILE_SIZE

        # dry-run 模式下只打印选择并退出（不创建窗口或主循环）
        if getattr(args, 'dry_run', False):
            print(f"dry-run: chosen spawn tile = ({sx},{sy}), map px = ({sx*TILE_SIZE},{sy*TILE_SIZE})")
            print(f"dry-run: tile_draw_size = {tile_draw_size}, scale = {scale}")
            sys.exit(0)

# movement: pixels per second
player_speed_pixels = 140

# 碰撞盒收缩（像素）：宽高各减少 shrink_pixels，碰撞框位于角色底部
shrink_pixels = 4
player_bbox_w = max(1, TILE_SIZE - shrink_pixels)
player_bbox_h = max(1, TILE_SIZE - shrink_pixels)
player_bbox_xoff = (TILE_SIZE - player_bbox_w) // 2
player_bbox_yoff = (TILE_SIZE - player_bbox_h)

# 相机与活动区设置
ACTIVITY_H = 400  # 活动区高度（像素）
activity_top = (SCREEN_HEIGHT - ACTIVITY_H) // 2
activity_rect = pygame.Rect(0, activity_top, SCREEN_WIDTH, ACTIVITY_H)
# camera_x 是缩放后（目标 surface 像素）中的水平滚动偏移（0..max_scroll)
camera_x = 0
max_scroll = max(0, target_w - SCREEN_WIDTH)

# 碰撞检测函数
def check_collision(new_x, new_y):
    # new_x, new_y are map-pixel coordinates (top-left of tile).
    # use a smaller bbox aligned to player's feet for collisions
    pr = pygame.Rect(int(new_x + player_bbox_xoff), int(new_y + player_bbox_yoff), player_bbox_w, player_bbox_h)
    for tile_rect in collision_tiles:
        if pr.colliderect(tile_rect):
            return True
    return False

# 绘制交互气泡（使用指定字体），camera-aware
def draw_bubble(text, map_x, map_y, cam_x, off_x, off_y):
    # map_x,map_y 为地图像素坐标；将其转换为屏幕坐标并考虑 camera_x
    sx = int(round(map_x * scale)) + off_x - int(round(cam_x))
    sy = int(round(map_y * scale)) + off_y
    text_surf = game_font.render(text, True, (0, 0, 0))  # 黑色文字
    # 使用 tile_draw_size 保证气泡中心对齐瓦片中心
    bubble_center_x = sx + (tile_draw_size // 2)
    bubble_rect = text_surf.get_rect(center=(bubble_center_x, sy - 18))
    bubble_rect.inflate_ip(10, 8)  # 气泡内边距

    # 背景与边框（浅色 + 黑边）
    pygame.draw.rect(screen, (255, 255, 200), bubble_rect, border_radius=5)
    pygame.draw.rect(screen, (0, 0, 0), bubble_rect, 1, border_radius=5)
    screen.blit(text_surf, text_surf.get_rect(center=bubble_rect.center))

# 主循环
clock = pygame.time.Clock()
running = True
current_interactive = None  # 当前可交互物体

while running:
    # 黑色背景（未被地图覆盖的区域）
    screen.fill((0, 0, 0))

    # 1. 绘制背景层到离屏 surface，然后居中 blit 到屏幕
    try:
        m_bg = dict(m)
        m_bg['layers'] = [layer for layer in m.get('layers', []) if (layer.get('name') or '') != 'foreground_furniture']
        off_bg = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        draw_map(off_bg, m_bg, tiles_by_gid, scale=scale)
        screen.blit(off_bg, (offset_x - int(round(camera_x)), offset_y))
    except Exception:
        # fallback: keep screen black
        pass
    
    # 2. 处理玩家移动（基于帧时间）
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
    
    # 检测碰撞
    if not check_collision(new_x, new_y):
        player_x, player_y = new_x, new_y

    # 计算玩家在缩放后画布上的屏幕坐标（未应用 camera_x）
    player_screen_x_nocam = int(round(player_x * scale)) + offset_x
    player_screen_y = int(round(player_y * scale)) + offset_y

    # 如果玩家超出活动区，计算目标 camera_x，把玩家拉回活动区内（但不立刻设置，用平滑插值）
    # 注意 camera_x 是对缩放后地图的水平像素偏移
    player_screen_x_rel = player_screen_x_nocam - camera_x
    desired_camera_x = camera_x
    if player_screen_x_rel < activity_rect.left:
        desired_camera_x = camera_x - (activity_rect.left - player_screen_x_rel)
    elif player_screen_x_rel > activity_rect.right:
        desired_camera_x = camera_x + (player_screen_x_rel - activity_rect.right)
    # clamp desired
    desired_camera_x = max(0, min(max_scroll, desired_camera_x))

    # 平滑参数（每秒近似响应速度）
    camera_smooth = 8.0
    # 插值到目标 camera_x，使用帧时间 dt 保证与帧率无关
    lerp_t = max(0.0, min(1.0, camera_smooth * dt))
    camera_x = camera_x + (desired_camera_x - camera_x) * lerp_t
    
    # 3. 绘制玩家（在背景与前景之间）
    screen_x = int(round(player_x * scale)) + offset_x - int(round(camera_x))
    screen_y = int(round(player_y * scale)) + offset_y
    screen.blit(player_img, (screen_x, screen_y))

    # 4. 绘制前景遮挡家具（如果存在）
    # 4. 绘制前景遮挡家具（如果存在），作为覆盖层
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
    
    # 5. 检测并显示交互提示
    player_rect = pygame.Rect(player_x, player_y, TILE_SIZE, TILE_SIZE)
    current_interactive = None
    for obj in interactive_objects:
        if player_rect.colliderect(obj["rect"].inflate(10, 10)):  # 扩大检测范围
            current_interactive = obj
            # 绘制提示时传入 camera_x 与 offset
            draw_bubble(obj["prompt"], obj["rect"].x, obj["rect"].y, camera_x, offset_x, offset_y)
            break
    
    # 6. 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 右键点击交互
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if current_interactive:
                # 播放音效
                sound_path = current_interactive["sound_path"]
                if sound_path:
                    try:
                        pygame.mixer.Sound(sound_path).play()
                    except Exception as e:
                        print(f"音效播放失败：{e}")
                
                # 输出交互信息
                print(f"与【{current_interactive['name']}】交互")
    
    pygame.display.flip()

# 退出游戏
pygame.quit()
sys.exit()