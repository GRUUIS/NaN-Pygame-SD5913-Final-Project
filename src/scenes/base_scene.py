"""
Base Scene Class

This module provides a base class for all game scenes.
All scenes should inherit from this class.
"""

import pygame

class BaseScene:
    """
    Base class for all game scenes.
    """
    
    def __init__(self, game_manager):
        """
        Initialize the base scene.
        
        Args:
            game_manager: Reference to the main game manager
        """
        self.game_manager = game_manager
        self.active = False
    
    def enter(self):
        """
        Called when entering this scene.
        Override in child classes for scene-specific initialization.
        """
        self.active = True
        print(f"Entering scene: {self.__class__.__name__}")
    
    def exit(self):
        """
        Called when exiting this scene.
        Override in child classes for scene-specific cleanup.
        """
        self.active = False
        print(f"Exiting scene: {self.__class__.__name__}")
    
    def handle_event(self, event):
        """
        Handle input events.
        Override in child classes for scene-specific event handling.
        
        Args:
            event: Pygame event object
        """
        pass
    
    def update(self, dt):
        """
        Update scene logic.
        Override in child classes for scene-specific updates.
        
        Args:
            dt: Delta time in seconds
        """
        pass
    
    def draw(self, screen):
        """
        Render the scene.
        Override in child classes for scene-specific rendering.
        
        Args:
            screen: Pygame display surface
        """
        pass