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
				px = tx * tile_w * scale_int
				py = ty * tile_h * scale_int
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

	# create player near the top-center of the map (position above floor)
	spawn_x = max(16, map_pixel_w // 2)
	spawn_y = max(16, map_pixel_h // 4 - (tile_h * 2 * scale_int))
	player = MapPlayer(spawn_x, spawn_y, scale=scale_int, tile_w=tile_w, tile_h=tile_h)

	clock = pygame.time.Clock()
	running = True
	last_teleport = -1.0
	teleport_cooldown = 0.35

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
			# forward to inventory
			if inventory:
				inventory.handle_event(ev)

		# update
		player.update(dt, platforms)

		# door handling: if player overlaps any door rect, teleport to opposite side
		now = time.time()
		if now - last_teleport > teleport_cooldown:
			for d in door_rects:
				if player.rect.colliderect(d):
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

		# optionally draw platforms (debug)
		for p in platforms:
			pygame.draw.rect(screen, (255, 0, 255, 40), p, 1)

		# draw doors (invisible in final but drawn faintly for debugging)
		for d in door_rects:
			pygame.draw.rect(screen, (0, 255, 0), d, 1)

		player.draw(screen)

		# debug overlay: show player physics and animation state
		try:
			info = f"x={player.x:.1f} y={player.y:.1f} vx={player.vx:.1f} vy={player.vy:.1f} on={player.on_ground} anim={getattr(player,'cur_anim',None)} frame={getattr(player,'anim_frame',0)} facing={getattr(player,'facing','?')}"
			surf = debug_font.render(info, True, (255, 255, 255))
			screen.blit(surf, (8, 8))
		except Exception:
			pass

		if inventory:
			inventory.draw(screen)

		pygame.display.flip()

	return
