"""
Game Over Scene - End game screen

This module contains the game over scene shown after victory or defeat.
"""

import pygame
from .base_scene import BaseScene

class GameOverScene(BaseScene):
    """
    Game over scene with restart and menu options.
    """
    
    def __init__(self, game_manager):
        super().__init__(game_manager)
        
        # Colors
        self.background_color = (20, 20, 20)
        self.text_color = (255, 255, 255)
        self.highlight_color = (255, 100, 100)
        
        # Game over state
        self.victory = False
        self.message = "Game Over"
        
        # Menu options
        self.menu_options = ["Play Again", "Main Menu"]
        self.selected_option = 0
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
    
    def set_game_over_state(self, victory=False, message="Game Over"):
        """
        Set the game over state.
        
        Args:
            victory: Whether the player won or lost
            message: Custom message to display
        """
        self.victory = victory
        self.message = message
    
    def handle_event(self, event):
        """Handle game over input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.select_option()
    
    def select_option(self):
        """Handle menu option selection."""
        if self.selected_option == 0:  # Play Again
            self.game_manager.change_scene('gameplay')
        elif self.selected_option == 1:  # Main Menu
            self.game_manager.change_scene('menu')
    
    def update(self, dt):
        """Update game over logic."""
        pass
    
    def draw(self, screen):
        """Render the game over screen."""
        # Clear background
        screen.fill(self.background_color)
        
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Draw main message
        message_color = (100, 255, 100) if self.victory else (255, 100, 100)
        message_surface = self.font_large.render(self.message, True, message_color)
        message_rect = message_surface.get_rect(center=(screen_width // 2, 200))
        screen.blit(message_surface, message_rect)
        
        # Draw flavor text based on outcome
        flavor_text = "The mind finds peace..." if self.victory else "The shadows remain..."
        flavor_surface = self.font_medium.render(flavor_text, True, self.text_color)
        flavor_rect = flavor_surface.get_rect(center=(screen_width // 2, 280))
        screen.blit(flavor_surface, flavor_rect)
        
        # Draw menu options
        start_y = 400
        for i, option in enumerate(self.menu_options):
            color = self.highlight_color if i == self.selected_option else self.text_color
            text_surface = self.font_medium.render(option, True, color)
            text_rect = text_surface.get_rect(center=(screen_width // 2, start_y + i * 60))
            screen.blit(text_surface, text_rect)
        
        # Draw instructions
        instruction_text = "Use W/S to navigate, Enter/Space to select"
        instruction_surface = pygame.font.Font(None, 24).render(instruction_text, True, self.text_color)
        instruction_rect = instruction_surface.get_rect(center=(screen_width // 2, screen_height - 50))
        screen.blit(instruction_surface, instruction_rect)