"""Inventory system used by the map scene.

This provides a small in-game inventory with simple slot storage and a
toggleable UI. The drawing is intentionally lightweight but communicates
the state so it can be replaced by a richer UI later.
"""

import pygame
import os


class Inventory:
	def __init__(self, max_slots=8):
		self.max_slots = max_slots
		self.items = []
		self.visible = False

		# cache for item icons keyed by item id to avoid reloading every frame
		self._icon_cache = {}


	def add_item(self, item):
		"""Add an item (any Python object). Returns True on success."""
		if len(self.items) >= self.max_slots:
			return False
		# If the item is a dict with an 'id', attempt to load an icon once.
		try:
			item_id = None
			if isinstance(item, dict):
				item_id = item.get('id')
			elif hasattr(item, 'id'):
				item_id = getattr(item, 'id')
			if item_id and item_id not in self._icon_cache:
				# try to find an asset matching the id (e.g. 'hourglass.png')
				candidates = [
					os.path.join('assets', f"{item_id}.png"),
					os.path.join('assets', 'sprites', 'items', f"{item_id}.png"),
					os.path.join('assets', 'sprites', f"{item_id}.png"),
				]
				from os import path
				found = None
				for p in candidates:
					if path.exists(p):
						found = p
						break
				if not found and path.exists('assets'):
					for root, dirs, files in os.walk('assets'):
						for fn in files:
							if fn.lower() == f"{item_id}.png":
								found = os.path.join(root, fn)
								break
						if found:
							break
				if found:
					try:
						surf = pygame.image.load(found).convert_alpha()
						self._icon_cache[item_id] = surf
					except Exception:
						# swallow load errors and leave cache empty for this id
						self._icon_cache[item_id] = None
		except Exception:
			# fail silently; item still added
			pass
		self.items.append(item)
		return True

	def has_item(self, item_id: str) -> bool:
		"""Return True if any item in inventory matches the given id."""
		for it in self.items:
			try:
				if isinstance(it, dict) and it.get('id') == item_id:
					return True
				if hasattr(it, 'id') and getattr(it, 'id') == item_id:
					return True
			except Exception:
				continue
		return False

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
				item = self.items[i]
				inner = r.inflate(-8, -8)
				# try to draw a cached icon if present
				item_id = None
				if isinstance(item, dict):
					item_id = item.get('id')
				elif hasattr(item, 'id'):
					item_id = getattr(item, 'id')
				icon = None
				if item_id:
					icon = self._icon_cache.get(item_id)
				if icon:
					# scale icon to inner rect while preserving integer scaling for pixel art
					iw, ih = icon.get_size()
					scale_x = max(1, inner.width // iw)
					scale_y = max(1, inner.height // ih)
					scale_use = min(scale_x, scale_y)
					new_w = iw * scale_use
					new_h = ih * scale_use
					try:
						icon_scaled = pygame.transform.scale(icon, (new_w, new_h))
					except Exception:
						icon_scaled = icon
					off_x = inner.left - x + (inner.width - new_w) // 2
					off_y = inner.top - y + (inner.height - new_h) // 2
					panel.blit(icon_scaled, (off_x, off_y))
				else:
					pygame.draw.rect(panel, (200, 160, 60), inner)
		x += slot_w + 6

		# blit panel
		panel_x = (w - panel_w) // 2
		panel_y = (h - panel_h) // 2
		surface.blit(panel, (panel_x, panel_y))

		# show hover tooltip if mouse over a slot
		mx, my = pygame.mouse.get_pos()
		rel_x = mx - panel_x
		rel_y = my - panel_y
		if 0 <= rel_x < panel_w and 0 <= rel_y < panel_h:
			# compute which slot index mouse is over
			slot_index = (rel_x - padding) // (slot_w + 6)
			if 0 <= slot_index < self.max_slots and (rel_x >= padding + slot_index * (slot_w + 6)) and (rel_x < padding + slot_index * (slot_w + 6) + slot_w):
				if slot_index < len(self.items):
					item = self.items[slot_index]
					name = ''
					if isinstance(item, dict):
						name = item.get('name', item.get('id', ''))
					elif hasattr(item, 'name'):
						name = getattr(item, 'name')
					if name:
						font = pygame.font.Font(None, 18)
						surf = font.render(name, True, (255, 255, 220))
						bg = pygame.Surface((surf.get_width()+6, surf.get_height()+6))
						bg.fill((10,10,10))
						surface.blit(bg, (mx+12, my+12))
						surface.blit(surf, (mx+15, my+15))
