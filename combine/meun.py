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
import globals as g
from src.utils.font import get_font, draw_text


class Meun:
    """A minimal menu that exposes `run()` which returns 'start' or 'quit'.
    """

    def __init__(self, screen):
        self.screen = screen
        # Try to load Silver.ttf from assets/art, fall back to default font
        font_path = None
        candidates = [
            os.path.join('assets', 'art', 'Silver.ttf'),
            os.path.join('assets', 'art', 'silver.ttf'),
            os.path.join('assets', 'art', 'Silver.TTF'),
        ]
        for c in candidates:
            if os.path.exists(c):
                font_path = c
                break

        # Use centralized font helper which prefers Silver.ttf
        # Title larger, subtitle smaller per request
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

            frame_img = None
            for p in candidates:
                if os.path.exists(p):
                    try:
                        frame_img = pygame.image.load(p).convert_alpha()
                        break
                    except Exception:
                        frame_img = None

            if frame_img is not None:
                try:
                    # Scale the frame to the overlay rect while preserving aspect via smoothscale
                    frame_scaled = pygame.transform.smoothscale(frame_img, (rect.width, rect.height))
                    self.screen.blit(frame_scaled, rect.topleft)
                except Exception:
                    # Fall back to filled overlay on error
                    overlay = pygame.Surface((rect.width, rect.height))
                    overlay.fill((40, 40, 60))
                    overlay.set_alpha(230)
                    self.screen.blit(overlay, rect.topleft)
            else:
                overlay = pygame.Surface((rect.width, rect.height))
                overlay.fill((40, 40, 60))
                overlay.set_alpha(230)
                self.screen.blit(overlay, rect.topleft)

            instr_lines = [
                "Controls:",
                "  WASD / Arrow Keys: Move",
                "  Mouse: Aim and interact",
                "  ESC: Back / Quit",
                "",
                "Press Enter/Space to close this screen."
            ]

            for idx, line in enumerate(instr_lines):
                draw_text(self.screen, self.font_small_bold, line, self.text_color,
                          (rect.left + 20, rect.top + 20 + idx * 28), spacing=self.letter_spacing, align='topleft')

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
