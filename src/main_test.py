import pygame
import sys
from globals import *

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
        pygame.display.set_caption("Mind's Maze - Test Build")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Basic colors for testing
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)

    def run(self):
        while self.running:
            self.update()
            self.draw()
        self.close()

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        
        self.clock.tick(FPS)

    def draw(self):
        # Clear screen with black background
        self.screen.fill(self.BLACK)
        
        # Draw a simple test rectangle
        pygame.draw.rect(self.screen, self.RED, (100, 100, 50, 50))
        
        # Update display
        pygame.display.flip()

    def close(self):
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()