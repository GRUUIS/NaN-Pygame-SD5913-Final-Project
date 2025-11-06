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

    # --- Player: use the existing Player entity from the game code ---
    try:
        from src.entities.player import Player as GamePlayer
        import globals as g
        # Instantiate player at a safe spawn (tile 2,2)
        start_x = int(2 * tile_w * draw_scale)
        start_y = int(2 * tile_h * draw_scale)
        player = GamePlayer(start_x, start_y)
        # Override player size to match tile scaling
        player.width = int(max(8, g.PLAYER_SIZE * draw_scale))
        player.height = int(max(8, g.PLAYER_SIZE * draw_scale))
    except Exception:
        # Fallback to simple rectangle player if import fails
        player_w = int(16 * draw_scale)
        player_h = int(28 * draw_scale)
        player = {
            "rect": pygame.Rect(32, 32, player_w, player_h),
            "vel": [0.0, 0.0],
            "on_ground": False,
        }

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
        # Build platform wrappers from collision rects for player collision
        class _P:
            def __init__(self, rect):
                self.rect = rect

        platforms = [ _P(r) for r in collision_rects ]

        try:
            # GamePlayer has update(dt, platforms)
            player.update(dt, platforms)
        except Exception:
            # Fallback: if player is the simple dict, perform previous simple physics
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
                player['vel'][1] = -420 * draw_scale
                player['on_ground'] = False
            gravity = 1200 * draw_scale
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

        # Draw player (simple rectangle)
        pr = pygame.Rect(player['rect'].x - cam.x, player['rect'].y - cam.y, player['rect'].width, player['rect'].height)
        pygame.draw.rect(screen, (50, 150, 250), pr)

        # Optionally center camera on player (clamp to map bounds)
        cam.x = max(0, min(int(player['rect'].centerx - cam.width // 2), max(0, map_pixel_w - cam.width)))
        cam.y = max(0, min(int(player['rect'].centery - cam.height // 2), max(0, map_pixel_h - cam.height)))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0


if __name__ == "__main__":
    map_path = sys.argv[1] if len(sys.argv) > 1 else "testing/tilemap/testingmap.tmj"
    sys.exit(main(map_path))
