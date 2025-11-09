"""Third puzzle corridor-style scene.

This scene is intentionally small and self-contained. It draws a Tiled map
into a cached surface (if available), letterboxes vertically so the active
area is ACTIVITY_H pixels tall, and allows horizontal camera scrolling.

It intentionally keeps Aseprite/vendor imports out — those can be added via
an adapter if you want full animation support. For now this is a working
framework that reads object layers from the TMJ and exposes simple
right-click interaction.
"""

from __future__ import annotations

import os
import math
from typing import List, Optional, Tuple

import pygame

import globals as g
from ..entities.platform import Platform
from ..systems.ui import UIManager, TextPopup

try:
    from src.tiled_loader import load_map, draw_map, extract_collision_rects
except Exception:
    load_map = draw_map = extract_collision_rects = None

SCREEN_W = g.SCREENWIDTH
SCREEN_H = g.SCREENHEIGHT
ACTIVITY_H = 400
LETTERBOX_TOP = (SCREEN_H - ACTIVITY_H) // 2


class Item:
    def __init__(self, id: str, type: str, pos: Tuple[int, int]):
        self.id = id
        self.type = type
        self.x, self.y = pos
        self.w, self.h = 32, 32

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, (200, 180, 60), self.rect())


class TopDownPlayer:
    def __init__(self, x: float, y: float, speed: float = 140.0):
        self.x = x
        self.y = y
        self.w = 24
        self.h = 40
        self.speed = speed

    def draw(self, screen: pygame.Surface, scene: "ThirdPuzzleScene"):
        screen_x = int(self.x * scene.draw_scale) - scene.camera_x + scene.map_offset[0]
        screen_y = int(self.y * scene.draw_scale) + scene.map_offset[1]
        rw = int(self.w * scene.draw_scale)
        rh = int(self.h * scene.draw_scale)
        pygame.draw.rect(screen, g.COLORS.get('player', (200, 100, 100)), (screen_x, screen_y, rw, rh))


class ThirdPuzzleScene:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.ui = UIManager()
        self.player = TopDownPlayer(200, 200)
        self.platforms = [Platform(0, g.SCREENHEIGHT - 50, g.SCREENWIDTH, 50)]
        self.items = [Item('battery_1', 'battery', (220, g.SCREENHEIGHT - 140)), Item('bulb_1', 'bulb', (420, g.SCREENHEIGHT - 140))]

        self.map = None
        self.tiles_by_gid = {}
        self.tileset_meta = {}
        self.map_surface: Optional[pygame.Surface] = None
        self.draw_scale: float = 1.0
        self.map_offset = (0, LETTERBOX_TOP)
        self.camera_x = 0
        self.collision_rects: List[pygame.Rect] = []
        self.interactables: List[dict] = []

        map_path = os.path.join('testing', 'tilemap', 'testingmap.tmj')
        try:
            if load_map and os.path.exists(map_path):
                m, tiles_by_gid, tileset_meta = load_map(map_path)
                self.map, self.tiles_by_gid, self.tileset_meta = m, tiles_by_gid, tileset_meta

                tile_w = m.get('tilewidth', 16)
                tile_h = m.get('tileheight', 16)
                map_w_tiles = m.get('width', 0)
                map_h_tiles = m.get('height', 0)
                map_px_w = map_w_tiles * tile_w
                map_px_h = map_h_tiles * tile_h

                if map_px_h > 0:
                    desired_scale = ACTIVITY_H / float(map_px_h)
                    self.draw_scale = max(0.1, desired_scale)

                scaled_w = int(map_px_w * self.draw_scale)
                scaled_h = int(map_px_h * self.draw_scale)

                try:
                    self.map_surface = pygame.Surface((scaled_w, scaled_h), pygame.SRCALPHA)
                    draw_map(self.map_surface, m, tiles_by_gid, camera_rect=None, scale=self.draw_scale)
                except Exception:
                    self.map_surface = None

                if self.map_surface and self.map_surface.get_width() < SCREEN_W:
                    self.map_offset = ((SCREEN_W - self.map_surface.get_width()) // 2, LETTERBOX_TOP)

                collidable_gids = set()
                try:
                    for firstgid, meta in (self.tileset_meta or {}).items():
                        name = (meta.get('name') or '').lower()
                        if any(k in name for k in ('overlay', 'furn', 'collision')):
                            for i in range(meta.get('tilecount', 0)):
                                collidable_gids.add(firstgid + i)
                except Exception:
                    collidable_gids = set()

                try:
                    if extract_collision_rects:
                        self.collision_rects = extract_collision_rects(self.map, self.tileset_meta, collidable_gids=collidable_gids, scale=self.draw_scale) or []
                except Exception:
                    self.collision_rects = []

                for layer in m.get('layers', []):
                    if layer.get('type') == 'objectgroup':
                        for obj in layer.get('objects', []):
                            ox = int(obj.get('x', 0) * self.draw_scale)
                            oy = int(obj.get('y', 0) * self.draw_scale)
                            ow = int(obj.get('width', 16) * self.draw_scale)
                            oh = int(obj.get('height', 16) * self.draw_scale)
                            rect = pygame.Rect(ox, oy - oh, max(1, ow), max(1, oh))
                            props = {p.get('name'): p.get('value') for p in (obj.get('properties') or [])}
                            itm = {'id': props.get('id') or obj.get('id'), 'type': props.get('type') or obj.get('type'), 'rect': rect, 'props': props}
                            self.interactables.append(itm)
        except Exception:
            self.map = None

    def handle_event(self, event: pygame.event.EventType):
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            sx, sy = event.pos
            for it in list(self.interactables):
                obj_screen = it['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                if obj_screen.collidepoint((sx, sy)):
                    px = int(self.player.x * self.draw_scale) - self.camera_x + self.map_offset[0]
                    py = int(self.player.y * self.draw_scale) + self.map_offset[1]
                    dist = math.hypot(px - obj_screen.centerx, py - obj_screen.centery)
                    if dist < 180:
                        self.ui.add(TextPopup(f"Interacted: {it.get('type')}", lambda: (obj_screen.x, obj_screen.y), duration=1.0))
                        return

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx != 0 and dy != 0:
            factor = 0.7071
        else:
            factor = 1.0
        move_x = dx * self.player.speed * factor * dt
        move_y = dy * self.player.speed * factor * dt

        old_x = self.player.x
        self.player.x += move_x
        spr = pygame.Rect(int(self.player.x * self.draw_scale), int(self.player.y * self.draw_scale), int(self.player.w * self.draw_scale), int(self.player.h * self.draw_scale))
        collided = any(spr.colliderect(r) for r in getattr(self, 'collision_rects', []))
        if collided:
            self.player.x = old_x

        old_y = self.player.y
        self.player.y += move_y
        spr = pygame.Rect(int(self.player.x * self.draw_scale), int(self.player.y * self.draw_scale), int(self.player.w * self.draw_scale), int(self.player.h * self.draw_scale))
        collided = any(spr.colliderect(r) for r in getattr(self, 'collision_rects', []))
        if collided:
            self.player.y = old_y

        self.ui.update(dt)
        self.update_camera()

    def update_camera(self):
        if not self.map_surface:
            self.camera_x = 0
            return
        scaled_map_w = self.map_surface.get_width()
        player_scaled_x = int(self.player.x * self.draw_scale)
        target_cam_x = player_scaled_x - (SCREEN_W // 2)
        max_cam_x = max(0, scaled_map_w - SCREEN_W)
        self.camera_x = max(0, min(target_cam_x, max_cam_x))

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        if self.map_surface:
            if self.map_surface.get_width() >= SCREEN_W:
                screen.blit(self.map_surface, (-self.camera_x + self.map_offset[0], self.map_offset[1]))
            else:
                screen.blit(self.map_surface, (self.map_offset[0], self.map_offset[1]))

        drawables = []
        for obj in self.interactables:
            drawables.append(('obj', obj))
        drawables.append(('player', self.player))

        def sort_key(item):
            kind, data = item
            if kind == 'player':
                return int((self.player.y + self.player.h) * self.draw_scale)
            else:
                return data['rect'].bottom

        drawables.sort(key=sort_key)
        for kind, data in drawables:
            if kind == 'obj':
                obj = data
                screen_rect = obj['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                pygame.draw.rect(screen, (150, 120, 100), screen_rect)
            else:
                self.player.draw(screen, self)

        for it in self.items:
            screen_x = int(it.x * self.draw_scale) - self.camera_x + self.map_offset[0]
            screen_y = int(it.y * self.draw_scale) + self.map_offset[1]
            pygame.draw.rect(screen, (200, 180, 60), (screen_x, screen_y, int(it.w * self.draw_scale), int(it.h * self.draw_scale)))

        self.ui.draw(screen)


import os
import sys
import math
from typing import List, Optional, Tuple

import pygame

import globals as g
from ..entities.platform import Platform
from ..systems.ui import UIManager, TextPopup

try:
    from src.tiled_loader import load_map, draw_map, extract_collision_rects
except Exception:
    load_map = draw_map = extract_collision_rects = None

SCREEN_W = g.SCREENWIDTH
SCREEN_H = g.SCREENHEIGHT
ACTIVITY_H = 400
LETTERBOX_TOP = (SCREEN_H - ACTIVITY_H) // 2


class Item:
    def __init__(self, id: str, type: str, pos: Tuple[int, int]):
        self.id = id
        self.type = type
        self.x, self.y = pos
        self.w, self.h = 32, 32

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, (200, 180, 60), self.rect())


class TopDownPlayer:
    def __init__(self, x: float, y: float, speed: float = 140.0):
        self.x = x
        self.y = y
        self.w = 24
        self.h = 40
        self.speed = speed

    def draw(self, screen: pygame.Surface, scene: "ThirdPuzzleScene"):
        screen_x = int(self.x * scene.draw_scale) - scene.camera_x + scene.map_offset[0]
        screen_y = int(self.y * scene.draw_scale) + scene.map_offset[1]
        rw = int(self.w * scene.draw_scale)
        rh = int(self.h * scene.draw_scale)
        pygame.draw.rect(screen, g.COLORS.get('player', (200, 100, 100)), (screen_x, screen_y, rw, rh))


class ThirdPuzzleScene:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.ui = UIManager()
        self.player = TopDownPlayer(200, 200)
        self.platforms = [Platform(0, g.SCREENHEIGHT - 50, g.SCREENWIDTH, 50)]
        self.items = [Item('battery_1', 'battery', (220, g.SCREENHEIGHT - 140)), Item('bulb_1', 'bulb', (420, g.SCREENHEIGHT - 140))]

        self.map = None
        self.tiles_by_gid = {}
        self.tileset_meta = {}
        self.map_surface: Optional[pygame.Surface] = None
        self.draw_scale: float = 1.0
        self.map_offset = (0, LETTERBOX_TOP)
        self.camera_x = 0
        self.collision_rects: List[pygame.Rect] = []
        self.interactables: List[dict] = []

        map_path = os.path.join('testing', 'tilemap', 'testingmap.tmj')
        try:
            if load_map and os.path.exists(map_path):
                m, tiles_by_gid, tileset_meta = load_map(map_path)
                self.map, self.tiles_by_gid, self.tileset_meta = m, tiles_by_gid, tileset_meta

                tile_w = m.get('tilewidth', 16)
                tile_h = m.get('tileheight', 16)
                map_w_tiles = m.get('width', 0)
                map_h_tiles = m.get('height', 0)
                map_px_w = map_w_tiles * tile_w
                map_px_h = map_h_tiles * tile_h

                if map_px_h > 0:
                    desired_scale = ACTIVITY_H / float(map_px_h)
                    self.draw_scale = max(0.1, desired_scale)

                scaled_w = int(map_px_w * self.draw_scale)
                scaled_h = int(map_px_h * self.draw_scale)

                try:
                    self.map_surface = pygame.Surface((scaled_w, scaled_h), pygame.SRCALPHA)
                    draw_map(self.map_surface, m, tiles_by_gid, camera_rect=None, scale=self.draw_scale)
                except Exception:
                    self.map_surface = None

                if self.map_surface and self.map_surface.get_width() < SCREEN_W:
                    self.map_offset = ((SCREEN_W - self.map_surface.get_width()) // 2, LETTERBOX_TOP)

                collidable_gids = set()
                try:
                    for firstgid, meta in (self.tileset_meta or {}).items():
                        name = (meta.get('name') or '').lower()
                        if any(k in name for k in ('overlay', 'furn', 'collision')):
                            for i in range(meta.get('tilecount', 0)):
                                collidable_gids.add(firstgid + i)
                except Exception:
                    collidable_gids = set()

                try:
                    if extract_collision_rects:
                        self.collision_rects = extract_collision_rects(self.map, self.tileset_meta, collidable_gids=collidable_gids, scale=self.draw_scale) or []
                except Exception:
                    self.collision_rects = []

                for layer in m.get('layers', []):
                    if layer.get('type') == 'objectgroup':
                        for obj in layer.get('objects', []):
                            ox = int(obj.get('x', 0) * self.draw_scale)
                            oy = int(obj.get('y', 0) * self.draw_scale)
                            ow = int(obj.get('width', 16) * self.draw_scale)
                            oh = int(obj.get('height', 16) * self.draw_scale)
                            rect = pygame.Rect(ox, oy - oh, max(1, ow), max(1, oh))
                            props = {p.get('name'): p.get('value') for p in (obj.get('properties') or [])}
                            itm = {'id': props.get('id') or obj.get('id'), 'type': props.get('type') or obj.get('type'), 'rect': rect, 'props': props}
                            self.interactables.append(itm)
        except Exception:
            self.map = None

    def handle_event(self, event: pygame.event.EventType):
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            sx, sy = event.pos
            for it in list(self.interactables):
                obj_screen = it['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                if obj_screen.collidepoint((sx, sy)):
                    px = int(self.player.x * self.draw_scale) - self.camera_x + self.map_offset[0]
                    py = int(self.player.y * self.draw_scale) + self.map_offset[1]
                    dist = math.hypot(px - obj_screen.centerx, py - obj_screen.centery)
                    if dist < 180:
                        self.ui.add(TextPopup(f"Interacted: {it.get('type')}", lambda: (obj_screen.x, obj_screen.y), duration=1.0))
                        return

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx != 0 and dy != 0:
            factor = 0.7071
        else:
            factor = 1.0
        move_x = dx * self.player.speed * factor * dt
        move_y = dy * self.player.speed * factor * dt

        old_x = self.player.x
        self.player.x += move_x
        spr = pygame.Rect(int(self.player.x * self.draw_scale), int(self.player.y * self.draw_scale), int(self.player.w * self.draw_scale), int(self.player.h * self.draw_scale))
        collided = any(spr.colliderect(r) for r in getattr(self, 'collision_rects', []))
        if collided:
            self.player.x = old_x

        old_y = self.player.y
        self.player.y += move_y
        spr = pygame.Rect(int(self.player.x * self.draw_scale), int(self.player.y * self.draw_scale), int(self.player.w * self.draw_scale), int(self.player.h * self.draw_scale))
        collided = any(spr.colliderect(r) for r in getattr(self, 'collision_rects', []))
        if collided:
            self.player.y = old_y

        self.ui.update(dt)
        self.update_camera()

    def update_camera(self):
        if not self.map_surface:
            self.camera_x = 0
            return
        scaled_map_w = self.map_surface.get_width()
        player_scaled_x = int(self.player.x * self.draw_scale)
        target_cam_x = player_scaled_x - (SCREEN_W // 2)
        max_cam_x = max(0, scaled_map_w - SCREEN_W)
        self.camera_x = max(0, min(target_cam_x, max_cam_x))

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        if self.map_surface:
            if self.map_surface.get_width() >= SCREEN_W:
                screen.blit(self.map_surface, (-self.camera_x + self.map_offset[0], self.map_offset[1]))
            else:
                screen.blit(self.map_surface, (self.map_offset[0], self.map_offset[1]))

        drawables = []
        for obj in self.interactables:
            drawables.append(('obj', obj))
        drawables.append(('player', self.player))

        def sort_key(item):
            kind, data = item
            if kind == 'player':
                return int((self.player.y + self.player.h) * self.draw_scale)
            else:
                return data['rect'].bottom

        drawables.sort(key=sort_key)
        for kind, data in drawables:
            if kind == 'obj':
                obj = data
                screen_rect = obj['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                pygame.draw.rect(screen, (150, 120, 100), screen_rect)
            else:
                self.player.draw(screen, self)

        for it in self.items:
            screen_x = int(it.x * self.draw_scale) - self.camera_x + self.map_offset[0]
            screen_y = int(it.y * self.draw_scale) + self.map_offset[1]
            pygame.draw.rect(screen, (200, 180, 60), (screen_x, screen_y, int(it.w * self.draw_scale), int(it.h * self.draw_scale)))

    self.ui.draw(screen)

from ..systems.ui import UIManager, TextPopup

# Safe tiled loader imports (optional)
try:
    from src.tiled_loader import load_map, draw_map, extract_collision_rects
except Exception:
    load_map = draw_map = extract_collision_rects = None

# Layout constants
SCREEN_W = g.SCREENWIDTH
SCREEN_H = g.SCREENHEIGHT
ACTIVITY_H = 400
from __future__ import annotations

import os
import sys
import math
from typing import List, Optional, Tuple

import pygame

import globals as g
from ..entities.platform import Platform
from ..systems.ui import UIManager, TextPopup

try:
    from src.tiled_loader import load_map, draw_map, extract_collision_rects
except Exception:
    load_map = draw_map = extract_collision_rects = None

SCREEN_W = g.SCREENWIDTH
SCREEN_H = g.SCREENHEIGHT
ACTIVITY_H = 400
LETTERBOX_TOP = (SCREEN_H - ACTIVITY_H) // 2


class Item:
    def __init__(self, id: str, type: str, pos: Tuple[int, int]):
        self.id = id
        self.type = type
        self.x, self.y = pos
        self.w, self.h = 32, 32

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, (200, 180, 60), self.rect())


class TopDownPlayer:
    def __init__(self, x: float, y: float, speed: float = 140.0):
        self.x = x
        self.y = y
        self.w = 24
        self.h = 40
        self.speed = speed

    def draw(self, screen: pygame.Surface, scene: "ThirdPuzzleScene"):
        screen_x = int(self.x * scene.draw_scale) - scene.camera_x + scene.map_offset[0]
        screen_y = int(self.y * scene.draw_scale) + scene.map_offset[1]
        rw = int(self.w * scene.draw_scale)
        rh = int(self.h * scene.draw_scale)
        pygame.draw.rect(screen, g.COLORS.get('player', (200, 100, 100)), (screen_x, screen_y, rw, rh))


class ThirdPuzzleScene:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.ui = UIManager()
        self.player = TopDownPlayer(200, 200)
        self.platforms = [Platform(0, g.SCREENHEIGHT - 50, g.SCREENWIDTH, 50)]
        self.items = [Item('battery_1', 'battery', (220, g.SCREENHEIGHT - 140)), Item('bulb_1', 'bulb', (420, g.SCREENHEIGHT - 140))]

        self.map = None
        self.tiles_by_gid = {}
        self.tileset_meta = {}
        self.map_surface: Optional[pygame.Surface] = None
        self.draw_scale: float = 1.0
        self.map_offset = (0, LETTERBOX_TOP)
        self.camera_x = 0
        self.collision_rects: List[pygame.Rect] = []
        self.interactables: List[dict] = []

        map_path = os.path.join('testing', 'tilemap', 'testingmap.tmj')
        try:
            if load_map and os.path.exists(map_path):
                m, tiles_by_gid, tileset_meta = load_map(map_path)
                self.map, self.tiles_by_gid, self.tileset_meta = m, tiles_by_gid, tileset_meta

                tile_w = m.get('tilewidth', 16)
                tile_h = m.get('tileheight', 16)
                map_w_tiles = m.get('width', 0)
                map_h_tiles = m.get('height', 0)
                map_px_w = map_w_tiles * tile_w
                map_px_h = map_h_tiles * tile_h

                if map_px_h > 0:
                    desired_scale = ACTIVITY_H / float(map_px_h)
                    self.draw_scale = max(0.1, desired_scale)

                scaled_w = int(map_px_w * self.draw_scale)
                scaled_h = int(map_px_h * self.draw_scale)

                try:
                    self.map_surface = pygame.Surface((scaled_w, scaled_h), pygame.SRCALPHA)
                    draw_map(self.map_surface, m, tiles_by_gid, camera_rect=None, scale=self.draw_scale)
                except Exception:
                    self.map_surface = None

                if self.map_surface and self.map_surface.get_width() < SCREEN_W:
                    self.map_offset = ((SCREEN_W - self.map_surface.get_width()) // 2, LETTERBOX_TOP)

                # simple collidable gid heuristic
                collidable_gids = set()
                try:
                    for firstgid, meta in (self.tileset_meta or {}).items():
                        name = (meta.get('name') or '').lower()
                        if any(k in name for k in ('overlay', 'furn', 'collision')):
                            for i in range(meta.get('tilecount', 0)):
                                collidable_gids.add(firstgid + i)
                except Exception:
                    collidable_gids = set()

                try:
                    if extract_collision_rects:
                        self.collision_rects = extract_collision_rects(self.map, self.tileset_meta, collidable_gids=collidable_gids, scale=self.draw_scale) or []
                except Exception:
                    self.collision_rects = []

                # load objectgroup interactables
                for layer in m.get('layers', []):
                    if layer.get('type') == 'objectgroup':
                        for obj in layer.get('objects', []):
                            ox = int(obj.get('x', 0) * self.draw_scale)
                            oy = int(obj.get('y', 0) * self.draw_scale)
                            ow = int(obj.get('width', 16) * self.draw_scale)
                            oh = int(obj.get('height', 16) * self.draw_scale)
                            rect = pygame.Rect(ox, oy - oh, max(1, ow), max(1, oh))
                            props = {p.get('name'): p.get('value') for p in (obj.get('properties') or [])}
                            itm = {'id': props.get('id') or obj.get('id'), 'type': props.get('type') or obj.get('type'), 'rect': rect, 'props': props}
                            self.interactables.append(itm)
        except Exception:
            self.map = None

    def handle_event(self, event: pygame.event.EventType):
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            sx, sy = event.pos
            for it in list(self.interactables):
                obj_screen = it['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                if obj_screen.collidepoint((sx, sy)):
                    px = int(self.player.x * self.draw_scale) - self.camera_x + self.map_offset[0]
                    py = int(self.player.y * self.draw_scale) + self.map_offset[1]
                    dist = math.hypot(px - obj_screen.centerx, py - obj_screen.centery)
                    if dist < 180:
                        self.ui.add(TextPopup(f"Interacted: {it.get('type')}", lambda: (obj_screen.x, obj_screen.y), duration=1.0))
                        return

    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx != 0 and dy != 0:
            factor = 0.7071
        else:
            factor = 1.0
        move_x = dx * self.player.speed * factor * dt
        move_y = dy * self.player.speed * factor * dt

        # X axis
        old_x = self.player.x
        self.player.x += move_x
        spr = pygame.Rect(int(self.player.x * self.draw_scale), int(self.player.y * self.draw_scale), int(self.player.w * self.draw_scale), int(self.player.h * self.draw_scale))
        collided = any(spr.colliderect(r) for r in getattr(self, 'collision_rects', []))
        if collided:
            self.player.x = old_x

        # Y axis
        old_y = self.player.y
        self.player.y += move_y
        spr = pygame.Rect(int(self.player.x * self.draw_scale), int(self.player.y * self.draw_scale), int(self.player.w * self.draw_scale), int(self.player.h * self.draw_scale))
        collided = any(spr.colliderect(r) for r in getattr(self, 'collision_rects', []))
        if collided:
            self.player.y = old_y

        self.ui.update(dt)
        self.update_camera()

    def update_camera(self):
        if not self.map_surface:
            self.camera_x = 0
            return
        scaled_map_w = self.map_surface.get_width()
        player_scaled_x = int(self.player.x * self.draw_scale)
        target_cam_x = player_scaled_x - (SCREEN_W // 2)
        max_cam_x = max(0, scaled_map_w - SCREEN_W)
        self.camera_x = max(0, min(target_cam_x, max_cam_x))

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        if self.map_surface:
            if self.map_surface.get_width() >= SCREEN_W:
                screen.blit(self.map_surface, (-self.camera_x + self.map_offset[0], self.map_offset[1]))
            else:
                screen.blit(self.map_surface, (self.map_offset[0], self.map_offset[1]))

        drawables = []
        for obj in self.interactables:
            drawables.append(('obj', obj))
        drawables.append(('player', self.player))

        def sort_key(item):
            kind, data = item
            if kind == 'player':
                return int((self.player.y + self.player.h) * self.draw_scale)
            else:
                return data['rect'].bottom

        drawables.sort(key=sort_key)
        for kind, data in drawables:
            if kind == 'obj':
                obj = data
                screen_rect = obj['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                pygame.draw.rect(screen, (150, 120, 100), screen_rect)
            else:
                self.player.draw(screen, self)

        for it in self.items:
            screen_x = int(it.x * self.draw_scale) - self.camera_x + self.map_offset[0]
            screen_y = int(it.y * self.draw_scale) + self.map_offset[1]
            pygame.draw.rect(screen, (200, 180, 60), (screen_x, screen_y, int(it.w * self.draw_scale), int(it.h * self.draw_scale)))

        self.ui.draw(screen)
        for t in self.tools:
            if t.projecting:
                proj_surf, proj_rect = t.render_projection()
                proj_mask = pygame.mask.from_surface(proj_surf)
                for area in self.areas:
                    if area.completed:
                        continue
                    offset = (area.rect.x - proj_rect.x, area.rect.y - proj_rect.y)
                    overlap = proj_mask.overlap_mask(area.mask, offset)
                    cov = overlap.count() / area.mask.count() if area.mask.count() else 0
                    if cov >= 0.5:
                        area.completed = True
                        t.projecting = False
                        self.ui.add(TextPopup('Area completed', lambda: (area.rect.x, area.rect.y), duration=1.2))
    def draw(self, screen: pygame.Surface):
        screen.fill(g.COLORS.get('background',(30,30,40)))
        for a in self.areas:
            a.draw(screen)
        for it in self.items:
            it.draw(screen)
        for t in self.tools:
            if t.projecting:
                surf, r = t.render_projection()
                screen.blit(surf, r.topleft)
            t.draw(screen)
        for p in self.platforms:
            p.draw(screen)
        self.player.draw(screen)
        if self.held_item:
            font = pygame.font.Font(None, 24)
            screen.blit(font.render(f"Holding: {self.held_item.type}", True, (255,255,255)), (10,10))
        self.ui.draw(screen)
