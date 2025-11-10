"""Scene module to run the exploration map (newmap01).

This scene intentionally removes the physics/collision system. The player
is a simple position/rect in scaled screen coordinates. Decorative object
layers (layer index 1 or named "object") are ignored for collision.

Features kept:
- Map rendering using src.tiled_loader.draw_map
- Door teleport behavior (player teleports to opposite door when inventory empty)
- Object pickup from object layers (objects are non-blocking)
"""
from __future__ import annotations
import os
from collections import Counter
import pygame
from typing import Optional

import globals as g


def run(screen: pygame.Surface):
    """Run the `newmap01` exploration scene without physics.

    This blocks until the scene exits. It looks for a tiled map under
    `assets/newmap01` and prefers `.tmj` over `.tmx` if both exist.
    """
    try:
        from src.tiled_loader import load_map, draw_map
    except Exception:
        print('newmap_scene: could not import tiled loader')
        return

    base_dir = os.path.join('assets', 'newmap01')
    map_path = None
    if os.path.exists(base_dir):
        found_tmj = []
        found_tmx = []
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                lower = fn.lower()
                if lower.endswith('.tmj'):
                    found_tmj.append(os.path.join(root, fn))
                elif lower.endswith('.tmx'):
                    found_tmx.append(os.path.join(root, fn))

        def choose_preferred(found_list, preferred_name):
            for p in found_list:
                if os.path.basename(p).lower() == preferred_name:
                    return p
            return found_list[0] if found_list else None

        map_path = choose_preferred(found_tmj, 'newmap01.tmj') or choose_preferred(found_tmx, 'newmap01.tmx') or (found_tmj[0] if found_tmj else (found_tmx[0] if found_tmx else None))

    if not map_path:
        print('newmap_scene: no tiled map found; returning')
        return

    m, tiles_by_gid, tileset_meta = load_map(map_path)

    # Ensure we have visible placeholder tiles if loader returned few tiles
    if not tiles_by_gid or len(tiles_by_gid) < 8:
        gids = set()
        for layer in m.get('layers', []):
            if layer.get('type') != 'tilelayer':
                continue
            for raw in layer.get('data', []):
                gid = raw & 0x1FFFFFFF
                if gid:
                    gids.add(gid)

        tile_w = m.get('tilewidth', 32)
        tile_h = m.get('tileheight', 32)
        import pygame as _pygame
        for gid in sorted(gids):
            surf = _pygame.Surface((tile_w, tile_h), _pygame.SRCALPHA)
            r = (gid * 97) % 200 + 20
            gcol = (gid * 57) % 200 + 20
            b = (gid * 31) % 200 + 20
            surf.fill((r, gcol, b))
            try:
                f = _pygame.font.SysFont(None, max(12, tile_w // 3))
                txt = f.render(str(gid), True, (255, 255, 255))
                surf.blit(txt, (2, 2))
            except Exception:
                pass
            tiles_by_gid[gid] = surf

    # Classify tiles as floor/door/wall heuristically so we can pick a spawn
    # on a floor tile and detect doors for teleportation.
    wall_gids = set()
    floor_gids = set()
    door_gids = set()
    gid_avg = {}
    for gid, surf in list(tiles_by_gid.items()):
        try:
            w, h = surf.get_size()
            pts = [(w // 2, h // 2), (max(0, w // 4), h // 2), (min(w - 1, 3 * w // 4), h // 2)]
            total = [0, 0, 0]
            valid = 0
            for (x, y) in pts:
                c = surf.get_at((x, y))
                if len(c) > 3 and c[3] < 128:
                    continue
                total[0] += c[0]
                total[1] += c[1]
                total[2] += c[2]
                valid += 1
            if valid == 0:
                continue
            avg = (total[0] // valid, total[1] // valid, total[2] // valid)
            gid_avg[gid] = avg
            brightness = sum(avg) / 3.0

            # Door heuristic: many white pixels in center column
            white_count = 0
            try:
                for yy in range(h):
                    c = surf.get_at((w // 2, yy))
                    if len(c) > 3 and c[3] < 128:
                        continue
                    if (c[0] + c[1] + c[2]) / 3.0 > 230:
                        white_count += 1
            except Exception:
                white_count = 0

            if white_count >= int(h * 0.7):
                door_gids.add(gid)
            else:
                if brightness > 180:
                    floor_gids.add(gid)
                elif brightness < 120 and abs(avg[0] - avg[1]) < 60 and abs(avg[1] - avg[2]) < 60:
                    wall_gids.add(gid)
        except Exception:
            continue

    # Find common background color and treat nearby colors as floor
    rounded = [((r // 8, g_ // 8, b // 8)) for (r, g_, b) in gid_avg.values()]
    if rounded:
        most = Counter(rounded).most_common(1)[0][0]
        background_color = (most[0] * 8, most[1] * 8, most[2] * 8)
        def color_dist(a, b):
            return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5
        for gid, avg in gid_avg.items():
            if gid in door_gids:
                continue
            if color_dist(avg, background_color) < 40:
                floor_gids.add(gid)

    # Map sizes and draw scale
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

    map_surface: Optional[pygame.Surface] = None
    try:
        map_surface = pygame.Surface((map_px_w, map_px_h), pygame.SRCALPHA)
        draw_map(map_surface, m, tiles_by_gid, camera_rect=None, scale=draw_scale)
    except Exception:
        map_surface = None

    map_offset = (0, 0)
    if map_surface is not None and map_surface.get_width() < g.SCREENWIDTH:
        map_offset = ((g.SCREENWIDTH - map_surface.get_width()) // 2, (g.SCREENHEIGHT - map_surface.get_height()) // 2)

    # Door rects (in scaled coords)
    door_rects = []
    for layer_idx, layer in enumerate(m.get('layers', [])):
        if layer.get('type') != 'tilelayer':
            continue
        if (layer.get('name') or '').lower() == 'object' or layer_idx == 1:
            continue
        data = layer.get('data', [])
        for idx, raw_gid in enumerate(data):
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0:
                continue
            if gid in door_gids:
                tx = idx % map_w_tiles
                ty = idx // map_w_tiles
                px = tx * tile_w * draw_scale
                py = ty * tile_h * draw_scale
                door_rects.append(pygame.Rect(int(px), int(py), int(tile_w * draw_scale), int(tile_h * draw_scale)))

    # Objects (scaled)
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
                srect = pygame.Rect(int(ox * draw_scale), int(top * draw_scale), max(1, int(ow * draw_scale)), max(1, int(oh * draw_scale)))
                objects.append({'id': oprops.get('id') or obj.get('id'), 'type': oprops.get('type') or obj.get('type'), 'rect': srect, 'props': oprops})

    # Choose spawn position: prefer a floor tile near center
    player_w, player_h = 32, 48
    phys_player_w = player_w * draw_scale
    phys_player_h = player_h * draw_scale
    spawn_x = (map_px_w_natural / 2.0) * draw_scale
    spawn_y = (tile_h * 3) * draw_scale
    try:
        mid_tx = map_w_tiles / 2.0
        candidates = []
        for layer_idx, layer in enumerate(m.get('layers', [])):
            if layer.get('type') != 'tilelayer':
                continue
            if layer_idx == 1:
                continue
            data = layer.get('data', [])
            for idx, raw_gid in enumerate(data):
                gid = raw_gid & 0x1FFFFFFF
                if gid not in floor_gids:
                    continue
                tx = idx % map_w_tiles
                ty = idx // map_w_tiles
                # check that tile above isn't a wall (gives headroom)
                above_idx = (ty - 1) * map_w_tiles + tx
                above_ok = True
                if ty - 1 >= 0 and above_idx < len(data):
                    above_gid = data[above_idx] & 0x1FFFFFFF
                    if above_gid in wall_gids:
                        above_ok = False
                if not above_ok:
                    continue
                score = (abs(tx - mid_tx), -ty)
                candidates.append((score, (tx, ty)))
        if candidates:
            candidates.sort()
            tx, ty = candidates[0][1]
            spawn_x = (tx * tile_w + tile_w / 2.0) * draw_scale
            spawn_y = ((ty + 1) * tile_h) * draw_scale - (phys_player_h / 2.0)
    except Exception:
        pass

    player_x = float(spawn_x)
    player_y = float(spawn_y)
    inventory = set()

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)
    dbg_font = pygame.font.SysFont(None, 18)
    running = True

    while running:
        dt = clock.tick(g.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        vx = 0.0
        SPEED = 200.0 * draw_scale
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vx = -SPEED
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vx = SPEED

        # simple horizontal motion only; vertical is fixed
        player_x += vx * dt

        player_rect = pygame.Rect(int(player_x - phys_player_w / 2.0), int(player_y - phys_player_h / 2.0), max(1, int(phys_player_w)), max(1, int(phys_player_h)))

        # Door teleport (when player has no items)
        try:
            if door_rects:
                def find_opposite(drect):
                    cx, cy = drect.centerx, drect.centery
                    mid_x = (map_px_w_natural * draw_scale) / 2.0
                    if cx < mid_x:
                        candidates = [d for d in door_rects if d.centerx > mid_x]
                    else:
                        candidates = [d for d in door_rects if d.centerx < mid_x]
                    if not candidates:
                        candidates = [d for d in door_rects if d is not drect]
                    if not candidates:
                        return None
                    return min(candidates, key=lambda dd: abs(dd.centery - cy))

                for d in door_rects:
                    if player_rect.colliderect(d):
                        if len(inventory) == 0:
                            opp = find_opposite(d)
                            if opp:
                                player_x = float(opp.centerx)
                                player_y = float(opp.centery)
                                player_rect.topleft = (int(player_x - phys_player_w / 2.0), int(player_y - phys_player_h / 2.0))
                                break
        except Exception:
            pass

        # object pickup
        for obj in list(objects):
            if player_rect.colliderect(obj['rect']):
                inventory.add(obj.get('id'))
                objects.remove(obj)

        # draw
        screen.fill((10, 10, 20))
        if map_surface is not None:
            screen.blit(map_surface, map_offset)
        else:
            try:
                draw_map(screen, m, tiles_by_gid, camera_rect=None, scale=draw_scale)
            except Exception as e:
                print('newmap_scene: draw_map fallback failed:', e)
                pygame.draw.rect(screen, (80, 40, 120), (0, 0, 200, 200))

        for obj in objects:
            sr = obj['rect'].move(map_offset[0], map_offset[1])
            pygame.draw.rect(screen, (200, 200, 100), sr)

        # debug HUD
        try:
            lines = [
                f'map: {os.path.basename(map_path)}',
                f'size: {m.get("width")}x{m.get("height")} tiles',
                f'tile: {m.get("tilewidth")}x{m.get("tileheight")} ',
                f'layers: {len(m.get("layers", []))}',
                f'tiles_by_gid: {len(tiles_by_gid)}',
                f'map_surface: {"yes" if map_surface is not None else "no"}',
                f'walls: {len(wall_gids)} floors: {len(floor_gids)} doors: {len(door_gids)}',
            ]
            for i, ln in enumerate(lines):
                surf = dbg_font.render(ln, True, (255, 255, 255))
                screen.blit(surf, (8, 32 + i * 18))
        except Exception:
            pass

        # draw player
        screen_pr = player_rect.move(map_offset[0], map_offset[1])
        pygame.draw.rect(screen, (100, 180, 255), screen_pr)

        txt = font.render(f'Inventory: {sorted(list(inventory))}', True, (255, 255, 255))
        screen.blit(txt, (8, 8))

        pygame.display.flip()

    return
