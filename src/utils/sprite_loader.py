import pygame
import os
from typing import List

class SpriteSheet:
    """
    Utility class to load and slice sprite sheets.
    Supports automatic slicing using mask detection (connected components).
    """
    def __init__(self, filename: str):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except FileNotFoundError:
            print(f"ERROR: Sprite sheet not found: {filename}")
            # Create a placeholder surface (magenta)
            self.sheet = pygame.Surface((64, 64))
            self.sheet.fill((255, 0, 255))

    def get_image(self, x: int, y: int, width: int, height: int) -> pygame.Surface:
        """Extracts a single image from the sheet."""
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        return image

    def auto_slice(self) -> List[pygame.Surface]:
        """
        Automatically detects sprites in the sheet using pygame.mask.
        Returns a list of surfaces, sorted left-to-right.
        """
        mask = pygame.mask.from_surface(self.sheet)
        # get_bounding_rects returns a list of Rects for connected components
        rects = mask.get_bounding_rects()
        
        # Sort rects: top-to-bottom, then left-to-right
        rects.sort(key=lambda r: (r.y, r.x))
        
        sprites = []
        for rect in rects:
            # Filter out tiny noise if necessary
            if rect.width > 1 and rect.height > 1:
                sprites.append(self.get_image(rect.x, rect.y, rect.width, rect.height))
        
        return sprites

def load_animation_strip(path: str) -> List[pygame.Surface]:
    """
    Loads an image file and auto-slices it into frames.
    """
    if not os.path.exists(path):
        print(f"Warning: Animation file not found: {path}")
        return []
        
    sheet = SpriteSheet(path)
    return sheet.auto_slice()
