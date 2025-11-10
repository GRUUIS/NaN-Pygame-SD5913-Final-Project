"""Inventory system used by the map scene.

This provides a small in-game inventory with simple slot storage and a
toggleable UI. The drawing is intentionally lightweight but communicates
the state so it can be replaced by a richer UI later.
"""

import pygame


class Inventory:
	def __init__(self, max_slots=8):
		self.max_slots = max_slots
		self.items = []
		self.visible = False

	def add_item(self, item):
		"""Add an item (any Python object). Returns True on success."""
		if len(self.items) >= self.max_slots:
			return False
		self.items.append(item)
		return True

	def toggle(self):
		self.visible = not self.visible

	def handle_event(self, event):
		# toggle with TAB
		if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
			self.toggle()

	def draw(self, surface):
		"""Draw a very small inventory panel in the center of the surface.

		This is intentionally minimal: shows slot boxes and item count.
		"""
		if surface is None:
			return
		if not self.visible:
			return

		w, h = surface.get_size()
		panel_w = min(400, w - 40)
		panel_h = 100
		panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
		panel.fill((0, 0, 0, 180))
		# draw slots
		slot_w = 40
		padding = 10
		x = padding
		y = (panel_h - slot_w) // 2
		for i in range(self.max_slots):
			r = pygame.Rect(x, y, slot_w, slot_w)
			pygame.draw.rect(panel, (180, 180, 180), r, 2)
			if i < len(self.items):
				# draw a small filled square to indicate an item
				inner = r.inflate(-8, -8)
				pygame.draw.rect(panel, (200, 160, 60), inner)
			x += slot_w + 6

		surface.blit(panel, ((w - panel_w) // 2, (h - panel_h) // 2))
