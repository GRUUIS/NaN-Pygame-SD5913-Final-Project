"""
Run this file to start a minimal demo of the Third Puzzle (projection) scene.

Usage:
    python testing/third_puzzle_demo.py

Controls:
    WASD: move
    Mouse left click: pick up item / interact with tool
    Move mouse while projecting to aim
    ESC: quit

This demo uses placeholder assets generated earlier; it is intended for
development and integration testing.
"""
import pygame
import sys
import os
# ensure repository root is on sys.path so imports like `import globals` and `src.*` work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import globals as g
from src.scenes.third_puzzle_scene import ThirdPuzzleScene


def main():
    pygame.init()
    screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
    pygame.display.set_caption('Third Puzzle Demo')
    clock = pygame.time.Clock()

    scene = ThirdPuzzleScene(screen)

    running = True
    while running:
        dt = clock.tick(g.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                scene.handle_event(event)

        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
