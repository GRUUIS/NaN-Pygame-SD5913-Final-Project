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
		# Try to load the map scene (map01). If it's not available fall back
		# to the older newmap scene. We also create an Inventory instance and
		# pass it into the scene so inventory features are available.
		try:
			from src.systems.inventory import Inventory
			inv = Inventory()
		except Exception:
			inv = None

		try:
			# prefer map01 scene when present
			from src.scenes.map01_scene import run as run_map01
			run_map01(screen, inventory=inv)
		except Exception:
			try:
				from src.scenes.newmap_scene import run as run_newmap
				run_newmap(screen)
			except Exception as e:
				print('Failed to import any map scene:', e)
				pygame.quit()
				return

	pygame.quit()


if __name__ == '__main__':
	main()

