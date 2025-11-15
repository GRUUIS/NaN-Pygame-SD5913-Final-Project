# Copied from src/scenes/map01_scene.py
"""Map01 scene: load the Room1 map from `assets/map01` and run a small
playable viewer. This is a pragmatic, self-contained scene used by the
launcher to test tile collisions and basic door teleporting logic.

The implementation keeps imports local to `run` so importing the module is
cheap; calling `run(screen, inventory=...)` will import pygame and the
other helpers.
"""
import os
import glob
import time

def run(screen, inventory=None):
    import pygame
    from src.tiled_loader import load_map, draw_map, extract_collision_rects
    from src.entities.player_map import MapPlayer
    from src.ui.dialog_box import SpeechBubble

    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    map_path = None
    for p in glob.iglob(os.path.join(ROOT, 'assets', 'map01', 'Room1.*')):
        if p.lower().endswith('.tmj'):
            map_path = p
            break
        if p.lower().endswith('.tmx') and map_path is None:
            map_path = p
    if not map_path:
        print('map01_scene: Room1 map not found under assets/map01; aborting')
        return
    try:
        m, tiles_by_gid, tileset_meta = load_map(map_path)
    except Exception as e:
        print('map01_scene: failed to load map:', e)
        return
    tile_w = m.get('tilewidth', 16)
    tile_h = m.get('tileheight', 16)
    width = m.get('width', 0)
    height = m.get('height', 0)
    draw_scale = 1.0
    scale_int = max(1, round(draw_scale))
    collidable_gids = set()
    layer_names = [((layer.get('name') or '').strip(), layer.get('type')) for layer in m.get('layers', [])]
    for layer in m.get('layers', []):
        name = (layer.get('name') or '').lower()
        if name == 'collusion':
            for gid in layer.get('data', []):
                g = gid & 0x1FFFFFFF
                if g != 0:
                    collidable_gids.add(g)
    platforms = extract_collision_rects(m, tileset_meta, collidable_gids=collidable_gids, scale=scale_int, authoritative_layer_name='collusion', shift_tiles=1)
    try:
        print('[map01_scene DEBUG] layers:', layer_names)
        print('[map01_scene DEBUG] collidable_gids count:', len(collidable_gids), 'sample:', list(sorted(collidable_gids))[:10])
        print('[map01_scene DEBUG] platforms (before door filter):', len(platforms))
        for i, p in enumerate(platforms[:30]):
            print(f"[map01_scene DEBUG] platform[{i}] = {p} -> tiles (tx,ty)=({p.x//tile_w},{p.y//tile_h})")
    except Exception:
        pass
    door_rects = []
    edge_cols = 1
    # ...rest of the function remains unchanged...
