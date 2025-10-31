"""Note entity - collectible note object

Simple square note that can be picked up by the player with the C key.
"""

import pygame
import globals as g


class Note:
    """A small collectible note placed on platforms."""
    def __init__(self, x: float, y: float, size: int = 18, name: str = "note 01", content: str = "Hello world"):
        self.x = x
        self.y = y
        self.size = size
        # Keep rect up to date
        self.rect = pygame.Rect(int(self.x), int(self.y), self.size, self.size)
        self.collected = False
        # Identification and content
        self.name = name
        self.content = content

    def collect(self):
        self.collected = True

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def draw(self, screen: pygame.Surface):
        """Draw the note as a small square if not collected."""
        if self.collected:
            return

        color = (230, 200, 80)  # paper-like yellow
        pygame.draw.rect(screen, color, self.rect)
        # subtle border
        pygame.draw.rect(screen, (120, 90, 30), self.rect, 2)

        if g.SHOW_COLLISION_BOXES:
            pygame.draw.rect(screen, (255, 0, 255), self.rect, 1)

    def render_content(self, screen: pygame.Surface, center_x: int, center_y: int, width: int = 360, height: int = 240):
        """Render an open note as a lined square with the note content centered near the top."""
        # background box
        box_rect = pygame.Rect(center_x - width//2, center_y - height//2, width, height)
        pygame.draw.rect(screen, (245, 245, 230), box_rect)  # off-white paper
        pygame.draw.rect(screen, (120, 90, 30), box_rect, 3)

        # draw horizontal lines
        line_color = (220, 220, 200)
        padding = 20
        line_y = box_rect.top + padding
        font = pygame.font.Font(None, 28)
        while line_y < box_rect.bottom - padding:
            pygame.draw.line(screen, line_color, (box_rect.left + padding, line_y), (box_rect.right - padding, line_y), 1)
            line_y += 28

        # draw content text (wrap simple single-line)
        text_surf = font.render(self.content, True, (40, 40, 40))
        screen.blit(text_surf, (box_rect.left + padding + 4, box_rect.top + padding + 4))

        # draw name/title at top center
        title_font = pygame.font.Font(None, 22)
        title_surf = title_font.render(self.name, True, (80, 80, 80))
        title_rect = title_surf.get_rect(center=(center_x, box_rect.top + 12))
        screen.blit(title_surf, title_rect)
