"""
Simple menu module for the `combine` runner.

This is a lightweight copy/adaptation of the project's main menu so the
`combine/game.py` file can show a menu on startup without depending on the
full `GameManager` class.
"""
import pygame
import os
import math
import random
from pathlib import Path
import sys
# Ensure repository root is on sys.path so imports like `import globals` work
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
import globals as g
from src.utils.font import get_font, draw_text
from PIL import Image


class Meun:
    """A minimal menu that exposes `run()` which returns 'start' or 'quit'.
    """

    def __init__(self, screen):
        self.screen = screen
        # Try to load Silver.ttf from assets (root) or common asset folders; fall back to default
        # Use repo root so paths are correct regardless of CWD
        repo_root = Path(__file__).resolve().parents[1]
        candidates = [
            repo_root / 'assets' / 'Silver.ttf',
            repo_root / 'assets' / 'silver.ttf',
            repo_root / 'assets' / 'Silver.TTF',
            repo_root / 'assets' / 'art' / 'Silver.ttf',
            repo_root / 'assets' / 'fonts' / 'Silver.ttf',
            repo_root / 'combine' / 'docs' / 'Silver.ttf',
        ]

        font_path = None
        for p in candidates:
            try:
                if p.exists():
                    font_path = str(p)
                    break
            except Exception:
                # Ignore invalid path checks and continue
                continue

        # Use centralized font helper which prefers Silver.ttf
        # Prefer an explicit pygame.font.Font created from the resolved font path
        try:
            from src.utils.font import get_font_path
            self.font_path = get_font_path()
        except Exception:
            self.font_path = None

        # If a Silver.ttf (or similar) was found, create Font objects directly from it
        if self.font_path:
            try:
                self.font_large = pygame.font.Font(self.font_path, 96)
                self.font_subtitle = pygame.font.Font(self.font_path, 28)
                self.font_medium = pygame.font.Font(self.font_path, 48)
                self.font_small = pygame.font.Font(self.font_path, 24)

                # Create bold variants by copying and requesting fake bold where necessary
                self.font_large_bold = pygame.font.Font(self.font_path, 96)
                self.font_large_bold.set_bold(True)
                self.font_subtitle_bold = pygame.font.Font(self.font_path, 28)
                self.font_subtitle_bold.set_bold(True)
                self.font_medium_bold = pygame.font.Font(self.font_path, 48)
                self.font_medium_bold.set_bold(True)
                self.font_small_bold = pygame.font.Font(self.font_path, 24)
                self.font_small_bold.set_bold(True)
            except Exception:
                # If direct loading fails for any reason, fall back to helper
                self.font_large = get_font(96)
                self.font_subtitle = get_font(28)
                self.font_medium = get_font(48)
                self.font_small = get_font(24)
                self.font_large_bold = get_font(96)
                self.font_large_bold.set_bold(True)
                self.font_subtitle_bold = get_font(28)
                self.font_subtitle_bold.set_bold(True)
                self.font_medium_bold = get_font(48)
                self.font_medium_bold.set_bold(True)
                self.font_small_bold = get_font(24)
                self.font_small_bold.set_bold(True)
        else:
            # No explicit font found; use the helper which searches for Silver.ttf or falls back
            self.font_large = get_font(96)   # title
            self.font_subtitle = get_font(28)  # subtitle (smaller)
            self.font_medium = get_font(48)  # menu options
            self.font_small = get_font(24)   # instructions/footer

            # Create bold variants. Some TTFs don't include a bold face;
            # pygame will fake bolding if necessary via set_bold(True).
            try:
                self.font_large_bold = get_font(96)
                self.font_large_bold.set_bold(True)
                self.font_subtitle_bold = get_font(28)
                self.font_subtitle_bold.set_bold(True)
                self.font_medium_bold = get_font(48)
                self.font_medium_bold.set_bold(True)
                self.font_small_bold = get_font(24)
                self.font_small_bold.set_bold(True)
            except Exception:
                # Fallback to non-bold if creation fails
                self.font_large_bold = self.font_large
                self.font_subtitle_bold = self.font_subtitle
                self.font_medium_bold = self.font_medium
                self.font_small_bold = self.font_small

        # Debug: store and print resolved font path (if any)
        try:
            from src.utils.font import get_font_path
            self.font_path = get_font_path()
        except Exception:
            self.font_path = None

        if self.font_path:
            print(f"[meun] Using font: {self.font_path}")
        else:
            # Helpful instruction for developers: where to place Silver.ttf
            print("[meun] Silver.ttf not found; using default font")
            print("[meun] To use the Silver font place `Silver.ttf` (or `silver.ttf`) in one of:")
            print("         assets/art/   assets/fonts/   assets/   combine/docs/")

        self.background_color = (20, 20, 40)
        self.text_color = (255, 255, 255)
        self.highlight_color = (100, 150, 255)

        self.menu_options = ["Start Game", "Instructions", "Quit"]
        self.selected_option = 0
        self.show_instructions = False

        self.clock = pygame.time.Clock()

        # letter spacing (kerning) in pixels; increase to make text less condensed
        self.letter_spacing = 2

        # Load or generate a cave background similar to boss hollow
        try:
            self.background = self._load_or_generate_background()
        except Exception:
            self.background = None
        # Background scroll speed multiplier (pixels per tick factor)
        self.bg_scroll_speed = 0.02

        # Cache for resized frame surface to avoid repeated Pillow work each frame
        self._cached_frame_path = None
        self._cached_frame_surf = None
        self._cached_frame_size = (0, 0)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.select_option()
            elif event.key == pygame.K_ESCAPE:
                return 'quit'
        return None

    def select_option(self):
        if self.selected_option == 0:
            return 'start'
        elif self.selected_option == 1:
            # Toggle instructions overlay
            self.show_instructions = not self.show_instructions
            return None
        elif self.selected_option == 2:
            return 'quit'

    def update(self, dt):
        # No dynamic behaviour required for this minimal menu
        pass

    def _load_or_generate_background(self):
        """Try to load assets/backgrounds/boss_hollow_cave.png, otherwise generate
        a similar cave background Surface adapted from testing/generate_cave_background.py.
        This does not call pygame.init() or touch SDL environment; it uses a local RNG.
        """
        # Determine target size from current screen
        screen_w = max(1, self.screen.get_width())
        screen_h = max(1, self.screen.get_height())

        repo_root = Path(__file__).resolve().parents[1]
        out_path = repo_root / 'assets' / 'backgrounds'
        out_path.mkdir(parents=True, exist_ok=True)
        output_file = out_path / 'boss_hollow_cave.png'

        # If the canonical background exists, load and scale it to screen size
        if output_file.exists():
            try:
                img = pygame.image.load(str(output_file)).convert()
                if img.get_size() != (screen_w, screen_h):
                    img = pygame.transform.smoothscale(img, (screen_w, screen_h))
                return img
            except Exception:
                # Fall through to generation on any load error
                pass

        # Generate background onto a surface
        WIDTH = screen_w
        HEIGHT = screen_h
        LAYERS = 4
        SEED = 42

        rnd = random.Random(SEED)

        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Gradient (deep descent feel)
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(15 + 25 * (1 - t))
            g_c = int(10 + 15 * (1 - t))
            b = int(30 + 40 * (1 - t))
            pygame.draw.line(surf, (r, g_c, b, 255), (0, y), (WIDTH, y))

        # Parallax cavern layers
        for layer in range(LAYERS):
            layer_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            color_base = 20 + layer * 10
            alpha = max(30, 120 - layer * 25)
            col = (color_base, color_base // 2, color_base + 40, alpha)
            points_top = []
            x = 0
            while x < WIDTH:
                span = rnd.randint(60, 160)
                peak = rnd.randint(40 + layer * 20, 160 + layer * 30)
                points_top.append((x, peak))
                x += span
            points_top.append((WIDTH, rnd.randint(60, 180)))
            poly = [(0, 0)] + points_top + [(WIDTH, 0)]
            pygame.draw.polygon(layer_surf, col, poly)

            # Inverted stalagmites at bottom (give infinite depth)
            points_bottom = []
            x = 0
            while x < WIDTH:
                span = rnd.randint(50, 140)
                depth = rnd.randint(HEIGHT - 140 - layer * 40, HEIGHT - 40 - layer * 20)
                points_bottom.append((x, depth))
                x += span
            points_bottom.append((WIDTH, rnd.randint(HEIGHT - 180, HEIGHT - 60)))
            poly_b = [(0, HEIGHT)] + points_bottom + [(WIDTH, HEIGHT)]
            pygame.draw.polygon(layer_surf, col, poly_b)
            surf.blit(layer_surf, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

        # Falling particle glow specks
        particle_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(250):
            px = rnd.randint(0, WIDTH - 1)
            py = rnd.randint(0, HEIGHT - 1)
            size = rnd.choice([1, 1, 2])
            brightness = rnd.randint(160, 255)
            particle_surf.fill((0, 0, 0, 0))
            pygame.draw.circle(particle_surf, (brightness, max(0, brightness - 40), 255, 90), (px, py), size)
            surf.blit(particle_surf, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

        # Optionally save the generated background for reuse
        try:
            pygame.image.save(surf, str(output_file))
        except Exception:
            # Ignore save failures (read-only filesystems etc.)
            pass

        return surf

    def draw(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        # Background (animated vertical scroll if available)
        if getattr(self, 'background', None) is not None:
            try:
                t = pygame.time.get_ticks() * self.bg_scroll_speed
                offset_y = int(t) % self.background.get_height()
                # Tile vertically to create infinite descent illusion
                self.screen.blit(self.background, (0, -offset_y))
                self.screen.blit(self.background, (0, -offset_y + self.background.get_height()))
            except Exception:
                # Fallback to plain fill if any error occurs
                self.screen.fill(self.background_color)
        else:
            self.screen.fill(self.background_color)

        # Title (bold) with increased letter spacing
        draw_text(self.screen, self.font_large_bold, "Mind's Maze", self.text_color,
                  (screen_width // 2, 155), spacing=self.letter_spacing, align='center')

        # Subtitle (smaller)
        draw_text(self.screen, self.font_subtitle_bold, "A Psychological Journey", self.text_color,
                  (screen_width // 2, 210), spacing=self.letter_spacing, align='center')

        # Menu options
        start_y = 350
        for i, option in enumerate(self.menu_options):
            color = self.highlight_color if i == self.selected_option else self.text_color
            draw_text(self.screen, self.font_medium_bold, option, color,
                      (screen_width // 2, start_y + i * 60), spacing=self.letter_spacing, align='center')

        # Instructions overlay
        if self.show_instructions:
            # Instruction overlay area
            rect = pygame.Rect(0, 0, screen_width - 200, screen_height - 200)
            rect.center = (screen_width // 2, screen_height // 2)

            # Try to use a UI frame image as the background for the instructions.
            # Look in a few likely locations for the requested asset name.
            frame_filename = 'UI_Flat_FrameSlot02a.png'
            candidates = [
                os.path.join('assets', frame_filename),
                os.path.join('assets', 'ui', frame_filename),
                os.path.join('assets', 'art', frame_filename),
                os.path.join('assets', 'sprites', 'ui', frame_filename),
                os.path.join('assets', 'sprites', frame_filename),
                os.path.join('combine', 'docs', frame_filename),
            ]

            # Prefer to keep the path to the frame image and defer actual loading
            # to Pillow so we can resize using nearest-neighbour for pixel art.
            frame_path = None
            for p in candidates:
                if os.path.exists(p):
                    frame_path = p
                    break

            # If the frame wasn't found in the common locations, search assets/ recursively
            if frame_path is None:
                assets_dir = os.path.join('assets')
                if os.path.exists(assets_dir):
                    for root, dirs, files in os.walk(assets_dir):
                        for fname in files:
                            if fname.lower() == frame_filename.lower():
                                candidate = os.path.join(root, fname)
                                frame_path = candidate
                                break
                        if frame_path is not None:
                            break
            if frame_path is not None:
                try:
                    # Fit the frame into the rect while preserving aspect ratio and leave padding
                    padding = 20
                    max_w = max(1, rect.width - padding * 2)
                    max_h = max(1, rect.height - padding * 2)

                    # Load with Pillow so we can resize using nearest-neighbour to keep pixel art crisp.
                    pil_img = Image.open(frame_path).convert('RGBA')
                    fw, fh = pil_img.size
                    scale = min(max_w / fw, max_h / fh)
                    new_w = max(1, int(fw * scale))
                    new_h = max(1, int(fh * scale))

                    # Source - https://stackoverflow.com/a
                    # Posted by ToddMcCullough
                    # Retrieved 2025-11-10, License - CC BY-SA 4.0
                    #
                    # Use nearest-neighbour resampling to preserve pixel art
                    pil_resized = pil_img.resize((new_w, new_h), resample=Image.NEAREST)

                    # Slight hue shift towards purple so the tutorial window has a subtle purple tint.
                    # Convert to HSV, shift the H channel, then convert back.
                    hsv = pil_resized.convert('HSV')
                    h, s, v = hsv.split()
                    # Small positive shift (0-255 range). Tweak this value for stronger tint.
                    hue_shift = 12
                    h = h.point(lambda p: (p + hue_shift) % 256)
                    hsv_shifted = Image.merge('HSV', (h, s, v))
                    pil_shifted = hsv_shifted.convert('RGBA')

                    # Convert back to a pygame.Surface
                    mode = pil_shifted.mode
                    data = pil_shifted.tobytes()
                    frame_scaled = pygame.image.fromstring(data, (new_w, new_h), mode).convert_alpha()

                    # Center the scaled frame inside the overlay rect
                    frame_x = rect.left + (rect.width - new_w) // 2
                    frame_y = rect.top + (rect.height - new_h) // 2
                    self.screen.blit(frame_scaled, (frame_x, frame_y))

                    # Compute an inner rect for text and draw a semi-opaque purple panel so the text
                    # sits on a surface (not 'floating'). This also respects the padding inside the frame.
                    inner_left = frame_x + padding
                    inner_top = frame_y + padding
                    inner_w = max(1, new_w - padding * 2)
                    inner_h = max(1, new_h - padding * 2)
                    # Move text inward so it doesn't touch the frame edge; 24px inset looks better
                    text_origin_x = inner_left + 24
                    text_origin_y = inner_top + 24

                    panel = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
                    # Slight purple with alpha
                    panel.fill((120, 80, 160, 160))
                    self.screen.blit(panel, (inner_left, inner_top))
                except Exception:
                    # Fall back to filled overlay on error
                    overlay = pygame.Surface((rect.width, rect.height))
                    overlay.fill((40, 40, 60))
                    overlay.set_alpha(230)
                    self.screen.blit(overlay, rect.topleft)
                    # Fallback inset when frame scaling fails
                    text_origin_x = rect.left + 40
                    text_origin_y = rect.top + 40
            else:
                overlay = pygame.Surface((rect.width, rect.height))
                overlay.fill((40, 40, 60))
                overlay.set_alpha(230)
                self.screen.blit(overlay, rect.topleft)
                # Ensure text origin exists even when frame image is not available
                text_origin_x = rect.left + 40
                text_origin_y = rect.top + 40

            instr_lines = [
                "Controls:",
                "  WASD / Arrow Keys: Move",
                "  Mouse: Aim and interact",
                "  ESC: Back / Quit",
                "",
                "Press Enter/Space",
                "to close this screen."
            ]

            # Draw instruction lines starting from the computed text origin so they don't overlap the frame.
            # Ensure the final instruction line (e.g. "Press Enter/Space to close this screen.")
            # is always visible by anchoring it to the bottom of the inner panel if needed.
            line_h = self.font_small_bold.get_linesize()
            spacing_v = line_h + 6

            # Determine inner bottom (where text can end). If we created an inner panel use its bounds,
            # otherwise fall back to the overlay rect bottom with a small margin.
            if 'inner_top' in locals() and 'inner_h' in locals():
                inner_bottom = inner_top + inner_h
            else:
                inner_bottom = rect.top + rect.height - 24

            available_h = inner_bottom - text_origin_y
            # How many lines fit in available space
            max_lines = max(1, available_h // spacing_v)

            if len(instr_lines) <= max_lines:
                for idx, line in enumerate(instr_lines):
                    draw_text(self.screen, self.font_small_bold, line, self.text_color,
                              (text_origin_x, text_origin_y + idx * spacing_v), spacing=self.letter_spacing, align='topleft')
            else:
                # Draw as many top lines as fit minus one (reserve space for anchored last line)
                top_count = max(0, int(max_lines) - 1)
                for idx in range(top_count):
                    draw_text(self.screen, self.font_small_bold, instr_lines[idx], self.text_color,
                              (text_origin_x, text_origin_y + idx * spacing_v), spacing=self.letter_spacing, align='topleft')

                # Anchor the last instructional line to the bottom of the inner area
                last_line = instr_lines[-1]
                last_y = inner_bottom - line_h - 8
                draw_text(self.screen, self.font_small_bold, last_line, self.text_color,
                          (text_origin_x, last_y), spacing=self.letter_spacing, align='topleft')

        # Footer instruction
        draw_text(self.screen, self.font_small_bold,
                  "Use W/S or Arrow Keys to navigate, Enter/Space to select",
                  self.text_color, (screen_width // 2, screen_height - 40), spacing=self.letter_spacing, align='center')

    def run(self):
        fps = getattr(g, 'FPS', 60)
        while True:
            dt = self.clock.tick(fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                result = self.handle_event(event)
                if result in ('start', 'quit'):
                    return result

            self.update(dt)
            self.draw()
            pygame.display.flip()
