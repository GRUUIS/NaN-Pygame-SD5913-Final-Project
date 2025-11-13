"""Scale-aware player used in map scenes.

This player uses simple rectangle physics: horizontal movement, gravity,
and separate-axis collision resolution against a list of platform rects.
It's intentionally small and dependency-light so it can be used in the
map viewer and tested easily.
"""

import os
import pygame


class MapPlayer:
	SPEED = 120
	JUMP_V = -320
	GRAVITY = 900

	def __init__(self, x=0, y=0, scale=1, tile_w=16, tile_h=16, jump_tiles=None):
		"""Create a player sized to 1 tile wide and 2 tiles tall by default.

		tile_w/tile_h are in pixels (map native tile size). scale is applied on
		top of tile units (from the map scene).
		"""
		self.scale = int(scale) if scale else 1
		self.tile_w = int(tile_w)
		self.tile_h = int(tile_h)
		# visual_scale: extra multiplier to make the character larger visually
		# set to >1.0 to increase character size (also scales collision here)
		self.visual_scale = 4.0
		# collision size: player is one tile wide, two tiles high (scaled by map scale)
		# keep collision size independent of visual_scale so a large sprite doesn't
		# make the physics box huge and cause immediate blocking near spawn.
		self.collision_scale = 1.0
		self.cw = int(self.tile_w * self.scale * self.collision_scale)
		self.ch = int(self.tile_h * 2 * self.scale * self.collision_scale)

		# visual (sprite) size: can be larger than collision box for aesthetic
		self.w_vis = int(self.tile_w * self.scale * self.visual_scale)
		self.h_vis = int(self.tile_h * 2 * self.scale * self.visual_scale)

		self.x = float(x)
		self.y = float(y)
		self.vx = 0.0
		self.vy = 0.0
		self.on_ground = False
		# default facing so draw/animation selection works before sprite loads
		self.facing = 'right'

		# movement values scaled to runtime scale so movement feels consistent
		# Movement values should be based on collision scale so physics remain
		# consistent even when the sprite is visually larger.
		self.speed = float(self.SPEED) * float(self.scale) * float(self.collision_scale)
		self.gravity_v = float(self.GRAVITY) * float(self.scale) * float(self.collision_scale)
		# compute jump velocity from desired jump height in tiles so jump height scales
		# allow callers to override jump height; default to a taller jump (7 tiles)
		desired_jump_tiles = float(jump_tiles) if jump_tiles is not None else 10.0
		jump_height_px = desired_jump_tiles * self.tile_h * float(self.scale) * float(self.collision_scale)
		# v = -sqrt(2 * g * h)
		import math
		self.jump_v = -math.sqrt(2.0 * self.gravity_v * max(1.0, jump_height_px))

		# sprite surface lazy-loaded in draw
		self._sprite = None
		# mark whether we've attempted to load sprite/animations
		self._loaded = False

	@property
	def rect(self):
		return pygame.Rect(int(self.x), int(self.y), int(self.cw), int(self.ch))

	def handle_input(self, keys):
		self.vx = 0.0
		if keys[pygame.K_LEFT] or keys[pygame.K_a]:
			self.vx = -self.speed
		if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
			self.vx = self.speed
		# update facing immediately based on input so the character faces movement
		if self.vx < 0:
			self.facing = 'left'
		elif self.vx > 0:
			self.facing = 'right'
		if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
			self.vy = self.jump_v
			self.on_ground = False

	def update(self, dt, platforms=None):
		# dt in seconds
		keys = pygame.key.get_pressed()
		self.handle_input(keys)

		# apply gravity (scaled)
		self.vy += self.gravity_v * dt

		# horizontal move and resolve
		self.x += self.vx * dt
		if platforms:
			r = self.rect
			for p in platforms:
				if r.colliderect(p):
					if self.vx > 0:
						self.x = p.left - self.cw
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
						self.y = p.top - self.ch
						self.vy = 0
						self.on_ground = True
					elif self.vy < 0:
						self.y = p.bottom
						self.vy = 0
					r = self.rect

	# ---- animation state update ----
		# determine desired animation based on horizontal speed
		try:
			spd = abs(self.vx)
		except Exception:
			spd = 0
		# threshold scaled to speed so we avoid jitter around 0
		threshold = max(1.0, self.speed * 0.05)
		base = 'run' if spd > threshold else 'idle'
		# update facing only when movement is significant to avoid jitter
		if self.vx < - (self.speed * 0.02):
			self.facing = 'left'
		elif self.vx > (self.speed * 0.02):
			self.facing = 'right'

		# choose animation key: prefer direction-specific then generic
		chosen = None
		if hasattr(self, 'animations') and self.animations:
			pref = f"{base}_{self.facing}"
			if pref in self.animations:
				chosen = pref
			elif base in self.animations:
				chosen = base
			else:
				chosen = next(iter(self.animations.keys())) if self.animations else None

		if chosen:
			# If switching between direction variants of the same base animation
			# (e.g. 'run_right' <-> 'run_left'), preserve the anim_frame and
			# anim_time so the flip doesn't look like a teleport. Only reset
			# when the base animation actually changed.
			prev = getattr(self, 'cur_anim', None)
			if prev != chosen:
				prev_base = prev.split('_')[0] if prev else None
				new_base = chosen.split('_')[0]
				if prev_base == new_base:
					# same base (directional change) -> keep frame/time
					self.cur_anim = chosen
				else:
					print(f"[player_map] anim change: {prev} -> {chosen}")
					self.cur_anim = chosen
					self.anim_frame = 0
					self.anim_time = 0.0

			# advance animation frame timer (durations expected in ms)
			self.anim_time += dt * 1000.0
			dur_list = self.animations.get(self.cur_anim, {}).get('durations', None)
			frames = self.animations.get(self.cur_anim, {}).get('frames', [])
			if frames:
				cur_dur = dur_list[self.anim_frame] if dur_list and len(dur_list) > self.anim_frame else 100
				while self.anim_time >= cur_dur:
					self.anim_time -= cur_dur
					self.anim_frame = (self.anim_frame + 1) % len(frames)
					cur_dur = dur_list[self.anim_frame] if dur_list and len(dur_list) > self.anim_frame else 100

	def _load_sprite(self):
		# Attempt to use the local Aseprite plugin to load tagged animations
		root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
		ase_path = os.path.join(root, 'assets', 'sprites', 'Blue_witch', 'B_witch.aseprite')
		# If an .aseprite file exists and the plugin is available, parse tags
		if os.path.exists(ase_path):
			try:
				# add plugin src to sys.path so we can import py_aseprite and the helper
				plugin_src = os.path.join(root, 'combine', 'aseprite_plugin', 'src')
				if plugin_src not in __import__('sys').path:
					__import__('sys').path.insert(0, plugin_src)

				from pygame_aseprite_animation import Animation as AseAnim
				from py_aseprite import AsepriteFile

				ase_anim = AseAnim(ase_path)
				# ase_anim.animation_frames is a list of full-frame surfaces
				# try to find frame tag ranges from the .aseprite metadata
				af = None
				with open(ase_path, 'rb') as f:
					af = AsepriteFile(f.read())

				tags = {}
				# frame tags are stored in FrameTagsChunk instances inside frames
				for frame in getattr(af, 'frames', []):
					for chunk in getattr(frame, 'chunks', []):
						if hasattr(chunk, 'tags'):
							for t in getattr(chunk, 'tags', []):
								name = t.get('name', '').lower()
								tags[name] = (t.get('from', 0), t.get('to', 0))

				# Build animations by tag name (if present)
				animations = {}
				if tags:
					for name, (f0, f1) in tags.items():
						frames = ase_anim.animation_frames[f0:f1 + 1]
						durations = ase_anim.frame_duration[f0:f1 + 1]
						animations[name] = {'frames': frames, 'durations': durations}

					# Debug: print discovered tags and built animation keys
					try:
						print('[player_map] discovered ase sprite tags:', list(tags.keys()))
						print('[player_map] built animation keys:', list(animations.keys()))
					except Exception:
						pass

				# Common tag names to look for
				preferred = [
					('idle_right', 'idle_left', 'idle'),
					('run_right', 'run_left', 'run', 'walk')
				]

				# Decide which animations to use for idle/run + facing
				self.animations = {}
				for group in preferred:
					# base is group[0] mapping to facing right; try to find specific tags
					base = group[0]
					for name in group:
						if name in animations:
							# If tag includes direction, split on suffix; otherwise use as both
							if name.endswith('_right'):
								self.animations['idle_right' if 'idle' in name else 'run_right'] = animations[name]
							elif name.endswith('_left'):
								self.animations['idle_left' if 'idle' in name else 'run_left'] = animations[name]
							else:
								# assign generic to both
								key_idle = 'idle' if 'idle' in name else 'run'
								self.animations[key_idle] = animations[name]

				# If we didn't find separate left/right tags, but found generic idle/run, assign them
				for k in ('idle', 'run'):
					if k in animations and k not in self.animations:
						self.animations[k] = animations[k]

				# store frames list for fallback if no tags
				if not self.animations:
					# fallback: use entire frame list as 'idle' if short, else split
					frames = ase_anim.animation_frames
					if len(frames) <= 2:
						self.animations['idle'] = {'frames': frames, 'durations': ase_anim.frame_duration}
					else:
						mid = max(1, len(frames) // 2)
						self.animations['idle'] = {'frames': frames[:mid], 'durations': ase_anim.frame_duration[:mid]}
						self.animations['run'] = {'frames': frames[mid:], 'durations': ase_anim.frame_duration[mid:]}

				# set animator state
				self.cur_anim = 'idle'
				self.anim_frame = 0
				self.anim_time = 0.0
				self.facing = 'right'
				self._ase_frame_size = ase_anim.animation_frames[0].get_size() if ase_anim.animation_frames else (int(self.w_vis), int(self.h_vis))
				# scale frames to player size
				def _process_frame(frame_surf):
					# Ensure we have per-pixel alpha. If the source has no alpha, use the top-left pixel as background
					try:
						# If frame already has alpha channel and corner is transparent, keep as-is
						corner = frame_surf.get_at((0, 0))
					except Exception:
						corner = None
					fs = frame_surf
					# convert to alpha-capable surface
					try:
						fs = frame_surf.convert_alpha()
					except Exception:
						fs = frame_surf.copy()
					# if corner pixel is transparent we keep per-pixel alpha; otherwise attempt to remove solid bg
					bg = None
					try:
						bg = frame_surf.get_at((0, 0))
					except Exception:
						bg = None
					# If the frame already has per-pixel alpha and corner is transparent, we keep it as-is
					if bg is not None and getattr(bg, 'a', None) == 0:
						pass
					else:
						# If frame has no alpha or corner was opaque, try to remove exact background color
						# Create an alpha-capable surface to copy into
						try:
							w0, h0 = fs.get_size()
							clean = pygame.Surface((w0, h0), pygame.SRCALPHA)
							# If we have a bg candidate, make pixels matching that RGB fully transparent
							if bg is not None:
								bg_rgb = (bg.r, bg.g, bg.b) if getattr(bg, 'r', None) is not None else (bg[0], bg[1], bg[2])
								for yy in range(h0):
									for xx in range(w0):
										col = fs.get_at((xx, yy))
										try:
											pix_rgb = (col.r, col.g, col.b) if getattr(col, 'r', None) is not None else (col[0], col[1], col[2])
										except Exception:
											pix_rgb = (col[0], col[1], col[2])
										if pix_rgb == bg_rgb:
											# leave transparent
											continue
										else:
											clean.set_at((xx, yy), col)
							else:
								# No bg candidate: just copy (we already have alpha via convert_alpha)
								clean.blit(fs, (0, 0))
							fs = clean
						except Exception:
							# on any failure, leave fs as-is
							pass

					# preserve aspect ratio when fitting into player rect
					fw, fh = fs.get_size()
					if fw == 0 or fh == 0:
						# empty frame, return blank sized to visual sprite plus pivot
						blank = pygame.Surface((int(self.w_vis), int(self.h_vis)), pygame.SRCALPHA)
						pivot = (int(self.w_vis) // 2, int(self.h_vis) - 1)
						return blank, pivot
					# desired float scale
					float_scale_w = float(self.w_vis) / fw
					float_scale_h = float(self.h_vis) / fh
					float_scale = min(float_scale_w, float_scale_h)
					# Compute target pixel size and use nearest-neighbour scaling to avoid blur
					new_w = max(1, int(round(fw * float_scale)))
					new_h = max(1, int(round(fh * float_scale)))
					try:
						# use nearest-neighbour scaling (pygame.transform.scale is nearest by default)
						scaled = pygame.transform.scale(fs, (new_w, new_h))
					except Exception:
						scaled = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
					# blit into a target surface sized to the visual sprite, align bottom (feet on floor)
					target = pygame.Surface((int(self.w_vis), int(self.h_vis)), pygame.SRCALPHA)
					tx = (int(self.w_vis) - new_w) // 2
					# place the scaled image so its bottom aligns with the visual sprite bottom
					ty = max(0, int(self.h_vis) - new_h)
					try:
						target.blit(scaled, (tx, ty))
					except Exception:
						pass
					# compute pivot: try to find non-transparent pixels near the bottom
					w_t, h_t = target.get_size()
					pivot_x = None
					pivot_y = None
					search_h = max(1, h_t // 4)
					for row in range(h_t - 1, h_t - 1 - search_h, -1):
						xs = []
						for xx in range(w_t):
							col = target.get_at((xx, row))
							# col may be (r,g,b,a) or similar
							alpha = getattr(col, 'a', None) if hasattr(col, 'a') else (col[3] if len(col) > 3 else 255)
							if alpha and alpha > 0:
								xs.append(xx)
						if xs:
							pivot_x = int(round(sum(xs) / len(xs)))
							pivot_y = row
							break
					if pivot_x is None:
						pivot_x = w_t // 2
						pivot_y = h_t - 1
					return target, (pivot_x, pivot_y)

				for a in self.animations.values():
					scaled = []
					pivots = []
					for f in a['frames']:
						try:
							proc, pivot = _process_frame(f)
						except Exception:
							proc = pygame.Surface((int(self.w_vis), int(self.h_vis)), pygame.SRCALPHA)
							pivot = (int(self.w_vis) // 2, int(self.h_vis) - 1)
						scaled.append(proc)
						pivots.append(pivot)
					a['frames'] = scaled
					a['pivots'] = pivots
				# After scaling frames to visual size, generate flipped variants for
				# missing left/right animations so we can reuse a single-set of
				# frames and smoothly flip them when needed.
				# Example: if 'run' exists but 'run_left'/'run_right' do not, create
				# 'run_right' (copy) and 'run_left' (flipped).
				try:
					keys = list(self.animations.keys())
					for k in keys:
						# skip already direction-specific keys
						if k.endswith('_left') or k.endswith('_right'):
							continue
						base = k
						right = f"{base}_right"
						left = f"{base}_left"
						# ensure right exists (copy of base if missing)
						if right not in self.animations:
							self.animations[right] = {
								'frames': [f.copy() for f in self.animations[base]['frames']],
								'durations': list(self.animations[base].get('durations', [])),
								'pivots': list(self.animations[base].get('pivots', []))
							}
						# ensure left exists (flipped from right)
						if left not in self.animations:
							src = self.animations[right]
							flipped = [pygame.transform.flip(f, True, False) for f in src['frames']]
							# flip pivots horizontally
							flipped_pivots = []
							for (px, py) in src.get('pivots', []):
								fw = src['frames'][0].get_width() if src['frames'] else int(self.w_vis)
								flipped_pivots.append((fw - px, py))
							self.animations[left] = {'frames': flipped, 'durations': list(src.get('durations', [])), 'pivots': flipped_pivots}
				except Exception:
					# non-fatal: if flipping fails, continue without variants
					pass
				# mark loaded so we don't reparse every frame
				self._loaded = True
				return
			except Exception:
				# plugin failed; fall through to simple PNG loading below
				pass

		# Fallback: load individual PNGs (idle/run) if present and scale them
		candidates = [
			os.path.join(root, 'assets', 'sprites', 'Blue_witch', 'B_witch_idle.png'),
			os.path.join(root, 'assets', 'sprites', 'Blue_witch', 'B_witch_run.png'),
			os.path.join(root, 'assets', 'sprites', 'Blue_witch', 'B_witch.png'),
		]
		for p in candidates:
			if os.path.exists(p):
				try:
					surf = pygame.image.load(p)
					# process the loaded surface the same way as ase frames
					try:
						proc, pivot = _process_frame(surf)
					except Exception:
						proc = pygame.Surface((int(self.w_vis), int(self.h_vis)), pygame.SRCALPHA)
						pivot = (int(self.w_vis) // 2, int(self.h_vis) - 1)
					# store as single-frame idle animation
					self.animations = {'idle': {'frames': [proc], 'durations': [200], 'pivots': [pivot]}}
					self.cur_anim = 'idle'
					self.anim_frame = 0
					self.anim_time = 0.0
					self.facing = 'right'
					self._loaded = True
					return
				except Exception:
					continue
		# fallback: leave _sprite as None and draw rect
		self._sprite = None
		self._loaded = True

	def draw(self, surface):
		if not getattr(self, '_loaded', False):
			self._load_sprite()
		# prefer playing animations if available
		if hasattr(self, 'animations') and getattr(self, 'cur_anim', None) in getattr(self, 'animations', {}):
			key = self.cur_anim
			# if key is generic (no direction suffix), try direction-specific variant
			if not (key.endswith('_left') or key.endswith('_right')):
				candidate = f"{key}_{self.facing}"
				if candidate in self.animations:
					key = candidate
			anim = self.animations.get(key, self.animations.get(self.cur_anim, {}))
			frames = anim.get('frames', [])
			if frames:
				idx = self.anim_frame % len(frames)
				frame = frames[idx]
				# base draw position (centered over collision box, bottom-aligned)
				draw_x_base = int(self.x + (self.cw - self.w_vis) // 2)
				draw_y = int(self.y + (self.ch - self.h_vis))
				frame_w = frame.get_width()
				# determine pivot to compute correction so anchor stays fixed
				pivot_used = None
				is_left = key.endswith('_left')
				base_name = key.rsplit('_', 1)[0] if '_' in key else key
				# Prefer pivot data from the right-facing animation (base_right)
				right_key = f"{base_name}_right"
				if is_left and right_key in self.animations and 'pivots' in self.animations[right_key]:
					pivot_used = self.animations[right_key]['pivots'][idx]
				elif 'pivots' in anim and len(anim.get('pivots', [])) > idx:
					pivot_used = anim['pivots'][idx]
				else:
					pivot_used = (frame_w // 2, frame.get_height() - 1)
				# compute correction = frameWidth - 2 * pivotX (pixels)
				correction = frame_w - 2 * pivot_used[0]
				# when drawing flipped (left) frames, shift by -correction to align anchor
				if is_left:
					draw_x = draw_x_base - int(round(correction))
				else:
					draw_x = draw_x_base
				# draw anchor for debugging if requested
				if getattr(self, 'debug_draw_anchor', False):
					anchor_x = draw_x + pivot_used[0]
					anchor_y = draw_y + pivot_used[1]
					try:
						pygame.draw.circle(surface, (255, 0, 0), (int(anchor_x), int(anchor_y)), 2)
					except Exception:
						pass
				# blit the frame at corrected position
				surface.blit(frame, (draw_x, draw_y))
				return
		# fallback to single sprite
		if self._sprite:
				# center sprite over collision box and align bottoms
				draw_x = int(self.x + (self.cw - self.w_vis) // 2)
				draw_y = int(self.y + (self.ch - self.h_vis))
				surface.blit(self._sprite, (draw_x, draw_y))
		else:
			pygame.draw.rect(surface, (200, 80, 80), self.rect)

	def get_visual_rect(self):
		"""Return the pygame.Rect where the visual sprite is drawn on the surface.
		This mirrors the positioning logic used in `draw()` so callers (UI, dialog)
		can anchor to the visible animation frame/pivot rather than the collision box.
		Returns None on failure.
		"""
		try:
			if not getattr(self, '_loaded', False):
				self._load_sprite()

			# prefer playing animations if available
			if hasattr(self, 'animations') and getattr(self, 'cur_anim', None) in getattr(self, 'animations', {}):
				key = self.cur_anim
				# if generic key, prefer direction-specific
				if not (key.endswith('_left') or key.endswith('_right')):
					candidate = f"{key}_{self.facing}"
					if candidate in self.animations:
						key = candidate
				anim = self.animations.get(key, self.animations.get(self.cur_anim, {}))
				frames = anim.get('frames', [])
				if frames:
					idx = getattr(self, 'anim_frame', 0) % len(frames)
					frame = frames[idx]
					frame_w = frame.get_width()
					# determine pivot_used as in draw()
					is_left = key.endswith('_left')
					base_name = key.rsplit('_', 1)[0] if '_' in key else key
					right_key = f"{base_name}_right"
					if is_left and right_key in self.animations and 'pivots' in self.animations[right_key]:
						pivots = self.animations[right_key].get('pivots', [])
						pivot_used = pivots[idx] if len(pivots) > idx else (frame_w // 2, frame.get_height() - 1)
					elif 'pivots' in anim and len(anim.get('pivots', [])) > idx:
						pivot_used = anim['pivots'][idx]
					else:
						pivot_used = (frame_w // 2, frame.get_height() - 1)
					vis_w = int(getattr(self, 'w_vis', frame.get_width()))
					vis_h = int(getattr(self, 'h_vis', frame.get_height()))
					cw = int(getattr(self, 'cw', vis_w))
					# compute draw_x_base and draw_y like draw()
					draw_x_base = int(self.x + (cw - vis_w) // 2)
					draw_y = int(self.y + (self.ch - vis_h))
					correction = frame_w - 2 * pivot_used[0]
					if is_left:
						draw_x = draw_x_base - int(round(correction))
					else:
						draw_x = draw_x_base
					return pygame.Rect(draw_x, draw_y, vis_w, vis_h)

		# fallback: use visual sizes and align bottoms over collision box
			vis_w = int(getattr(self, 'w_vis', self.cw))
			vis_h = int(getattr(self, 'h_vis', self.ch))
			cw = int(getattr(self, 'cw', vis_w))
			draw_x = int(self.x + (cw - vis_w) // 2)
			draw_y = int(self.y + (self.ch - vis_h))
			return pygame.Rect(draw_x, draw_y, vis_w, vis_h)
		except Exception:
			return None
