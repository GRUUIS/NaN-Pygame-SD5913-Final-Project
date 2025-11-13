"""Generate improved pixel‑art Sloth sprites (creepy version).

Approach
- Draw at low resolution (pixel grid), then upscale with nearest neighbor
    to get crisp pixels. Final frame size remains 160x110.
- Shell uses banded rings and speckles for an ominous spiral vibe.
- Body is sickly green/gray with dark outline; attack frames glow toxic
    green at the mouth, with drips.
- Bounding boxes are tight to ensure fair collisions.

Note: These are still procedural placeholders; replace with hand art for
production when available.
"""
import pygame, os, math, random

pygame.init()

FRAME_W = 160
FRAME_H = 110
PIX_SCALE = 2  # 2x upscale from pixel canvas to final frame
PIX_W = FRAME_W // PIX_SCALE
PIX_H = FRAME_H // PIX_SCALE

OUTPUTS = [
    ("assets/sprites/boss/boss_sloth_walk.png", 8, 'walk'),
    ("assets/sprites/boss/boss_sloth_attack.png", 6, 'attack'),
    ("assets/sprites/boss/boss_sloth_fade.png", 6, 'fade'),
]

def ensure_dirs(path):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)

def draw_snail_pixel(surface_px: pygame.Surface, frame: int, total: int, mode: str):
    """Draw a creepy pixel‑art snail on a low‑res surface."""
    rng = random.Random(1337 + frame)
    w,h = surface_px.get_size()

    # Palette (muted, eerie)
    SHELL_DARK = (38, 26, 18)
    SHELL_MID = (72, 44, 24)
    SHELL_LIGHT = (122, 84, 44)
    SHELL_BLEACH = (170, 150, 110)
    BODY = (48, 66, 54)
    BODY_LIGHT = (72, 92, 78)
    OUTLINE = (10, 10, 12)
    EYE = (222, 238, 220)
    PUPIL = (8, 8, 10)
    GLOW = (40, 160, 80)
    SHADOW = (12, 16, 14)

    # Bobbing animation
    bob = int(math.sin(frame/ max(1,total) * math.tau) * 1.5)

    # Clear
    surface_px.fill((0,0,0,0))

    # Ground shadow
    shadow = pygame.Surface((w,h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (*SHADOW, 150), (12, h-14+bob, w-24, 10))
    surface_px.blit(shadow,(0,0))

    # Shell (banded rings with speckles)
    shell_cx = int(w*0.60)
    shell_cy = int(h*0.42)+bob
    max_r = int(min(w,h)*0.28)
    for r in range(max_r, 0, -1):
        col = SHELL_DARK if (r//2)%3==0 else (SHELL_MID if (r//2)%3==1 else SHELL_LIGHT)
        pygame.draw.circle(surface_px, col, (shell_cx, shell_cy), r)
        # occasional speckle
        if r % 4 == 0:
            for _ in range(2):
                ax = shell_cx + rng.randint(-r, r)
                ay = shell_cy + rng.randint(-r, r)
                if (ax-shell_cx)**2 + (ay-shell_cy)**2 <= r*r:
                    surface_px.set_at((max(0,min(w-1,ax)), max(0,min(h-1,ay))), SHELL_BLEACH)
    # Shell highlight arc
    pygame.draw.arc(surface_px, SHELL_BLEACH,
                    (shell_cx-max_r, shell_cy-max_r, max_r*2, max_r*2),
                    -0.6, 0.1, 1)
    # Shell outline
    pygame.draw.circle(surface_px, OUTLINE, (shell_cx, shell_cy), max_r, 1)

    # Body (low profile ellipse + head)
    body_rect = pygame.Rect(int(w*0.10), int(h*0.55)+bob, int(w*0.68), int(h*0.22))
    pygame.draw.ellipse(surface_px, BODY, body_rect)
    pygame.draw.ellipse(surface_px, OUTLINE, body_rect, 1)
    head_cx = int(w*0.24)
    head_cy = int(h*0.58)+bob
    pygame.draw.circle(surface_px, BODY_LIGHT, (head_cx, head_cy), 7)
    pygame.draw.circle(surface_px, OUTLINE, (head_cx, head_cy), 7, 1)

    # Eye stalks
    pygame.draw.line(surface_px, BODY_LIGHT, (head_cx-4, head_cy-6), (head_cx-8, head_cy-14), 2)
    pygame.draw.line(surface_px, BODY_LIGHT, (head_cx+4, head_cy-6), (head_cx+10, head_cy-14), 2)
    pygame.draw.circle(surface_px, EYE, (head_cx-8, head_cy-16), 2)
    pygame.draw.circle(surface_px, EYE, (head_cx+10, head_cy-16), 2)
    pygame.draw.circle(surface_px, PUPIL, (head_cx-8, head_cy-16), 1)
    pygame.draw.circle(surface_px, PUPIL, (head_cx+10, head_cy-16), 1)

    # Mouth + toxic glow in attack frames
    if mode == 'attack':
        t = (frame/ max(1,total-1))
        m_w = 4 + int(3*math.sin(t*math.pi))
        m_rect = pygame.Rect(head_cx- m_w, head_cy+2, m_w*2, 3)
        pygame.draw.rect(surface_px, PUPIL, m_rect)
        # glow and drips
        for r in range(6, 0, -1):
            a = int(80 * (r/6)**2)
            pygame.draw.circle(surface_px, (GLOW[0], GLOW[1], GLOW[2], a), (head_cx, head_cy+3), r)
        for d in range(2):
            dx = -2 if d==0 else 2
            pygame.draw.line(surface_px, GLOW, (head_cx+dx, head_cy+6), (head_cx+dx, head_cy+8+rng.randint(0,2)), 1)

    # Fade overlay
    if mode == 'fade':
        t = frame/max(1,total-1)
        overlay = pygame.Surface((w,h), pygame.SRCALPHA)
        overlay.fill((220,230,220, int(120*t)))
        surface_px.blit(overlay,(0,0))

def build_sheet(path, frames, mode):
    ensure_dirs(path)
    sheet = pygame.Surface((FRAME_W*frames, FRAME_H), pygame.SRCALPHA)
    for i in range(frames):
        # draw on pixel canvas then upscale for crisp pixel look
        px = pygame.Surface((PIX_W, PIX_H), pygame.SRCALPHA)
        draw_snail_pixel(px, i, frames, mode)
        frame_surf = pygame.transform.scale(px, (FRAME_W, FRAME_H))
        sheet.blit(frame_surf, (i*FRAME_W, 0))
    pygame.image.save(sheet, path)
    print(f"[sloth_v2] wrote {path} ({frames} frames)")

def main():
    for path, frames, mode in OUTPUTS:
        build_sheet(path, frames, mode)
    print("Done. Remember to update BOSS2 constants if adopting new frame size.")

if __name__ == '__main__':
    main()
