"""
Yume Nikki (梦日记) Style Puzzle Scene
A surreal dream world with REAL puzzles to solve.
Each effect orb requires solving a unique puzzle.
"""

import pygame
import sys
import os
import math
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --------------------------
# Configuration
# --------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TILE_SIZE = 32
MAP_WIDTH = 25
MAP_HEIGHT = 19

CHAR_FRAME_WIDTH = 23
CHAR_FRAME_HEIGHT = 36
CHAR_SCALE = 1.5
ANIMATION_SPEED = 0.2

DIRECTION_MAP = {
    'down': 0, 'down_right': 1, 'right': 2, 'up_right': 3,
    'up': 4, 'up_left': 5, 'left': 6, 'down_left': 7,
}

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "Silver.ttf")
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "yume_nikki")
TILES_DIR = os.path.join(ASSET_DIR, "tiles")
SPRITES_DIR = os.path.join(ASSET_DIR, "sprites")

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_DREAM = (40, 20, 50)
COLOR_TEXT = (200, 180, 220)


class Character:
    def __init__(self, sprite_path: str, x: float, y: float):
        self.x = x
        self.y = y
        self.speed = 120.0
        self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
        self.frames = self._load_frames()
        self.direction = 'down'
        self.is_moving = False
        self.frame_index = 0
        self.animation_timer = 0.0
        self.collision_width = 16
        self.collision_height = 12
    
    def _load_frames(self) -> dict:
        frames = {}
        for dir_name, row in DIRECTION_MAP.items():
            frames[dir_name] = []
            for col in range(9):
                rect = pygame.Rect(col * CHAR_FRAME_WIDTH, row * CHAR_FRAME_HEIGHT,
                                   CHAR_FRAME_WIDTH, CHAR_FRAME_HEIGHT)
                frame = self.sprite_sheet.subsurface(rect)
                scaled = pygame.transform.scale(frame,
                    (int(CHAR_FRAME_WIDTH * CHAR_SCALE), int(CHAR_FRAME_HEIGHT * CHAR_SCALE)))
                frames[dir_name].append(scaled)
        return frames
    
    def update(self, dt: float, dx: float, dy: float, collision_check=None):
        if dx != 0 or dy != 0:
            self.is_moving = True
            self.direction = self._get_direction(dx, dy)
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071
            new_x = self.x + dx * self.speed * dt
            new_y = self.y + dy * self.speed * dt
            if collision_check:
                if not collision_check(new_x, self.y, self.collision_width, self.collision_height):
                    self.x = new_x
                if not collision_check(self.x, new_y, self.collision_width, self.collision_height):
                    self.y = new_y
            else:
                self.x, self.y = new_x, new_y
        else:
            self.is_moving = False
        
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= ANIMATION_SPEED:
                self.animation_timer = 0
                self.frame_index = (self.frame_index % 8) + 1
        else:
            self.frame_index = 0
    
    def _get_direction(self, dx, dy):
        if dx > 0 and dy > 0: return 'down_right'
        elif dx < 0 and dy > 0: return 'down_left'
        elif dx > 0 and dy < 0: return 'up_right'
        elif dx < 0 and dy < 0: return 'up_left'
        elif dx > 0: return 'right'
        elif dx < 0: return 'left'
        elif dy > 0: return 'down'
        return 'up'
    
    def draw(self, surface, camera_x=0, camera_y=0):
        frame = self.frames[self.direction][self.frame_index]
        draw_x = self.x - camera_x - frame.get_width() // 2
        draw_y = self.y - camera_y - frame.get_height() + self.collision_height
        surface.blit(frame, (draw_x, draw_y))
    
    def get_tile_pos(self):
        return (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))


class DreamEffect:
    def __init__(self):
        self.static_timer = 0
        self.static_intensity = 0
        self.flash_alpha = 0
        self.flash_color = (255, 255, 255)
        self.screen_shake = 0
        self.shake_intensity = 0
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'speed': random.uniform(10, 30),
                'size': random.randint(1, 3),
                'alpha': random.randint(50, 120),
                'color': random.choice([(200, 180, 255), (255, 200, 220), (180, 255, 220)])
            })
    
    def trigger_static(self, duration=0.5):
        self.static_timer = duration
        self.static_intensity = 255
    
    def flash(self, color, alpha):
        self.flash_color = color
        self.flash_alpha = alpha
    
    def shake(self, duration=0.3, intensity=5):
        self.screen_shake = duration
        self.shake_intensity = intensity
    
    def get_shake_offset(self):
        if self.screen_shake > 0:
            return (random.uniform(-self.shake_intensity, self.shake_intensity),
                    random.uniform(-self.shake_intensity, self.shake_intensity))
        return (0, 0)
    
    def update(self, dt):
        if self.static_timer > 0:
            self.static_timer -= dt
            self.static_intensity = int(255 * (self.static_timer / 0.5))
        else:
            self.static_intensity = 0
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 300 * dt)
        if self.screen_shake > 0:
            self.screen_shake -= dt
        for p in self.particles:
            p['y'] -= p['speed'] * dt
            p['x'] += math.sin(p['y'] * 0.02) * 0.5
            if p['y'] < -10:
                p['y'] = SCREEN_HEIGHT + 10
                p['x'] = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, surface):
        for p in self.particles:
            ps = pygame.Surface((p['size']*2+2, p['size']*2+2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p['color'], p['alpha']), (p['size']+1, p['size']+1), p['size'])
            surface.blit(ps, (int(p['x']), int(p['y'])))
        
        if self.static_intensity > 0:
            ss = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            for _ in range(int(800 * self.static_intensity / 255)):
                x, y = random.randint(0, SCREEN_WIDTH-1), random.randint(0, SCREEN_HEIGHT-1)
                gray = random.randint(100, 255)
                pygame.draw.rect(ss, (gray, gray, gray, min(255, self.static_intensity)), (x, y, 2, 2))
            surface.blit(ss, (0, 0))
        
        if self.flash_alpha > 0:
            fs = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            fs.fill((*self.flash_color, int(self.flash_alpha)))
            surface.blit(fs, (0, 0))
        
        vignette = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for i in range(60):
            alpha = int(80 * (1 - i / 60))
            pygame.draw.rect(vignette, (0, 0, 0, alpha), (i, i, SCREEN_WIDTH-i*2, SCREEN_HEIGHT-i*2), 1)
        surface.blit(vignette, (0, 0))


class DialogueBox:
    def __init__(self):
        self.active = False
        self.text = ""
        self.display_text = ""
        self.char_index = 0
        self.char_timer = 0
        self.char_speed = 0.02
        try:
            self.font = pygame.font.Font(FONT_PATH, 26)
        except:
            self.font = pygame.font.Font(None, 26)
    
    def show(self, text):
        self.active = True
        self.text = text
        self.display_text = ""
        self.char_index = 0
    
    def update(self, dt):
        if self.active and self.char_index < len(self.text):
            self.char_timer += dt
            if self.char_timer >= self.char_speed:
                self.char_timer = 0
                self.display_text += self.text[self.char_index]
                self.char_index += 1
    
    def skip(self):
        if self.char_index < len(self.text):
            self.display_text = self.text
            self.char_index = len(self.text)
        else:
            self.active = False
    
    def draw(self, surface):
        if not self.active:
            return
        box_h = 110
        box_rect = pygame.Rect(30, SCREEN_HEIGHT - box_h - 30, SCREEN_WIDTH - 60, box_h)
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        box_surf.fill((20, 10, 35, 240))
        pygame.draw.rect(box_surf, (120, 80, 160), (0, 0, box_rect.width, box_rect.height), 3)
        surface.blit(box_surf, box_rect.topleft)
        
        for i, line in enumerate(self.display_text.split('\n')):
            text_surf = self.font.render(line, True, COLOR_TEXT)
            surface.blit(text_surf, (box_rect.x + 20, box_rect.y + 15 + i * 28))
        
        if self.char_index >= len(self.text):
            if int(pygame.time.get_ticks() / 500) % 2:
                ind = self.font.render(">>", True, (180, 150, 220))
                surface.blit(ind, (box_rect.right - 45, box_rect.bottom - 30))


# ==================== PUZZLE CLASSES ====================

class SequencePuzzle:
    """谜题1: 按正确顺序踩踏地板符文"""
    def __init__(self, tiles_pos, correct_sequence):
        self.tiles_pos = tiles_pos  # [(x,y), ...]
        self.correct_sequence = correct_sequence  # [0, 2, 1, 3] indices
        self.current_sequence = []
        self.solved = False
        self.tile_colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
        self.hint_shown = False
        self.flash_tile = -1
        self.flash_timer = 0
    
    def check_step(self, char_x, char_y):
        if self.solved:
            return None
        
        tile_x, tile_y = int(char_x // TILE_SIZE), int(char_y // TILE_SIZE)
        
        for i, (tx, ty) in enumerate(self.tiles_pos):
            if tile_x == tx and tile_y == ty:
                if len(self.current_sequence) == 0 or self.current_sequence[-1] != i:
                    self.current_sequence.append(i)
                    self.flash_tile = i
                    self.flash_timer = 0.3
                    
                    # Check if correct so far
                    if self.current_sequence == self.correct_sequence[:len(self.current_sequence)]:
                        if len(self.current_sequence) == len(self.correct_sequence):
                            self.solved = True
                            return "solved"
                        return "correct"
                    else:
                        self.current_sequence = []
                        return "wrong"
        return None
    
    def update(self, dt):
        if self.flash_timer > 0:
            self.flash_timer -= dt
    
    def draw(self, surface, camera_x, camera_y):
        for i, (tx, ty) in enumerate(self.tiles_pos):
            draw_x = tx * TILE_SIZE - camera_x
            draw_y = ty * TILE_SIZE - camera_y
            
            color = self.tile_colors[i % len(self.tile_colors)]
            if self.flash_tile == i and self.flash_timer > 0:
                color = (255, 255, 255)
            
            # Draw rune tile
            tile_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(tile_surf, (*color, 100), (0, 0, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(tile_surf, (*color, 200), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            
            # Draw symbol
            symbols = ['◆', '●', '▲', '■']
            try:
                font = pygame.font.Font(None, 24)
            except:
                font = pygame.font.Font(None, 24)
            sym = font.render(symbols[i % 4], True, color)
            tile_surf.blit(sym, (TILE_SIZE//2 - sym.get_width()//2, TILE_SIZE//2 - sym.get_height()//2))
            
            surface.blit(tile_surf, (draw_x, draw_y))


class MemoryPuzzle:
    """谜题2: 记忆序列 - 一次性显示整个序列，玩家重复点击"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pattern = []
        self.player_input = []
        self.showing_pattern = False
        self.show_timer = 0
        self.input_mode = False
        self.solved = False
        self.level = 1
        self.max_level = 3  # 3关: 3个、4个、5个
        self.grid = [(0, 0), (1, 0), (0, 1), (1, 1)]  # 2x2 grid
        self.highlight = -1
        self.click_highlight_timer = 0
        self.colors = [(255, 100, 150), (100, 255, 150), (150, 100, 255), (255, 200, 100)]
        self.failed = False
        self.started = False
        # For showing all at once with sequence
        self.show_sequence = []  # List of (cell_index, start_time, end_time)
        self.pattern_duration = 0
    
    def start_round(self):
        # Generate pattern based on level (level 1 = 3 items, level 2 = 4, level 3 = 5)
        pattern_length = self.level + 2
        self.pattern = [random.randint(0, 3) for _ in range(pattern_length)]
        self.player_input = []
        self.showing_pattern = True
        self.show_timer = 0
        self.input_mode = False
        self.failed = False
        self.started = True
        
        # Build show sequence - each light flashes for 0.4s with 0.1s gap
        self.show_sequence = []
        time = 0.3  # Small delay before starting
        for idx in self.pattern:
            self.show_sequence.append((idx, time, time + 0.4))
            time += 0.5
        self.pattern_duration = time + 0.3  # Extra time at end
    
    def handle_click(self, rel_x, rel_y):
        if not self.input_mode or self.solved:
            return None
        
        cell_size = TILE_SIZE
        gx = int(rel_x // cell_size)
        gy = int(rel_y // cell_size)
        
        if 0 <= gx < 2 and 0 <= gy < 2:
            cell_idx = gy * 2 + gx
            self.player_input.append(cell_idx)
            self.highlight = cell_idx
            self.click_highlight_timer = 0.25
            
            # Check input
            if self.player_input[-1] != self.pattern[len(self.player_input) - 1]:
                self.failed = True
                self.player_input = []
                self.pattern = []
                self.level = 1
                self.started = False
                return "wrong"
            
            if len(self.player_input) == len(self.pattern):
                self.level += 1
                if self.level > self.max_level:
                    self.solved = True
                    return "solved"
                else:
                    # Short delay before next round
                    self.input_mode = False
                    self.show_timer = -0.5  # Negative = delay before showing
                    self.showing_pattern = True
                    self.start_round()
                    return "next_level"
        
        return "input"
    
    def update(self, dt):
        if self.showing_pattern:
            self.show_timer += dt
            if self.show_timer >= self.pattern_duration:
                self.showing_pattern = False
                self.input_mode = True
        
        if self.click_highlight_timer > 0:
            self.click_highlight_timer -= dt
            if self.click_highlight_timer <= 0:
                self.highlight = -1
    
    def _get_current_highlights(self):
        """Return list of currently highlighted cells"""
        if not self.showing_pattern or self.show_timer < 0:
            return []
        highlights = []
        for cell_idx, start, end in self.show_sequence:
            if start <= self.show_timer <= end:
                highlights.append(cell_idx)
        return highlights
    
    def draw(self, surface, camera_x, camera_y):
        base_x = self.x * TILE_SIZE - camera_x
        base_y = self.y * TILE_SIZE - camera_y
        
        current_highlights = self._get_current_highlights()
        
        # Draw 2x2 grid
        for i, (gx, gy) in enumerate(self.grid):
            dx = base_x + gx * TILE_SIZE
            dy = base_y + gy * TILE_SIZE
            
            color = self.colors[i]
            alpha = 80
            is_highlighted = False
            
            # Highlight during pattern show
            if i in current_highlights:
                alpha = 255
                is_highlighted = True
            # Highlight on click
            elif self.highlight == i and self.click_highlight_timer > 0:
                alpha = 220
                is_highlighted = True
            
            # Draw glow effect first
            if is_highlighted:
                glow = pygame.Surface((TILE_SIZE+16, TILE_SIZE+16), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 120), (0, 0, TILE_SIZE+16, TILE_SIZE+16), border_radius=8)
                surface.blit(glow, (dx-8, dy-8))
            
            cell_surf = pygame.Surface((TILE_SIZE-2, TILE_SIZE-2), pygame.SRCALPHA)
            pygame.draw.rect(cell_surf, (*color, alpha), (0, 0, TILE_SIZE-2, TILE_SIZE-2))
            pygame.draw.rect(cell_surf, (*color, 200), (0, 0, TILE_SIZE-2, TILE_SIZE-2), 2)
            surface.blit(cell_surf, (dx+1, dy+1))
        
        # Draw status text
        try:
            font = pygame.font.Font(FONT_PATH, 18)
        except:
            font = pygame.font.Font(None, 18)
        
        if not self.started:
            hint = font.render("Press SPACE to start", True, (200, 180, 220))
            surface.blit(hint, (base_x - 20, base_y - 25))
        elif self.showing_pattern:
            hint = font.render(f"Memorize! ({len(self.pattern)} lights)", True, (255, 200, 100))
            surface.blit(hint, (base_x - 25, base_y - 25))
        elif self.input_mode:
            progress = f"{len(self.player_input)}/{len(self.pattern)}"
            hint = font.render(f"Repeat! {progress} - Level {self.level}/{self.max_level}", True, (100, 255, 150))
            surface.blit(hint, (base_x - 45, base_y - 25))


class LightsPuzzle:
    """谜题3: 关灯游戏 - 2x2格子，点击会翻转自己和相邻格子"""
    def __init__(self, x, y, size=2):
        self.x = x
        self.y = y
        self.size = size
        # Start with only one light on - requires thinking to solve
        # Solution: click the one that's off diagonally
        self.grid = [[1, 0], [0, 1]]  # Diagonal pattern
        self.solved = False
        self.colors = [(60, 40, 80), (220, 180, 255)]  # Off / On colors
        self.click_timer = 0
        self.last_clicked = None
        self.affected_cells = []  # Track cells affected by last click
    
    def toggle(self, gx, gy):
        if self.solved:
            return
        
        self.last_clicked = (gx, gy)
        self.click_timer = 0.3
        self.affected_cells = []
        
        # Toggle clicked cell and adjacent cells (up, down, left, right)
        for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                self.grid[ny][nx] = 1 - self.grid[ny][nx]
                self.affected_cells.append((nx, ny))
        
        # Check if solved (all off or all on)
        first = self.grid[0][0]
        self.solved = all(self.grid[y][x] == first 
                         for y in range(self.size) for x in range(self.size))
    
    def handle_click(self, rel_x, rel_y):
        cell_size = TILE_SIZE
        gx = int(rel_x // cell_size)
        gy = int(rel_y // cell_size)
        
        if 0 <= gx < self.size and 0 <= gy < self.size:
            self.toggle(gx, gy)
            return "solved" if self.solved else "toggle"
        return None
    
    def update(self, dt):
        if self.click_timer > 0:
            self.click_timer -= dt
    
    def draw(self, surface, camera_x, camera_y):
        base_x = self.x * TILE_SIZE - camera_x
        base_y = self.y * TILE_SIZE - camera_y
        
        for gy in range(self.size):
            for gx in range(self.size):
                dx = base_x + gx * TILE_SIZE
                dy = base_y + gy * TILE_SIZE
                
                is_on = self.grid[gy][gx] == 1
                color = self.colors[1] if is_on else self.colors[0]
                
                # Glow effect for lit cells
                if is_on:
                    glow = pygame.Surface((TILE_SIZE+14, TILE_SIZE+14), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (200, 150, 255, 60), 
                                      (TILE_SIZE//2+7, TILE_SIZE//2+7), TILE_SIZE//2+7)
                    surface.blit(glow, (dx-7, dy-7))
                
                # Click feedback - show affected cells
                if (gx, gy) in self.affected_cells and self.click_timer > 0:
                    color = (255, 255, 200) if (gx, gy) == self.last_clicked else (200, 200, 180)
                
                cell_surf = pygame.Surface((TILE_SIZE-2, TILE_SIZE-2), pygame.SRCALPHA)
                pygame.draw.rect(cell_surf, (*color, 230), (0, 0, TILE_SIZE-2, TILE_SIZE-2), border_radius=4)
                pygame.draw.rect(cell_surf, (180, 140, 220), (0, 0, TILE_SIZE-2, TILE_SIZE-2), 2, border_radius=4)
                surface.blit(cell_surf, (dx+1, dy+1))
        
        try:
            font = pygame.font.Font(FONT_PATH, 18)
            small_font = pygame.font.Font(FONT_PATH, 14)
        except:
            font = pygame.font.Font(None, 18)
            small_font = pygame.font.Font(None, 14)
        
        # Count how many are on
        on_count = sum(self.grid[y][x] for y in range(self.size) for x in range(self.size))
        hint = font.render(f"Make all same! ({on_count}/4 lit)", True, (200, 180, 220))
        surface.blit(hint, (base_x - 25, base_y - 25))
        
        # Show that clicking affects neighbors
        hint2 = small_font.render("Click toggles + neighbors", True, (150, 130, 170))
        surface.blit(hint2, (base_x - 30, base_y + self.size * TILE_SIZE + 5))


class CodePuzzle:
    """谜题4: 密码锁 - 根据提示输入正确数字"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.code = [random.randint(1, 9) for _ in range(3)]
        self.current = [0, 0, 0]
        self.selected = 0
        self.solved = False
        self.hints_found = 0
        self.revealed_digits = [False, False, False]  # Track which digits are revealed
        self.hint_locations = []  # Will be set by game
    
    def reveal_digit(self, index):
        """Reveal a specific digit when hint is found"""
        if 0 <= index < 3:
            self.revealed_digits[index] = True
            self.hints_found += 1
    
    def adjust(self, index, delta):
        if self.solved:
            return
        self.current[index] = (self.current[index] + delta) % 10
        
        # Check solution
        if self.current == self.code:
            self.solved = True
            return "solved"
        return "adjust"
    
    def draw(self, surface, camera_x, camera_y):
        base_x = self.x * TILE_SIZE - camera_x
        base_y = self.y * TILE_SIZE - camera_y
        
        try:
            font = pygame.font.Font(FONT_PATH, 32)
            small_font = pygame.font.Font(FONT_PATH, 18)
            big_font = pygame.font.Font(FONT_PATH, 24)
        except:
            font = pygame.font.Font(None, 32)
            small_font = pygame.font.Font(None, 18)
            big_font = pygame.font.Font(None, 24)
        
        # Draw title
        title = big_font.render("CODE LOCK", True, (255, 200, 100))
        surface.blit(title, (base_x + 52 - title.get_width()//2, base_y - 55))
        
        # Draw code display
        for i in range(3):
            dx = base_x + i * 35
            
            # Up arrow
            up_color = (100, 255, 100) if self.selected == i else (80, 80, 80)
            pygame.draw.polygon(surface, up_color, 
                              [(dx+15, base_y-15), (dx+5, base_y), (dx+25, base_y)])
            
            # Number box - highlight if correct
            box_surf = pygame.Surface((30, 40), pygame.SRCALPHA)
            if self.current[i] == self.code[i]:
                box_surf.fill((30, 80, 30, 220))  # Green tint if correct
                pygame.draw.rect(box_surf, (100, 255, 100), (0, 0, 30, 40), 2)
            else:
                box_surf.fill((30, 20, 50, 200))
                pygame.draw.rect(box_surf, (150, 100, 200), (0, 0, 30, 40), 2)
            
            num_text = font.render(str(self.current[i]), True, (255, 200, 150))
            box_surf.blit(num_text, (15 - num_text.get_width()//2, 5))
            surface.blit(box_surf, (dx, base_y + 5))
            
            # Down arrow
            down_color = (100, 255, 100) if self.selected == i else (80, 80, 80)
            pygame.draw.polygon(surface, down_color,
                              [(dx+15, base_y+60), (dx+5, base_y+45), (dx+25, base_y+45)])
        
        # Instructions
        hint = small_font.render("<-/->: select, Up/Down: change", True, (180, 160, 200))
        surface.blit(hint, (base_x - 25, base_y + 68))
        
        # Show how many hints found (without revealing the actual digits)
        hints_text = small_font.render(f"Hints found: {self.hints_found}/3", True, (255, 220, 100))
        surface.blit(hints_text, (base_x + 5, base_y + 88))


class EffectOrb:
    def __init__(self, x, y, effect_name, puzzle=None):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.effect_name = effect_name
        self.puzzle = puzzle
        self.active = True
        self.collected = False
        self.visible = False  # Only visible after puzzle solved
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.glow_timer = 0
        self.pulse_timer = 0
        self.colors = {
            'cat': (255, 200, 150),
            'knife': (255, 100, 100),
            'bicycle': (150, 200, 255),
            'neon': (255, 100, 255),
        }
        self.orb_color = self.colors.get(effect_name, (255, 255, 200))
    
    def update(self, dt):
        self.bob_offset += dt * 2
        self.glow_timer += dt
        self.pulse_timer += dt * 3
        
        # Check if puzzle is solved to make orb visible
        if self.puzzle and self.puzzle.solved and not self.visible:
            self.visible = True
    
    def is_near(self, char_x, char_y, distance=40):
        if not self.visible or self.collected:
            return False
        dx = char_x - self.rect.centerx
        dy = char_y - self.rect.centery
        return math.sqrt(dx*dx + dy*dy) < distance
    
    def collect(self):
        if self.visible and not self.collected:
            self.collected = True
            self.active = False
            return True
        return False
    
    def draw(self, surface, camera_x, camera_y):
        if not self.visible or self.collected:
            return
        
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y - camera_y + math.sin(self.bob_offset) * 8
        
        # Outer glow
        pulse = (math.sin(self.pulse_timer) + 1) / 2
        glow_size = 35 + pulse * 15
        glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
        for r in range(int(glow_size), 0, -2):
            alpha = int(60 * (1 - r / glow_size) * (0.7 + pulse * 0.3))
            pygame.draw.circle(glow_surf, (*self.orb_color, alpha), 
                             (int(glow_size), int(glow_size)), r)
        surface.blit(glow_surf, (draw_x - glow_size + 12, draw_y - glow_size + 12))
        
        # Inner orb
        orb_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(orb_surf, (*self.orb_color, 200), (15, 15), 10)
        pygame.draw.circle(orb_surf, (255, 255, 255, 200), (15, 15), 6)
        pygame.draw.circle(orb_surf, (255, 255, 255, 255), (12, 12), 3)
        surface.blit(orb_surf, (draw_x - 3, draw_y - 3))


class DreamDoor:
    def __init__(self, x, y, sprite=None):
        self.rect = pygame.Rect(x, y, 32, 64)
        self.sprite = sprite
        self.locked = True
        self.opened = False
        self.glow_timer = 0
        self.highlight = False
    
    def update(self, dt):
        self.glow_timer += dt
    
    def is_near(self, char_x, char_y, distance=50):
        dx = char_x - self.rect.centerx
        dy = char_y - self.rect.centery
        self.highlight = math.sqrt(dx*dx + dy*dy) < distance
        return self.highlight
    
    def draw(self, surface, camera_x, camera_y):
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y - camera_y
        
        # Glow if unlocked
        if not self.locked:
            glow_size = 50 + math.sin(self.glow_timer * 2) * 10
            glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
            for r in range(int(glow_size), 0, -3):
                alpha = int(40 * (1 - r / glow_size))
                pygame.draw.circle(glow_surf, (200, 180, 255, alpha),
                                 (int(glow_size), int(glow_size)), r)
            surface.blit(glow_surf, (draw_x + 16 - glow_size, draw_y + 32 - glow_size))
        
        if self.sprite:
            surface.blit(self.sprite, (draw_x, draw_y))
        else:
            pygame.draw.rect(surface, (60, 40, 50), (draw_x, draw_y, 32, 64))
            pygame.draw.rect(surface, (100, 60, 80), (draw_x+4, draw_y+4, 24, 56))
            knob_color = (100, 255, 100) if not self.locked else (150, 50, 50)
            pygame.draw.circle(surface, knob_color, (draw_x + 24, draw_y + 35), 4)
        
        if self.locked and self.highlight:
            try:
                font = pygame.font.Font(FONT_PATH, 18)
            except:
                font = pygame.font.Font(None, 18)
            lock_text = font.render("LOCKED", True, (255, 100, 100))
            surface.blit(lock_text, (draw_x - 5, draw_y - 20))


class HintObject:
    """Hint objects scattered around - interact to get puzzle hints"""
    def __init__(self, x, y, hint_text, puzzle_type, hint_number=0):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hint_text = hint_text
        self.puzzle_type = puzzle_type
        self.hint_number = hint_number  # 1, 2, 3 for code hints
        self.found = False
        self.glow_timer = 0
    
    def update(self, dt):
        self.glow_timer += dt
    
    def is_near(self, char_x, char_y, distance=50):  # Increased distance
        dx = char_x - self.rect.centerx
        dy = char_y - self.rect.centery
        return math.sqrt(dx*dx + dy*dy) < distance
    
    def draw(self, surface, camera_x, camera_y):
        if self.found:
            return
        
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y - camera_y
        
        # Different style for code hints - much more visible
        if self.puzzle_type == 'code':
            # Large pulsing glow
            pulse = (math.sin(self.glow_timer * 3) + 1) / 2
            glow_size = 40 + pulse * 20
            glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
            for r in range(int(glow_size), 0, -3):
                alpha = int(80 * (1 - r / glow_size) * (0.5 + pulse * 0.5))
                pygame.draw.circle(glow_surf, (255, 150, 50, alpha),
                                  (int(glow_size), int(glow_size)), r)
            surface.blit(glow_surf, (draw_x + TILE_SIZE//2 - glow_size, 
                                    draw_y + TILE_SIZE//2 - glow_size))
            
            # Bright golden book/scroll icon
            icon_surf = pygame.Surface((TILE_SIZE + 8, TILE_SIZE + 8), pygame.SRCALPHA)
            pygame.draw.rect(icon_surf, (200, 150, 50, 220), (4, 4, TILE_SIZE, TILE_SIZE), border_radius=5)
            pygame.draw.rect(icon_surf, (255, 220, 100), (4, 4, TILE_SIZE, TILE_SIZE), 3, border_radius=5)
            
            # Number indicator (1, 2, or 3)
            try:
                num_font = pygame.font.Font(FONT_PATH, 28)
            except:
                num_font = pygame.font.Font(None, 28)
            num_text = num_font.render(str(self.hint_number), True, (80, 40, 0))
            icon_surf.blit(num_text, (TILE_SIZE//2 + 4 - num_text.get_width()//2, 
                                      TILE_SIZE//2 + 4 - num_text.get_height()//2))
            surface.blit(icon_surf, (draw_x - 4, draw_y - 4))
            
            # Floating text "HINT"
            try:
                label_font = pygame.font.Font(FONT_PATH, 16)
            except:
                label_font = pygame.font.Font(None, 16)
            float_y = math.sin(self.glow_timer * 2) * 5
            label = label_font.render("CODE HINT", True, (255, 220, 100))
            surface.blit(label, (draw_x + TILE_SIZE//2 - label.get_width()//2, 
                                draw_y - 22 + float_y))
        else:
            # Regular hint style for other puzzles
            pulse = (math.sin(self.glow_timer * 2) + 1) / 2
            glow_surf = pygame.Surface((TILE_SIZE + 20, TILE_SIZE + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 200, 100, int(50 + pulse * 50)),
                              (TILE_SIZE//2 + 10, TILE_SIZE//2 + 10), TILE_SIZE//2 + 10)
            surface.blit(glow_surf, (draw_x - 10, draw_y - 10))
            
            # Symbol
            try:
                font = pygame.font.Font(None, 32)
            except:
                font = pygame.font.Font(None, 32)
            symbol = font.render("?", True, (255, 220, 150))
            surface.blit(symbol, (draw_x + TILE_SIZE//2 - symbol.get_width()//2,
                                  draw_y + TILE_SIZE//2 - symbol.get_height()//2))


class YumeNikkiPuzzle:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dream Diary - Puzzle Edition")
        self.clock = pygame.time.Clock()
        
        self._load_assets()
        self._generate_map()
        
        sprite_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "8Direction_TopDown_Character Sprites_ByBossNelNel", "SpriteSheet.png"
        )
        
        spawn_x = 12 * TILE_SIZE + TILE_SIZE // 2
        spawn_y = 10 * TILE_SIZE + TILE_SIZE // 2
        self.character = Character(sprite_path, spawn_x, spawn_y)
        
        self.camera_x = 0
        self.camera_y = 0
        
        self.effects_collected = []
        self.dialogue = DialogueBox()
        self.dream_effect = DreamEffect()
        self.game_complete = False
        
        self._create_puzzles()
        
        self.active_puzzle = None  # Currently interacting puzzle
        self.dream_effect.trigger_static(1.0)
        self.dialogue.show("A strange dream world...\nFour effects are hidden here, each guarded by a puzzle.\n\nExplore and solve them to awaken.")
    
    def _load_assets(self):
        self.tiles = {}
        self.sprites = {}
        
        for filename in ['floor_checker.png', 'void.png', 'eye_tile.png', 'flesh_wall.png',
                        'neon_pink.png', 'neon_cyan.png', 'neon_green.png', 'neon_purple.png', 'static_tv.png']:
            path = os.path.join(TILES_DIR, filename)
            if os.path.exists(path):
                self.tiles[filename.replace('.png', '')] = pygame.image.load(path).convert_alpha()
        
        for filename in ['door.png', 'pillar.png', 'bed.png', 'uboa.png']:
            path = os.path.join(SPRITES_DIR, filename)
            if os.path.exists(path):
                self.sprites[filename.replace('.png', '')] = pygame.image.load(path).convert_alpha()
    
    def _generate_map(self):
        random.seed(42)
        self.map_data = []
        self.collision_map = []
        
        for y in range(MAP_HEIGHT):
            row = []
            collision_row = []
            for x in range(MAP_WIDTH):
                if x == 0 or x == MAP_WIDTH-1 or y == 0 or y == MAP_HEIGHT-1:
                    row.append('void')
                    collision_row.append(1)
                elif x == 1 or x == MAP_WIDTH-2 or y == 1 or y == MAP_HEIGHT-2:
                    row.append('flesh_wall' if random.random() > 0.3 else 'eye_tile')
                    collision_row.append(1)
                else:
                    if random.random() < 0.08:
                        row.append(random.choice(['neon_pink', 'neon_cyan', 'neon_green', 'neon_purple']))
                    else:
                        row.append('floor_checker')
                    collision_row.append(0)
            self.map_data.append(row)
            self.collision_map.append(collision_row)
        
        random.seed()
        
        self.map_surface = pygame.Surface((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
        self.map_surface.fill(COLOR_DREAM)
        
        for y, row in enumerate(self.map_data):
            for x, tile_name in enumerate(row):
                tile = self.tiles.get(tile_name)
                if tile:
                    self.map_surface.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
                else:
                    color = (60, 40, 70) if self.collision_map[y][x] else (40, 20, 50)
                    pygame.draw.rect(self.map_surface, color, 
                                   (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    
    def _create_puzzles(self):
        """Create all puzzles and effect orbs"""
        self.puzzles = []
        self.orbs = []
        self.hints = []
        
        # Puzzle 1: Sequence puzzle (top-left area)
        seq_tiles = [(4, 4), (5, 4), (4, 5), (5, 5)]
        seq_puzzle = SequencePuzzle(seq_tiles, [0, 2, 3, 1])  # Correct order
        self.puzzles.append(('sequence', seq_puzzle))
        orb1 = EffectOrb(4 * TILE_SIZE + 20, 3 * TILE_SIZE, 'Fight Perfectionism', seq_puzzle)
        self.orbs.append(orb1)
        
        # Hint for sequence puzzle
        hint1 = HintObject(7 * TILE_SIZE, 6 * TILE_SIZE, 
                          "The sequence: Red, Blue, Yellow, Green\n(Top-left, Bottom-left, Bottom-right, Top-right)", 
                          'sequence')
        self.hints.append(hint1)
        
        # Puzzle 2: Memory puzzle (top-right area)
        mem_puzzle = MemoryPuzzle(19, 4)
        self.puzzles.append(('memory', mem_puzzle))
        orb2 = EffectOrb(20 * TILE_SIZE + 20, 3 * TILE_SIZE, 'Resist Procrastination', mem_puzzle)
        self.orbs.append(orb2)
        
        # Puzzle 3: Lights puzzle (bottom-left area) - 2x2 simple version
        lights_puzzle = LightsPuzzle(4, 13, 2)
        self.puzzles.append(('lights', lights_puzzle))
        orb3 = EffectOrb(5 * TILE_SIZE, 12 * TILE_SIZE, 'Pursue Nature', lights_puzzle)
        self.orbs.append(orb3)
        
        # Puzzle 4: Code puzzle (bottom-right area)
        code_puzzle = CodePuzzle(19, 13)
        self.puzzles.append(('code', code_puzzle))
        orb4 = EffectOrb(20 * TILE_SIZE + 20, 12 * TILE_SIZE, 'Sort Out Thoughts', code_puzzle)
        self.orbs.append(orb4)
        
        # Hints for code puzzle scattered around - with hint numbers
        code = code_puzzle.code
        hint2 = HintObject(10 * TILE_SIZE, 8 * TILE_SIZE,
                          f"The FIRST digit is: [ {code[0]} ]", 'code', 1)
        hint3 = HintObject(15 * TILE_SIZE, 5 * TILE_SIZE,
                          f"The SECOND digit is: [ {code[1]} ]", 'code', 2)
        hint4 = HintObject(13 * TILE_SIZE, 14 * TILE_SIZE,
                          f"The THIRD digit is: [ {code[2]} ]", 'code', 3)
        self.hints.extend([hint2, hint3, hint4])
        
        # Exit door
        self.exit_door = DreamDoor(12 * TILE_SIZE, 2 * TILE_SIZE, self.sprites.get('door'))
        self.collision_map[2][12] = 1
        self.collision_map[3][12] = 0
    
    def check_collision(self, x, y, width, height):
        check_points = [(x, y), (x - width//2, y), (x + width//2, y),
                       (x, y - height//2), (x, y + height//2)]
        
        for px, py in check_points:
            tile_x, tile_y = int(px // TILE_SIZE), int(py // TILE_SIZE)
            if tile_x < 0 or tile_x >= MAP_WIDTH or tile_y < 0 or tile_y >= MAP_HEIGHT:
                return True
            if self.collision_map[tile_y][tile_x] == 1:
                return True
        return False
    
    def update_camera(self):
        target_x = self.character.x - SCREEN_WIDTH // 2
        target_y = self.character.y - SCREEN_HEIGHT // 2
        max_x = MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH
        max_y = MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT
        target_x = max(0, min(target_x, max_x))
        target_y = max(0, min(target_y, max_y))
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
    
    def _update_code_puzzle_proximity(self):
        """Auto-activate code puzzle when near, deactivate when far"""
        char_x, char_y = self.character.x, self.character.y
        
        for ptype, puzzle in self.puzzles:
            if ptype == 'code' and not puzzle.solved:
                px, py = puzzle.x * TILE_SIZE, puzzle.y * TILE_SIZE
                distance = math.sqrt((char_x - px - 50)**2 + (char_y - py - 30)**2)
                
                # Activate when close
                if distance < 80:
                    if not self.active_puzzle or self.active_puzzle[0] != 'code':
                        self.active_puzzle = ('code', puzzle)
                # Deactivate when far
                elif distance > 120:
                    if self.active_puzzle and self.active_puzzle[0] == 'code':
                        self.active_puzzle = None
                break
    
    def _update_puzzle_proximity(self):
        """Auto-deactivate memory/lights puzzle if player walks too far"""
        if not self.active_puzzle:
            return
        
        ptype, puzzle = self.active_puzzle
        char_x, char_y = self.character.x, self.character.y
        
        if ptype == 'memory':
            px, py = puzzle.x * TILE_SIZE, puzzle.y * TILE_SIZE
            distance = math.sqrt((char_x - px - TILE_SIZE)**2 + (char_y - py - TILE_SIZE)**2)
            if distance > 100:
                # Reset puzzle and deactivate
                puzzle.started = False
                puzzle.pattern = []
                puzzle.player_input = []
                self.active_puzzle = None
        
        elif ptype == 'lights':
            px, py = puzzle.x * TILE_SIZE, puzzle.y * TILE_SIZE
            size = puzzle.size * TILE_SIZE
            distance = math.sqrt((char_x - px - size//2)**2 + (char_y - py - size//2)**2)
            if distance > 120:
                self.active_puzzle = None
    
    def handle_interaction(self):
        char_x, char_y = self.character.x, self.character.y
        
        # Check hints
        for hint in self.hints:
            if hint.is_near(char_x, char_y) and not hint.found:
                hint.found = True
                self.dialogue.show(f"*** CODE HINT DISCOVERED! ***\n{hint.hint_text}")
                self.dream_effect.flash((255, 220, 100), 120)
                self.dream_effect.shake(0.2, 3)
                if hint.puzzle_type == 'code':
                    for ptype, puzzle in self.puzzles:
                        if ptype == 'code':
                            # Reveal the specific digit based on hint_number
                            digit_index = hint.hint_number - 1  # Convert 1,2,3 to 0,1,2
                            puzzle.reveal_digit(digit_index)
                return
        
        # Check orbs
        for orb in self.orbs:
            if orb.is_near(char_x, char_y):
                if orb.collect():
                    self.effects_collected.append(orb.effect_name)
                    self.dialogue.show(f"Obtained [{orb.effect_name.upper()}] effect!")
                    self.dream_effect.flash(orb.orb_color, 150)
                    self.dream_effect.shake(0.3, 5)
                    
                    if len(self.effects_collected) >= 4:
                        self.exit_door.locked = False
                        self.collision_map[2][12] = 0
                return
        
        # Check door
        if self.exit_door.is_near(char_x, char_y):
            if self.exit_door.locked:
                remaining = 4 - len(self.effects_collected)
                self.dialogue.show(f"The door is sealed.\nSolve {remaining} more puzzle(s) to unlock.")
                self.dream_effect.flash((100, 50, 50), 50)
            else:
                self.exit_door.opened = True
                self.dialogue.show("All puzzles solved...\nYou feel yourself awakening...")
                self.dream_effect.flash((255, 255, 255), 200)
                self.game_complete = True
            return
        
        # Check puzzles
        for ptype, puzzle in self.puzzles:
            if ptype == 'sequence':
                # Handled in update via stepping
                pass
            elif ptype == 'memory':
                px, py = puzzle.x * TILE_SIZE, puzzle.y * TILE_SIZE
                if abs(char_x - px - TILE_SIZE) < 50 and abs(char_y - py - TILE_SIZE) < 50:
                    if not puzzle.started and not puzzle.solved:
                        puzzle.start_round()
                        self.dialogue.show("Memory puzzle started!\nWatch the pattern and repeat it.")
                        self.active_puzzle = ('memory', puzzle)
                    return
            elif ptype == 'lights':
                px, py = puzzle.x * TILE_SIZE, puzzle.y * TILE_SIZE
                size = puzzle.size * TILE_SIZE
                if abs(char_x - px - size//2) < 60 and abs(char_y - py - size//2) < 60:
                    if not puzzle.solved:
                        self.dialogue.show("Lights puzzle!\nClick tiles to toggle them.\nMake all lights the same color.")
                        self.active_puzzle = ('lights', puzzle)
                    return
            elif ptype == 'code':
                # Code puzzle is auto-activated by proximity, no need for SPACE
                pass
        
        # Don't show "..." if nothing was found - just do nothing
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.active_puzzle:
                        # Reset puzzle state if needed
                        ptype, puzzle = self.active_puzzle
                        if ptype == 'memory' and puzzle.started:
                            puzzle.started = False
                            puzzle.pattern = []
                            puzzle.player_input = []
                        self.active_puzzle = None
                        self.dialogue.active = False  # Close any dialogue
                    else:
                        return False
                
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if self.dialogue.active:
                        self.dialogue.skip()
                    elif not self.active_puzzle:
                        self.handle_interaction()
                
                # Code puzzle input (use arrow keys to avoid conflict with movement)
                if self.active_puzzle and self.active_puzzle[0] == 'code':
                    puzzle = self.active_puzzle[1]
                    if event.key == pygame.K_LEFT:
                        puzzle.selected = (puzzle.selected - 1) % 3
                    elif event.key == pygame.K_RIGHT:
                        puzzle.selected = (puzzle.selected + 1) % 3
                    elif event.key == pygame.K_UP:
                        result = puzzle.adjust(puzzle.selected, 1)
                        if result == "solved":
                            self.dialogue.show("Code correct! The lock opens!")
                            self.dream_effect.flash((100, 255, 100), 150)
                            self.active_puzzle = None
                    elif event.key == pygame.K_DOWN:
                        result = puzzle.adjust(puzzle.selected, -1)
                        if result == "solved":
                            self.dialogue.show("Code correct! The lock opens!")
                            self.dream_effect.flash((100, 255, 100), 150)
                            self.active_puzzle = None
                
                if event.key == pygame.K_e:
                    if self.effects_collected:
                        effects = ", ".join([f"[{e.upper()}]" for e in self.effects_collected])
                        self.dialogue.show(f"Collected Effects ({len(self.effects_collected)}/4):\n{effects}")
                    else:
                        self.dialogue.show("No effects yet. Solve the puzzles!")
            
            # Mouse input for memory and lights puzzles
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                if self.active_puzzle:
                    ptype, puzzle = self.active_puzzle
                    
                    if ptype == 'memory' and puzzle.input_mode:
                        px = puzzle.x * TILE_SIZE - self.camera_x
                        py = puzzle.y * TILE_SIZE - self.camera_y
                        rel_x, rel_y = mx - px, my - py
                        
                        if 0 <= rel_x < 2*TILE_SIZE and 0 <= rel_y < 2*TILE_SIZE:
                            result = puzzle.handle_click(rel_x, rel_y)
                            if result == "solved":
                                self.dialogue.show("Memory puzzle complete!")
                                self.dream_effect.flash((100, 255, 100), 150)
                                self.active_puzzle = None
                            elif result == "wrong":
                                self.dialogue.show("Wrong! Pattern reset. Press SPACE to try again.")
                                self.dream_effect.flash((255, 100, 100), 100)
                                self.dream_effect.shake(0.2, 3)
                                self.active_puzzle = None  # Allow player to move and retry
                            elif result == "next_level":
                                self.dialogue.show(f"Correct! Level {puzzle.level}/{puzzle.max_level}")
                    
                    elif ptype == 'lights':
                        px = puzzle.x * TILE_SIZE - self.camera_x
                        py = puzzle.y * TILE_SIZE - self.camera_y
                        rel_x, rel_y = mx - px, my - py
                        
                        if 0 <= rel_x < puzzle.size*TILE_SIZE and 0 <= rel_y < puzzle.size*TILE_SIZE:
                            result = puzzle.handle_click(rel_x, rel_y)
                            if result == "solved":
                                self.dialogue.show("Lights puzzle complete!")
                                self.dream_effect.flash((100, 255, 100), 150)
                                self.active_puzzle = None
        
        return True
    
    def update(self, dt):
        if self.game_complete:
            self.dialogue.update(dt)
            self.dream_effect.update(dt)
            return
        
        # Character movement
        # Allow movement for most puzzles, only block during pattern showing in memory puzzle
        can_move = True
        if self.active_puzzle:
            ptype, puzzle = self.active_puzzle
            # Only block movement during memory puzzle pattern showing phase
            if ptype == 'memory' and puzzle.showing_pattern:
                can_move = False
            # Lights puzzle allows movement
            # Code puzzle allows movement
        
        if can_move:
            keys = pygame.key.get_pressed()
            dx = dy = 0
            # WASD always works for movement
            if keys[pygame.K_w]: dy = -1
            if keys[pygame.K_s]: dy = 1
            if keys[pygame.K_a]: dx = -1
            if keys[pygame.K_d]: dx = 1
            
            # Arrow keys work for movement only when NOT in code puzzle
            if not (self.active_puzzle and self.active_puzzle[0] == 'code'):
                if keys[pygame.K_UP]: dy = -1
                if keys[pygame.K_DOWN]: dy = 1
                if keys[pygame.K_LEFT]: dx = -1
                if keys[pygame.K_RIGHT]: dx = 1
            
            self.character.update(dt, dx, dy, self.check_collision)
        
        self.update_camera()
        
        # Auto-activate/deactivate code puzzle based on proximity
        self._update_code_puzzle_proximity()
        
        # Auto-deactivate memory/lights puzzle if player walks away
        self._update_puzzle_proximity()
        
        # Update puzzles
        for ptype, puzzle in self.puzzles:
            if ptype == 'sequence':
                puzzle.update(dt)
                result = puzzle.check_step(self.character.x, self.character.y)
                if result == "solved":
                    self.dialogue.show("Sequence correct! The seal breaks!")
                    self.dream_effect.flash((100, 255, 100), 150)
                elif result == "wrong":
                    self.dialogue.show("Wrong sequence... The tiles reset.")
                    self.dream_effect.flash((255, 100, 100), 80)
                elif result == "correct":
                    self.dream_effect.flash((200, 200, 100), 30)
            elif ptype == 'memory':
                puzzle.update(dt)
            elif ptype == 'lights':
                puzzle.update(dt)
        
        # Update orbs
        for orb in self.orbs:
            orb.update(dt)
        
        # Update hints
        for hint in self.hints:
            hint.update(dt)
        
        # Update door
        self.exit_door.update(dt)
        self.exit_door.is_near(self.character.x, self.character.y)
        
        self.dialogue.update(dt)
        self.dream_effect.update(dt)
    
    def draw(self):
        shake_x, shake_y = self.dream_effect.get_shake_offset()
        self.screen.fill(COLOR_DREAM)
        
        # Draw map
        self.screen.blit(self.map_surface, (-self.camera_x + shake_x, -self.camera_y + shake_y))
        
        # Draw puzzles
        for ptype, puzzle in self.puzzles:
            puzzle.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw hints
        for hint in self.hints:
            hint.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw door
        self.exit_door.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw orbs
        for orb in self.orbs:
            orb.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw character
        self.character.draw(self.screen, self.camera_x - shake_x, self.camera_y - shake_y)
        
        # Draw effects
        self.dream_effect.draw(self.screen)
        
        # Draw UI
        self._draw_ui()
        
        # Draw dialogue
        self.dialogue.draw(self.screen)
        
        pygame.display.flip()
    
    def _draw_ui(self):
        try:
            font = pygame.font.Font(FONT_PATH, 24)
            small_font = pygame.font.Font(FONT_PATH, 18)
        except:
            font = pygame.font.Font(None, 24)
            small_font = pygame.font.Font(None, 18)
        
        # Effect indicators
        effect_colors = {
            'cat': (255, 200, 150), 'knife': (255, 100, 100),
            'bicycle': (150, 200, 255), 'neon': (255, 100, 255),
        }
        
        ui_bg = pygame.Surface((200, 80), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 100))
        self.screen.blit(ui_bg, (5, 5))
        
        title_text = font.render("EFFECTS", True, COLOR_TEXT)
        self.screen.blit(title_text, (15, 10))
        
        all_effects = ['cat', 'knife', 'bicycle', 'neon']
        for i, effect in enumerate(all_effects):
            x, y = 15 + i * 45, 40
            if effect in self.effects_collected:
                color = effect_colors[effect]
                pygame.draw.circle(self.screen, color, (x + 15, y + 10), 12)
                pygame.draw.circle(self.screen, (255, 255, 255), (x + 15, y + 10), 8)
            else:
                pygame.draw.circle(self.screen, (60, 50, 70), (x + 15, y + 10), 12)
                pygame.draw.circle(self.screen, (40, 30, 50), (x + 15, y + 10), 10, 2)
        
        # Controls hint
        hint_text = "WASD/Arrows: Move | SPACE: Interact | E: Effects"
        if self.active_puzzle:
            ptype = self.active_puzzle[0]
            if ptype == 'memory':
                hint_text = "Click tiles to repeat the pattern | ESC: Exit"
            elif ptype == 'lights':
                hint_text = "Click tiles to toggle | ESC: Exit"
            elif ptype == 'code':
                hint_text = "WASD: Move | Arrow Keys: Change Code"
        
        hint = small_font.render(hint_text, True, (100, 80, 120))
        self.screen.blit(hint, (10, SCREEN_HEIGHT - 25))
        
        # Puzzle status
        solved_count = sum(1 for _, p in self.puzzles if p.solved)
        status = small_font.render(f"Puzzles: {solved_count}/4", True, (150, 130, 180))
        self.screen.blit(status, (SCREEN_WIDTH - 100, 10))
        
        # Game complete
        if self.game_complete:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            alpha = min(200, int(pygame.time.get_ticks() % 3000 / 10))
            overlay.fill((255, 255, 255, alpha))
            self.screen.blit(overlay, (0, 0))
            
            try:
                big_font = pygame.font.Font(FONT_PATH, 64)
            except:
                big_font = pygame.font.Font(None, 64)
            text = big_font.render("Awakening...", True, (80, 60, 100))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    game = YumeNikkiPuzzle()
    game.run()


if __name__ == "__main__":
    main()
