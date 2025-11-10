import os
import sys
import pygame

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
		# Placeholder game loop after selecting Start
		clock = pygame.time.Clock()
		font = pygame.font.Font(None, 36)
		running = True
		while running:
			dt = clock.tick(g.FPS) / 1000.0
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					running = False

			screen.fill((30, 30, 30))
			text = font.render('Game started (placeholder). Press ESC to quit.', True, (255, 255, 255))
			screen.blit(text, (50, 50))
			pygame.display.flip()

	pygame.quit()


if __name__ == '__main__':
	main()

