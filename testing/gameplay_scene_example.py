"""
Gameplay Scene (Example) - Integrated combat copy

This is a disposable example file created from the modified
`GameplayScene` that embeds the `BossBattleScene`. Use this
for testing or reference; the original `gameplay_scene.py` has
been restored to its placeholder implementation.
"""

import pygame
# Use absolute imports so this example file can be imported when run from
# the `testing/` directory or when loaded via importlib by the test runner.
from src.scenes.base_scene import BaseScene
from src.entities.player import Player
from src.entities.bullets import BulletManager
from src.entities.platform import Platform
# Note may live in testing/note.py (this repo has a testing copy). Try to
# import the src version first, fall back to the testing copy if not present.
try:
    from src.entities.note import Note
except Exception:
    import importlib.util, os
    note_path = os.path.join(os.path.dirname(__file__), 'note.py')
    spec = importlib.util.spec_from_file_location('testing_note', note_path)
    note_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(note_mod)
    Note = getattr(note_mod, 'Note')
import globals as g


class GameplayScene(BaseScene):
    """
    Example gameplay scene that starts directly in a player-only test mode.
    Contains a Player, simple platforms, a collectible Note ("note 01"),
    an inventory slot at the bottom center and an open-note overlay.
    """

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # Game colors
        self.background_color = (40, 20, 60)  # Dark purple for mind-scape
        self.ground_color = (80, 40, 120)

        # Player and combat components
        self.player = Player(100, g.SCREENHEIGHT - 150)
        self.bullet_manager = BulletManager()

        # Simple platforms
        self.platforms = [
            Platform(0, g.SCREENHEIGHT - 50, g.SCREENWIDTH, 50),
            Platform(100, g.SCREENHEIGHT - 200, 200, 20),
            Platform(g.SCREENWIDTH - 300, g.SCREENHEIGHT - 200, 200, 20),
        ]

        # Place a note on the ground platform near x=200
        ground = self.platforms[0]
        note_size = 18
        note_x = 200
        note_y = ground.rect.top - note_size
        self.note = Note(note_x, note_y, size=note_size, name='note 01', content='Hello world')
        self.note_prompt_shown = False

        # Inventory and UI state
        self.inventory = []
        self.opened_note = None
        self.hovered_name = ''
        # Rect for the close button of opened note overlay (set during draw)
        self.opened_note_close_rect = None

        # Head message shown above player when collecting
        self.head_message = ''
        self.head_message_timer = 0

        # Generic UI message
        self.message = ''
        self.message_timer = 0
        self.font = pygame.font.Font(None, 36)
    
    def enter(self):
        """Initialize gameplay when entering scene."""
        super().enter()
        self.message = "Welcome to Mind's Maze - Press ESC to return to menu"
        self.message_timer = 3.0  # Show message for 3 seconds
    
    def handle_event(self, event):
        """Handle gameplay input events."""
        # Global shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Exit to menu or quit if menu isn't needed
                try:
                    self.game_manager.quit_game()
                except Exception:
                    pass
            elif event.key == pygame.K_SPACE:
                # Basic feedback for now
                self.message = "Action triggered"
                self.message_timer = 1.0
            elif event.key == pygame.K_c:
                # Try to pick up a nearby note
                if self.note and not self.note.collected:
                    player_rect = pygame.Rect(int(self.player.x), int(self.player.y), self.player.width, self.player.height)
                    if player_rect.colliderect(self.note.get_rect()):
                        self.note.collect()
                        # add the collected note object to inventory
                        self.inventory.append(self.note)
                        self.opened_note = None
                        self.head_message = f"Picked up {self.note.name}"
                        self.head_message_timer = 2.0
            elif event.key == pygame.K_i:
                # Open last collected note (if any)
                if self.inventory:
                    self.opened_note = self.inventory[-1]

        # Mouse interactions: hover and click
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered_name = ''
            # Hover over note
            if self.note and not self.note.collected and self.note.get_rect().collidepoint(mx, my):
                self.hovered_name = self.note.name
            # Hover over inventory slot -> show last collected note name
            else:
                screen_w = g.SCREENWIDTH
                inv_w = 48
                inv_h = 48
                inv_x = screen_w//2 - inv_w//2
                inv_y = g.SCREENHEIGHT - inv_h - 10
                inv_rect = pygame.Rect(inv_x, inv_y, inv_w, inv_h)
                if inv_rect.collidepoint(mx, my) and self.inventory:
                    self.hovered_name = self.inventory[-1].name

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Click the note to open (does not auto-collect)
            if self.note and self.note.get_rect().collidepoint(mx, my):
                self.opened_note = self.note
            else:
                # Click inventory slot to open last collected note
                screen_w = g.SCREENWIDTH
                inv_w = 48
                inv_h = 48
                inv_x = screen_w//2 - inv_w//2
                inv_y = g.SCREENHEIGHT - inv_h - 10
                inv_rect = pygame.Rect(inv_x, inv_y, inv_w, inv_h)
                if inv_rect.collidepoint(mx, my) and self.inventory:
                    self.opened_note = self.inventory[-1]

            # If an overlay is open, check for its close button
            if self.opened_note and hasattr(self, 'opened_note_close_rect') and self.opened_note_close_rect:
                if self.opened_note_close_rect.collidepoint(mx, my):
                    # Close the overlay
                    self.opened_note = None

        # For completeness: forward events if specific handling is needed in the future
        # (BossBattleScene uses pygame.get_pressed and mouse state internally)
    
    def update(self, dt):
        """Update gameplay logic."""
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
        # Update player and bullets
        self.player.update(dt, self.platforms)
        # Bullet manager can be updated without a boss (pass None)
        try:
            self.bullet_manager.update(dt, self.player, None)
            self.bullet_manager.check_collisions(self.player, None)
        except Exception:
            # In case bullet manager expects a boss object, ignore for this example
            pass

        # Update head message timer
        if self.head_message_timer > 0:
            self.head_message_timer -= dt
            if self.head_message_timer <= 0:
                self.head_message = ''

        # Simple proximity prompt for note
        if self.note and not self.note.collected:
            player_rect = pygame.Rect(int(self.player.x), int(self.player.y), self.player.width, self.player.height)
            if player_rect.colliderect(self.note.get_rect()):
                self.note_prompt_shown = True
            else:
                self.note_prompt_shown = False
        else:
            # If note doesn't exist or is collected, hide prompt
            self.note_prompt_shown = False
    
    def draw(self, screen):
        """Render the gameplay scene."""
        # Simple player-focused rendering
        screen.fill(self.background_color)
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        # Draw platforms (includes ground platform)
        for p in self.platforms:
            p.draw(screen)

        # Draw note and player
        if self.note:
            self.note.draw(screen)

        self.player.draw(screen)

        # Draw bullets
        try:
            self.bullet_manager.draw(screen)
        except Exception:
            pass

        # Draw current message if any
        if self.message and self.message_timer > 0:
            text_surface = self.font.render(self.message, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(screen.get_width() // 2, 50))
            screen.blit(text_surface, text_rect)

        # Draw basic UI help
        ui_text = "ESC: Quit | C: Pick up note | I: Open last note"
        ui_surface = pygame.font.Font(None, 24).render(ui_text, True, (200, 200, 200))
        screen.blit(ui_surface, (10, 10))

        # Draw head message above player
        if self.head_message and self.head_message_timer > 0:
            head_surf = pygame.font.Font(None, 24).render(self.head_message, True, (255, 255, 255))
            head_rect = head_surf.get_rect(center=(int(self.player.x + self.player.width/2), int(self.player.y) - 16))
            screen.blit(head_surf, head_rect)

        # Draw inventory slot at bottom center
        inv_w = 48
        inv_h = 48
        inv_x = screen_width//2 - inv_w//2
        inv_y = screen_height - inv_h - 10
        inv_rect = pygame.Rect(inv_x, inv_y, inv_w, inv_h)
        pygame.draw.rect(screen, (30, 30, 30), inv_rect)
        pygame.draw.rect(screen, (180, 180, 180), inv_rect, 2)
        if self.inventory:
            # Draw a thumbnail for the last collected note
            thumb_rect = pygame.Rect(inv_x + 6, inv_y + 6, inv_w - 12, inv_h - 12)
            pygame.draw.rect(screen, (230, 200, 80), thumb_rect)

        # Draw note prompt
        if self.note_prompt_shown:
            prompt = "Press C to pick up"
            prompt_surf = pygame.font.Font(None, 20).render(prompt, True, (255, 255, 255))
            screen.blit(prompt_surf, (int(self.player.x), int(self.player.y) - 28))

        # Hover name display (near cursor)
        if self.hovered_name:
            mx, my = pygame.mouse.get_pos()
            hover_surf = pygame.font.Font(None, 20).render(self.hovered_name, True, (255, 255, 200))
            hover_rect = hover_surf.get_rect(topleft=(mx + 12, my + 12))
            # Small background for readability
            bg = pygame.Surface((hover_rect.width + 6, hover_rect.height + 6))
            bg.set_alpha(200)
            bg.fill((20, 20, 20))
            screen.blit(bg, (hover_rect.left - 3, hover_rect.top - 3))
            screen.blit(hover_surf, hover_rect)

        # Draw opened note overlay if any, and render a close button at bottom-left
        if self.opened_note:
            # Use same dimensions as Note.render_content defaults
            note_w = 360
            note_h = 240
            center_x = screen_width//2
            center_y = screen_height//2
            # Render the note content
            self.opened_note.render_content(screen, center_x, center_y, width=note_w, height=note_h)

            # Calculate the overlay box rect (same as in render_content)
            box_rect = pygame.Rect(center_x - note_w//2, center_y - note_h//2, note_w, note_h)

            # Close button at bottom-left inside the note box
            btn_w, btn_h = 80, 28
            btn_x = box_rect.left + 10
            btn_y = box_rect.bottom - btn_h - 10
            close_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            pygame.draw.rect(screen, (180, 50, 50), close_rect)
            pygame.draw.rect(screen, (0, 0, 0), close_rect, 2)
            btn_font = pygame.font.Font(None, 20)
            btn_text = btn_font.render('Close', True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=close_rect.center)
            screen.blit(btn_text, btn_text_rect)

            # Store rect for click handling
            self.opened_note_close_rect = close_rect
        else:
            self.opened_note_close_rect = None
