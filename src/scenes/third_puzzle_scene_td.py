from __future__ import annotations
"""Top-down Third Puzzle Scene (walk-only) - clean implementation.
"""
import pygame
import math
from typing import List, Optional, Tuple
import globals as g
from ..entities.platform import Platform
from ..systems.ui import UIManager, TextPopup

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
    def __init__(self, x: float, y: float, speed: float = 180.0):
        self.x = x
        self.y = y
        self.w = 32
        self.h = 48
        self.speed = speed
    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx != 0 and dy != 0:
            factor = 0.7071
        else:
            factor = 1.0
        self.x += dx * self.speed * factor * dt
        self.y += dy * self.speed * factor * dt
        self.x = max(0, min(g.SCREENWIDTH - self.w, self.x))
        self.y = max(0, min(g.SCREENHEIGHT - self.h, self.y))
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, g.COLORS.get('player', (200, 100, 100)), (int(self.x), int(self.y), self.w, self.h))

class Tool:
    def __init__(self, kind: str, pos: Tuple[int, int], accepts: List[str]):
        self.kind = kind
        self.x, self.y = pos
        self.rect = pygame.Rect(self.x-16, self.y-16, 32, 32)
        self.accepts = accepts
        self.ready = False
        self.projecting = False
        self.angle = 0.0
        surf = pygame.Surface((160, 160), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (255,255,255,200), (20, 20, 120, 120))
        self.proj_surf = surf
    def install_component(self, item: Item) -> bool:
        if item.type in self.accepts and not self.ready:
            self.ready = True
            return True
        return False
    def toggle(self):
        if self.ready:
            self.projecting = not self.projecting
    def set_angle(self, target: Tuple[int,int]):
        dx = target[0] - self.x
        dy = target[1] - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))
    def render_projection(self):
        surf = pygame.transform.rotate(self.proj_surf, self.angle)
        rect = surf.get_rect(center=(self.x + 60, self.y - 20))
        return surf, rect
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, (120,120,200) if self.ready else (120,80,80), self.rect)

class ProjectionArea:
    def __init__(self, rect: pygame.Rect, threshold: float = 0.5):
        self.rect = rect
        self.mask = pygame.Mask((rect.width, rect.height))
        self.mask.fill()
        self.completed = False
    def draw(self, screen: pygame.Surface):
        col = (80,180,80,120) if self.completed else (120,120,120,80)
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((col[0],col[1],col[2],80))
        screen.blit(s, (self.rect.x, self.rect.y))

class ThirdPuzzleScene:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.ui = UIManager()
        self.player = TopDownPlayer(200, g.SCREENHEIGHT-180)
        self.platforms = [Platform(0, g.SCREENHEIGHT-50, g.SCREENWIDTH, 50)]
        self.items = [Item('battery_1','battery',(220,g.SCREENHEIGHT-140)), Item('bulb_1','bulb',(420,g.SCREENHEIGHT-140))]
        self.tools = [Tool('flashlight',(500,g.SCREENHEIGHT-130),['battery']), Tool('lamp',(700,g.SCREENHEIGHT-130),['bulb'])]
        self.areas = [ProjectionArea(pygame.Rect(600,120,160,200)), ProjectionArea(pygame.Rect(360,120,160,200))]
        self.held_item: Optional[Item] = None
    def handle_event(self, event: pygame.event.EventType):
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mx,my = pygame.mouse.get_pos()
            for it in list(self.items):
                if it.rect().collidepoint((mx,my)):
                    dx = (self.player.x + self.player.w/2) - (it.x + it.w/2)
                    dy = (self.player.y + self.player.h/2) - (it.y + it.h/2)
                    if math.hypot(dx,dy) < 120:
                        self.held_item = it
                        self.items.remove(it)
                        self.ui.add(TextPopup(f"Picked up {it.type}", lambda: (self.player.x,self.player.y), duration=1.2))
                        return
            for t in self.tools:
                if t.rect.collidepoint((mx,my)):
                    if self.held_item and t.install_component(self.held_item):
                        self.ui.add(TextPopup('Installed', lambda: (t.x,t.y), duration=1.0))
                        self.held_item = None
                        return
                    else:
                        if t.ready:
                            t.toggle()
                            return
        elif event.type == pygame.MOUSEMOTION:
            mx,my = event.pos
            for t in self.tools:
                if t.projecting:
                    t.set_angle((mx,my))
    def update(self, dt: float):
        self.player.update(dt)
        self.ui.update(dt)
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
