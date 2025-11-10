newmap01

This folder contains the programmatic map "newmap01" used as a non-boss exploration area.

Design notes:
- Tile size: 32x32 px
- Logical map size: 40 x 23 tiles (1280 x 736 px)
- Non-boss area: designed for item collection, puzzles and exploration (not a boss arena).

Map purpose
- Non-boss exploration area. The player collects items (notes/keys) to solve a small mystery
	and unlock an exit leading to another map (target_map = newmap02).

Files provided:
- map.py (not included) - see src/maps/newmap01.py for the programmatic map loader.

To use:
- Import the map loader: from src.maps.newmap01 import load_newmap
- Call load_newmap() to get (m, tiles_by_gid, collidable_gids) and pass to your rendering/collision systems.
