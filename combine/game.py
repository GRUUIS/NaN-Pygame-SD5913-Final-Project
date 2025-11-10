import os
import sys
import pygame
import pymunk

# Ensure repository root is on sys.path so imports like `import globals` work
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
		# Delegate the exploration map scene to the new scene module so this
		# launcher stays small. The scene will run until the player exits it.
		try:
			from src.scenes.newmap_scene import run as run_newmap
		except Exception as e:
			print('Failed to import newmap scene:', e)
			pygame.quit()
			return

		run_newmap(screen)

	pygame.quit()


if __name__ == '__main__':
	main()

