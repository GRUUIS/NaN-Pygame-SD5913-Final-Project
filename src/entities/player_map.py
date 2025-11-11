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

	def __init__(self, x=0, y=0, scale=1, tile_w=16, tile_h=16):
		"""Create a player sized to 1 tile wide and 2 tiles tall by default.

		tile_w/tile_h are in pixels (map native tile size). scale is applied on
		top of tile units (from the map scene).
		"""
		self.scale = int(scale) if scale else 1
		self.tile_w = int(tile_w)
		self.tile_h = int(tile_h)
		# player is one tile wide, two tiles high
		self.w = self.tile_w * self.scale
		self.h = self.tile_h * 2 * self.scale

		self.x = float(x)
		self.y = float(y)
		self.vx = 0.0
		self.vy = 0.0
		self.on_ground = False

		# movement values scaled to runtime scale so movement feels consistent
		self.speed = float(self.SPEED) * float(self.scale)
		self.jump_v = float(self.JUMP_V) * float(self.scale)
		self.gravity_v = float(self.GRAVITY) * float(self.scale)

		# sprite surface lazy-loaded in draw
		self._sprite = None
		# mark whether we've attempted to load sprite/animations
		self._loaded = False

	@property
	def rect(self):
		return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

	def handle_input(self, keys):
		self.vx = 0.0
		if keys[pygame.K_LEFT] or keys[pygame.K_a]:
			self.vx = -self.speed
		if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
			self.vx = self.speed
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
			if getattr(self, 'cur_anim', None) != chosen:
				print(f"[player_map] anim change: {getattr(self,'cur_anim',None)} -> {chosen}")
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
				self._ase_frame_size = ase_anim.animation_frames[0].get_size() if ase_anim.animation_frames else (int(self.w), int(self.h))
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
						# empty frame, return blank
						return pygame.Surface((int(self.w), int(self.h)), pygame.SRCALPHA)
					scale = min(float(self.w) / fw, float(self.h) / fh)
					new_w = max(1, int(fw * scale))
					new_h = max(1, int(fh * scale))
					try:
						scaled = pygame.transform.scale(fs, (new_w, new_h))
					except Exception:
						scaled = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
					# blit into a target surface of exact player size, align bottom (feet on floor)
					target = pygame.Surface((int(self.w), int(self.h)), pygame.SRCALPHA)
					tx = (int(self.w) - new_w) // 2
					# place the scaled image so its bottom aligns with the player's bottom
					ty = max(0, int(self.h) - new_h)
					try:
						target.blit(scaled, (tx, ty))
					except Exception:
						pass
					return target

				for a in self.animations.values():
					scaled = []
					for f in a['frames']:
						try:
							proc = _process_frame(f)
						except Exception:
							proc = pygame.Surface((int(self.w), int(self.h)), pygame.SRCALPHA)
						scaled.append(proc)
					a['frames'] = scaled
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
						proc = _process_frame(surf)
					except Exception:
						proc = pygame.Surface((int(self.w), int(self.h)), pygame.SRCALPHA)
					# store as single-frame idle animation
					self.animations = {'idle': {'frames': [proc], 'durations': [200]}}
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
				frame = frames[self.anim_frame % len(frames)]
				surface.blit(frame, (int(self.x), int(self.y)))
				return
		# fallback to single sprite
		if self._sprite:
			surface.blit(self._sprite, (int(self.x), int(self.y)))
		else:
			pygame.draw.rect(surface, (200, 80, 80), self.rect)
