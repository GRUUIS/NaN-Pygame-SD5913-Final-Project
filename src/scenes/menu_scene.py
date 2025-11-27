"""
Menu Scene - Main menu implementation

This module contains the main menu scene with navigation options.
"""

import pygame
import os
from pathlib import Path
import globals as g
from .base_scene import BaseScene

class MenuScene(BaseScene):
    """
    Main menu scene with game options.
    """
    
    def __init__(self, game_manager):
        super().__init__(game_manager)
        
        # Menu colors
        self.background_color = (20, 20, 40)
        self.text_color = (255, 255, 255)
        self.highlight_color = (100, 150, 255)
        
        # Menu options
        self.menu_options = ["Start Game", "Settings", "Quit"]
        self.selected_option = 0

        # Settings overlay state
        self.show_settings = False
        self.music_volume = getattr(g, 'music_volume', 0.2)
        self._settings_dragging = False
        # Developer mode flag exposed in settings (default: False)
        self.developer_mode = getattr(g, 'DEVELOPER_MODE', False)
        self._ui_bar = None
        self._ui_fill = None
        self._ui_handle = None
        self._settings_bar_rect = None
        self._dev_checkbox_rect = None
        
        # Font (will use default for now)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 24)
        
        # Title
        self.title_text = "Mind's Maze"
        self.subtitle_text = "A Psychological Journey"
    
    def handle_event(self, event):
        """Handle menu input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.select_option()
            elif event.key == pygame.K_ESCAPE:
                # close settings overlay if open
                if self.show_settings:
                    self.show_settings = False

        # mouse handling for settings slider
        if self.show_settings:
            try:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    rect = getattr(self, '_settings_bar_rect', None)
                    if rect and rect.inflate(12, 16).collidepoint(mx, my):
                        # start dragging and set volume based on click position
                        self._settings_dragging = True
                        rel = (mx - rect.x) / float(rect.width)
                        self.music_volume = max(0.0, min(1.0, rel))
                        try:
                            pygame.mixer.music.set_volume(self.music_volume)
                        except Exception:
                            pass
                    # Developer checkbox click
                    try:
                        chk = getattr(self, '_dev_checkbox_rect', None)
                        if chk and chk.collidepoint(mx, my):
                            self.developer_mode = not getattr(self, 'developer_mode', False)
                            setattr(g, 'DEVELOPER_MODE', self.developer_mode)
                            setattr(g, 'DEBUG_MODE', self.developer_mode)
                    except Exception:
                        pass
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self._settings_dragging = False
                elif event.type == pygame.MOUSEMOTION and self._settings_dragging:
                    mx, my = event.pos
                    rect = getattr(self, '_settings_bar_rect', None)
                    if rect:
                        rel = (mx - rect.x) / float(rect.width)
                        self.music_volume = max(0.0, min(1.0, rel))
                        try:
                            pygame.mixer.music.set_volume(self.music_volume)
                        except Exception:
                            pass
            except Exception:
                pass
    
    def select_option(self):
        """Handle menu option selection."""
        if self.selected_option == 0:  # Start Game
            self.game_manager.change_scene('gameplay')
        elif self.selected_option == 1:  # Settings
            # Toggle settings overlay
            self.show_settings = not self.show_settings
        elif self.selected_option == 2:  # Quit
            self.game_manager.quit_game()
    
    def update(self, dt):
        """Update menu logic."""
        pass
    
    def draw(self, screen):
        """Render the menu."""
        # Clear background
        screen.fill(self.background_color)
        
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Draw title
        title_surface = self.font_large.render(self.title_text, True, self.text_color)
        title_rect = title_surface.get_rect(center=(screen_width // 2, 150))
        screen.blit(title_surface, title_rect)
        
        # Draw subtitle
        subtitle_surface = self.font_medium.render(self.subtitle_text, True, self.text_color)
        subtitle_rect = subtitle_surface.get_rect(center=(screen_width // 2, 200))
        screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw menu options
        start_y = 350
        for i, option in enumerate(self.menu_options):
            color = self.highlight_color if i == self.selected_option else self.text_color
            text_surface = self.font_medium.render(option, True, color)
            text_rect = text_surface.get_rect(center=(screen_width // 2, start_y + i * 60))
            screen.blit(text_surface, text_rect)

        # Either draw the small instruction lines, or the settings overlay
        if self.show_settings:
            # draw settings window (frame + volume slider)
            try:
                # load frame if needed
                frame_orig = None
                frame_path = os.path.join('assets', 'UI', 'Complete_UI_Essential_Pack_Free', '01_Flat_Theme', 'Sprites', 'UI_Flat_FrameSlot01a.png')
                repo_root = Path(__file__).resolve().parents[1]
                full_frame = repo_root / frame_path
                if full_frame.exists():
                    frame_orig = pygame.image.load(str(full_frame)).convert_alpha()

                fw = 400
                fh = 200
                frame_surf = None
                if frame_orig:
                    try:
                        iw, ih = frame_orig.get_size()
                        s = max(1, fw // iw)
                        while iw * s < fw or ih * s < fh:
                            s += 1
                        frame_surf = pygame.transform.scale(frame_orig, (iw * s, ih * s))
                    except Exception:
                        frame_surf = None

                frame_x = (screen_width - (frame_surf.get_width() if frame_surf else fw)) // 2
                frame_y = (screen_height - (frame_surf.get_height() if frame_surf else fh)) // 2
                # try generated settings background first (pixel art)
                try:
                    bg_path = repo_root / 'assets' / 'UI' / 'settings_background.png'
                    if bg_path.exists():
                        bg_img = pygame.image.load(str(bg_path)).convert_alpha()
                        bw = frame_surf.get_width() if frame_surf else fw
                        bh = frame_surf.get_height() if frame_surf else fh
                        bg_s = pygame.transform.smoothscale(bg_img, (bw, bh))
                        screen.blit(bg_s, (frame_x, frame_y))
                    elif frame_surf:
                        screen.blit(frame_surf, (frame_x, frame_y))
                except Exception:
                    if frame_surf:
                        screen.blit(frame_surf, (frame_x, frame_y))

                # title
                title_surf = self.font_medium.render('Settings', True, self.text_color)
                title_rect = title_surf.get_rect(center=(screen_width // 2, frame_y + 34))
                screen.blit(title_surf, title_rect)

                # load UI sprites for slider if not cached
                sprites_dir = repo_root / 'assets' / 'UI' / 'Complete_UI_Essential_Pack_Free' / '01_Flat_Theme' / 'Sprites'
                if self._ui_bar is None:
                    bar_path = sprites_dir / 'UI_Flat_Bar01a.png'
                    fill_path = sprites_dir / 'UI_Flat_BarFill01a.png'
                    
                    # Try generated handle first, then fallback
                    gen_handle_path = repo_root / 'assets' / 'UI' / 'settings_handle.png'
                    handle_path = sprites_dir / 'UI_Flat_Handle01a.png'
                    
                    try:
                        if bar_path.exists():
                            self._ui_bar = pygame.image.load(str(bar_path)).convert_alpha()
                        if fill_path.exists():
                            self._ui_fill = pygame.image.load(str(fill_path)).convert_alpha()
                            
                        if gen_handle_path.exists():
                            self._ui_handle = pygame.image.load(str(gen_handle_path)).convert_alpha()
                        elif handle_path.exists():
                            self._ui_handle = pygame.image.load(str(handle_path)).convert_alpha()
                    except Exception:
                        self._ui_bar = self._ui_fill = self._ui_handle = None

                bar_w = 240
                bar_h = 24
                bar_x = (screen_width - bar_w) // 2
                bar_y = frame_y + 80

                # store slider rect for event handling
                try:
                    self._settings_bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                except Exception:
                    self._settings_bar_rect = None

                if self._ui_bar:
                    try:
                        bar_img = pygame.transform.smoothscale(self._ui_bar, (bar_w, bar_h))
                        screen.blit(bar_img, (bar_x, bar_y))
                    except Exception:
                        pygame.draw.rect(screen, (60,60,60), (bar_x, bar_y, bar_w, bar_h))
                else:
                    pygame.draw.rect(screen, (60,60,60), (bar_x, bar_y, bar_w, bar_h))

                fill_w = int(self.music_volume * bar_w)
                if self._ui_fill:
                    try:
                        fill_img = pygame.transform.smoothscale(self._ui_fill, (max(1, fill_w), bar_h))
                        screen.blit(fill_img, (bar_x, bar_y))
                    except Exception:
                        pygame.draw.rect(screen, (120,170,255), (bar_x, bar_y, fill_w, bar_h))
                else:
                    pygame.draw.rect(screen, (120,170,255), (bar_x, bar_y, fill_w, bar_h))

                handle_w = 20
                handle_h = 30
                handle_x = bar_x + fill_w - handle_w // 2
                handle_y = bar_y + (bar_h - handle_h) // 2
                if self._ui_handle:
                    try:
                        h_img = pygame.transform.smoothscale(self._ui_handle, (handle_w, handle_h))
                        screen.blit(h_img, (handle_x, handle_y))
                    except Exception:
                        pygame.draw.circle(screen, (200,200,200), (handle_x+handle_w//2, handle_y+handle_h//2), handle_w//2)
                else:
                    pygame.draw.circle(screen, (200,200,200), (handle_x+handle_w//2, handle_y+handle_h//2), handle_w//2)

                # volume label
                vol_surf = self.font_small.render(f"Music Volume: {int(self.music_volume*100)}%", True, self.text_color)
                vol_rect = vol_surf.get_rect(center=(screen_width // 2, bar_y - 26))
                screen.blit(vol_surf, vol_rect)
                # Developer Mode checkbox
                try:
                    chk_size = 18
                    chk_x = screen_width // 2 - 80
                    chk_y = bar_y + 40
                    self._dev_checkbox_rect = pygame.Rect(chk_x, chk_y, chk_size, chk_size)
                    pygame.draw.rect(screen, (200,200,200), self._dev_checkbox_rect, 2)
                    if getattr(self, 'developer_mode', False):
                        pygame.draw.rect(screen, (100,150,255), self._dev_checkbox_rect.inflate(-4, -4))
                    label_surf = self.font_small.render('Developer Mode', True, self.text_color)
                    label_rect = label_surf.get_rect(topleft=(chk_x + chk_size + 8, chk_y))
                    screen.blit(label_surf, label_rect)
                except Exception:
                    self._dev_checkbox_rect = None
            except Exception:
                pass
        else:
            # Draw instructions (include in-game pickup hint)
            instruction_text = "Use W/S or Arrow Keys to navigate, Space to select."
            instruction_surface = pygame.font.Font(None, 20).render(instruction_text, True, self.text_color)
            instruction_rect = instruction_surface.get_rect(center=(screen_width // 2, screen_height - 66))
            screen.blit(instruction_surface, instruction_rect)

            # control legend removed per UX change