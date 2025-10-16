import pygame
import sys
from globals import *
class Game:
    def _init_ (self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREENWIDTH,SCREENHEIGHT))
        self.clock = pygame.time.Clock()


        self.running = True
    def run(self):
        while self.running:
            self.update()
            self.draw()
        self.close()
    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        pygame.display.update()
        self.clock.tick(FPS)
    def draw(self):
        pass
    def close(self):
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    gane = Game()
    game.run()