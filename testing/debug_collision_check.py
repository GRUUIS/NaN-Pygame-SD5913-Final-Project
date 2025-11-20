import pygame
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from src.tiled_loader import load_map

def check_collision_at_spawn():
    pygame.init()
    pygame.display.set_mode((100, 100)) # Dummy display
    
    map_path = "assets/tilemaps/test puzzle scene.tmj"
    try:
        m, tiles_by_gid, tileset_meta = load_map(map_path)
    except Exception as e:
        print(f"Failed to load map: {e}")
        return

    TILE_SIZE = m.get('tilewidth', 32)
    width = m.get('width', 0)
    height = m.get('height', 0)
    
    print(f"Map Size: {width}x{height}, Tile Size: {TILE_SIZE}")
    
    # Build collision map
    collision_tiles = []
    tile_props = {}
    
    # Parse tileset properties
    for ts in m.get('tilesets', []):
        firstgid = ts.get('firstgid', 0)
        for t in ts.get('tiles', []) or []:
            local_id = t.get('id')
            props = {}
            for p in t.get('properties', []) or []:
                props[p.get('name')] = p.get('value')
            tile_props[firstgid + int(local_id)] = props
            
    def is_truthy(v):
        return v in (True, 'true', 'True', 1, '1')

    # Check layers
    for layer in m.get('layers', []):
        if layer.get('type') != 'tilelayer':
            continue
        data = layer.get('data', [])
        
        for idx, raw_gid in enumerate(data):
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0: continue
            
            tx = idx % width
            ty = idx // width
            
            props = tile_props.get(gid, {})
            if is_truthy(props.get('collidable')):
                print(f"Collision at ({tx}, {ty}) - GID: {gid}")
                collision_tiles.append((tx, ty))

    spawn_x, spawn_y = 16, 15
    print(f"Checking Spawn ({spawn_x}, {spawn_y})")
    
    if (spawn_x, spawn_y) in collision_tiles:
        print("!!! SPAWN POINT IS INSIDE A COLLISION TILE !!!")
    else:
        print("Spawn point seems clear of direct tile collision.")
        
    # Check neighbors
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            nx, ny = spawn_x + dx, spawn_y + dy
            if (nx, ny) in collision_tiles:
                print(f"Neighbor ({nx}, {ny}) is collidable.")

if __name__ == "__main__":
    check_collision_at_spawn()
