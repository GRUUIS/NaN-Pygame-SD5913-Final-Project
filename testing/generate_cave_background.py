import os, math, random, pygame
from pathlib import Path

WIDTH = 1280
HEIGHT = 720
LAYERS = 4
SEED = 42

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / 'assets' / 'backgrounds'
OUT_PATH.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUT_PATH / 'boss_hollow_cave.png'

random.seed(SEED)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()

surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# Gradient (deep descent feel)
for y in range(HEIGHT):
    t = y / HEIGHT
    # dark violet to near black
    r = int(15 + 25 * (1 - t))
    g = int(10 + 15 * (1 - t))
    b = int(30 + 40 * (1 - t))
    pygame.draw.line(surf, (r, g, b, 255), (0, y), (WIDTH, y))

# Parallax cavern layers
for layer in range(LAYERS):
    layer_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    color_base = 20 + layer * 10
    alpha = max(30, 120 - layer * 25)
    col = (color_base, color_base // 2, color_base + 40, alpha)
    points_top = []
    x = 0
    while x < WIDTH:
        span = random.randint(60, 160)
        peak = random.randint(40 + layer * 20, 160 + layer * 30)
        points_top.append((x, peak))
        x += span
    points_top.append((WIDTH, random.randint(60, 180)))
    poly = [(0,0)] + points_top + [(WIDTH,0)]
    pygame.draw.polygon(layer_surf, col, poly)
    # Inverted stalagmites at bottom (give infinite depth)
    points_bottom = []
    x = 0
    while x < WIDTH:
        span = random.randint(50, 140)
        depth = random.randint(HEIGHT-140-layer*40, HEIGHT-40-layer*20)
        points_bottom.append((x, depth))
        x += span
    points_bottom.append((WIDTH, random.randint(HEIGHT-180, HEIGHT-60)))
    poly_b = [(0,HEIGHT)] + points_bottom + [(WIDTH,HEIGHT)]
    pygame.draw.polygon(layer_surf, col, poly_b)
    surf.blit(layer_surf, (0,0), special_flags=pygame.BLEND_PREMULTIPLIED)

# Falling particle glow specks
particle_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for _ in range(250):
    px = random.randint(0, WIDTH-1)
    py = random.randint(0, HEIGHT-1)
    size = random.choice([1,1,2])
    brightness = random.randint(160, 255)
    particle_surf.fill((0,0,0,0))
    pygame.draw.circle(particle_surf, (brightness, brightness-40, 255, 90), (px, py), size)
    surf.blit(particle_surf, (0,0), special_flags=pygame.BLEND_PREMULTIPLIED)

pygame.image.save(surf, OUTPUT_FILE)
print(f"Generated cave background: {OUTPUT_FILE}")
pygame.quit()
