"""
Platform Entity - 2D Collision Platforms

Simple platform objects for collision detection in the game world.
Uses configuration from globals.py.
"""

import pygame
import globals as g


class Platform:
    """Simple platform for collision"""
    def __init__(self, x: float, y: float, width: float, height: float):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_ground = height > 20  # Distinguish between platforms and ground
    
    def draw(self, screen: pygame.Surface):
        """Draw the platform"""
        color = g.COLORS['ground'] if self.is_ground else g.COLORS['platform']
        pygame.draw.rect(screen, color, self.rect)
        
        if g.SHOW_COLLISION_BOXES:
            pygame.draw.rect(screen, (0, 255, 0), self.rect, 1)