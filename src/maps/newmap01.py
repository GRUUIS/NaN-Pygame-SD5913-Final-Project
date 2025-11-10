"""Programmatic map loader for newmap01.

Returns a minimal Tiled-like map dict and a tiles_by_gid mapping so it can be
rendered with the project's existing draw_map() helper in src/tiled_loader.py.

Usage:
    from src.maps.newmap01 import load_newmap
    m, tiles_by_gid, collidable = load_newmap()
    draw_map(surface, m, tiles_by_gid)
"""
from __future__ import annotations
import pygame
from typing import Tuple, Dict, List


def _create_tile_surface(color, size=(32, 32)):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    return surf


def load_newmap() -> Tuple[dict, Dict[int, pygame.Surface], List[int]]:
    """Create and return (m, tiles_by_gid, collidable_gids).

    - m: map dict compatible with tiled_loader.draw_map (keys: width,height,tilewidth,tileheight,layers)
    - tiles_by_gid: mapping gid->pygame.Surface
    - collidable_gids: list of gids considered collidable (useful for extracting rects)
    """
    TILE = 32
    WIDTH = 40  # tiles
    HEIGHT = 23  # tiles

    # Simple tileset: gid 1 = floor, gid 2 = wall, gid 3 = rock, gid 4 = decorative
    tiles_by_gid = {}
    tiles_by_gid[1] = _create_tile_surface((120, 85, 60, 255), (TILE, TILE))  # floor brown
    tiles_by_gid[2] = _create_tile_surface((90, 90, 100, 255), (TILE, TILE))  # wall grey
    tiles_by_gid[3] = _create_tile_surface((100, 120, 100, 255), (TILE, TILE))  # rock green
    tiles_by_gid[4] = _create_tile_surface((200, 200, 80, 255), (TILE, TILE))  # decoration

    # Build layers: background (empty), floor, obstacles
    # background layer: all zeros (transparent)
    bg_layer = [0] * (WIDTH * HEIGHT)

    # floor layer: put floor tiles on the bottom 3 rows
    floor_layer = [0] * (WIDTH * HEIGHT)
    for x in range(WIDTH):
        for y in range(HEIGHT - 3, HEIGHT):
            idx = y * WIDTH + x
            floor_layer[idx] = 1

    # obstacle layer: simple walls around edges and some pillars
    obs_layer = [0] * (WIDTH * HEIGHT)
    # borders
    for x in range(WIDTH):
        obs_layer[0 * WIDTH + x] = 2  # top border
        obs_layer[(HEIGHT - 1) * WIDTH + x] = 2  # bottom border
    for y in range(HEIGHT):
        obs_layer[y * WIDTH + 0] = 2  # left border
        obs_layer[y * WIDTH + (WIDTH - 1)] = 2  # right border

    # place a few interior pillars (rocks)
    pillar_positions = [(10, 10), (29, 8), (20, 13), (15, 5)]
    for (px, py) in pillar_positions:
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            obs_layer[py * WIDTH + px] = 3

    # decorative tiles
    deco_layer = [0] * (WIDTH * HEIGHT)
    deco_layer[(5) + (3) * WIDTH] = 4
    deco_layer[(35) + (4) * WIDTH] = 4

    layers = [
        {
            "type": "tilelayer",
            "name": "background",
            "visible": True,
            "data": bg_layer,
        },
        {
            "type": "tilelayer",
            "name": "floor",
            "visible": True,
            "data": floor_layer,
        },
        {
            "type": "tilelayer",
            "name": "obstacles",
            "visible": True,
            "data": obs_layer,
        },
        {
            "type": "tilelayer",
            "name": "decor",
            "visible": True,
            "data": deco_layer,
        },
        # Object layer for interactables (collectible items) and an exit trigger
        {
            "type": "objectgroup",
            "name": "objects",
            "visible": True,
            "objects": [
                # Each object uses pixel coordinates (x,y) relative to map origin.
                # Tiled convention: object y is the bottom of the object; the scene loader
                # expects that and computes rect by (x, y - height).
                {
                    "id": 1,
                    "name": "note_1",
                    "type": "collectible",
                    "x": 6 * TILE,
                    "y": 4 * TILE,
                    "width": 32,
                    "height": 32,
                    "properties": [{"name": "id", "value": "note_1"}, {"name": "type", "value": "note"}]
                },
                {
                    "id": 2,
                    "name": "key_1",
                    "type": "collectible",
                    "x": 34 * TILE,
                    "y": 5 * TILE,
                    "width": 32,
                    "height": 32,
                    "properties": [{"name": "id", "value": "key_1"}, {"name": "type", "value": "key"}]
                },
                {
                    "id": 3,
                    "name": "exit_door",
                    "type": "exit",
                    "x": 20 * TILE,
                    "y": (HEIGHT - 1) * TILE,
                    "width": 48,
                    "height": 64,
                    "properties": [{"name": "target_map", "value": "newmap02"}]
                }
            ],
        },
    ]

    m = {
        "height": HEIGHT,
        "width": WIDTH,
        "tilewidth": TILE,
        "tileheight": TILE,
        "layers": layers,
    }

    collidable_gids = [2, 3]

    return m, tiles_by_gid, collidable_gids
