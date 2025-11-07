"""
Map viewer / quick demo for Tiled (.tmj) maps

How to run
1. From the project root, activate the project's virtualenv (created by the helper):
    source .venv/bin/activate

2. Run the testing runner (this file) from the project root so imports resolve:
    python testing/run_map.py

Notes / controls
- WASD: pan camera
- F: toggle fullscreen
- ESC: quit
- Window is resizable; the map will scale to fill the window proportionally.

If the window doesn't appear or is very small, make sure you're running locally (not headless)
and that the venv has pygame installed (`pip install -r requirements.txt`).

Quick edits you can make
- Change `BASE_SCALE` near the top of this file to increase/decrease default tile size.
- Adjust `MAX_WIN_W` / `MAX_WIN_H` to cap initial window size.
- To mark tiles as collidable in a data-driven way, open your .tsx in Tiled and add a
  custom property `collide=true` to the tile(s). I can update the loader to read this.

Next steps you can work on (recommended order)
1) Add tile properties for `collide` in Tiled and update the loader to use them.
2) Add an object layer in Tiled for `player_spawn` and `enemy_spawn` and load positions.
3) Integrate Pymunk and create static bodies from collision rects so a player can collide.
4) Add a simple player sprite and movement code (keyboard + physics).
5) Replace the manual TMJ parser with `pytiled-parser` if you need advanced Tiled features
    (tile flipping, tile properties, complex objects).

This file is a demo — feel free to modify and I can help wire any of the above.
"""

import sys
import os
from pathlib import Path
import pygame
import time

# Ensure project root is on sys.path so this script can be executed from the testing/ folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tiled_loader import load_map, draw_map
# Optional physics engine
try:
    import pymunk
    USE_PYMUNK = True
except Exception:
    pymunk = None
    USE_PYMUNK = False


def main(map_path="testing/tilemap/testingmap.tmj"):
    pygame.init()

    # Create a tiny temporary display so image.convert_alpha() can work on macOS/backends
    # We'll resize to the real window after the map is loaded.
    pygame.display.set_mode((1, 1))

    if not os.path.exists(map_path):
        print(f"Map file not found: {map_path}")
        return 1

    # load_map now returns (map_dict, tiles_by_gid, tileset_meta)
    m, tiles_by_gid, tileset_meta = load_map(map_path)

    # Base integer scale you want for gameplay (tiles get larger). We will
    # compute a FINAL_SCALE that fits the map to the native screen if needed.
    BASE_SCALE = 3
    # Character visual scale multiplier (1.0 = native Aseprite size). Increase to make character look bigger.
    CHARACTER_SCALE = 1.9

    # Native display size (we already created a tiny display earlier)
    info = pygame.display.Info()
    screen_native_w, screen_native_h = info.current_w, info.current_h
    # Some environments (remote CI, headless) report 1x1 — treat that as bogus
    if screen_native_w <= 1 or screen_native_h <= 1:
        # Use a large value so fit_scale stays at 1.0 (no shrink-to-fit)
        screen_native_w, screen_native_h = 9999, 9999

    map_w_tiles = m.get("width", 0)
    map_h_tiles = m.get("height", 0)
    tile_w = m.get("tilewidth", 16)
    tile_h = m.get("tileheight", 16)

    # Map size at base scale
    map_pixel_w_base = map_w_tiles * tile_w * BASE_SCALE
    map_pixel_h_base = map_h_tiles * tile_h * BASE_SCALE

    # If the map would be bigger than the screen at base scale, shrink to fit
    fit_w = screen_native_w / map_pixel_w_base if map_pixel_w_base > 0 else 1.0
    fit_h = screen_native_h / map_pixel_h_base if map_pixel_h_base > 0 else 1.0
    fit_scale = min(fit_w, fit_h, 1.0)

    FINAL_SCALE = BASE_SCALE * fit_scale

    map_pixel_w = int(map_w_tiles * tile_w * FINAL_SCALE)
    map_pixel_h = int(map_h_tiles * tile_h * FINAL_SCALE)

    # Window size: fit the map but cap it so it's not enormous for gameplay
    # Use a reasonable maximum window size (pixels). You can tweak these.
    MAX_WIN_W, MAX_WIN_H = 1200, 800
    # Enforce a sensible minimum so the window is visible
    MIN_W, MIN_H = 320, 240

    # If native screen info was bogus we set screen_native_w to a large number.
    # Only consider the native screen when it's realistic (>1px).
    native_valid = (info.current_w > 1 and info.current_h > 1)
    cap_w = min(MAX_WIN_W, screen_native_w) if native_valid else MAX_WIN_W
    cap_h = min(MAX_WIN_H, screen_native_h) if native_valid else MAX_WIN_H

    win_w = max(MIN_W, min(map_pixel_w, cap_w))
    win_h = max(MIN_H, min(map_pixel_h, cap_h))

    # Create a resizable window so you can expand/shrink if desired
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption("Tiled TMJ Map Viewer")

    # Debug/logging: print computed values to help if window doesn't appear
    print("[map debug] tiles: {}x{} @ {}x{} px tile".format(map_w_tiles, map_h_tiles, tile_w, tile_h))
    print(f"[map debug] BASE_SCALE={BASE_SCALE:.3f} FINAL_SCALE={FINAL_SCALE:.3f}")
    print(f"[map debug] map_pixel (w,h) = ({map_pixel_w},{map_pixel_h})")
    print(f"[map debug] initial window (w,h) = ({win_w},{win_h}) screen_native=({screen_native_w},{screen_native_h})")
    try:
        ws = screen.get_size()
        print(f"[map debug] pygame display created size={ws}")
    except Exception as e:
        print(f"[map debug] pygame display created but get_size() failed: {e}")

    clock = pygame.time.Clock()
    running = True

    # Simple inventory state for the map viewer (re-uses the inventory UI from
    # the gameplay example). Toggle visibility with TAB. Inventory is drawn
    # centered at the middle of the map (world coordinates) and rendered
    # semi-transparently on top of the map when visible.
    inventory_slots = 10
    inventory = [None] * inventory_slots
    show_inventory = False
    # Opened note overlay (None or Note instance)
    opened_note = None
    opened_note_close_rect = None
    # simple on-screen message (text + timer)
    message = ""
    message_timer = 0.0
    # Inventory hover name for tooltip
    inv_hover_name = ''

    # natural map pixel size (no scale)
    map_pixel_w_natural = map_w_tiles * tile_w
    map_pixel_h_natural = map_h_tiles * tile_h

    def compute_draw_scale(win_w, win_h):
        sx = win_w / float(map_pixel_w_natural) if map_pixel_w_natural > 0 else 1.0
        sy = win_h / float(map_pixel_h_natural) if map_pixel_h_natural > 0 else 1.0
        return min(sx, sy)

    # initial draw_scale so the map fills the window proportionally
    draw_scale = compute_draw_scale(win_w, win_h)

    # Simple camera rect to pan around if map is larger than window
    cam = pygame.Rect(0, 0, win_w, win_h)

    # Build collidable gid set
    collidable_gids = set()
    # border/brown edges in your TMJ appear to be gid 44 and 43 — include them
    collidable_gids.update({43, 44})
    # include all tiles from overlaywalls (firstgid 57) and furniture (firstgid 97) if present
    if 57 in tileset_meta:
        fg = 57
        for i in range(tileset_meta[57].get("tilecount", 0)):
            collidable_gids.add(fg + i)
    if 97 in tileset_meta:
        fg = 97
        for i in range(tileset_meta[97].get("tilecount", 0)):
            collidable_gids.add(fg + i)
    # Extract collision rects (in scaled world coords) using the draw_scale so overlays match tiles
    try:
        from src.tiled_loader import extract_collision_rects
        collision_rects = extract_collision_rects(m, tileset_meta, collidable_gids=collidable_gids, scale=draw_scale)
    except Exception:
        collision_rects = []

    # --- Pymunk integration: build physics world from collision_rects ---
    space = None
    pymunk_player = None  # tuple (body, shape, w, h)
    pymunk_static_shapes = []

    import globals as g
    # make gravity a bit stronger than the game's default so jumps feel less floaty
    GRAVITY_BASE = float(getattr(g, 'GRAVITY', 1200)) * 1.5

    def build_pymunk_world(player_pos=None):
        """Create a fresh pymunk.Space and static shapes from collision_rects.
        If player_pos is provided, recreate the dynamic player at that position.
        """
        nonlocal space, pymunk_player, pymunk_static_shapes
        # clear old
        pymunk_player = None
        pymunk_static_shapes = []
        if not USE_PYMUNK:
            space = None
            return
        space = pymunk.Space()
        # Pymunk uses pixels as units here; use the stronger gravity base
        space.gravity = (0.0, float(GRAVITY_BASE))

        # Add static boxes for each collision rect
        for r in collision_rects:
            bx = float(r.x + r.width / 2.0)
            by = float(r.y + r.height / 2.0)
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (bx, by)
            poly = pymunk.Poly.create_box(body, (float(r.width), float(r.height)))
            poly.friction = 1.0
            poly.elasticity = 0.0
            space.add(body, poly)
            pymunk_static_shapes.append(poly)

        # (re)create dynamic player if requested
        if player_pos is not None:
            px, py, pw, ph = player_pos
            try:
                mass = 1.0
                moment = pymunk.moment_for_box(mass, (pw, ph))
                body = pymunk.Body(mass, moment)
                body.position = (px, py)
                shape = pymunk.Poly.create_box(body, (pw, ph))
                shape.friction = 1.0
                shape.elasticity = 0.0
                space.add(body, shape)
                pymunk_player = (body, shape, pw, ph)
            except Exception:
                pymunk_player = None

    # Determine a sensible spawn position so the player starts on the floor
    # Spawn X: center of the map (middle)
    spawn_x = float((map_pixel_w_natural * draw_scale) / 2.0)
    # Default spawn platform top is the bottom of the map
    map_pixel_h = int(map_pixel_h_natural * draw_scale)
    spawn_platform_top = float(map_pixel_h)
    try:
        # Find any collision rects under spawn_x and choose the lowest (largest y)
        candidates = [r for r in collision_rects if float(r.left) <= spawn_x <= float(r.right)]
        if candidates:
            # choose the platform with the largest top (closest to the bottom)
            spawn_platform_top = float(max(candidates, key=lambda r: r.top).top)
    except Exception:
        pass

    # Build initial world (no player_pos yet)
    build_pymunk_world()

    # Create initial player: prefer Pymunk dynamic body
    # start_x/start_y used below will be set relative to spawn_platform_top
    start_x = spawn_x
    # start_y for pymunk is the center y (we'll offset by half player height when creating)
    start_y = float(spawn_platform_top)
    player = None
    use_game_player = False
    if USE_PYMUNK and space is not None:
        pw = float(max(8, 16 * draw_scale))
        ph = float(max(8, 28 * draw_scale))
        # For pymunk the player_pos expects the center; place the player so its bottom
        # sits on the spawn_platform_top
        center_y = start_y - (ph / 2.0)
        build_pymunk_world(player_pos=(start_x, center_y, pw, ph))
        if pymunk_player:
            player = pymunk_player
    # If pymunk failed, fallback to game Player or dict
    if player is None:
        try:
            from src.entities.player import Player as GamePlayer
            import globals as g
            start_x = int(2 * tile_w * draw_scale)
            start_y = int(2 * tile_h * draw_scale)
            # For GamePlayer constructor we pass top-left coordinates. Place the player
            # so their bottom sits on the spawn_platform_top and centered at spawn_x.
            pw = int(max(8, g.PLAYER_SIZE * draw_scale))
            ph = int(max(8, g.PLAYER_SIZE * draw_scale))
            px = int(spawn_x - pw // 2)
            py = int(spawn_platform_top - ph)
            player = GamePlayer(px, py)
            player.width = pw
            player.height = ph
            use_game_player = True
        except Exception:
            player_w = int(16 * draw_scale)
            player_h = int(28 * draw_scale)
            player = {
                "rect": pygame.Rect(int(spawn_x - player_w // 2), int(spawn_platform_top - player_h), player_w, player_h),
                "vel": [0.0, 0.0],
                "on_ground": False,
            }

    # Try to load a test Note object (use src.entities.note if present, otherwise testing/note.py)
    try:
        from src.entities.note import Note
    except Exception:
        try:
            import importlib.util
            note_path = os.path.join(os.path.dirname(__file__), 'note.py')
            spec = importlib.util.spec_from_file_location('testing_note', note_path)
            note_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(note_mod)
            Note = getattr(note_mod, 'Note')
        except Exception:
            Note = None

    note = None
    if Note is not None:
        try:
            note_size = int(max(8, 18 * draw_scale))
            note_x = int(spawn_x + 24 * draw_scale)
            note_y = int(spawn_platform_top - note_size)
            note = Note(note_x, note_y, size=note_size, name='note 01', content='A small scrap with scribbles')
        except Exception:
            note = None

    # Try to load icon images for note (book) and close (delete)
    note_img = None
    close_img = None
    try:
        book_path = PROJECT_ROOT / 'testing' / 'rpgiab_icon_pack_v1.3' / '16x16' / 'book.png'
        delete_path = PROJECT_ROOT / 'testing' / 'rpgiab_icon_pack_v1.3' / '16x16' / 'delete.png'
        if book_path.exists():
            note_img = pygame.image.load(str(book_path)).convert_alpha()
        if delete_path.exists():
            close_img = pygame.image.load(str(delete_path)).convert_alpha()
    except Exception:
        note_img = None
        close_img = None

    # Try to load TravelBook page left/right images for note background
    tb_left = None
    tb_right = None
    try:
        tb_base = PROJECT_ROOT / 'testing' / 'Complete_UI_Book_Styles_Pack_Free_v1.0' / '01_TravelBookLite' / 'Sprites'
        left_path = tb_base / 'UI_TravelBook_BookPageLeft01a.png'
        right_path = tb_base / 'UI_TravelBook_BookPageRight01a.png'
        if left_path.exists():
            tb_left = pygame.image.load(str(left_path)).convert_alpha()
        if right_path.exists():
            tb_right = pygame.image.load(str(right_path)).convert_alpha()
    except Exception:
        tb_left = None
        tb_right = None

    # (player was created above: either pymunk dynamic body, GamePlayer, or dict fallback)
    # Center camera on the player initially so they don't appear off-screen
    try:
        map_pixel_w = int(map_pixel_w_natural * draw_scale)
        map_pixel_h = int(map_pixel_h_natural * draw_scale)
        if USE_PYMUNK and isinstance(player, tuple):
            body, shape, pw, ph = player
            px = float(body.position.x)
            py = float(body.position.y)
            print(f"[spawn] pymunk player at ({px:.1f},{py:.1f})")
            cam.x = max(0, min(int(px - cam.width // 2), max(0, map_pixel_w - cam.width)))
            cam.y = max(0, min(int(py - cam.height // 2), max(0, map_pixel_h - cam.height)))
        elif hasattr(player, 'x'):
            px = float(getattr(player, 'x', 0))
            py = float(getattr(player, 'y', 0))
            print(f"[spawn] GamePlayer at ({px:.1f},{py:.1f})")
            cam.x = max(0, min(int(px + player.width//2 - cam.width // 2), max(0, map_pixel_w - cam.width)))
            cam.y = max(0, min(int(py + player.height//2 - cam.height // 2), max(0, map_pixel_h - cam.height)))
        else:
            rect = player.get('rect') if isinstance(player, dict) else None
            if rect is not None:
                print(f"[spawn] dict player rect at {rect.topleft}")
                cam.x = max(0, min(int(rect.centerx - cam.width // 2), max(0, map_pixel_w - cam.width)))
                cam.y = max(0, min(int(rect.centery - cam.height // 2), max(0, map_pixel_h - cam.height)))
    except Exception:
        pass

    # Try to load a character sprite if present (user added Blue_witch PNGs)
    sprite_surface = None
    try:
        # prefer an idle image if available
        possible = [
            PROJECT_ROOT / "testing" / "Blue_witch" / "B_witch_idle.png",
            PROJECT_ROOT / "testing" / "Blue_witch" / "B_witch_run.png",
        ]
        for p in possible:
            if p.exists():
                img = pygame.image.load(str(p)).convert_alpha()
                sprite_surface = img
                break
    except Exception:
        sprite_surface = None
    # Create a scaled sprite surface matching the chosen player's size
    scaled_sprite = None
    try:
        if sprite_surface is not None:
            if USE_PYMUNK and isinstance(player, tuple):
                _, _, pw, ph = player
                scaled_sprite = pygame.transform.smoothscale(sprite_surface, (int(pw), int(ph)))
            elif hasattr(player, 'width'):
                scaled_sprite = pygame.transform.smoothscale(sprite_surface, (int(player.width), int(player.height)))
            elif isinstance(player, dict) and 'rect' in player:
                r = player['rect']
                scaled_sprite = pygame.transform.smoothscale(sprite_surface, (r.width, r.height))
    except Exception:
        scaled_sprite = None

    # Try to load the Aseprite-based animation loader from the cloned repo.
    ase_manager = None
    ase_anim_map = {}
    ase_current_tag = None
    try:
        ase_src = PROJECT_ROOT / 'testing' / 'pygame_aseprite_animator' / 'src'
        if str(ase_src) not in sys.path:
            sys.path.insert(0, str(ase_src))
        from pygame_aseprite_animation.pygame_aseprite_animation import Animation, AnimationManager
        from py_aseprite.chunks import FrameTagsChunk
        ase_file = PROJECT_ROOT / 'testing' / 'Blue_witch' / 'B_witch.aseprite'
        if ase_file.exists():
            try:
                anim = Animation(str(ase_file))
                # Do NOT rescale frames to the player's physics rect here; keep native ratio.
                # However, we will optionally increase visual size by CHARACTER_SCALE while preserving ratio.
                def _ensure_transparency(frame_surf: 'pygame.Surface'):
                    # Guarantee an alpha channel. If the frame already contains transparent pixels, keep as-is.
                    try:
                        fs = frame_surf.convert_alpha()
                    except Exception:
                        fs = frame_surf.copy()
                        fs = fs.convert_alpha()
                    # fast check for any non-255 alpha
                    try:
                        import pygame.surfarray as surfarray
                        alpha = surfarray.pixels_alpha(fs)
                        any_transparent = alpha.min() < 255
                        del alpha
                    except Exception:
                        any_transparent = False
                    if any_transparent:
                        return fs
                    # No per-pixel alpha found — assume a solid background color in corners.
                    w, h = fs.get_size()
                    try:
                        corners = [fs.get_at((0,0))[:3], fs.get_at((max(0,w-1),0))[:3], fs.get_at((0,max(0,h-1)))[:3], fs.get_at((max(0,w-1),max(0,h-1)))[:3]]
                    except Exception:
                        return fs
                    from collections import Counter
                    bg = Counter(corners).most_common(1)[0][0]
                    # make this color transparent
                    fs.set_colorkey(bg)
                    return fs.convert_alpha()
                # Build a map of named tags -> (start, end) frame indices using py_aseprite frame chunks.
                tag_ranges = {}
                for frame in anim.aseprite_file.frames:
                    for chunk in getattr(frame, 'chunks', []):
                        if isinstance(chunk, FrameTagsChunk):
                            for t in chunk.tags:
                                name = t.get('name', '').lower()
                                tag_ranges[name] = (int(t.get('from', 0)), int(t.get('to', 0)))

                # Build simple Animation-like objects per tag so AnimationManager can switch between them.
                class _SimpleAnim:
                    def __init__(self, frames, durations, anchors):
                        self.animation_frames = frames
                        self.frame_duration = durations
                        # anchors: list of (anchor_x, anchor_y) per frame in surface pixels
                        self.anchors = anchors

                # If no tags found, treat whole file as a single anonymous animation
                if not tag_ranges:
                    frames = []
                    anchors = []
                    durations = list(anim.frame_duration)
                    for f in anim.animation_frames:
                        fs = _ensure_transparency(f)
                        fw, fh = fs.get_size()
                        if CHARACTER_SCALE != 1.0:
                            nw = max(1, int(round(fw * CHARACTER_SCALE)))
                            nh = max(1, int(round(fh * CHARACTER_SCALE)))
                            try:
                                fs = pygame.transform.smoothscale(fs, (nw, nh))
                            except Exception:
                                fs = pygame.transform.scale(fs, (nw, nh))
                        try:
                            br = fs.get_bounding_rect()
                            anchor_x = float(br.x + br.width / 2.0)
                            anchor_y = float(br.y + br.height)
                        except Exception:
                            anchor_x = float(fs.get_width() / 2)
                            anchor_y = float(fs.get_height())
                        frames.append(fs)
                        anchors.append((anchor_x, anchor_y))
                    ase_anim_map['default'] = _SimpleAnim(frames, durations, anchors)
                else:
                    for name, (s, e) in tag_ranges.items():
                        frames = []
                        anchors = []
                        durations = anim.frame_duration[s:e+1]
                        for f in anim.animation_frames[s:e+1]:
                            fs = _ensure_transparency(f)
                            # enlarge visually while keeping native ratio
                            fw, fh = fs.get_size()
                            if CHARACTER_SCALE != 1.0:
                                nw = max(1, int(round(fw * CHARACTER_SCALE)))
                                nh = max(1, int(round(fh * CHARACTER_SCALE)))
                                try:
                                    fs = pygame.transform.smoothscale(fs, (nw, nh))
                                except Exception:
                                    fs = pygame.transform.scale(fs, (nw, nh))
                            # compute bounding rect of visible pixels to find anchor
                            try:
                                br = fs.get_bounding_rect()
                                anchor_x = float(br.x + br.width / 2.0)
                                anchor_y = float(br.y + br.height)  # bottom of bounding box
                            except Exception:
                                anchor_x = float(fs.get_width() / 2)
                                anchor_y = float(fs.get_height())
                            frames.append(fs)
                            anchors.append((anchor_x, anchor_y))
                        ase_anim_map[name] = _SimpleAnim(frames, durations, anchors)

                # Create precomputed left-facing variants for animations when explicit left tags are not present.
                existing = set(ase_anim_map.keys())
                for name in list(existing):
                    # common left-name patterns to check
                    left_variants = [f"{name}_left", f"left_{name}", f"{name}left", f"{name}_l"]
                    found = any(v in existing for v in left_variants)
                    if not found:
                        # build left flipped frames for this animation
                        src = ase_anim_map[name]
                        try:
                            flipped_frames = [pygame.transform.flip(f, True, False) for f in src.animation_frames]
                            # compute anchors for flipped frames
                            flipped_anchors = []
                            for f in flipped_frames:
                                try:
                                    br = f.get_bounding_rect()
                                    ax = float(br.x + br.width / 2.0)
                                    ay = float(br.y + br.height)
                                except Exception:
                                    ax = float(f.get_width() / 2)
                                    ay = float(f.get_height())
                                flipped_anchors.append((ax, ay))
                            ase_anim_map[f"{name}_left"] = _SimpleAnim(flipped_frames, list(src.frame_duration), flipped_anchors)
                        except Exception:
                            # if flipping fails, skip creating left variant
                            pass

                # Choose a sensible default order: idle then walk/run then default
                anim_list = []
                if 'idle' in ase_anim_map:
                    anim_list.append(ase_anim_map['idle'])
                if 'run' in ase_anim_map:
                    anim_list.append(ase_anim_map['run'])
                if 'walk' in ase_anim_map and 'run' not in ase_anim_map:
                    anim_list.append(ase_anim_map['walk'])
                # add any remaining animations
                for k, v in ase_anim_map.items():
                    if v not in anim_list:
                        anim_list.append(v)

                if anim_list:
                    ase_manager = AnimationManager(anim_list, screen)
                    # helper to advance ase_manager timing and return current frame surface
                    def _ase_get_current_frame(manager):
                        """Advance timing and return (surface, anchor_x, anchor_y) for the current frame.
                        Returns (surface, anchor_x, anchor_y) or (None, None, None) on failure.
                        """
                        try:
                            now = round(time.time() * 1000)
                            if now > manager.tend:
                                if manager.framenum == len(manager.current_animation.frame_duration) - 1:
                                    if manager.next_animation is not None:
                                        manager.current_animation = manager.next_animation
                                    manager.framenum = 0
                                else:
                                    manager.framenum += 1
                                manager.tstart = now
                                manager.tend = manager.tstart + manager.current_animation.frame_duration[manager.framenum]
                            ca = manager.current_animation
                            fi = int(getattr(manager, 'framenum', 0))
                            if ca and ca.animation_frames:
                                surf = ca.animation_frames[fi]
                                try:
                                    ax, ay = ca.anchors[fi]
                                except Exception:
                                    ax = float(surf.get_width() / 2)
                                    ay = float(surf.get_height())
                                return surf, ax, ay
                        except Exception:
                            return None, None, None
                        return None, None, None
                else:
                    ase_manager = None
            except Exception:
                ase_manager = None
    except Exception:
        ase_manager = None

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                # Basic WASD camera movement (pan by one tile at draw_scale)
                pan_x = max(8, int(tile_w * draw_scale))
                pan_y = max(8, int(tile_h * draw_scale))
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_a:
                    cam.x = max(0, cam.x - pan_x)
                elif ev.key == pygame.K_d:
                    cam.x = min(max(0, map_pixel_w - cam.width), cam.x + pan_x)
                elif ev.key == pygame.K_w:
                    cam.y = max(0, cam.y - pan_y)
                elif ev.key == pygame.K_s:
                    cam.y = min(max(0, map_pixel_h - cam.height), cam.y + pan_y)
                elif ev.key == pygame.K_f:
                    # toggle fullscreen
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        info = pygame.display.Info()
                        win_w, win_h = info.current_w, info.current_h
                        cam.width, cam.height = win_w, win_h
                    else:
                        screen = pygame.display.set_mode((min(800, map_pixel_w), min(600, map_pixel_h)), pygame.RESIZABLE)
                        cam.width, cam.height = screen.get_size()
                    draw_scale = compute_draw_scale(cam.width, cam.height)
                    try:
                        collision_rects = extract_collision_rects(m, tileset_meta, collidable_gids=collidable_gids, scale=draw_scale)
                    except Exception:
                        collision_rects = []
                elif ev.key == pygame.K_TAB:
                    # Toggle inventory overlay visibility
                    try:
                        show_inventory = not show_inventory
                    except Exception:
                        show_inventory = True
                elif ev.key == pygame.K_c:
                    # Try to pick up nearby note (if present and not already collected)
                    try:
                        if note and not note.collected:
                            # find player rect in world coords
                            if USE_PYMUNK and isinstance(player, tuple):
                                body, _, pw, ph = player
                                player_rect = pygame.Rect(int(body.position.x - pw/2), int(body.position.y - ph/2), int(pw), int(ph))
                            elif hasattr(player, 'x'):
                                player_rect = pygame.Rect(int(player.x), int(player.y), int(player.width), int(player.height))
                            else:
                                player_rect = player.get('rect') if isinstance(player, dict) else None
                            if player_rect and player_rect.colliderect(note.get_rect()):
                                note.collect()
                                placed = False
                                for si in range(inventory_slots):
                                    if inventory[si] is None:
                                        inventory[si] = note
                                        placed = True
                                        break
                                if not placed:
                                    message = 'Inventory full'
                                    message_timer = 2.0
                                else:
                                    message = f'Picked up {note.name}'
                                    message_timer = 2.0
                    except Exception:
                        pass
            elif ev.type == pygame.VIDEORESIZE:
                # Window resized by the user
                win_w, win_h = ev.w, ev.h
                cam.width, cam.height = win_w, win_h
                draw_scale = compute_draw_scale(win_w, win_h)
                try:
                    collision_rects = extract_collision_rects(m, tileset_meta, collidable_gids=collidable_gids, scale=draw_scale)
                except Exception:
                    collision_rects = []
            elif ev.type == pygame.MOUSEMOTION:
                # Inventory slot hover detection (show item name tooltip)
                try:
                    mx, my = ev.pos
                    inv_hover_name = ''
                    if show_inventory:
                        inv_w = 48
                        inv_h = 48
                        spacing = 8
                        total_w = inventory_slots * inv_w + (inventory_slots - 1) * spacing
                        center_map_x = int((map_pixel_w_natural * draw_scale) / 2.0)
                        center_map_y = int((map_pixel_h_natural * draw_scale) / 2.0)
                        screen_cx = center_map_x - cam.x
                        screen_cy = center_map_y - cam.y
                        panel_w = total_w + 20
                        panel_h = inv_h + 20
                        panel_x = int(screen_cx - panel_w // 2)
                        panel_y = int(screen_cy - panel_h // 2)
                        for i in range(inventory_slots):
                            inv_x = panel_x + 10 + i * (inv_w + spacing)
                            inv_rect = pygame.Rect(inv_x, panel_y + 10, inv_w, inv_h)
                            if inv_rect.collidepoint(mx, my):
                                item = inventory[i]
                                if item is not None:
                                    try:
                                        if isinstance(item, dict):
                                            inv_hover_name = item.get('name', '')
                                        else:
                                            inv_hover_name = getattr(item, 'name', '')
                                    except Exception:
                                        inv_hover_name = ''
                                break
                except Exception:
                    inv_hover_name = ''
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Left click: first, if an opened-note close button exists, allow clicking it to close
                try:
                    mx, my = ev.pos
                    if opened_note_close_rect is not None:
                        try:
                            if opened_note_close_rect.collidepoint(mx, my):
                                opened_note = None
                                opened_note_close_rect = None
                                # consume the click
                                continue
                        except Exception:
                            pass
                    # Otherwise, if inventory overlay is visible, attempt to open clicked slot
                    if show_inventory:
                        inv_w = 48
                        inv_h = 48
                        spacing = 8
                        total_w = inventory_slots * inv_w + (inventory_slots - 1) * spacing
                        center_map_x = int((map_pixel_w_natural * draw_scale) / 2.0)
                        center_map_y = int((map_pixel_h_natural * draw_scale) / 2.0)
                        screen_cx = center_map_x - cam.x
                        screen_cy = center_map_y - cam.y
                        panel_w = total_w + 20
                        panel_h = inv_h + 20
                        panel_x = int(screen_cx - panel_w // 2)
                        panel_y = int(screen_cy - panel_h // 2)
                        mx, my = ev.pos
                        # compute local coords relative to panel
                        lx = mx - panel_x
                        ly = my - panel_y
                        for i in range(inventory_slots):
                            inv_x = 10 + i * (inv_w + spacing)
                            inv_rect = pygame.Rect(panel_x + inv_x, panel_y + 10, inv_w, inv_h)
                            if inv_rect.collidepoint(mx, my):
                                item = inventory[i]
                                if item is not None and hasattr(item, 'render_content'):
                                    opened_note = item
                                break
                        # If there is an opened note close button from a previous frame, allow clicking it to close
                        try:
                            if opened_note_close_rect is not None:
                                if opened_note_close_rect.collidepoint(mx, my):
                                    opened_note = None
                                    opened_note_close_rect = None
                        except Exception:
                            pass
                except Exception:
                    pass
        # --- player update using game Player if available ---
        dt = clock.get_time() / 1000.0
        # If we're using a Pymunk-backed player (tuple: (body, shape, w, h)),
        # drive it here and step the physics space so it isn't left untouched
        # (previously the code fell through and later tried to treat the tuple
        # like a dict which raised the TypeError you saw).
        if USE_PYMUNK and isinstance(player, tuple) and space is not None:
            try:
                body, shape, pw, ph = player
                keys = pygame.key.get_pressed()
                move_speed = 160 * draw_scale
                # horizontal control (set velocity directly for simplicity)
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    vx = -move_speed
                elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    vx = move_speed
                else:
                    vx = body.velocity.x * 0.8

                vy = body.velocity.y
                # simple grounded check: if vertical speed is very small, allow jump
                # reduce jump impulse so player doesn't jump too high
                if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and abs(body.velocity.y) < 1.0:
                    vy = -300 * draw_scale

                body.velocity = (float(vx), float(vy))
                # Step the physics world for this frame
                try:
                    space.step(dt)
                except Exception:
                    pass
            except Exception:
                # If anything goes wrong with the pymunk path, continue to
                # the other player code paths (we'll avoid treating tuple as dict)
                pass
        # Build platform wrappers from collision rects for player collision
        class _P:
            def __init__(self, rect):
                self.rect = rect

        platforms = [ _P(r) for r in collision_rects ]

        # Only call the game Player update path if the player is not a pymunk tuple
        if not (USE_PYMUNK and isinstance(player, tuple)):
            try:
                # GamePlayer has update(dt, platforms)
                player.update(dt, platforms)
            except Exception as e:
                # If player is the fallback dict, run the simple physics fallback.
                # If player is a Player instance, avoid treating it like a dict (which raises
                # TypeError: 'Player' object is not subscriptable). Instead log the error and skip.
                import traceback
                traceback.print_exc()
                if isinstance(player, dict):
                    dt = clock.get_time() / 1000.0
                    keys = pygame.key.get_pressed()
                    move_speed = 160 * draw_scale
                    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                        player['vel'][0] = -move_speed
                    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                        player['vel'][0] = move_speed
                    else:
                        player['vel'][0] *= 0.8
                    if keys[pygame.K_SPACE] and player['on_ground']:
                        # reduced jump impulse for the fallback physics
                        player['vel'][1] = -300 * draw_scale
                        player['on_ground'] = False
                        # use the stronger gravity base for the simple fallback physics
                        gravity = GRAVITY_BASE * draw_scale
                    player['vel'][1] += gravity * dt
                    dx = player['vel'][0] * dt
                    dy = player['vel'][1] * dt
                    player['rect'].x += int(dx)
                    for r in collision_rects:
                        if player['rect'].colliderect(r):
                            if dx > 0:
                                player['rect'].right = r.left
                            elif dx < 0:
                                player['rect'].left = r.right
                            player['vel'][0] = 0
                    player['rect'].y += int(dy)
                    player['on_ground'] = False
                    for r in collision_rects:
                        if player['rect'].colliderect(r):
                            if dy > 0:
                                player['rect'].bottom = r.top
                                player['vel'][1] = 0
                                player['on_ground'] = True
                            elif dy < 0:
                                player['rect'].top = r.bottom
                                player['vel'][1] = 0
                else:
                    print("Warning: player.update failed for Player instance; skipping fallback.")

        # --- wrap-around through opposite-side doors ---
        # If the player walks out past the map edge, teleport them to the opposite side.
        # This is a simple wrap behavior (can be limited to door tiles later).
        cur_map_w = int(map_pixel_w_natural * draw_scale)
        cur_map_h = int(map_pixel_h_natural * draw_scale)
        try:
            if USE_PYMUNK and isinstance(player, tuple):
                body, shape, pw, ph = player
                halfw = float(pw) / 2.0
                halfh = float(ph) / 2.0
                bx = float(body.position.x)
                by = float(body.position.y)
                wrapped = False
                if bx < -halfw:
                    body.position = (cur_map_w + halfw, by)
                    wrapped = True
                elif bx > cur_map_w + halfw:
                    body.position = (-halfw, by)
                    wrapped = True
                if by < -halfh:
                    body.position = (body.position.x, cur_map_h + halfh)
                    wrapped = True
                elif by > cur_map_h + halfh:
                    body.position = (body.position.x, -halfh)
                    wrapped = True
                if wrapped:
                    # damp velocities when teleporting to avoid flying off
                    try:
                        body.velocity = (0.0, 0.0)
                    except Exception:
                        pass
            elif hasattr(player, 'x'):
                # Game Player instance
                px = float(getattr(player, 'x', 0))
                py = float(getattr(player, 'y', 0))
                pw = float(getattr(player, 'width', 16))
                ph = float(getattr(player, 'height', 16))
                halfw = pw / 2.0
                halfh = ph / 2.0
                wrapped = False
                if px + halfw < 0:
                    player.x = cur_map_w - halfw
                    wrapped = True
                elif px - halfw > cur_map_w:
                    player.x = halfw
                    wrapped = True
                if py + halfh < 0:
                    player.y = cur_map_h - halfh
                    wrapped = True
                elif py - halfh > cur_map_h:
                    player.y = halfh
                    wrapped = True
                if wrapped:
                    # try to zero velocities if available
                    if hasattr(player, 'vx'):
                        try:
                            player.vx = 0
                        except Exception:
                            pass
                    if hasattr(player, 'vy'):
                        try:
                            player.vy = 0
                        except Exception:
                            pass
            else:
                # dict fallback
                rect = player.get('rect') if isinstance(player, dict) else None
                if rect is not None:
                    wrapped = False
                    if rect.centerx < 0:
                        rect.centerx = cur_map_w - 1
                        wrapped = True
                    elif rect.centerx > cur_map_w:
                        rect.centerx = 1
                        wrapped = True
                    if rect.centery < 0:
                        rect.centery = cur_map_h - 1
                        wrapped = True
                    elif rect.centery > cur_map_h:
                        rect.centery = 1
                        wrapped = True
                    if wrapped:
                        # reset vertical velocity so they don't immediately fall through
                        try:
                            player['vel'][0] = 0
                            player['vel'][1] = 0
                        except Exception:
                            pass
        except Exception:
            # non-critical: if wrap logic errors, continue without wrapping
            pass

        screen.fill((0, 0, 0))
        # Recompute map display pixel size for current draw_scale (for camera bounds)
        map_pixel_w = int(map_pixel_w_natural * draw_scale)
        map_pixel_h = int(map_pixel_h_natural * draw_scale)
        draw_map(screen, m, tiles_by_gid, camera_rect=cam, scale=draw_scale)

        # Draw collision rects (brown translucent)
        for r in collision_rects:
            rr = pygame.Rect(r.x - cam.x, r.y - cam.y, r.width, r.height)
            s = pygame.Surface((rr.width, rr.height), pygame.SRCALPHA)
            s.fill((139, 69, 19, 160))  # brown with alpha
            screen.blit(s, (rr.x, rr.y))

        # Draw note in world coordinates (if present and not collected)
        try:
                if note is not None and not getattr(note, 'collected', False):
                    nr = note.get_rect()
                    screen_nr = pygame.Rect(int(nr.x - cam.x), int(nr.y - cam.y), nr.width, nr.height)
                    # If we loaded a book icon, draw it; otherwise draw paper-colored rect
                    try:
                        if note_img is not None:
                            # scale icon to note size
                            try:
                                img = pygame.transform.smoothscale(note_img, (screen_nr.width, screen_nr.height))
                            except Exception:
                                img = pygame.transform.scale(note_img, (screen_nr.width, screen_nr.height))
                            screen.blit(img, screen_nr.topleft)
                        else:
                            pygame.draw.rect(screen, (230, 200, 80), screen_nr)
                            pygame.draw.rect(screen, (120, 90, 30), screen_nr, 2)
                        # optional collision box debug
                        try:
                            if getattr(g, 'SHOW_COLLISION_BOXES', False):
                                pygame.draw.rect(screen, (255, 0, 255), screen_nr, 1)
                        except Exception:
                            pass
                    except Exception:
                        pass
        except Exception:
            pass

        # Draw player (use game Player if available)
        if hasattr(player, 'x'):
            # GamePlayer: compute screen rect
            pr = pygame.Rect(int(player.x - cam.x), int(player.y - cam.y), int(player.width), int(player.height))
            # choose color similarly to Player.draw
            import globals as g
            if getattr(player, 'invincible_time', 0) > 0:
                if int(getattr(player, 'invincible_time', 0) * 10) % 2:
                    color = g.COLORS['player_invincible']
                else:
                    color = g.COLORS['player']
            elif not getattr(player, 'on_ground', True):
                color = g.COLORS['player_jumping']
            else:
                color = g.COLORS['player']
            if ase_manager is not None and ase_anim_map:
                try:
                    # choose animation based on horizontal speed
                    desired = 'idle'
                    vx = 0.0
                    if USE_PYMUNK and isinstance(player, tuple):
                        body, _, _, _ = player
                        vx = float(body.velocity.x)
                    elif hasattr(player, 'vx'):
                        vx = float(getattr(player, 'vx', 0.0))
                    elif isinstance(player, dict) and 'vel' in player:
                        try:
                            vx = float(player['vel'][0])
                        except Exception:
                            vx = 0.0
                    if abs(vx) > 10.0:
                        if 'run' in ase_anim_map:
                            desired = 'run'
                        elif 'walk' in ase_anim_map:
                            desired = 'walk'
                    # switch animation if needed
                    desired_anim = ase_anim_map.get(desired) or next(iter(ase_anim_map.values()))
                    if getattr(ase_manager, 'current_animation', None) is not desired_anim:
                        try:
                            ase_manager.start_animation(desired_anim)
                        except Exception:
                            pass
                    # align sprite using per-frame anchors so flipping doesn't shift the visible character
                    try:
                        # determine horizontal velocity for facing
                        vx = 0.0
                        if hasattr(player, 'vx'):
                            try:
                                vx = float(getattr(player, 'vx', 0.0))
                            except Exception:
                                vx = 0.0
                        elif hasattr(player, 'vel'):
                            try:
                                vx = float(getattr(player, 'vel')[0])
                            except Exception:
                                vx = 0.0
                        facing_left = vx < -10.0
                        # prefer left-named animation if available
                        desired_key = desired + ("_left" if facing_left else "")
                        desired_anim2 = ase_anim_map.get(desired_key) or ase_anim_map.get(desired) or next(iter(ase_anim_map.values()))
                        if getattr(ase_manager, 'current_animation', None) is not desired_anim2:
                            try:
                                ase_manager.start_animation(desired_anim2)
                            except Exception:
                                pass
                        # draw current frame using anchors
                        ca = ase_manager.current_animation
                        fi = int(getattr(ase_manager, 'framenum', 0))
                        if ca and ca.animation_frames:
                            try:
                                surf = ca.animation_frames[fi]
                                ax, ay = ca.anchors[fi] if fi < len(ca.anchors) else (float(surf.get_width()/2), float(surf.get_height()))
                                fw, fh = surf.get_size()
                                draw_x = int(pr.x + (pr.width / 2.0) - ax)
                                draw_y = int(pr.y + (pr.height) - ay)
                                screen.blit(surf, (draw_x, draw_y))
                            except Exception:
                                try:
                                    screen.blit(ca.animation_frames[fi], (pr.x, pr.y))
                                except Exception:
                                    pass
                        else:
                            try:
                                ase_manager.update_self(pr.x, pr.y)
                            except Exception:
                                pass
                    except Exception:
                        try:
                            ase_manager.update_self(pr.x, pr.y)
                        except Exception:
                            pass
                except Exception:
                    if scaled_sprite is not None:
                        try:
                            screen.blit(scaled_sprite, pr.topleft)
                        except Exception:
                            pygame.draw.rect(screen, color, pr)
                    else:
                        pygame.draw.rect(screen, color, pr)
            elif scaled_sprite is not None:
                try:
                    screen.blit(scaled_sprite, pr.topleft)
                except Exception:
                    pygame.draw.rect(screen, color, pr)
            else:
                pygame.draw.rect(screen, color, pr)

            # center camera on player (clamped)
            cam.x = max(0, min(int(player.x + player.width//2 - cam.width // 2), max(0, map_pixel_w - cam.width)))
            cam.y = max(0, min(int(player.y + player.height//2 - cam.height // 2), max(0, map_pixel_h - cam.height)))
        elif USE_PYMUNK and isinstance(player, tuple):
            # Pymunk player tuple: (body, shape, w, h)
            try:
                body, shape, pw, ph = player
                # body.position is center-based; compute top-left for pygame.Rect
                bx = float(body.position.x)
                by = float(body.position.y)
                pr = pygame.Rect(int(bx - float(pw) / 2.0 - cam.x), int(by - float(ph) / 2.0 - cam.y), int(pw), int(ph))
                if ase_manager is not None and ase_anim_map:
                    try:
                        # For pymunk player, pick animation based on horizontal speed
                        vx = float(body.velocity.x)
                        desired = 'idle'
                        if abs(vx) > 10.0:
                            if 'run' in ase_anim_map:
                                desired = 'run'
                            elif 'walk' in ase_anim_map:
                                desired = 'walk'
                        # decide facing and prefer left-named animation if needed
                        facing_left = vx < -10.0
                        desired_key = desired + ("_left" if facing_left else "")
                        desired_anim = ase_anim_map.get(desired_key) or ase_anim_map.get(desired) or next(iter(ase_anim_map.values()))
                        if getattr(ase_manager, 'current_animation', None) is not desired_anim:
                            try:
                                ase_manager.start_animation(desired_anim)
                            except Exception:
                                pass
                        # compute draw position so sprite bottom aligns with physics rect bottom
                        try:
                            cur_anim = ase_manager.current_animation
                            fi = int(getattr(ase_manager, 'framenum', 0))
                            if cur_anim and cur_anim.animation_frames:
                                try:
                                    surf = cur_anim.animation_frames[fi]
                                    ax, ay = cur_anim.anchors[fi] if fi < len(cur_anim.anchors) else (float(surf.get_width()/2), float(surf.get_height()))
                                    fw, fh = surf.get_size()
                                    draw_x = int(pr.x + (pr.width / 2.0) - ax)
                                    draw_y = int(pr.y + (pr.height) - ay)
                                    screen.blit(surf, (draw_x, draw_y))
                                except Exception:
                                    try:
                                        screen.blit(cur_anim.animation_frames[fi], (pr.x, pr.y))
                                    except Exception:
                                        pass
                            else:
                                try:
                                    ase_manager.update_self(pr.x, pr.y)
                                except Exception:
                                    pass
                        except Exception:
                            try:
                                ase_manager.update_self(pr.x, pr.y)
                            except Exception:
                                pass
                    except Exception:
                        if scaled_sprite is not None:
                            try:
                                screen.blit(scaled_sprite, pr.topleft)
                            except Exception:
                                pygame.draw.rect(screen, (50, 150, 250), pr)
                        else:
                            pygame.draw.rect(screen, (50, 150, 250), pr)
                elif scaled_sprite is not None:
                    try:
                        screen.blit(scaled_sprite, pr.topleft)
                    except Exception:
                        pygame.draw.rect(screen, (50, 150, 250), pr)
                else:
                    pygame.draw.rect(screen, (50, 150, 250), pr)
                # center camera on player's body position
                cam.x = max(0, min(int(bx - cam.width // 2), max(0, map_pixel_w - cam.width)))
                cam.y = max(0, min(int(by - cam.height // 2), max(0, map_pixel_h - cam.height)))
            except Exception:
                # If something unexpected, skip drawing the pymunk player to avoid errors
                pass
        else:
            pr = pygame.Rect(player['rect'].x - cam.x, player['rect'].y - cam.y, player['rect'].width, player['rect'].height)
            if ase_manager is not None and ase_anim_map:
                try:
                    # choose animation based on dict velocity if available
                    vx = 0.0
                    try:
                        vx = float(player.get('vel', [0.0, 0.0])[0])
                    except Exception:
                        vx = 0.0
                    desired = 'idle'
                    if abs(vx) > 10.0:
                        if 'run' in ase_anim_map:
                            desired = 'run'
                        elif 'walk' in ase_anim_map:
                            desired = 'walk'
                    # choose left variant if moving left
                    facing_left = vx < -10.0
                    desired_key = desired + ("_left" if facing_left else "")
                    desired_anim = ase_anim_map.get(desired_key) or ase_anim_map.get(desired) or next(iter(ase_anim_map.values()))
                    if getattr(ase_manager, 'current_animation', None) is not desired_anim:
                        try:
                            ase_manager.start_animation(desired_anim)
                        except Exception:
                            pass
                    try:
                        cur_anim = ase_manager.current_animation
                        fi = int(getattr(ase_manager, 'framenum', 0))
                        if cur_anim and cur_anim.animation_frames:
                            try:
                                surf = cur_anim.animation_frames[fi]
                                ax, ay = cur_anim.anchors[fi] if fi < len(cur_anim.anchors) else (float(surf.get_width()/2), float(surf.get_height()))
                                fw, fh = surf.get_size()
                                draw_x = int(pr.x + (pr.width / 2.0) - ax)
                                draw_y = int(pr.y + (pr.height) - ay)
                                screen.blit(surf, (draw_x, draw_y))
                            except Exception:
                                try:
                                    screen.blit(cur_anim.animation_frames[fi], (pr.x, pr.y))
                                except Exception:
                                    pass
                        else:
                            try:
                                ase_manager.update_self(pr.x, pr.y)
                            except Exception:
                                pass
                    except Exception:
                        try:
                            ase_manager.update_self(pr.x, pr.y)
                        except Exception:
                            pass
                except Exception:
                    if scaled_sprite is not None:
                        try:
                            screen.blit(scaled_sprite, pr.topleft)
                        except Exception:
                            pygame.draw.rect(screen, (50, 150, 250), pr)
                    else:
                        pygame.draw.rect(screen, (50, 150, 250), pr)
            elif scaled_sprite is not None:
                try:
                    screen.blit(scaled_sprite, pr.topleft)
                except Exception:
                    pygame.draw.rect(screen, (50, 150, 250), pr)
            else:
                pygame.draw.rect(screen, (50, 150, 250), pr)
            cam.x = max(0, min(int(player['rect'].centerx - cam.width // 2), max(0, map_pixel_w - cam.width)))
            cam.y = max(0, min(int(player['rect'].centery - cam.height // 2), max(0, map_pixel_h - cam.height)))

        # Draw inventory overlay (centered on the map world center) if toggled
        if show_inventory:
            try:
                inv_w = 48
                inv_h = 48
                spacing = 8
                total_w = inventory_slots * inv_w + (inventory_slots - 1) * spacing
                # Map center in world pixels
                center_map_x = int((map_pixel_w_natural * draw_scale) / 2.0)
                center_map_y = int((map_pixel_h_natural * draw_scale) / 2.0)
                # Convert to screen coordinates by subtracting camera
                screen_cx = center_map_x - cam.x
                screen_cy = center_map_y - cam.y

                panel_w = total_w + 20
                panel_h = inv_h + 20
                panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                # semi-transparent dark background
                panel_surf.fill((10, 10, 10, 180))

                # Draw individual slots onto panel_surf
                for i in range(inventory_slots):
                    inv_x = 10 + i * (inv_w + spacing)
                    inv_rect = pygame.Rect(inv_x, 10, inv_w, inv_h)
                    # slot bg (semi-opaque)
                    pygame.draw.rect(panel_surf, (30, 30, 30, 220), inv_rect)
                    # border
                    pygame.draw.rect(panel_surf, (180, 180, 180, 255), inv_rect, 2)
                    item = inventory[i]
                    if item is not None:
                            thumb_rect = pygame.Rect(inv_x + 6, 10 + 6, inv_w - 12, inv_h - 12)
                            # If item is a note and we have an icon, draw it
                            try:
                                if hasattr(item, 'render_content') and note_img is not None:
                                    try:
                                        img = pygame.transform.smoothscale(note_img, (thumb_rect.width, thumb_rect.height))
                                    except Exception:
                                        img = pygame.transform.scale(note_img, (thumb_rect.width, thumb_rect.height))
                                    panel_surf.blit(img, (thumb_rect.x, thumb_rect.y))
                                else:
                                    # simple thumbnail placeholder (tools/unknown)
                                    pygame.draw.rect(panel_surf, (230, 200, 80, 255), thumb_rect)
                            except Exception:
                                pygame.draw.rect(panel_surf, (230, 200, 80, 255), thumb_rect)

                # Blit panel centered at map center on screen
                panel_x = int(screen_cx - panel_w // 2)
                panel_y = int(screen_cy - panel_h // 2)
                screen.blit(panel_surf, (panel_x, panel_y))
            except Exception:
                # drawing overlay is non-critical; ignore failures
                pass

            # Draw inventory hover tooltip if any
            try:
                if show_inventory and inv_hover_name:
                    mx, my = pygame.mouse.get_pos()
                    tip_font = pygame.font.Font(None, 20)
                    tip_surf = tip_font.render(inv_hover_name, True, (255, 255, 255))
                    tip_rect = tip_surf.get_rect(topleft=(mx + 12, my + 12))
                    bg = pygame.Surface((tip_rect.width + 8, tip_rect.height + 6), pygame.SRCALPHA)
                    bg.fill((10, 10, 10, 200))
                    screen.blit(bg, (tip_rect.left - 4, tip_rect.top - 3))
                    screen.blit(tip_surf, tip_rect)
            except Exception:
                pass

        # Draw opened note overlay if any
        if opened_note is not None:
            try:
                sw, sh = screen.get_size()
                # Note overlay dimensions (enlarged)
                note_w = 540
                note_h = 360
                center_x = sw // 2
                center_y = sh // 2
                box_rect = pygame.Rect(center_x - note_w//2, center_y - note_h//2, note_w, note_h)

                # Draw TravelBook background if assets available: left + center paper + right
                left_w = 0
                right_w = 0
                try:
                    if tb_left is not None or tb_right is not None:
                        # compute left image scaled to note_h height
                        left_w = 0
                        right_w = 0
                        if tb_left is not None:
                            lw, lh = tb_left.get_size()
                            scale_l = float(note_h) / float(lh)
                            left_w = max(1, int(round(lw * scale_l)))
                            try:
                                left_img = pygame.transform.smoothscale(tb_left, (left_w, note_h))
                            except Exception:
                                left_img = pygame.transform.scale(tb_left, (left_w, note_h))
                            screen.blit(left_img, (box_rect.left, box_rect.top))
                        if tb_right is not None:
                            rw, rh = tb_right.get_size()
                            scale_r = float(note_h) / float(rh)
                            right_w = max(1, int(round(rw * scale_r)))
                            try:
                                right_img = pygame.transform.smoothscale(tb_right, (right_w, note_h))
                            except Exception:
                                right_img = pygame.transform.scale(tb_right, (right_w, note_h))
                            screen.blit(right_img, (box_rect.right - right_w, box_rect.top))
                        # fill center area between left and right with paper color
                        center_left = box_rect.left + left_w
                        center_right = box_rect.right - right_w
                        if center_right > center_left:
                            center_rect = pygame.Rect(center_left, box_rect.top, center_right - center_left, note_h)
                            pygame.draw.rect(screen, (245, 245, 230), center_rect)
                        # draw outer border around the composed book page
                        try:
                            pygame.draw.rect(screen, (120, 90, 30), box_rect, 3)
                        except Exception:
                            pass
                    else:
                        # fallback background box
                        pygame.draw.rect(screen, (245, 245, 230), box_rect)
                        pygame.draw.rect(screen, (120, 90, 30), box_rect, 3)
                except Exception:
                    try:
                        pygame.draw.rect(screen, (245, 245, 230), box_rect)
                        pygame.draw.rect(screen, (120, 90, 30), box_rect, 3)
                    except Exception:
                        pass

                # Draw horizontal lines on the paper area
                padding = 18
                try:
                    line_color = (220, 220, 200)
                    line_y = box_rect.top + padding
                    line_spacing = 24
                    while line_y < box_rect.bottom - padding:
                        pygame.draw.line(screen, line_color, (box_rect.left + padding, line_y), (box_rect.right - padding, line_y), 1)
                        line_y += line_spacing
                except Exception:
                    pass

                # Draw content text and title (smaller font, left-page alignment)
                try:
                    # Title at top center
                    title_font = pygame.font.Font(None, 20)
                    title_surf = title_font.render(getattr(opened_note, 'name', ''), True, (80, 80, 80))
                    # Draw title above the note window with a subtle background for readability
                    title_rect = title_surf.get_rect(center=(center_x, box_rect.top - (title_surf.get_height() // 2) - 8))
                    try:
                        # subtle paper-tinted background behind title (not black)
                        bg_rect = pygame.Rect(title_rect.left - 6, title_rect.top - 4, title_rect.width + 12, title_rect.height + 6)
                        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                        bg_surf.fill((245, 245, 230, 200))
                        screen.blit(bg_surf, (bg_rect.left, bg_rect.top))
                    except Exception:
                        pass
                    # render title text (darker color for readability)
                    try:
                        title_surf = title_font.render(getattr(opened_note, 'name', ''), True, (40, 40, 40))
                        screen.blit(title_surf, title_rect)
                    except Exception:
                        screen.blit(title_surf, title_rect)

                    # Determine left page area: use the left half of the note box (respect padding)
                    # This ensures text always starts visually on the left-hand page.
                    inner_top = box_rect.top + padding
                    inner_bottom = box_rect.bottom - padding
                    inner_left = box_rect.left + padding
                    inner_width = max(1, box_rect.width - (padding * 2))
                    page_width = max(1, inner_width // 2)
                    left_page_rect = pygame.Rect(inner_left, inner_top, page_width, inner_bottom - inner_top)

                    # Content font (smaller)
                    content_font = pygame.font.Font(None, 18)
                    max_text_w = left_page_rect.width - (padding * 2)
                    words = getattr(opened_note, 'content', '').split()
                    lines = []
                    cur = ''
                    for w in words:
                        test = (cur + ' ' + w).strip()
                        try:
                            if content_font.size(test)[0] <= max_text_w:
                                cur = test
                            else:
                                if cur:
                                    lines.append(cur)
                                cur = w
                        except Exception:
                            # fallback: append and reset
                            if cur:
                                lines.append(cur)
                            cur = w
                    if cur:
                        lines.append(cur)

                    # Render wrapped lines starting on the left page (respecting inner padding)
                    ly = left_page_rect.top + 6
                    line_height = content_font.get_linesize()
                    for ln in lines:
                        if ly + line_height > left_page_rect.bottom - padding:
                            break
                        text_surf = content_font.render(ln, True, (40, 40, 40))
                        screen.blit(text_surf, (left_page_rect.left + padding + 4, ly))
                        ly += line_height
                except Exception:
                    pass
                # Close button area: prefer to fit the delete icon without distortion
                max_btn_w, max_btn_h = 80, 28
                btn_x = box_rect.left + 10
                try:
                    if close_img is not None:
                        iw, ih = close_img.get_size()
                        # scale to fit within max_btn_w x max_btn_h while preserving aspect ratio
                        scale = min(float(max_btn_w) / float(iw), float(max_btn_h) / float(ih))
                        img_w = max(1, int(round(iw * scale)))
                        img_h = max(1, int(round(ih * scale)))
                        try:
                            img = pygame.transform.smoothscale(close_img, (img_w, img_h))
                        except Exception:
                            img = pygame.transform.scale(close_img, (img_w, img_h))
                        close_rect = pygame.Rect(btn_x, box_rect.bottom - img_h - 10, img_w, img_h)
                        screen.blit(img, close_rect.topleft)
                    else:
                        btn_w, btn_h = max_btn_w, max_btn_h
                        close_rect = pygame.Rect(btn_x, box_rect.bottom - btn_h - 10, btn_w, btn_h)
                        pygame.draw.rect(screen, (180, 50, 50), close_rect)
                        pygame.draw.rect(screen, (0, 0, 0), close_rect, 2)
                        btn_font = pygame.font.Font(None, 20)
                        btn_text = btn_font.render('Close', True, (255, 255, 255))
                        btn_text_rect = btn_text.get_rect(center=close_rect.center)
                        screen.blit(btn_text, btn_text_rect)
                except Exception:
                    # fallback: simple rect if anything goes wrong
                    try:
                        close_rect = pygame.Rect(btn_x, box_rect.bottom - max_btn_h - 10, max_btn_w, max_btn_h)
                        pygame.draw.rect(screen, (180, 50, 50), close_rect)
                    except Exception:
                        close_rect = None
                opened_note_close_rect = close_rect
            except Exception:
                opened_note = None
                opened_note_close_rect = None

        # Draw transient message if any
        try:
            if message_timer > 0:
                message_surf = pygame.font.Font(None, 24).render(message, True, (255, 255, 255))
                ms_rect = message_surf.get_rect(center=(screen.get_width()//2, 30))
                screen.blit(message_surf, ms_rect)
                # decrement after draw (simple approach)
                message_timer -= clock.get_time() / 1000.0
                if message_timer <= 0:
                    message = ''
                    message_timer = 0.0
        except Exception:
            pass

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0


if __name__ == "__main__":
    # Accept an optional map path argument. If none provided, prefer a path
    # relative to this script's folder so "python testing/run_map.py" AND
    # "cd testing; python run_map.py" both work.
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
    else:
        # Default to ./tilemap/testingmap.tmj next to this script
        candidate = str(Path(__file__).parent / "tilemap" / "testingmap.tmj")

    # If not found, also try the project-root relative path used previously
    # (testing/tilemap/testingmap.tmj) to be extra forgiving.
    try:
        if not os.path.exists(candidate):
            alt = Path(__file__).resolve().parents[1] / "testing" / "tilemap" / "testingmap.tmj"
            if alt.exists():
                candidate = str(alt)
    except Exception:
        pass

    sys.exit(main(candidate))
