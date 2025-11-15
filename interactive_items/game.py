# Copied from combine/game.py
import os
import sys
import pygame
import pymunk

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import globals as g
from combine.meun import Meun

def main():
    pygame.init()
    screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
    pygame.display.set_caption('Combine - Menu Demo')

    meun = Meun(screen)
    choice = meun.run()

    if choice == 'start':
        try:
            from src.systems.inventory import Inventory
            inv = Inventory()
        except Exception:
            inv = None

        try:
            from src.scenes.map01_scene import run as run_map01
            run_map01(screen, inventory=inv)
        except Exception as e:
            print('Failed to import or run map01 scene:', e)
            pygame.quit()
            return

    pygame.quit()

if __name__ == '__main__':
    main()
