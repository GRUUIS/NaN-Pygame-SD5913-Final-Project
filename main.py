"""
Mind's Maze - Main Entry Point

A 2D psychological puzzle-platformer game built with Pygame.
This is the main entry point for the game.

Author: Team NaN
Course: Creative Programming SD5913
"""

import pygame
import sys
import os
from src.scenes.game_manager import GameManager
from globals import *

def main():
    """
    Main game entry point.
    Initializes Pygame and starts the game manager.
    """
    try:
        # Initialize Pygame
        pygame.init()
        
        # Set up the game window
        screen = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
        pygame.display.set_caption("Mind's Maze - Psychological Platformer")
        
        # Set up game icon (placeholder for now)
        # pygame.display.set_icon(pygame.image.load("assets/images/ui/icon.png"))
        
        # Initialize game manager
        game_manager = GameManager(screen)
        
        # Start the game
        game_manager.run()
        
    except Exception as e:
        print(f"Error starting game: {e}")
        sys.exit(1)
    
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()