import os
import math
import random
import pygame
from pathlib import Path

# This script generates placeholder spritesheets for The Hollow in a pixel/dream-core style.
# Outputs go to assets/sprites/boss/boss_hollow_walk.png and boss_hollow_attack.png.
# Each sheet is a horizontal strip of frames with transparent background.

FRAME_W = 224
FRAME_H = 240
WALK_FRAMES = 15
ATTACK_FRAMES = 12

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / 'assets' / 'sprites' / 'boss'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Colors
BLACK = (10, 10, 10, 255)
PURPLE = (170, 80, 255, 120)
WHITE = (240, 240, 240, 255)
GRAY = (90, 90, 120, 120)
GLOW = (50, 30, 90, 80)
STAR = (220, 220, 240, 140)

random.seed(7)


def make_surface(w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    return surf


def draw_hollow_body(frame: pygame.Surface, t: float, pose: str = 'idle'):
    """Draw a hollow silhouette with subtle jitter/float and dream-core accents."""
    w, h = frame.get_width(), frame.get_height()
    cx, cy = w // 2, int(h * 0.55)

    # Slight drift in x/y for breathing/float effect
    jitter_x = int(3 * math.sin(t * 2.1))
    jitter_y = int(4 * math.sin(t * 1.7 + 0.6))

    # Body proportions
    head_r = int(h * 0.11)
    torso_w = int(w * 0.14)
    torso_h = int(h * 0.42)
    arm_len = int(h * 0.26)
    arm_w = int(w * 0.05)
    leg_h = int(h * 0.27)
    leg_w = int(w * 0.06)

    # Aura glow rings
    for r in range(1, 4):
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(glow, (GLOW[0], GLOW[1], GLOW[2], max(0, GLOW[3] - r * 15)), (cx + jitter_x, int(cy - torso_h * 0.6) + jitter_y), head_r + r * 6)
        frame.blit(glow, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

    # Torso
    torso_rect = pygame.Rect(cx - torso_w // 2 + jitter_x, cy - torso_h // 2 + jitter_y, torso_w, torso_h)
    pygame.draw.rect(frame, BLACK, torso_rect, border_radius=int(torso_w * 0.25))

    # Head
    pygame.draw.circle(frame, BLACK, (cx + jitter_x, int(cy - torso_h * 0.6) + jitter_y), head_r)

    # Eyes (hollow look)
    eye_dx = int(head_r * 0.6)
    eye_r = max(2, int(head_r * 0.35))
    left_eye = (cx - eye_dx + jitter_x, int(cy - torso_h * 0.7) + jitter_y)
    right_eye = (cx + eye_dx + jitter_x, int(cy - torso_h * 0.7) + jitter_y)
    pygame.draw.circle(frame, WHITE, left_eye, eye_r)
    pygame.draw.circle(frame, WHITE, right_eye, eye_r)

    # Arms / pose
    if pose == 'idle':
        # Slight sway
        ang = 0.3 * math.sin(t * 2.0)
        arm_dx = int(arm_len * math.cos(ang) * 0.1)
        arm_dy = int(arm_len * math.sin(ang) * 0.1)
        # left
        lrect = pygame.Rect(cx - torso_w // 2 - arm_w + jitter_x - 8, cy - arm_w // 2 + jitter_y + arm_dy, arm_w, arm_len)
        pygame.draw.rect(frame, BLACK, lrect, border_radius=int(arm_w * 0.5))
        # right
        rrect = pygame.Rect(cx + torso_w // 2 + jitter_x + 8, cy - arm_w // 2 + jitter_y - arm_dy, arm_w, arm_len)
        pygame.draw.rect(frame, BLACK, rrect, border_radius=int(arm_w * 0.5))
    else:
        # Attack: one arm raised casting void shard
        cast_ang = -0.9 + 0.2 * math.sin(t * 2.5)
        arm_x = cx + torso_w // 2 + jitter_x + 8
        arm_y = cy + jitter_y
        ex = arm_x + int(arm_len * 0.85 * math.cos(cast_ang))
        ey = arm_y + int(arm_len * 0.85 * math.sin(cast_ang))
        # arm path
        pygame.draw.line(frame, BLACK, (arm_x, arm_y), (ex, ey), arm_w)
        # void shard glow
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(glow, PURPLE, (ex, ey), int(arm_w * 2.2))
        frame.blit(glow, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)
        # shard core
        pygame.draw.rect(frame, BLACK, pygame.Rect(ex - arm_w // 2, ey - arm_w // 2, arm_w, arm_w))

    # Legs
    leg_off = int(torso_w * 0.25)
    lleg = pygame.Rect(cx - leg_off - leg_w // 2 + jitter_x, cy + torso_h // 2 + jitter_y - 6, leg_w, leg_h)
    rleg = pygame.Rect(cx + leg_off - leg_w // 2 + jitter_x, cy + torso_h // 2 + jitter_y - 6, leg_w, leg_h)
    pygame.draw.rect(frame, BLACK, lleg, border_radius=int(leg_w * 0.4))
    pygame.draw.rect(frame, BLACK, rleg, border_radius=int(leg_w * 0.4))

    # Starry noise on torso
    for _ in range(40):
        sx = random.randint(torso_rect.left, torso_rect.right - 1)
        sy = random.randint(torso_rect.top, torso_rect.bottom - 1)
        if random.random() < 0.2:
            frame.set_at((sx, sy), STAR)

    # Dream-core haze lines
    haze = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(6):
        y = int(h * 0.2) + i * 20 + int(3 * math.sin(t * 1.3 + i))
        pygame.draw.line(haze, GRAY, (int(w * 0.2), y), (int(w * 0.8), y), 1)
    frame.blit(haze, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)


def build_sheet(frames: int, pose: str, filename: str):
    sheet = make_surface(FRAME_W * frames, FRAME_H)
    for i in range(frames):
        f = make_surface(FRAME_W, FRAME_H)
        t = i / max(1, frames - 1)
        draw_hollow_body(f, t * 2 * math.pi, pose=pose)
        sheet.blit(f, (i * FRAME_W, 0))
    out_path = OUT_DIR / filename
    pygame.image.save(sheet, out_path)
    print(f"[gen] wrote {out_path} ({frames} frames @ {FRAME_W}x{FRAME_H})")


def main():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.init()
    build_sheet(WALK_FRAMES, 'idle', 'boss_hollow_walk.png')
    build_sheet(ATTACK_FRAMES, 'cast', 'boss_hollow_attack.png')
    pygame.quit()

if __name__ == '__main__':
    main()
