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

    # Procedurally generate a full puzzle room (ignore external assets)
    # We'll create a room sized to ACTIVITY_H height and make it slightly wider than the screen
        self.draw_scale = 1
        map_px_h = ACTIVITY_H
        # shorten horizontal length so player can't move indefinitely
        map_px_w = SCREEN_W + 400  # screen width plus some extra room
        # store map size on the scene for runtime clamping
        self.map_width = map_px_w
        self.map_height = map_px_h

        self.map_surface = pygame.Surface((map_px_w, map_px_h)).convert()

        # Background wall and floor
        wall_color = (200, 205, 194)  # pale greenish wall
        floor_base = (170, 140, 120)  # wooden floor base
        self.map_surface.fill(wall_color)

        # draw floor planks on bottom half
        floor_y = map_px_h // 2
        plank_h = 20
        for y in range(floor_y, map_px_h, plank_h):
            shade = (max(0,floor_base[0]- (y%40)//2), max(0,floor_base[1]- (y%40)//3), max(0,floor_base[2]- (y%40)//4))
            pygame.draw.rect(self.map_surface, shade, (0, y, map_px_w, plank_h))
            # plank separators
            for x in range(0, map_px_w, 80):
                pygame.draw.rect(self.map_surface, (max(0,floor_base[0]-30), max(0,floor_base[1]-20), max(0,floor_base[2]-15)), (x, y, 6, plank_h))

        # Add door on far left
        door_w, door_h = 120, 220
        door_x = 80
        door_y = floor_y - door_h
        pygame.draw.rect(self.map_surface, (80,45,30), (door_x, door_y, door_w, door_h))
        pygame.draw.rect(self.map_surface, (100,70,50), (door_x+8, door_y+8, door_w-16, door_h-16))
        knob_x = door_x + door_w - 30
        knob_y = door_y + door_h//2
        pygame.draw.circle(self.map_surface, (200,170,120), (knob_x, knob_y), 6)

        # Bed on right
        bed_w, bed_h = 220, 140
        bed_x = map_px_w - 300
        bed_y = floor_y - bed_h
        pygame.draw.rect(self.map_surface, (120, 60, 80), (bed_x-6, bed_y-6, bed_w+12, bed_h+12))  # frame
        pygame.draw.rect(self.map_surface, (240,240,235), (bed_x, bed_y, bed_w, bed_h))  # mattress
        pygame.draw.rect(self.map_surface, (200,200,210), (bed_x+10, bed_y+10, 80, 40))  # pillow

        # Dresser / TV center
        dresser_w, dresser_h = 260, 90
        dresser_x = map_px_w//2 - dresser_w//2
        dresser_y = floor_y - dresser_h + 10
        pygame.draw.rect(self.map_surface, (100,60,40), (dresser_x, dresser_y, dresser_w, dresser_h))
        # TV
        tv_w, tv_h = 100, 70
        tv_x = dresser_x + 20
        tv_y = dresser_y - tv_h - 10
        pygame.draw.rect(self.map_surface, (30,30,30), (tv_x, tv_y, tv_w, tv_h))
        pygame.draw.rect(self.map_surface, (10,10,10), (tv_x+6, tv_y+6, tv_w-12, tv_h-12))

        # Rug in lower-right
        rug_w, rug_h = 140, 140
        rug_x = bed_x - 40
        rug_y = floor_y - rug_h//2
        pygame.draw.rect(self.map_surface, (200,80,120), (rug_x, rug_y, rug_w, rug_h))
        pygame.draw.rect(self.map_surface, (170,60,90), (rug_x+10, rug_y+10, rug_w-20, rug_h-20))

        # Lamp on dresser
        lamp_x = dresser_x + dresser_w - 50
        lamp_y = dresser_y - 40
        pygame.draw.rect(self.map_surface, (160,120,90), (lamp_x, lamp_y, 12, 40))
        pygame.draw.circle(self.map_surface, (255,220,150), (lamp_x+6, lamp_y-8), 18)

        # Picture on wall above dresser
        pic_w, pic_h = 100, 80
        pic_x = dresser_x + dresser_w - pic_w - 20
        pic_y = dresser_y - pic_h - 40
        pygame.draw.rect(self.map_surface, (200,220,230), (pic_x, pic_y, pic_w, pic_h))
        pygame.draw.rect(self.map_surface, (120,140,160), (pic_x+10, pic_y+10, pic_w-20, pic_h-20))

        # Simple shelves / books left of dresser
        shelf_x = dresser_x - 140
        shelf_y = dresser_y - 40
        for i in range(3):
            pygame.draw.rect(self.map_surface, (90,60,40), (shelf_x, shelf_y + i*30, 100, 12))
            # books
            for b in range(3):
                bx = shelf_x + 6 + b*30
                by = shelf_y + i*30 - 10
                pygame.draw.rect(self.map_surface, (120+20*b, 80, 90), (bx, by+2, 18, 24))

        # Create collision rects: top wall and bed area
        self.collision_rects = []
        self.collision_rects.append(pygame.Rect(0, 0, map_px_w, 8))
        # bed collision
        self.collision_rects.append(pygame.Rect(bed_x, bed_y, bed_w, bed_h))

        # interactables: door, dresser, bed
        self.interactables = []
        def add_interactable_px(x,y,w,h,itype):
            r = pygame.Rect(x, y, w, h)
            surf = pygame.Surface((w*self.draw_scale, h*self.draw_scale), pygame.SRCALPHA)
            # sample from map as sprite
            try:
                surf.blit(self.map_surface, (0,0), area=r)
            except Exception:
                surf.fill((255,0,255))
            self.interactables.append({'id': f"it_{len(self.interactables)}", 'type': itype, 'rect': r, 'props': {}, 'sprite': surf})

        add_interactable_px(door_x, door_y, door_w, door_h, 'door')
        add_interactable_px(dresser_x, dresser_y, dresser_w, dresser_h, 'dresser')
        add_interactable_px(bed_x, bed_y, bed_w, bed_h, 'bed')

        # Add an additional table interactable (桌子)
        table_w, table_h = 140, 70
        table_x = dresser_x - 260
        table_y = floor_y - table_h
        pygame.draw.rect(self.map_surface, (120,80,50), (table_x-4, table_y-4, table_w+8, table_h+8))
        pygame.draw.rect(self.map_surface, (200,180,150), (table_x, table_y, table_w, table_h))
        add_interactable_px(table_x, table_y, table_w, table_h, 'table')

        # map offset so the map is vertically letterboxed
        self.map_offset = (0, LETTERBOX_TOP)

        # initial player pos in map pixels (center-left)
        self.player.x = map_px_w//3
        self.player.y = floor_y - 50

        # track horizontal movement bounds (in map pixels)
        self.player_min_x = 16
        self.player_max_x = map_px_w - 16

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

        # clamp player horizontally to scene bounds so the player cannot move indefinitely
        if hasattr(self, 'player_min_x') and hasattr(self, 'player_max_x'):
            self.player.x = max(self.player_min_x, min(self.player.x, self.player_max_x))

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
