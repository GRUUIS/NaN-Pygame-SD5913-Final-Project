"""检查地图中的交互物品位置"""
import json
import os
import xml.etree.ElementTree as ET

# Load map
with open('assets/tilemaps/test puzzle scene.tmj', encoding='utf-8') as f:
    m = json.load(f)

TILE_SIZE = m.get('tilewidth', 32)
width = m.get('width', 0)
height = m.get('height', 0)

print(f"Map size: {width}x{height} tiles, tile size: {TILE_SIZE}px")

# Parse tile properties from TSX files
tile_props = {}
for ts in m.get('tilesets', []):
    firstgid = ts.get('firstgid', 0)
    source = ts.get('source', '')
    if source:
        tsx_path = os.path.join('assets/tilemaps', source)
        if os.path.exists(tsx_path):
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
                        props[name] = val
                if props:
                    tile_props[firstgid + tid] = props

# Find interactive tiles
interactive_objects = []
for layer in m.get('layers', []):
    if layer.get('type') != 'tilelayer':
        continue
    lname = layer.get('name', '')
    data = layer.get('data', [])
    for idx, raw_gid in enumerate(data):
        gid = raw_gid & 0x1FFFFFFF
        if gid == 0:
            continue
        tx = idx % width
        ty = idx // width
        props = tile_props.get(gid, {})
        if props.get('interactive') in (True, 'true', 'True', '1', 1):
            interactive_objects.append({
                'tx': tx, 'ty': ty,
                'layer': lname,
                'gid': gid,
                'props': props
            })

print(f'\nFound {len(interactive_objects)} interactive objects:')
for i, obj in enumerate(interactive_objects):
    print(f'  {i+1}. Position: ({obj["tx"]}, {obj["ty"]}) Layer: {obj["layer"]} GID: {obj["gid"]}')
    print(f'      Props: {obj["props"]}')

# Check collision tiles
collision_tiles = []
for layer in m.get('layers', []):
    if layer.get('type') != 'tilelayer':
        continue
    data = layer.get('data', [])
    for idx, raw_gid in enumerate(data):
        gid = raw_gid & 0x1FFFFFFF
        if gid == 0:
            continue
        tx = idx % width
        ty = idx // width
        props = tile_props.get(gid, {})
        if props.get('collidable') in (True, 'true', 'True', '1', 1):
            collision_tiles.append((tx, ty))

# Check if interactive objects are in collision area
print(f'\n--- Checking accessibility ---')
print(f'Player spawn at (16, 15)')
OVERRIDE_NON_COLLIDABLE = {(15, 14), (16, 14), (17, 14), (21, 13)}
collision_set = set(collision_tiles) - OVERRIDE_NON_COLLIDABLE

for i, obj in enumerate(interactive_objects):
    tx, ty = obj['tx'], obj['ty']
    # Check if the tile itself is blocked or surrounded by collision
    blocked = (tx, ty) in collision_set
    # Check 4 directions
    neighbors_blocked = sum(1 for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)] if (tx+dx, ty+dy) in collision_set)
    print(f'  {i+1}. ({tx}, {ty}) - Blocked: {blocked}, Adjacent blocked: {neighbors_blocked}/4')
