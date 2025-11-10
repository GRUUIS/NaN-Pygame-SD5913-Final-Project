"""Scale-aware player used in map scenes.

This player uses simple rectangle physics: horizontal movement, gravity,
and separate-axis collision resolution against a list of platform rects.
It's intentionally small and dependency-light so it can be used in the
map viewer and tested easily.
"""

import pygame


class MapPlayer:
	SPEED = 120
	JUMP_V = -320
	GRAVITY = 900

	def __init__(self, x=0, y=0, scale=1):
		self.scale = int(scale) if scale else 1
		self.w = 12 * self.scale
		self.h = 20 * self.scale
		self.x = float(x)
		self.y = float(y)
		self.vx = 0.0
		self.vy = 0.0
		self.on_ground = False

	@property
	def rect(self):
		return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

	def handle_input(self, keys):
		self.vx = 0.0
		if keys[pygame.K_LEFT] or keys[pygame.K_a]:
			self.vx = -self.SPEED
		if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
			self.vx = self.SPEED
		if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
			self.vy = self.JUMP_V
			self.on_ground = False

	def update(self, dt, platforms=None):
		# dt in seconds
		keys = pygame.key.get_pressed()
		self.handle_input(keys)

		# apply gravity
		self.vy += self.GRAVITY * dt

		# horizontal move and resolve
		self.x += self.vx * dt
		if platforms:
			r = self.rect
			for p in platforms:
				if r.colliderect(p):
					if self.vx > 0:
						self.x = p.left - self.w
					elif self.vx < 0:
						self.x = p.right
					self.vx = 0
					r = self.rect

		# vertical move and resolve
		self.y += self.vy * dt
		self.on_ground = False
		if platforms:
			r = self.rect
			for p in platforms:
				if r.colliderect(p):
					if self.vy > 0:
						self.y = p.top - self.h
						self.vy = 0
						self.on_ground = True
					elif self.vy < 0:
						self.y = p.bottom
						self.vy = 0
					r = self.rect

	def draw(self, surface):
		pygame.draw.rect(surface, (200, 80, 80), self.rect)
