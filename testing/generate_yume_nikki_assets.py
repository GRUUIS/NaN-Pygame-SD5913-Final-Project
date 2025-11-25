"""
Generate Yume Nikki (梦日记) style pixel art assets.
Creates surreal, dreamlike tiles and objects.
"""

import pygame
import os
import random
import math

# Asset output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "yume_nikki")

def ensure_dir(path):
    """Ensure directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)

def create_checkerboard_floor(size=32):
    """Create a surreal checkerboard floor tile."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Dark purple/red checker pattern (Yume Nikki style)
    colors = [
        (40, 20, 40),   # Dark purple
        (60, 25, 35),   # Dark red-purple
    ]
    
    half = size // 2
    for i in range(2):
        for j in range(2):
            color = colors[(i + j) % 2]
            pygame.draw.rect(surface, color, (i * half, j * half, half, half))
    
    # Add subtle noise
    for _ in range(20):
        x = random.randint(0, size-1)
        y = random.randint(0, size-1)
        r, g, b = surface.get_at((x, y))[:3]
        variation = random.randint(-10, 10)
        new_color = (
            max(0, min(255, r + variation)),
            max(0, min(255, g + variation)),
            max(0, min(255, b + variation))
        )
        surface.set_at((x, y), new_color)
    
    return surface

def create_void_tile(size=32):
    """Create a dark void/abyss tile."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Near-black with subtle variation
    base_color = (8, 5, 12)
    surface.fill(base_color)
    
    # Add occasional dim stars/specks
    for _ in range(3):
        x = random.randint(0, size-1)
        y = random.randint(0, size-1)
        brightness = random.randint(20, 40)
        surface.set_at((x, y), (brightness, brightness, brightness + 10))
    
    return surface

def create_eye_tile(size=32):
    """Create a creepy eye pattern tile (iconic Yume Nikki element)."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill((30, 20, 35))  # Dark background
    
    # Eye white
    center = size // 2
    eye_radius = size // 3
    pygame.draw.ellipse(surface, (200, 180, 170), 
                        (center - eye_radius, center - eye_radius//2, 
                         eye_radius * 2, eye_radius))
    
    # Iris - blood red
    iris_radius = eye_radius // 2
    pygame.draw.circle(surface, (120, 30, 30), (center, center), iris_radius)
    
    # Pupil
    pupil_radius = iris_radius // 2
    pygame.draw.circle(surface, (10, 5, 15), (center, center), pupil_radius)
    
    # Highlight
    pygame.draw.circle(surface, (255, 240, 230), 
                      (center - pupil_radius//2, center - pupil_radius//2), 2)
    
    return surface

def create_flesh_wall(size=32):
    """Create organic flesh-like wall tile."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Flesh pink base
    base = (140, 80, 90)
    surface.fill(base)
    
    # Organic veiny patterns
    for _ in range(5):
        x1 = random.randint(0, size)
        y1 = random.randint(0, size)
        x2 = x1 + random.randint(-15, 15)
        y2 = y1 + random.randint(-15, 15)
        pygame.draw.line(surface, (100, 50, 60), (x1, y1), (x2, y2), 2)
    
    # Darker spots
    for _ in range(8):
        x = random.randint(2, size-3)
        y = random.randint(2, size-3)
        pygame.draw.circle(surface, (110, 60, 70), (x, y), random.randint(1, 3))
    
    return surface

def create_neon_tile(size=32, color_type='pink'):
    """Create neon/fluorescent colored tiles (Neon World style)."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    colors = {
        'pink': (255, 100, 180),
        'cyan': (100, 255, 255),
        'green': (100, 255, 100),
        'purple': (200, 100, 255),
    }
    
    base = colors.get(color_type, colors['pink'])
    
    # Darker version for base
    dark = tuple(c // 3 for c in base)
    surface.fill(dark)
    
    # Bright border pattern
    pygame.draw.rect(surface, base, (0, 0, size, 2))
    pygame.draw.rect(surface, base, (0, size-2, size, 2))
    pygame.draw.rect(surface, base, (0, 0, 2, size))
    pygame.draw.rect(surface, base, (size-2, 0, 2, size))
    
    return surface

def create_door_sprite(width=32, height=64):
    """Create a mysterious door (portal between dream worlds)."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Door frame - dark wood
    frame_color = (50, 30, 20)
    pygame.draw.rect(surface, frame_color, (0, 0, width, height))
    
    # Inner door - deep red
    inner_color = (80, 20, 30)
    pygame.draw.rect(surface, inner_color, (4, 4, width-8, height-8))
    
    # Mysterious glow from crack
    glow_color = (200, 150, 100)
    pygame.draw.line(surface, glow_color, (width//2, 8), (width//2, height-8), 2)
    
    # Door knob - eye-like
    knob_y = height // 2
    pygame.draw.circle(surface, (150, 130, 100), (width - 10, knob_y), 4)
    pygame.draw.circle(surface, (50, 20, 20), (width - 10, knob_y), 2)
    
    return surface

def create_jellyfish_sprite(size=32):
    """Create a floating jellyfish creature."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Semi-transparent body
    center_x = size // 2
    body_top = 4
    body_height = size // 2
    
    # Main body - translucent pink/purple
    body_color = (200, 150, 220, 180)
    pygame.draw.ellipse(surface, body_color, 
                       (4, body_top, size-8, body_height))
    
    # Inner glow
    glow_color = (255, 200, 255, 100)
    pygame.draw.ellipse(surface, glow_color,
                       (8, body_top + 4, size-16, body_height - 8))
    
    # Tentacles
    tentacle_color = (180, 130, 200, 150)
    for i in range(4):
        x = 8 + i * 5
        start_y = body_top + body_height - 4
        # Wavy tentacle
        for j in range(8):
            y = start_y + j * 2
            offset = math.sin(j * 0.5) * 2
            pygame.draw.circle(surface, tentacle_color, (int(x + offset), y), 1)
    
    return surface

def create_monoko_pillar(width=32, height=64):
    """Create a strange pillar/totem."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Stone base
    stone_color = (80, 75, 85)
    pygame.draw.rect(surface, stone_color, (4, 0, width-8, height))
    
    # Carved face patterns
    face_color = (50, 45, 55)
    
    # Multiple faces stacked
    for i in range(3):
        y_offset = i * 20 + 5
        # Eyes
        pygame.draw.circle(surface, face_color, (10, y_offset + 5), 3)
        pygame.draw.circle(surface, face_color, (22, y_offset + 5), 3)
        # Pupils - staring
        pygame.draw.circle(surface, (20, 15, 25), (10, y_offset + 5), 1)
        pygame.draw.circle(surface, (20, 15, 25), (22, y_offset + 5), 1)
        # Mouth - various expressions
        if i == 0:
            pygame.draw.line(surface, face_color, (10, y_offset + 12), (22, y_offset + 12), 2)
        elif i == 1:
            pygame.draw.arc(surface, face_color, (10, y_offset + 8, 12, 8), 0, 3.14, 2)
        else:
            pygame.draw.circle(surface, face_color, (16, y_offset + 12), 3)
    
    return surface

def create_effect_orb(size=24, effect_type='cat'):
    """Create collectible effect orbs."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Outer glow
    glow_colors = {
        'cat': (255, 200, 150),
        'knife': (255, 100, 100),
        'bicycle': (150, 200, 255),
        'umbrella': (100, 150, 255),
        'neon': (255, 100, 255),
    }
    
    color = glow_colors.get(effect_type, (255, 255, 200))
    
    # Radial gradient effect
    for r in range(size//2, 0, -1):
        alpha = int(100 * (1 - r / (size//2)))
        glow = (*color, alpha)
        pygame.draw.circle(surface, glow, (size//2, size//2), r)
    
    # Inner bright core
    pygame.draw.circle(surface, (*color, 255), (size//2, size//2), size//6)
    pygame.draw.circle(surface, (255, 255, 255), (size//2, size//2), size//10)
    
    return surface

def create_static_tv(size=32):
    """Create a static/noise TV (common Yume Nikki element)."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # TV frame
    frame_color = (40, 35, 45)
    pygame.draw.rect(surface, frame_color, (0, 0, size, size))
    
    # Screen area with static
    screen_rect = (3, 3, size-6, size-10)
    for x in range(screen_rect[0], screen_rect[0] + screen_rect[2]):
        for y in range(screen_rect[1], screen_rect[1] + screen_rect[3]):
            gray = random.randint(20, 200)
            surface.set_at((x, y), (gray, gray, gray))
    
    # TV base
    pygame.draw.rect(surface, (30, 25, 35), (8, size-5, size-16, 5))
    
    return surface

def create_bed(width=48, height=32):
    """Create a bed sprite (important in Yume Nikki)."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Bed frame
    frame_color = (60, 40, 30)
    pygame.draw.rect(surface, frame_color, (0, height//3, width, height*2//3))
    
    # Mattress/sheets - pinkish
    sheet_color = (200, 180, 190)
    pygame.draw.rect(surface, sheet_color, (2, height//3 + 2, width-4, height//2 - 4))
    
    # Pillow
    pillow_color = (220, 210, 200)
    pygame.draw.ellipse(surface, pillow_color, (4, height//3 + 4, 20, 12))
    
    # Blanket fold
    pygame.draw.line(surface, (180, 160, 170), (2, height//2), (width-2, height//2), 2)
    
    # Headboard
    pygame.draw.rect(surface, (50, 30, 25), (0, 0, width, height//3))
    
    return surface

def create_uboa_face(size=32):
    """Create Uboa-like face (iconic horror element)."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # White face
    face_color = (240, 235, 230)
    pygame.draw.ellipse(surface, face_color, (2, 2, size-4, size-4))
    
    # Black eyes - wide and unsettling
    eye_color = (10, 5, 15)
    pygame.draw.ellipse(surface, eye_color, (6, 8, 8, 10))
    pygame.draw.ellipse(surface, eye_color, (size-14, 8, 8, 10))
    
    # Wide grin
    mouth_color = (10, 5, 15)
    pygame.draw.arc(surface, mouth_color, (6, 14, size-12, 14), 3.14, 0, 3)
    
    return surface

def generate_all_assets():
    """Generate all Yume Nikki style assets."""
    pygame.init()
    
    ensure_dir(OUTPUT_DIR)
    tiles_dir = os.path.join(OUTPUT_DIR, "tiles")
    sprites_dir = os.path.join(OUTPUT_DIR, "sprites")
    ensure_dir(tiles_dir)
    ensure_dir(sprites_dir)
    
    print("Generating Yume Nikki style assets...")
    
    # Generate tiles
    tiles = {
        'floor_checker.png': create_checkerboard_floor(),
        'void.png': create_void_tile(),
        'eye_tile.png': create_eye_tile(),
        'flesh_wall.png': create_flesh_wall(),
        'neon_pink.png': create_neon_tile(color_type='pink'),
        'neon_cyan.png': create_neon_tile(color_type='cyan'),
        'neon_green.png': create_neon_tile(color_type='green'),
        'neon_purple.png': create_neon_tile(color_type='purple'),
        'static_tv.png': create_static_tv(),
    }
    
    for name, surface in tiles.items():
        path = os.path.join(tiles_dir, name)
        pygame.image.save(surface, path)
        print(f"  Created: {name}")
    
    # Generate sprites
    sprites = {
        'door.png': create_door_sprite(),
        'jellyfish.png': create_jellyfish_sprite(),
        'pillar.png': create_monoko_pillar(),
        'orb_cat.png': create_effect_orb(effect_type='cat'),
        'orb_knife.png': create_effect_orb(effect_type='knife'),
        'orb_bicycle.png': create_effect_orb(effect_type='bicycle'),
        'orb_neon.png': create_effect_orb(effect_type='neon'),
        'bed.png': create_bed(),
        'uboa.png': create_uboa_face(),
    }
    
    for name, surface in sprites.items():
        path = os.path.join(sprites_dir, name)
        pygame.image.save(surface, path)
        print(f"  Created: {name}")
    
    # Create additional variation tiles
    print("Creating tile variations...")
    for i in range(3):
        # Multiple void variations
        void = create_void_tile()
        pygame.image.save(void, os.path.join(tiles_dir, f'void_{i}.png'))
        
        # Multiple floor variations
        floor = create_checkerboard_floor()
        pygame.image.save(floor, os.path.join(tiles_dir, f'floor_{i}.png'))
    
    print(f"\nAll assets generated in: {OUTPUT_DIR}")
    pygame.quit()

if __name__ == "__main__":
    generate_all_assets()
