"""
Game Manager - Core game state management

This module handles the main game loop, scene transitions,
and overall game state management.
"""

import pygame
import sys
from ..utils.state_machine import StateMachine
from .menu_scene import MenuScene
from .gameplay_scene import GameplayScene
from .game_over_scene import GameOverScene
from globals import *

class GameManager:
    """
    Central game manager that handles scenes and main game loop.
    """
    
    def __init__(self, screen):
        """
        Initialize the game manager.
        
        Args:
            screen: Pygame display surface
        """
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize state machine for scene management
        self.state_machine = StateMachine()
        
        # Create scenes
        self.scenes = {
            'menu': MenuScene(self),
            'gameplay': GameplayScene(self),
            'game_over': GameOverScene(self)
        }
        
        # Set initial scene
        self.current_scene = 'menu'
        self.state_machine.change_state(self.scenes[self.current_scene])
    
    def run(self):
        """
        Main game loop.
        """
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.draw()
    
    def handle_events(self):
        """
        Handle global events and pass them to current scene.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            else:
                # Pass event to current scene
                if self.state_machine.current_state:
                    self.state_machine.current_state.handle_event(event)
    
    def update(self, dt):
        """
        Update the current scene.
        
        Args:
            dt: Delta time in seconds
        """
        if self.state_machine.current_state:
            self.state_machine.current_state.update(dt)
    
    def draw(self):
        """
        Render the current scene.
        """
        self.screen.fill((0, 0, 0))  # Clear screen
        
        if self.state_machine.current_state:
            self.state_machine.current_state.draw(self.screen)
        
        pygame.display.flip()
    
    def change_scene(self, scene_name):
        """
        Change to a different scene.
        
        Args:
            scene_name: Name of the scene to switch to
        """
        if scene_name in self.scenes:
            self.current_scene = scene_name
            self.state_machine.change_state(self.scenes[scene_name])
        else:
            print(f"Warning: Scene '{scene_name}' not found")
    
    def quit_game(self):
        """
        Safely quit the game.
        """
        self.running = False