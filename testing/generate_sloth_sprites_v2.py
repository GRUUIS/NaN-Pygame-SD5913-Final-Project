"""Generate improved pixel-art inspired placeholder sprites for The Sloth.

Creates 3 sheets (walk / attack / fade) with tighter bounding boxes so
collisions feel fair. Frames are deliberately small to avoid large
transparent padding: 160x110 per frame (adjust BOSS2 constants if you
adopt these permanently).

NOTE: This is still programmatic placeholder art. Replace with hand-drawn
pixel art for production.
"""
import pygame, os, math

pygame.init()

FRAME_W = 160
FRAME_H = 110

OUTPUTS = [
    ("assets/sprites/boss/boss_sloth_walk.png", 8, 'walk'),
    ("assets/sprites/boss/boss_sloth_attack.png", 6, 'attack'),
    ("assets/sprites/boss/boss_sloth_fade.png", 6, 'fade'),
]

def ensure_dirs(path):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)

def draw_snail(surface, frame, total, mode):
    # base colors
    shell_col = (70,70,78)
    body_col = (60,85,70)
    eye_col = (200,230,200)
    w,h = surface.get_size()
    # subtle bob
    bob = int(math.sin(frame/total*math.tau)*3)
    # body
    pygame.draw.ellipse(surface, body_col, (20, 50+bob, w-40, 40))
    # shell layers
    shell_rect = pygame.Rect(w//2-38, 24+bob, 76, 66)
    pygame.draw.ellipse(surface, shell_col, shell_rect)
    pygame.draw.ellipse(surface, (50,50,58), shell_rect.inflate(-18,-18))
    pygame.draw.ellipse(surface, (30,30,36), shell_rect.inflate(-36,-36))
    # face / eyes
    pygame.draw.circle(surface, body_col, (50, 68+bob), 18)
    pygame.draw.circle(surface, eye_col, (42, 60+bob), 6)
    pygame.draw.circle(surface, eye_col, (54, 60+bob), 6)
    # pupils
    pygame.draw.circle(surface, (10,10,12), (42, 60+bob), 2)
    pygame.draw.circle(surface, (10,10,12), (54, 60+bob), 2)
    # attack open mouth / slime glow
    if mode=='attack':
        t = (frame/ max(1,total-1))
        mouth_w = 10 + int(12*math.sin(t*math.pi))
        pygame.draw.rect(surface, (20,30,24), (46-mouth_w//2, 72+bob, mouth_w, 10))
        glow = pygame.Surface((w,h), pygame.SRCALPHA)
        pygame.draw.circle(glow, (40,120,60,120), (50, 72+bob), 20+int(6*math.sin(t*math.pi)))
        surface.blit(glow,(0,0))
    if mode=='fade':
        t = frame/max(1,total-1)
        fade_overlay = pygame.Surface((w,h), pygame.SRCALPHA)
        fade_overlay.fill((200,220,210,int(140*t)))
        surface.blit(fade_overlay,(0,0))

def build_sheet(path, frames, mode):
    ensure_dirs(path)
    sheet = pygame.Surface((FRAME_W*frames, FRAME_H), pygame.SRCALPHA)
    for i in range(frames):
        frame_surf = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
        draw_snail(frame_surf, i, frames, mode)
        sheet.blit(frame_surf, (i*FRAME_W,0))
    pygame.image.save(sheet, path)
    print(f"[sloth_v2] wrote {path} ({frames} frames)")

def main():
    for path, frames, mode in OUTPUTS:
        build_sheet(path, frames, mode)
    print("Done. Remember to update BOSS2 constants if adopting new frame size.")

if __name__ == '__main__':
    main()
