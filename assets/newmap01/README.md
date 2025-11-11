newmap01

This folder contains the programmatic map "newmap01" used as a non-boss exploration area.

Design notes:
- Tile size: 32x32 px
- Logical map size: 40 x 23 tiles (1280 x 736 px)
- Non-boss area: designed for item collection, puzzles and exploration (not a boss arena).

Map purpose
- Non-boss exploration area. The player collects items (notes/keys) to solve a small mystery

Files provided:
- map.py (not included) - see src/maps/newmap01.py for the programmatic map loader.

- Import the map loader: from src.maps.newmap01 import load_newmap
- Call load_newmap() to get (m, tiles_by_gid, collidable_gids) and pass to your rendering/collision systems.
REMOVED: newmap01

The `newmap01` map was removed from the project. The programmatic loader and
scene were deleted/disabled. This folder remains for archival purposes but is
no longer used by the game.

If you need to restore the map, check the git history or re-create the map
using `src/maps/newmap01.py` as a reference.
