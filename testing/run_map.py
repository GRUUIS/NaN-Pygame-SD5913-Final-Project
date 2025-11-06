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
            elif ev.type == pygame.VIDEORESIZE:
                # Window resized by the user
                win_w, win_h = ev.w, ev.h
                cam.width, cam.height = win_w, win_h
                draw_scale = compute_draw_scale(win_w, win_h)
                try:
                    collision_rects = extract_collision_rects(m, tileset_meta, collidable_gids=collidable_gids, scale=draw_scale)
                except Exception:
                    collision_rects = []
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
            if scaled_sprite is not None:
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
                if scaled_sprite is not None:
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
            if scaled_sprite is not None:
                try:
                    screen.blit(scaled_sprite, pr.topleft)
                except Exception:
                    pygame.draw.rect(screen, (50, 150, 250), pr)
            else:
                pygame.draw.rect(screen, (50, 150, 250), pr)
            cam.x = max(0, min(int(player['rect'].centerx - cam.width // 2), max(0, map_pixel_w - cam.width)))
            cam.y = max(0, min(int(player['rect'].centery - cam.height // 2), max(0, map_pixel_h - cam.height)))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0


if __name__ == "__main__":
    map_path = sys.argv[1] if len(sys.argv) > 1 else "testing/tilemap/testingmap.tmj"
    sys.exit(main(map_path))
