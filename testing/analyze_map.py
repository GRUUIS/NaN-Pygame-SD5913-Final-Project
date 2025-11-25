"""
Analyze the test puzzle scene map and visualize the grid system.
"""

import json
import os

# Load the map
map_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "assets", "tilemaps", "test puzzle scene.tmj"
)

with open(map_path, 'r') as f:
    map_data = json.load(f)

width = map_data['width']
height = map_data['height']

print(f"Map size: {width}x{height} tiles")
print(f"Tile size: {map_data['tilewidth']}x{map_data['tileheight']} pixels")
print()

# Analyze each layer
print("=" * 60)
print("LAYER ANALYSIS")
print("=" * 60)

for layer in map_data.get('layers', []):
    layer_name = layer.get('name', 'unknown')
    layer_id = layer.get('id')
    
    if layer.get('type') != 'tilelayer':
        continue
    
    data = layer.get('data', [])
    
    # Find non-zero tiles
    tiles = []
    for i, gid in enumerate(data):
        if gid > 0:
            tx = i % width
            ty = i // width
            tiles.append((tx, ty, gid))
    
    print(f"\nLayer: {layer_name} (id={layer_id})")
    print(f"  Non-zero tiles: {len(tiles)}")
    
    if tiles:
        min_x = min(t[0] for t in tiles)
        max_x = max(t[0] for t in tiles)
        min_y = min(t[1] for t in tiles)
        max_y = max(t[1] for t in tiles)
        print(f"  Bounds: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")
        
        # Show tile positions
        if len(tiles) <= 20:
            print(f"  Positions: {[(t[0], t[1]) for t in tiles]}")

# Create a combined view
print()
print("=" * 60)
print("COMBINED GRID VIEW (rows 10-17, columns 13-26)")
print("=" * 60)

# Build a grid showing which layers have content
grid = {}
layer_chars = {
    'background': 'B',
    'carpet': 'C',
    'hanging pictures': 'P',
    'clock': 'K',
    'window': 'W',
    'floor lamp': 'L',
    'bookshelf': 'S',
    'foreground_furniture': 'F',
    'bed': 'E',
    'door': 'D',
    'desk': 'T',
    'decoration': 'X',
}

for layer in map_data.get('layers', []):
    layer_name = layer.get('name', 'unknown')
    if layer.get('type') != 'tilelayer':
        continue
    
    data = layer.get('data', [])
    char = layer_chars.get(layer_name, '?')
    
    for i, gid in enumerate(data):
        if gid > 0:
            tx = i % width
            ty = i // width
            if (tx, ty) not in grid:
                grid[(tx, ty)] = []
            grid[(tx, ty)].append(char)

# Print header
print("     ", end="")
for x in range(13, 27):
    print(f"{x:3}", end="")
print()

# Print grid
for y in range(10, 18):
    print(f"{y:3}: ", end="")
    for x in range(13, 27):
        chars = grid.get((x, y), [])
        if chars:
            # Show up to 3 chars
            display = ''.join(chars[:3])
            print(f"{display:3}", end="")
        else:
            print("  .", end="")
    print()

print()
print("Legend:")
print("  B=background, C=carpet, P=hanging pictures, K=clock")
print("  W=window, L=floor lamp, S=bookshelf, F=foreground_furniture")
print("  E=bed, D=door, T=desk, X=decoration")

# Analyze walkable area
print()
print("=" * 60)
print("WALKABLE AREA ANALYSIS")
print("=" * 60)

# Find floor tiles (background layer with floor tiles, carpet)
floor_tiles = set()
for layer in map_data.get('layers', []):
    layer_name = layer.get('name', 'unknown')
    if layer_name in ['background', 'carpet']:
        data = layer.get('data', [])
        for i, gid in enumerate(data):
            if gid > 0:
                tx = i % width
                ty = i // width
                floor_tiles.add((tx, ty))

print(f"Floor tiles count: {len(floor_tiles)}")
if floor_tiles:
    min_x = min(t[0] for t in floor_tiles)
    max_x = max(t[0] for t in floor_tiles)
    min_y = min(t[1] for t in floor_tiles)
    max_y = max(t[1] for t in floor_tiles)
    print(f"Floor bounds: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")

# Find obstacle tiles
obstacle_tiles = set()
for layer in map_data.get('layers', []):
    layer_name = layer.get('name', 'unknown')
    if layer_name in ['desk', 'bed', 'bookshelf', 'door', 'foreground_furniture']:
        data = layer.get('data', [])
        for i, gid in enumerate(data):
            if gid > 0:
                tx = i % width
                ty = i // width
                obstacle_tiles.add((tx, ty))

print(f"Obstacle tiles count: {len(obstacle_tiles)}")
print(f"Obstacle positions: {sorted(obstacle_tiles)}")

# Show detailed grid for walkable analysis
print()
print("Walkable grid (F=floor only, O=obstacle on floor, W=wall/empty):")
print("     ", end="")
for x in range(13, 27):
    print(f"{x:2}", end="")
print()

for y in range(10, 18):
    print(f"{y:3}: ", end="")
    for x in range(13, 27):
        has_floor = (x, y) in floor_tiles
        has_obstacle = (x, y) in obstacle_tiles
        if has_obstacle:
            print(" O", end="")
        elif has_floor:
            print(" F", end="")
        else:
            print(" W", end="")
    print()
