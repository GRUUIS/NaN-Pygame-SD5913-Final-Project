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

        self.menu_options = ["Start Game", "Settings", "Quit"]
        self.show_settings = False
        self.music_volume = getattr(g, 'music_volume', 0.2)
        self._settings_dragging = False
        self.selected_option = 0
        self.show_instructions = False

        # slider rect cached for interaction
        self._settings_bar_rect = None

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
        # mouse handling for settings slider
        if getattr(self, 'show_settings', False):
            try:
                rect = getattr(self, '_settings_bar_rect', None)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if rect and rect.inflate(12, 16).collidepoint(mx, my):
                        self._settings_dragging = True
                        rel = (mx - rect.x) / float(rect.width)
                        self.music_volume = max(0.0, min(1.0, rel))
                        try:
                            pygame.mixer.music.set_volume(self.music_volume)
                        except Exception:
                            pass
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self._settings_dragging = False
                elif event.type == pygame.MOUSEMOTION and getattr(self, '_settings_dragging', False):
                    mx, my = event.pos
                    if rect:
                        rel = (mx - rect.x) / float(rect.width)
                        self.music_volume = max(0.0, min(1.0, rel))
                        try:
                            pygame.mixer.music.set_volume(self.music_volume)
                        except Exception:
                            pass
            except Exception:
                pass

        return None

    def select_option(self):
        if self.selected_option == 0:
            return 'start'
        elif self.selected_option == 1:
            # Toggle settings overlay
            self.show_settings = not self.show_settings
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
        # Simpler, normalized draw method to avoid indentation issues.
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Background
        if getattr(self, 'background', None) is not None:
            try:
                t = pygame.time.get_ticks() * self.bg_scroll_speed
                offset_y = int(t) % self.background.get_height()
                self.screen.blit(self.background, (0, -offset_y))
                self.screen.blit(self.background, (0, -offset_y + self.background.get_height()))
            except Exception:
                self.screen.fill(self.background_color)
        else:
            self.screen.fill(self.background_color)

        # Title and subtitle
        draw_text(self.screen, self.font_large_bold, "Mind's Maze", self.text_color,
                  (screen_width // 2, 155), spacing=self.letter_spacing, align='center')
        draw_text(self.screen, self.font_subtitle_bold, "A Psychological Journey", self.text_color,
                  (screen_width // 2, 210), spacing=self.letter_spacing, align='center')

        # Menu options
        start_y = 350
        for i, option in enumerate(self.menu_options):
            color = self.highlight_color if i == self.selected_option else self.text_color
            draw_text(self.screen, self.font_medium_bold, option, color,
                      (screen_width // 2, start_y + i * 60), spacing=self.letter_spacing, align='center')

        # Settings overlay (uses UI frame and a volume slider)
        if getattr(self, 'show_settings', False):
            try:
                repo_root = Path(__file__).resolve().parents[1]
                frame_path = repo_root / 'assets' / 'UI' / 'Complete_UI_Essential_Pack_Free' / '01_Flat_Theme' / 'Sprites' / 'UI_Flat_FrameSlot01a.png'
                frame_orig = None
                if frame_path.exists():
                    frame_orig = pygame.image.load(str(frame_path)).convert_alpha()

                screen_w, screen_h = self.screen.get_size()
                fw = 400
                fh = 200
                frame_surf = None
                if frame_orig:
                    iw, ih = frame_orig.get_size()
                    s = max(1, fw // iw)
                    while iw * s < fw or ih * s < fh:
                        s += 1
                    frame_surf = pygame.transform.scale(frame_orig, (iw * s, ih * s))

                frame_x = (screen_w - (frame_surf.get_width() if frame_surf else fw)) // 2
                frame_y = (screen_h - (frame_surf.get_height() if frame_surf else fh)) // 2
                # draw generated settings background if available
                try:
                    bg_path = repo_root / 'assets' / 'UI' / 'settings_background.png'
                    if bg_path.exists():
                        bg_img = pygame.image.load(str(bg_path)).convert_alpha()
                        bw = frame_surf.get_width() if frame_surf else fw
                        bh = frame_surf.get_height() if frame_surf else fh
                        bg_s = pygame.transform.smoothscale(bg_img, (bw, bh))
                        self.screen.blit(bg_s, (frame_x, frame_y))
                    elif frame_surf:
                        self.screen.blit(frame_surf, (frame_x, frame_y))
                except Exception:
                    if frame_surf:
                        self.screen.blit(frame_surf, (frame_x, frame_y))

                # Title
                draw_text(self.screen, self.font_subtitle_bold, "Settings", self.text_color,
                          (screen_w // 2, frame_y + 34), spacing=self.letter_spacing, align='center')

                # load UI sprites for slider
                sprites_dir = repo_root / 'assets' / 'UI' / 'Complete_UI_Essential_Pack_Free' / '01_Flat_Theme' / 'Sprites'
                try:
                    bar_path = sprites_dir / 'UI_Flat_Bar01a.png'
                    fill_path = sprites_dir / 'UI_Flat_BarFill01a.png'
                    
                    # Try generated handle first
                    gen_handle_path = repo_root / 'assets' / 'UI' / 'settings_handle.png'
                    handle_path = sprites_dir / 'UI_Flat_Handle01a.png'
                    
                    bar_img = pygame.image.load(str(bar_path)).convert_alpha() if bar_path.exists() else None
                    fill_img = pygame.image.load(str(fill_path)).convert_alpha() if fill_path.exists() else None
                    
                    if gen_handle_path.exists():
                        handle_img = pygame.image.load(str(gen_handle_path)).convert_alpha()
                    elif handle_path.exists():
                        handle_img = pygame.image.load(str(handle_path)).convert_alpha()
                    else:
                        handle_img = None
                except Exception:
                    bar_img = fill_img = handle_img = None

                bar_w = 240
                bar_h = 24
                bar_x = (screen_w - bar_w) // 2
                bar_y = frame_y + 80
                # cache slider rect for events
                try:
                    self._settings_bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                except Exception:
                    self._settings_bar_rect = None

                if bar_img:
                    try:
                        self.screen.blit(pygame.transform.smoothscale(bar_img, (bar_w, bar_h)), (bar_x, bar_y))
                    except Exception:
                        pygame.draw.rect(self.screen, (60,60,60), (bar_x, bar_y, bar_w, bar_h))
                else:
                    pygame.draw.rect(self.screen, (60,60,60), (bar_x, bar_y, bar_w, bar_h))

                fill_w = int(self.music_volume * bar_w)
                if fill_img:
                    try:
                        self.screen.blit(pygame.transform.smoothscale(fill_img, (max(1, fill_w), bar_h)), (bar_x, bar_y))
                    except Exception:
                        pygame.draw.rect(self.screen, (120,170,255), (bar_x, bar_y, fill_w, bar_h))
                else:
                    pygame.draw.rect(self.screen, (120,170,255), (bar_x, bar_y, fill_w, bar_h))

                handle_w, handle_h = 20, 30
                handle_x = bar_x + fill_w - handle_w // 2
                handle_y = bar_y + (bar_h - handle_h) // 2
                if handle_img:
                    try:
                        self.screen.blit(pygame.transform.smoothscale(handle_img, (handle_w, handle_h)), (handle_x, handle_y))
                    except Exception:
                        pygame.draw.circle(self.screen, (200,200,200), (handle_x+handle_w//2, handle_y+handle_h//2), handle_w//2)
                else:
                    pygame.draw.circle(self.screen, (200,200,200), (handle_x+handle_w//2, handle_y+handle_h//2), handle_w//2)

                # label
                draw_text(self.screen, self.font_small_bold, f"Music Volume: {int(self.music_volume*100)}%", self.text_color,
                          (screen_w // 2, bar_y - 26), spacing=self.letter_spacing, align='center')
            except Exception:
                pass
        # Footer instruction (two lines)
        draw_text(self.screen, self.font_small_bold,
                  "Use W/S or Arrow Keys to navigate, Enter/Space to select",
                  self.text_color, (screen_width // 2, screen_height - 56), spacing=self.letter_spacing, align='center')
        draw_text(self.screen, self.font_small_bold,
                  "C: collect items    (RMB: collect)",
                  self.text_color, (screen_width // 2, screen_height - 32), spacing=self.letter_spacing, align='center')

    def run(self):
        fps = getattr(g, 'FPS', 60)
        # Try to locate and play the requested menu music (looped)
        music_playing = False
        music_path = None
        repo_root = Path(__file__).resolve().parents[1]
        target_name = "WAV_There's_no_Heart_Like_Yours.wav"
        # common candidate locations
        candidates = [
            repo_root / 'assets' / 'sfx' / target_name,
            repo_root / 'assets' / 'music' / target_name,
            repo_root / 'assets' / target_name,
        ]
        for p in candidates:
            if p.exists():
                music_path = str(p)
                break
        # fallback: search assets for a wav containing 'heart' in the name
        if music_path is None:
            assets_dir = repo_root / 'assets'
            if assets_dir.exists():
                for root, dirs, files in os.walk(assets_dir):
                    for fname in files:
                        if fname.lower().endswith('.wav') and 'heart' in fname.lower():
                            music_path = os.path.join(root, fname)
                            break
                    if music_path:
                        break

        if music_path:
            try:
                # ensure mixer initialized
                try:
                    pygame.mixer.get_init()
                except Exception:
                    pygame.mixer.init()
                # use music playback (streaming) and loop indefinitely
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(loops=-1)
                try:
                    pygame.mixer.music.set_volume(getattr(g, 'music_volume', 0.2))
                except Exception:
                    pass
                music_playing = True
                print(f"[meun] playing menu music: {music_path}")
            except Exception as e:
                print(f"[meun] failed to play menu music {music_path}: {e}")
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

        # stop music when menu exits
        if music_playing:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
