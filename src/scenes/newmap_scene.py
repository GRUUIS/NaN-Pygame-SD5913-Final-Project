"""Scene module to run the exploration map (newmap01).

This moves the map-related logic out of `combine/game.py` so the launcher
stays small and clean. The module provides a single `run(screen)` function
that runs the map loop and returns when the player quits or the scene ends.
"""
from __future__ import annotations
import os
import pygame
import math
from typing import List, Optional

import globals as g


def run(screen: pygame.Surface):
    """Run the newmap01 exploration scene. Blocks until the scene exits.

    Returns when the player quits the scene (e.g., ESC or window close).
    """
    # Ensure project import paths are available
    try:
        from src.tiled_loader import load_map, draw_map, extract_collision_rects
    except Exception:
        load_map = draw_map = extract_collision_rects = None

    # Require a Tiled map file under assets/newmap01/. Do not fall back to
    # the programmatic map. If the TMJ/TMX or the Tiled loader is missing,
    # return early so the launcher/menu can remain in control.
    # Search recursively under assets/newmap01/ for any .tmj or .tmx file.
    # Prefer a file named `newmap01.tmj` (JSON) if available because it's
    # generally quicker to parse; otherwise prefer `newmap01.tmx` (XML),
    # then fall back to any .tmj, then any .tmx found.
    map_path = None
    base_dir = os.path.join('assets', 'newmap01')
    found_tmj = []
    found_tmx = []
    if os.path.exists(base_dir):
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                lower = fn.lower()
                if lower.endswith('.tmj'):
                    found_tmj.append(os.path.join(root, fn))
                elif lower.endswith('.tmx'):
                    found_tmx.append(os.path.join(root, fn))

    # Prefer exact newmap01.tmj then newmap01.tmx, then any tmj, then any tmx
    def choose_preferred(found_list, preferred_name):
        for p in found_list:
            if os.path.basename(p).lower() == preferred_name:
                return p
        return found_list[0] if found_list else None

    map_path = choose_preferred(found_tmj, 'newmap01.tmj') or choose_preferred(found_tmx, 'newmap01.tmx') or (found_tmj[0] if found_tmj else (found_tmx[0] if found_tmx else None))

    if map_path:
        print(f'newmap_scene: using tiled map file: {map_path}')

    if map_path is None:
        print('No Tiled map found for newmap01 under assets/newmap01/; returning to menu')
        return

    if load_map is None:
        print('Tiled loader (src.tiled_loader) not available; cannot load newmap01')
        return

    # Load the map using the project's Tiled loader
    m, tiles_by_gid, tileset_meta = load_map(map_path)
    print(f'newmap_scene: map size tiles: {m.get("width")}x{m.get("height")}, tile: {m.get("tilewidth")}x{m.get("tileheight")}')
    print(f'newmap_scene: tiles_by_gid count: {len(tiles_by_gid)}')
    # determine collidable gids heuristically from tileset names
    collidable_gids = set()
    for firstgid, meta in (tileset_meta or {}).items():
        name = (meta.get('name') or '').lower()
        if any(k in name for k in ('overlay', 'furn', 'collision', 'wall')):
            for i in range(meta.get('tilecount', 0)):
                collidable_gids.add(firstgid + i)

    # map natural pixel sizes
    tile_w = m.get('tilewidth', 32)
    tile_h = m.get('tileheight', 32)
    map_w_tiles = m.get('width', 40)
    map_h_tiles = m.get('height', 23)
    map_px_w_natural = map_w_tiles * tile_w
    map_px_h_natural = map_h_tiles * tile_h

    def compute_draw_scale(win_w, win_h):
        sx = win_w / float(map_px_w_natural) if map_px_w_natural > 0 else 1.0
        sy = win_h / float(map_px_h_natural) if map_px_h_natural > 0 else 1.0
        return min(sx, sy, 1.0)

    draw_scale = compute_draw_scale(g.SCREENWIDTH, g.SCREENHEIGHT)
    map_px_w = int(map_px_w_natural * draw_scale)
    map_px_h = int(map_px_h_natural * draw_scale)

    # Render map into cached surface
    if draw_map is not None:
        try:
            map_surface = pygame.Surface((map_px_w, map_px_h), pygame.SRCALPHA)
            try:
                draw_map(map_surface, m, tiles_by_gid, camera_rect=None, scale=draw_scale)
            except Exception as e:
                print('newmap_scene: draw_map failed when rendering to map_surface:', e)
                map_surface = None
        except Exception:
            map_surface = None
    else:
        map_surface = None

    # Centering offset
    map_offset = (0, 0)
    if map_surface is not None and map_surface.get_width() < g.SCREENWIDTH:
        map_offset = ((g.SCREENWIDTH - map_surface.get_width()) // 2, (g.SCREENHEIGHT - map_surface.get_height()) // 2)

    # Extract collision rects (in world pixels) at draw_scale
    try:
        collision_rects = extract_collision_rects(m, tileset_meta if 'tileset_meta' in locals() else {}, collidable_gids=collidable_gids, scale=draw_scale)
    except Exception:
        collision_rects = []

    # Setup Pymunk if available
    try:
        import pymunk
        USE_PYMUNK = True
    except Exception:
        pymunk = None
        USE_PYMUNK = False

    space = None
    if USE_PYMUNK:
        space = pymunk.Space()
        space.gravity = (0.0, float(getattr(g, 'GRAVITY', 800)))
        # create static shapes from collision_rects
        for r in collision_rects:
            bx = float(r.x + r.width / 2.0)
            by = float(r.y + r.height / 2.0)
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (bx, by)
            poly = pymunk.Poly.create_box(body, (float(r.width), float(r.height)))
            poly.friction = 1.0
            poly.elasticity = 0.0
            space.add(body, poly)

    # Create dynamic player body
    player_body = None
    player_w, player_h = 32, 48
    spawn_x = float(map_px_w_natural // 2)
    spawn_y = float(tile_h * 3)
    if USE_PYMUNK and space is not None:
        try:
            mass = 1.0
            moment = pymunk.moment_for_box(mass, (player_w, player_h))
            player_body = pymunk.Body(mass, moment)
            player_body.position = (spawn_x, spawn_y)
            player_shape = pymunk.Poly.create_box(player_body, (player_w, player_h))
            player_shape.friction = 1.0
            space.add(player_body, player_shape)
        except Exception:
            player_body = None

    # Load objects from objectgroup layers
    objects = []
    for layer in m.get('layers', []):
        if layer.get('type') == 'objectgroup':
            for obj in layer.get('objects', []):
                oprops = {p.get('name'): p.get('value') for p in (obj.get('properties') or [])}
                ox = int(obj.get('x', 0))
                oy = int(obj.get('y', 0))
                ow = int(obj.get('width', 32))
                oh = int(obj.get('height', 32))
                top = oy - oh
                objects.append({'id': oprops.get('id') or obj.get('id'), 'type': oprops.get('type') or obj.get('type'), 'rect': pygame.Rect(ox, top, ow, oh), 'props': oprops})

    inventory = set()

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)
    running = True
    # debug overlay font
    dbg_font = pygame.font.SysFont(None, 18)
    while running:
        dt = clock.tick(g.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        vx = 0.0
        SPEED = 200.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vx = -SPEED
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vx = SPEED
        if USE_PYMUNK and player_body is not None:
            vy = player_body.velocity.y
            player_body.velocity = (vx, vy)
            if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]):
                p1 = (player_body.position.x, player_body.position.y + player_h/2)
                p2 = (p1[0], p1[1] + 4)
                hit = space.segment_query_first(p1, p2, 0, pymunk.ShapeFilter())
                if hit is not None:
                    player_body.apply_impulse_at_local_point((0, -180.0))

        if USE_PYMUNK and space is not None:
            space.step(dt)

        player_rect = None
        if USE_PYMUNK and player_body is not None:
            px = int(player_body.position.x - player_w/2)
            py = int(player_body.position.y - player_h/2)
            player_rect = pygame.Rect(px, py, int(player_w), int(player_h))
        else:
            player_rect = pygame.Rect(64, 64, 32, 48)

        for obj in list(objects):
            if player_rect.colliderect(obj['rect']):
                inventory.add(obj.get('id'))
                objects.remove(obj)

        screen.fill((10, 10, 20))
        if map_surface is not None:
            screen.blit(map_surface, map_offset)
        else:
            try:
                draw_map(screen, m, tiles_by_gid, camera_rect=None, scale=draw_scale)
            except Exception as e:
                print('newmap_scene: draw_map fallback to screen failed:', e)
                # Draw a visible placeholder so the user sees something
                pygame.draw.rect(screen, (80, 40, 120), (0, 0, 200, 200))

        # On-screen debug overlay so you don't have to check the console
        try:
            lines = []
            lines.append(f'map: {os.path.basename(map_path) if map_path else "(none)"}')
            lines.append(f'size: {m.get("width")}x{m.get("height")} tiles')
            lines.append(f'tile: {m.get("tilewidth")}x{m.get("tileheight")}')
            lines.append(f'layers: {len(m.get("layers", []))}')
            lines.append(f'tiles_by_gid: {len(tiles_by_gid)}')
            lines.append(f'map_surface: {"yes" if map_surface is not None else "no"}')
            for i, ln in enumerate(lines):
                surf = dbg_font.render(ln, True, (255,255,255))
                screen.blit(surf, (8, 32 + i*18))
        except Exception:
            pass

        for obj in objects:
            sr = obj['rect'].move(map_offset[0], map_offset[1])
            pygame.draw.rect(screen, (200, 200, 100), sr)

        if player_rect:
            screen_pr = player_rect.move(map_offset[0], map_offset[1])
            pygame.draw.rect(screen, (100, 180, 255), screen_pr)

        txt = font.render(f'Inventory: {sorted(list(inventory))}', True, (255,255,255))
        screen.blit(txt, (8,8))

        pygame.display.flip()

    return
