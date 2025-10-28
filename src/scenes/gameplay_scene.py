"""
Gameplay Scene - Main game implementation

This module contains the core gameplay scene where boss battles occur.
"""

import pygame
from .base_scene import BaseScene

class GameplayScene(BaseScene):
    """
    Main gameplay scene with player and boss interactions.
    """
    
    def __init__(self, game_manager):
        super().__init__(game_manager)
        
        # Game colors
        self.background_color = (40, 20, 60)  # Dark purple for mind-scape
        self.ground_color = (80, 40, 120)
        
        # Placeholder for game entities (will be implemented by team members)
        self.player = None
        self.current_boss = None
        self.game_state = "exploring"  # exploring, combat, victory, defeat
        
        # Simple message system
        self.message = ""
        self.message_timer = 0
        self.font = pygame.font.Font(None, 36)
    
    def enter(self):
        """Initialize gameplay when entering scene."""
        super().enter()
        self.message = "Welcome to Mind's Maze - Press ESC to return to menu"
        self.message_timer = 3.0  # Show message for 3 seconds
    
    def handle_event(self, event):
        """Handle gameplay input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_manager.change_scene('menu')
            elif event.key == pygame.K_SPACE:
                self.message = "Combat system not yet implemented"
                self.message_timer = 2.0
    
    def update(self, dt):
        """Update gameplay logic."""
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
        
        # TODO: Update player, bosses, and game logic
        # This will be implemented by the combat systems developer
    
    def draw(self, screen):
        """Render the gameplay scene."""
        # Clear background with mind-scape color
        screen.fill(self.background_color)
        
        # Draw simple ground
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        ground_rect = pygame.Rect(0, screen_height - 100, screen_width, 100)
        pygame.draw.rect(screen, self.ground_color, ground_rect)
        
        # Draw placeholder player (red square)
        player_rect = pygame.Rect(100, screen_height - 150, 50, 50)
        pygame.draw.rect(screen, (255, 100, 100), player_rect)
        
        # Draw current message if any
        if self.message and self.message_timer > 0:
            text_surface = self.font.render(self.message, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(screen_width // 2, 50))
            screen.blit(text_surface, text_rect)
        
        # Draw basic UI
        ui_text = "ESC: Menu | SPACE: Action (Not implemented)"
        ui_surface = pygame.font.Font(None, 24).render(ui_text, True, (200, 200, 200))
        screen.blit(ui_surface, (10, 10))