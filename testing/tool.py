"""Tool entity - small circular collectible tool object (testing copy)

Tools are separate from notes and live next to notes in the level.
They can be picked up into inventory and later held by the player.
"""

import pygame


class Tool:
    def __init__(self, x: float, y: float, radius: int = 8, name: str = 'tool 01'):
        self.x = x
        self.y = y
        self.radius = radius
        self.name = name
        self.collected = False
        # rect used for collision/hover checks
        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def draw(self, screen: pygame.Surface):
        if self.collected:
            return
        circle_color = (100, 200, 220)
        pygame.draw.circle(screen, circle_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (30, 30, 30), (int(self.x), int(self.y)), self.radius, 2)

    def pick_up(self):
        self.collected = True
