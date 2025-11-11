"""
Menu Scene - Main menu implementation

This module contains the main menu scene with navigation options.
"""

import pygame
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
        self.menu_options = ["Start Game", "Instructions", "Quit"]
        self.selected_option = 0
        
        # Font (will use default for now)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        
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
    
    def select_option(self):
        """Handle menu option selection."""
        if self.selected_option == 0:  # Start Game
            self.game_manager.change_scene('gameplay')
        elif self.selected_option == 1:  # Instructions
            # TODO: Implement instructions scene
            print("Instructions not implemented yet")
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

        # Draw instructions (include in-game pickup hint)
        instruction_text = "Use W/S or Arrow Keys to navigate, Enter/Space to select."
        instruction_surface = pygame.font.Font(None, 20).render(instruction_text, True, self.text_color)
        instruction_rect = instruction_surface.get_rect(center=(screen_width // 2, screen_height - 66))
        screen.blit(instruction_surface, instruction_rect)

        # control legend (separate line)
        control_text = "C: collect items    (RMB: collect)"
        control_surface = pygame.font.Font(None, 18).render(control_text, True, self.text_color)
        control_rect = control_surface.get_rect(center=(screen_width // 2, screen_height - 40))
        screen.blit(control_surface, control_rect)