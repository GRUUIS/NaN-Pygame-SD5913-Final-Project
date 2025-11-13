import os
import math
import random
import pygame
from pathlib import Path

"""Generate placeholder spritesheets for Boss #2 The Sloth.

Outputs:
  assets/sprites/boss/boss_sloth_walk.png   (8 frames)
  assets/sprites/boss/boss_sloth_attack.png (6 frames)
  assets/sprites/boss/boss_sloth_fade.png   (6 frames)

Each frame: 260x180, simple gray snail with time-ripple lines that fade.
"""

FRAME_W = 260
FRAME_H = 180
WALK_FRAMES = 8
ATTACK_FRAMES = 6
FADE_FRAMES = 6

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'sprites' / 'boss'
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY = (140,140,145,255)
SHELL = (110,110,115,255)
RIPPLE = (200,200,210,90)
HIGHLIGHT = (235,235,240,160)

random.seed(3)

def make_surface(w,h):
    s = pygame.Surface((w,h), pygame.SRCALPHA)
    s.fill((0,0,0,0))
    return s

def draw_snail(frame: pygame.Surface, t: float, pose: str):
    w,h = frame.get_size()
    cx, cy = w//2, int(h*0.63)
    body_w = int(w*0.55)
    body_h = int(h*0.28)
    shell_r = int(h*0.25)
    # slight horizontal slide for walk
    offset = int(6*math.sin(t*math.pi*2)) if pose=='walk' else 0
    # body
    body_rect = pygame.Rect(cx - body_w//2 + offset, cy - body_h//2, body_w, body_h)
    pygame.draw.ellipse(frame, PRIMARY, body_rect)
    # shell
    shell_center = (cx + body_w//4 + offset, cy - body_h//3)
    pygame.draw.circle(frame, SHELL, shell_center, shell_r)
    # time ripples (concentric arcs)
    ripple_surf = pygame.Surface((w,h), pygame.SRCALPHA)
    for i in range(6):
        ang = t*2 + i*0.4
        rad = shell_r - i*6
        if rad <= 6: break
        color = (RIPPLE[0], RIPPLE[1], RIPPLE[2], max(0, RIPPLE[3]-i*10))
        pygame.draw.circle(ripple_surf, color, shell_center, rad, 2)
    frame.blit(ripple_surf,(0,0))
    # eye stalks
    eye_y = cy - body_h//2 - 10
    ex_left = cx - body_w//6 + offset
    ex_right = cx - body_w//10 + offset
    pygame.draw.line(frame, PRIMARY, (ex_left, eye_y), (ex_left, eye_y-18), 4)
    pygame.draw.line(frame, PRIMARY, (ex_right, eye_y), (ex_right, eye_y-14), 4)
    pygame.draw.circle(frame, HIGHLIGHT, (ex_left, eye_y-18), 4)
    pygame.draw.circle(frame, HIGHLIGHT, (ex_right, eye_y-14), 4)
    # fade pose overlay
    if pose=='fade':
        alpha = int(180 * (t))
        overlay = pygame.Surface((w,h), pygame.SRCALPHA)
        overlay.fill((255,255,255,alpha))
        frame.blit(overlay,(0,0))

def build_sheet(frames: int, pose: str, filename: str):
    sheet = make_surface(FRAME_W*frames, FRAME_H)
    for i in range(frames):
        f = make_surface(FRAME_W, FRAME_H)
        draw_snail(f, i/ max(1, frames-1), pose)
        sheet.blit(f, (i*FRAME_W,0))
    out = OUT / filename
    pygame.image.save(sheet, out)
    print('[gen] wrote', out)

def main():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.init()
    build_sheet(WALK_FRAMES,'walk','boss_sloth_walk.png')
    build_sheet(ATTACK_FRAMES,'walk','boss_sloth_attack.png')
    build_sheet(FADE_FRAMES,'fade','boss_sloth_fade.png')
    pygame.quit()

if __name__ == '__main__':
    main()
