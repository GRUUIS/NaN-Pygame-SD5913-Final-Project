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
        # currently hovered/nearby interactable (used to show "check" and enable clicks)
        self._hover_interactable: Optional[dict] = None
        # distance in pixels (screen-space) for proximity checks
        self._hover_distance: int = 120

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

        # If a Tiled map (tmj) exists in assets/tilemaps, load it and override the
        # procedural room. This lets you design the room in Tiled and have the
        # scene pick up collision and interactable object layers.
        try:
            tmj_path = os.path.join('assets', 'tilemaps', 'test puzzle scene.tmj')
        except Exception:
            tmj_path = None

        if tmj_path and load_map and draw_map and os.path.exists(tmj_path):
            try:
                m, tiles_by_gid, tileset_meta = load_map(tmj_path)
                # build map surface from tiled map
                tile_w = m.get('tilewidth', 16)
                tile_h = m.get('tileheight', 16)
                map_px_w = m.get('width', 0) * tile_w
                map_px_h = m.get('height', 0) * tile_h
                # scale map so its pixel height matches ACTIVITY_H (letterboxed)
                if map_px_h > 0:
                    desired_scale = ACTIVITY_H / float(map_px_h)
                    # clamp to reasonable range
                    self.draw_scale = max(0.1, min(2.0, desired_scale))
                # If you exported a full-map PNG (rendered map) place it at
                # assets/tilemaps/test scene2.png and we'll use it directly so
                # tileset lookup is not required. Otherwise fall back to drawing
                # from tiles_by_gid (may produce placeholders if tilesets missing).
                fullmap_png = os.path.join('assets', 'tilemaps', 'test scene2.png')
                if os.path.exists(fullmap_png):
                    try:
                        img = pygame.image.load(fullmap_png).convert_alpha()
                        if img.get_width() == map_px_w and img.get_height() == map_px_h:
                            self.map_surface = img.copy()
                        else:
                            # scale to map size (best effort)
                            try:
                                # scale the fullmap to the raw tiled pixel size, then scale later by draw_scale
                                raw = pygame.transform.smoothscale(img, (map_px_w, map_px_h))
                                sw = int(map_px_w * self.draw_scale)
                                sh = int(map_px_h * self.draw_scale)
                                self.map_surface = pygame.transform.smoothscale(raw, (sw, sh)).convert_alpha()
                            except Exception:
                                self.map_surface = img.copy()
                    except Exception:
                        # loading failed; fall back to tile rendering
                        # render from tiles at scaled size
                        sw = int(map_px_w * self.draw_scale)
                        sh = int(map_px_h * self.draw_scale)
                        self.map_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
                        draw_map(self.map_surface, m, tiles_by_gid, camera_rect=None, scale=self.draw_scale)
                else:
                    sw = int(map_px_w * self.draw_scale)
                    sh = int(map_px_h * self.draw_scale)
                    self.map_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    draw_map(self.map_surface, m, tiles_by_gid, camera_rect=None, scale=self.draw_scale)

                # center the map horizontally (respect artist margins). We set
                # map_offset so the full map is centered; also set an initial
                # camera_x so the visible window shows the map center when
                # the map is wider than the screen.
                try:
                    map_w = self.map_surface.get_width()
                    self.map_offset = ((SCREEN_W - map_w) // 2, LETTERBOX_TOP)
                    # initial camera shows center of map by default
                    self.camera_x = max(0, (map_w - SCREEN_W) // 2)
                except Exception:
                    self.map_offset = (0, LETTERBOX_TOP)
                    self.camera_x = 0

                # reset collision/interactables and repopulate from object layers
                self.collision_rects = []
                self.interactables = []

                # helper to read properties list into dict
                def _props_to_dict(plist):
                    out = {}
                    for p in plist or []:
                        out[p.get('name')] = p.get('value')
                    return out

                player_start_found = False
                for layer in m.get('layers', []):
                    if layer.get('type') != 'objectgroup':
                        continue
                    lname = (layer.get('name') or '').lower()
                    for obj in layer.get('objects', []):
                        # object coordinates in TMJ are raw pixels; keep raw values for logical map coords
                        ox_raw = int(obj.get('x', 0))
                        oy_raw = int(obj.get('y', 0))
                        ow_raw = int(obj.get('width', 0))
                        oh_raw = int(obj.get('height', 0))
                        gid = obj.get('gid')
                        props = _props_to_dict(obj.get('properties'))

                        # tile-objects in Tiled often store y at bottom (raw coords)
                        top_raw = oy_raw - oh_raw if gid else oy_raw
                        if ow_raw == 0 or oh_raw == 0:
                            ow_raw = ow_raw or tile_w
                            oh_raw = oh_raw or tile_h
                        # compute screen-space rect (scaled) for collisions and drawing
                        ox = int(ox_raw * self.draw_scale)
                        top = int(top_raw * self.draw_scale)
                        ow = int(ow_raw * self.draw_scale)
                        oh = int(oh_raw * self.draw_scale)
                        rect = pygame.Rect(ox, top, ow, oh)

                        # collision if layer is named collision or prop blocking
                        blocking = False
                        if lname in ('collision', 'block', 'blocking'):
                            blocking = True
                        if props.get('blocking') in (True, 'true', 'True', 1, '1'):
                            blocking = True
                        if blocking:
                            self.collision_rects.append(rect)

                        # create sprite: prefer gid tile image, else sample map_surface
                        sprite = None
                        if gid and gid in tiles_by_gid:
                            try:
                                # scale tile sprite to match draw_scale
                                base = tiles_by_gid[gid]
                                if self.draw_scale != 1.0:
                                    try:
                                        sprite = pygame.transform.smoothscale(base, (int(base.get_width() * self.draw_scale), int(base.get_height() * self.draw_scale))).convert_alpha()
                                    except Exception:
                                        sprite = base.copy()
                                else:
                                    sprite = base.copy()
                            except Exception:
                                sprite = None
                        if sprite is None:
                            try:
                                sprite = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                                # sample from scaled map_surface using scaled area
                                sprite.blit(self.map_surface, (0, 0), area=rect)
                            except Exception:
                                sprite = None

                        # register interactable if properties indicate or object has a type/name
                        obj_type = obj.get('type') or props.get('type') or ''
                        if obj_type or props.get('interactable') or props.get('action') or props.get('dialog'):
                            it = {
                                'id': props.get('id') or obj.get('name') or f"obj_{len(self.interactables)}",
                                'type': obj_type or 'interactable',
                                'rect': rect,
                                'props': props,
                                'sprite': sprite,
                            }
                            self.interactables.append(it)

                        # player start (store in RAW map pixels, not scaled)
                        if (obj.get('name') or '').lower() in ('player', 'player_start') or props.get('player_start'):
                            try:
                                ph = getattr(self.player, 'h', 40)
                            except Exception:
                                ph = 40
                            # keep logical player coords in raw map pixels so update() multiplies by draw_scale once
                            self.player.x = ox_raw + (ow_raw // 2)
                            self.player.y = top_raw
                            player_start_found = True

                # set map bounds/clamps
                self.map_width = map_px_w
                self.map_height = map_px_h
                self.player_min_x = 16
                self.player_max_x = max(16, map_px_w - 16)

                # if no explicit player_start object was found, place player in map center
                if not player_start_found:
                    try:
                        self.player.x = map_px_w // 2
                        # place vertically near mid/lower area (best-effort)
                        self.player.y = int(map_px_h * 0.55)
                    except Exception:
                        pass

                # keep references
                self.map = m
                self.tiles_by_gid = tiles_by_gid
                self.tileset_meta = tileset_meta
            except Exception:
                # if anything fails, keep procedural map as fallback
                pass

                # initialize font and sfx for interact prompts
                try:
                    pygame.font.init()
                    self._ui_font = pygame.font.SysFont(None, 18)
                except Exception:
                    self._ui_font = None
                # load click sound if available
                self._click_sound = None
                try:
                    sfx_path = os.path.join('assets', 'sfx', 'click.wav')
                    if os.path.exists(sfx_path):
                        try:
                            pygame.mixer.init()
                        except Exception:
                            pass
                        try:
                            self._click_sound = pygame.mixer.Sound(sfx_path)
                        except Exception:
                            self._click_sound = None
                except Exception:
                    self._click_sound = None

    def handle_event(self, event: pygame.event.EventType):
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # right-click: if clicking a nearby interactable, trigger its action and play click sound
            sx, sy = event.pos
            for it in list(self.interactables):
                obj_screen = it['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                if obj_screen.collidepoint((sx, sy)):
                    px = int(self.player.x * self.draw_scale) - self.camera_x + self.map_offset[0]
                    py = int(self.player.y * self.draw_scale) + self.map_offset[1]
                    dist = math.hypot(px - obj_screen.centerx, py - obj_screen.centery)
                    if dist < self._hover_distance:
                        # play click sound if available
                        if getattr(self, '_click_sound', None):
                            try:
                                self._click_sound.play()
                            except Exception:
                                pass
                        # simple feedback popup; real action hooks can be added later
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

        # determine nearest interactable within hover distance (screen-space)
        self._hover_interactable = None
        try:
            px = int(self.player.x * self.draw_scale) - self.camera_x + self.map_offset[0]
            py = int(self.player.y * self.draw_scale) + self.map_offset[1]
            nearest = None
            nd = float('inf')
            for it in self.interactables:
                obj_screen = it['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                d = math.hypot(px - obj_screen.centerx, py - obj_screen.centery)
                if d < self._hover_distance and d < nd:
                    nd = d
                    nearest = it
            self._hover_interactable = nearest
        except Exception:
            self._hover_interactable = None

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

        # show "check" tooltip when player is near an interactable
        try:
            if self._hover_interactable and self._ui_font:
                it = self._hover_interactable
                screen_rect = it['rect'].move(-self.camera_x + self.map_offset[0], self.map_offset[1])
                txt = "check"
                txt_surf = self._ui_font.render(txt, True, (255, 255, 255))
                tw, th = txt_surf.get_size()
                tx = screen_rect.centerx - tw // 2
                ty = screen_rect.top - th - 8
                # small backdrop
                pygame.draw.rect(screen, (0, 0, 0), (tx - 4, ty - 4, tw + 8, th + 8))
                screen.blit(txt_surf, (tx, ty))
        except Exception:
            pass

        self.ui.draw(screen)
