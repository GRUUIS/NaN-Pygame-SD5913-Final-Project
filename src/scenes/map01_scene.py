"""Map01 scene: load the Room1 map from `assets/map01` and run a small
playable viewer. This is a pragmatic, self-contained scene used by the
launcher to test tile collisions and basic door teleporting logic.

The implementation keeps imports local to `run` so importing the module is
cheap; calling `run(screen, inventory=...)` will import pygame and the
other helpers.
"""

import os
import glob
import time


def run(screen, inventory=None):
	import pygame
	from src.tiled_loader import load_map, draw_map, extract_collision_rects
	from src.entities.player_map import MapPlayer
	from src.ui.dialog_box import SpeechBubble

	ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
	# find Room1.tmj first, fallback to any Room1.tmx if necessary
	map_path = None
	for p in glob.iglob(os.path.join(ROOT, 'assets', 'map01', 'Room1.*')):
		if p.lower().endswith('.tmj'):
			map_path = p
			break
		if p.lower().endswith('.tmx') and map_path is None:
			map_path = p

	if not map_path:
		print('map01_scene: Room1 map not found under assets/map01; aborting')
		return

	# Prefer JSON TMJ loader; if .tmx is present and load_map fails, we'll raise
	try:
		m, tiles_by_gid, tileset_meta = load_map(map_path)
	except Exception as e:
		print('map01_scene: failed to load map:', e)
		return

	tile_w = m.get('tilewidth', 16)
	tile_h = m.get('tileheight', 16)
	width = m.get('width', 0)
	height = m.get('height', 0)

	# drawing scale (integer) to keep collision and visuals aligned
	draw_scale = 1.0
	scale_int = max(1, round(draw_scale))

	# identify collidable gids from a layer named 'collusion' (authoritative)
	collidable_gids = set()
	# collect layer names for debug
	layer_names = [((layer.get('name') or '').strip(), layer.get('type')) for layer in m.get('layers', [])]
	for layer in m.get('layers', []):
		name = (layer.get('name') or '').lower()
		if name == 'collusion':
			for gid in layer.get('data', []):
				g = gid & 0x1FFFFFFF
				if g != 0:
					collidable_gids.add(g)

	# build platforms from collidable gids (pixel rects)
	# Extract platforms only from the authoritative 'collusion' layer and
	# apply a +1 tile horizontal shift so collision matches tile visuals.
	platforms = extract_collision_rects(m, tileset_meta, collidable_gids=collidable_gids, scale=scale_int, authoritative_layer_name='collusion', shift_tiles=1)

	# DEBUG: print layer and collision info to help diagnose missing collisions
	try:
		print('[map01_scene DEBUG] layers:', layer_names)
		print('[map01_scene DEBUG] collidable_gids count:', len(collidable_gids), 'sample:', list(sorted(collidable_gids))[:10])
		print('[map01_scene DEBUG] platforms (before door filter):', len(platforms))
		for i, p in enumerate(platforms[:30]):
			print(f"[map01_scene DEBUG] platform[{i}] = {p} -> tiles (tx,ty)=({p.x//tile_w},{p.y//tile_h})")
	except Exception:
		pass

	# Build door candidate rects: only the outer 1 column on left and right
	door_rects = []
	edge_cols = 1
	map_pixel_w = tile_w * width * scale_int
	map_pixel_h = tile_h * height * scale_int

	# Build a map of outer-column tile rows (tx -> set of ty values) so we
	# can collapse contiguous vertical runs and limit each run to at most 5
	# tiles (keep the center-most 5). This prevents very tall door holes
	# at the map edges which can let the player drop out unexpectedly.
	edge_tiles = {}
	for layer in m.get('layers', []):
		if layer.get('type') != 'tilelayer':
			continue
		data = layer.get('data', [])
		for idx, raw_gid in enumerate(data):
			gid = raw_gid & 0x1FFFFFFF
			if gid == 0:
				continue
			tx = idx % width
			ty = idx // width
			if tx < edge_cols or tx >= (width - edge_cols):
				edge_tiles.setdefault(tx, set()).add(ty)

	def _limit_segment(tys, max_len=6):
		"""Given a sorted list of contiguous ty values, return at most
		`max_len` ty values centered within the segment."""
		L = len(tys)
		if L <= max_len:
			return tys
		# choose center-most window of length max_len
		start_idx = (L - max_len) // 2
		return tys[start_idx:start_idx + max_len]

	# convert limited ty lists into door rects
	# Apply a vertical shift so doors are moved down by a few tiles if desired.
	# Use 5 to move doors down by five tiles as requested.
	door_vertical_shift = 5
	for tx, tys in edge_tiles.items():
		if not tys:
			continue
		sorted_tys = sorted(tys)
		# find contiguous segments
		seg_start = sorted_tys[0]
		seg_prev = seg_start
		cur_seg = [seg_start]
		segments = []
		for ty in sorted_tys[1:]:
			if ty == seg_prev + 1:
				cur_seg.append(ty)
			else:
				segments.append(cur_seg)
				cur_seg = [ty]
			seg_prev = ty
		segments.append(cur_seg)

		# limit each segment to max 6 tiles and add rects
		for seg in segments:
			kept = _limit_segment(seg, max_len=6)
			for ty in kept:
				new_ty = ty + door_vertical_shift
				# skip if shifted tile outside vertical map bounds
				if new_ty < 0 or new_ty >= height:
					continue
				px = tx * tile_w * scale_int
				py = new_ty * tile_h * scale_int
				door_rects.append(pygame.Rect(px, py, tile_w * scale_int, tile_h * scale_int))

	# Remove any platform that overlaps a door so doors are passable
	filtered_platforms = []
	for p in platforms:
		blocked = False
		for d in door_rects:
			if p.colliderect(d):
				blocked = True
				break
		if not blocked:
			filtered_platforms.append(p)
	platforms = filtered_platforms

	# --- place a single 'hourglass' item on the top-most platform ---
	items = []
	try:
		if platforms:
			# choose the platform in the middle-area (exclude full-width floors/walls)
			map_pixel_w = tile_w * width * scale_int
			map_pixel_h = tile_h * height * scale_int
			# prefer platforms roughly in the horizontal middle third of the map
			mid_left = map_pixel_w * 0.25
			mid_right = map_pixel_w * 0.75
			candidates = [p for p in platforms if p.width < (map_pixel_w * 0.9) and p.top > (tile_h * 1) and p.top < (map_pixel_h - tile_h * 4) and (p.left + p.width/2) >= mid_left and (p.left + p.width/2) <= mid_right]
			if not candidates:
				# fallback to any non-full-width platform
				candidates = [p for p in platforms if p.width < (map_pixel_w * 0.99)]
			if not candidates:
				# ultimate fallback: use the top-most platform
				top_plat = min(platforms, key=lambda r: r.top)
			else:
				top_plat = min(candidates, key=lambda r: r.top)
			item_w = int(tile_w * scale_int)
			item_h = int(tile_h * scale_int)
			# center item horizontally on the platform and place it on top
			item_x = int(top_plat.left + (top_plat.width - item_w) // 2)
			item_y = int(top_plat.top - item_h)

			# try to load hourglass image; fallback to item_clock.png if not found
			def _find_asset(name):
				cands = [
					os.path.join('assets', name),
					os.path.join('assets', 'sprites', 'items', name),
					os.path.join('assets', 'sprites', name),
					os.path.join('assets', 'art', name),
				]
				for pth in cands:
					if os.path.exists(pth):
						return pth
				# recursive search
				for root, dirs, files in os.walk('assets'):
					for fn in files:
						if fn.lower() == name.lower():
							return os.path.join(root, fn)
				return None

			img_path = _find_asset('hourglass.png') or _find_asset('item_clock.png')
			if img_path:
				try:
					img = pygame.image.load(img_path).convert_alpha()
				except Exception:
					img = None
			else:
				img = None

			if img is not None:
				# scale using integer scaling to avoid blur
				iw, ih = img.get_size()
				scale_x = max(1, item_w // iw)
				scale_y = max(1, item_h // ih)
				scale_use = min(scale_x, scale_y)
				new_w = iw * scale_use
				new_h = ih * scale_use
				try:
					img_scaled = pygame.transform.scale(img, (new_w, new_h))
				except Exception:
					img_scaled = img
				# blit into a surface sized to item_w x item_h and center
				surf = pygame.Surface((item_w, item_h), pygame.SRCALPHA)
				offx = (item_w - new_w) // 2
				offy = (item_h - new_h) // 2
				surf.blit(img_scaled, (offx, offy))
			else:
				# fallback colored square
				surf = pygame.Surface((item_w, item_h), pygame.SRCALPHA)
				surf.fill((200, 180, 60))

			# clamp item inside map bounds
			item_x = max(0, min(item_x, map_pixel_w - item_w))
			item_y = max(0, min(item_y, map_pixel_h - item_h))
			items.append({'id': 'hourglass', 'rect': pygame.Rect(item_x, item_y, item_w, item_h), 'sprite': surf})
			print('[map01_scene DEBUG] placed hourglass at', item_x, item_y, 'platform top', top_plat.top)

	except Exception:
		items = []

	# create player near the top-center of the map (position above floor)
	spawn_x = max(16, map_pixel_w // 2)
	spawn_y = max(16, map_pixel_h // 4 - (tile_h * 2 * scale_int))
	player = MapPlayer(spawn_x, spawn_y, scale=scale_int, tile_w=tile_w, tile_h=tile_h)

	# make player visually larger (visual sprite only) and force sprite reload
	try:
		player.visual_scale = 6.0
		player.w_vis = int(player.tile_w * player.scale * player.visual_scale)
		player.h_vis = int(player.tile_h * 2 * player.scale * player.visual_scale)
		# force sprite to be reloaded/scaled next draw
		player._loaded = False
		player._sprite = None
	except Exception:
		pass

	# Create a static dialog in the top-right corner (doesn't follow player)
	try:
		screen_w, screen_h = screen.get_size()
		box_w = min(280, max(120, screen_w // 6))
		box_h = max(28, int(box_w * 0.20))
		margin = 12
		box_x = (screen_w - box_w) // 2
		box_y = margin

		def _anchor_static():
			# return a fixed screen-space rect so the dialog does not follow the player
			try:
				return pygame.Rect(box_x, box_y, box_w, box_h)
			except Exception:
				return None

		dialog = SpeechBubble(_anchor_static, size=(box_w, box_h), draw_background=False, face_offset=0.0, y_overlap=0, font_scale=0.72)
		dialog.set_text('Hi~')
		dialog.open()
	except Exception:
		dialog = None

	clock = pygame.time.Clock()
	running = True
	last_teleport = -1.0
	teleport_cooldown = 0.35

	# track if player is stuck above the top of the map
	stuck_above_time = 0.0
	# how many seconds player must remain above the top before we force-respawn
	stuck_above_timeout = 1.5
	# how far above the top counts as 'stuck' (pixels)
	stuck_above_limit = tile_h * 2 * scale_int

	# debug font for on-screen state
	try:
		debug_font = pygame.font.Font(os.path.join(ROOT, 'assets', 'Silver.ttf'), 14)
	except Exception:
		debug_font = pygame.font.SysFont('consolas', 14)

	while running:
		dt = clock.tick(60) / 1000.0
		for ev in pygame.event.get():
			if ev.type == pygame.QUIT:
				running = False
			elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
				running = False
			# press C to pick up nearest item (keyboard pickup)
			elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_c:
				# compute player center in screen/map coords
				px = int(player.x + player.cw // 2)
				py = int(player.y + player.ch // 2)
				from math import hypot
				for it in list(items):
					r = it['rect']
					dist = hypot(px - r.centerx, py - r.centery)
					if dist < max(tile_w * 6, 160):
						picked = False
						if inventory:
							picked = inventory.add_item({'id': it.get('id'), 'name': it.get('id')})
						if picked or not inventory:
							items.remove(it)
							print('Picked up', it.get('id'))
							break
			# forward to inventory
			if inventory:
				inventory.handle_event(ev)
			# right-click pickup for items
			if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
				sx, sy = ev.pos
				for it in list(items):
					obj_screen = it['rect']
					if obj_screen.collidepoint((sx, sy)):
						# compute player screen center
						px = int(player.x + player.cw // 2)
						py = int(player.y + player.ch // 2)
						from math import hypot
						dist = hypot(px - obj_screen.centerx, py - obj_screen.centery)
						if dist < max(tile_w * 6, 160):
							# attempt to add to inventory if available
							picked = False
							if inventory:
								picked = inventory.add_item({'id': it.get('id'), 'name': it.get('id')})
								if picked or not inventory:
									items.remove(it)
									print('Picked up', it.get('id'))
							break

		# update
		player.update(dt, platforms)

		# respawn player if they fall out of the map (below the visible map area)
		try:
			# use player's rect top/left; if the player y is beyond map height, respawn
			if getattr(player, 'y', None) is not None:
				if player.y > map_pixel_h + (tile_h * 4):
					print('[map01_scene DEBUG] player fell out of map, respawning')
					player.x = spawn_x
					player.y = spawn_y
					player.vx = 0
					player.vy = 0
					# reset on_ground state if present
					try:
						player.on_ground = False
					except Exception:
						pass
		except Exception:
			pass

		# detect if the player is stuck above the top of the map and cannot get down
		# accumulate time spent above a small negative threshold; if it exceeds
		# stuck_above_timeout, force a respawn to the spawn point.
		try:
			if getattr(player, 'y', None) is not None:
				if player.y < -stuck_above_limit:
					stuck_above_time += dt
				else:
					stuck_above_time = 0.0
				# if stuck too long, teleport back to spawn
				if stuck_above_time > stuck_above_timeout:
					print('[map01_scene DEBUG] player stuck above map, respawning')
					player.x = spawn_x
					player.y = spawn_y
					player.vx = 0
					player.vy = 0
					stuck_above_time = 0.0
					try:
						player.on_ground = False
					except Exception:
						pass
		except Exception:
			# swallow any errors here to avoid crashing the scene
			pass

		# door handling: if player overlaps any door rect, teleport to opposite side
		now = time.time()
		if now - last_teleport > teleport_cooldown:
			for d in door_rects:
				if player.rect.colliderect(d):
					# If the player is carrying the special 'hourglass', send them to boss1
					try:
						if inventory and inventory.has_item('hourglass'):
							print('[map01_scene DEBUG] player has hourglass - launching boss1')
							# import here to avoid circular imports at module load time
							try:
								import main as main_mod
								# call the main-run helper to start the boss test (boss2/3 hence the first one is deleted)
								main_mod.run_boss_test('hollow')
							except Exception as e:
								print('[map01_scene DEBUG] failed to launch boss:', e)
							running = False
							break
					except Exception:
						# ignore and continue with normal door behaviour
						pass
					# find opposite side candidate with same row (ty)
					ty = d.top // (tile_h * scale_int)
					left = d.left < (map_pixel_w // 2)
					candidates = [r for r in door_rects if (r.top // (tile_h * scale_int)) == ty and (r.left < (map_pixel_w // 2)) != left]
					if not candidates:
						# fallback: pick any door on opposite half
						candidates = [r for r in door_rects if (r.left < (map_pixel_w // 2)) != left]
					if candidates:
						dest = candidates[0]
						# move player to dest center
						player.x = dest.left + 4
						# use player's collision height (ch) rather than undefined 'h'
						player.y = dest.top - getattr(player, 'ch', getattr(player, 'h', 0))
						player.vx = 0
						player.vy = 0
						last_teleport = now
					break

		# draw
		draw_map(screen, m, tiles_by_gid, scale=scale_int)

		# debug overlays removed so collision tiles are visible
		# (platform and door debug rectangles were here and have been disabled)

		# draw items
		for it in items:
			try:
				screen.blit(it['sprite'], (it['rect'].x, it['rect'].y))
			except Exception:
				pygame.draw.rect(screen, (200, 180, 60), it['rect'])

		player.draw(screen)

		# debug overlay: show player physics and animation state
		try:
			info = f"x={player.x:.1f} y={player.y:.1f} vx={player.vx:.1f} vy={player.vy:.1f} on={player.on_ground} anim={getattr(player,'cur_anim',None)} frame={getattr(player,'anim_frame',0)} facing={getattr(player,'facing','?')}"
			surf = debug_font.render(info, True, (255, 255, 255))
			screen.blit(surf, (8, 8))
		except Exception:
			pass

		# instruction overlay removed from map scene per UI change; instructions
		# (including pickup hint) are now shown in the main menu.

		if inventory:
			inventory.draw(screen)

		# draw speech bubble if present
		try:
			if dialog:
				dialog.draw(screen)
		except Exception:
			pass

		pygame.display.flip()

	return
