"""Small speech-bubble UI anchored to a target rect.

This module provides a compact `SpeechBubble` class which can be given an
`anchor_getter` callable returning a `pygame.Rect` in screen coordinates.
The bubble will position itself relative to the returned rect and draw a
short text string. It's intentionally small and dependency-light for use
in the map viewer.

API:
	SpeechBubble(anchor_getter, size=(w,h), draw_background=False)
	.set_text(text)
	.open()/close()/toggle()
	.draw(surface)
"""

from __future__ import annotations

import os
import pygame
from typing import Callable, Optional, Tuple


class SpeechBubble:
	def __init__(self, anchor_getter: Callable[[], Optional[pygame.Rect]], size: Tuple[int, int] = (160, 40), draw_background: bool = False, padding: int = 6, face_offset: float = 0.35, y_overlap: int = -6, font_scale: float = 0.65):
		"""Create a SpeechBubble.

		Args:
			anchor_getter: callable returning either a `pygame.Rect` or a
				`(rect, facing)` tuple where `facing` is 'left' or 'right'.
			size: (w,h) pixel size for the bubble box.
			draw_background: whether to draw a translucent backdrop.
			padding: text padding inside the box.
			face_offset: fraction of target width to offset the bubble toward
				the facing direction (positive floats). Smaller => closer to center.
			y_overlap: extra vertical offset (px) to move bubble closer to/overlap head.
			font_scale: relative font size (fraction of box height).
		"""
		self._anchor = anchor_getter
		self.w, self.h = int(size[0]), int(size[1])
		self.padding = int(padding)
		self.visible = False
		self.text = ""
		self.draw_background = bool(draw_background)
		self.face_offset = float(face_offset)
		self.y_overlap = int(y_overlap)
		self.font_scale = float(font_scale)

		# Try to pick a readable font from assets first; increase size for readability
		try:
			root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
			path = os.path.join(root, 'assets', 'Silver.ttf')
			fsize = max(12, int(self.h * self.font_scale))
			if os.path.exists(path):
				self.font = pygame.font.Font(path, fsize)
			else:
				self.font = pygame.font.SysFont(None, fsize)
		except Exception:
			self.font = pygame.font.SysFont(None, max(12, int(self.h * self.font_scale)))

		# internal position state
		self.x = 0
		self.y = 0

	def set_text(self, text: str):
		self.text = str(text)

	def open(self):
		self.visible = True

	def close(self):
		self.visible = False

	def toggle(self):
		self.visible = not self.visible

	def draw(self, surface: pygame.Surface):
		if not self.visible:
			return
		try:
			targ = self._anchor() if self._anchor else None
			if targ is None:
				return
			# anchor_getter may return either a Rect or (Rect, facing)
			facing = None
			if isinstance(targ, (tuple, list)) and len(targ) >= 1:
				rect = targ[0]
				if len(targ) >= 2:
					facing = targ[1]
			else:
				rect = targ

			# Base x: center horizontally on target
			base_x = int(rect.centerx - (self.w // 2))
			# If facing is provided, offset bubble toward that side so it follows
			# the visible head direction. Positive face_offset moves bubble to the right
			# when facing 'right' and left when facing 'left'. Use target width to
			# compute a pixel offset.
			x_offset = 0
			try:
				if facing in ('left', 'right'):
					dir_sign = 1 if facing == 'right' else -1
					x_offset = int(dir_sign * max(0, rect.width * self.face_offset))
			except Exception:
				x_offset = 0
			self.x = base_x + x_offset

			# Place bubble slightly above the visual rect top (closer to head)
			self.y = int(rect.top - (self.h // 2) + self.y_overlap)

			# clamp to surface bounds
			sw, sh = surface.get_size()
			self.x = max(0, min(self.x, max(0, sw - self.w)))
			self.y = max(0, min(self.y, max(0, sh - self.h)))
		except Exception:
			return

		# Background (optional)
		if self.draw_background:
			try:
				s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
				s.fill((0, 0, 0, 180))
				pygame.draw.rect(s, (255, 255, 255), s.get_rect(), 1, border_radius=6)
				surface.blit(s, (self.x, self.y))
			except Exception:
				pygame.draw.rect(surface, (0, 0, 0), (self.x, self.y, self.w, self.h))

		# Render text centered
		if not self.text:
			return
		try:
			txt_s = self.font.render(self.text, True, (0, 0, 0))
		except Exception:
			txt_s = self.font.render(self.text, True, (255, 255, 255))
		tx = self.x + max(0, (self.w - txt_s.get_width()) // 2)
		ty = self.y + max(0, (self.h - txt_s.get_height()) // 2)
		surface.blit(txt_s, (tx, ty))
