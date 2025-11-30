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
import sys
import pygame

# Ensure project root is in sys.path for imports if run directly
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
	sys.path.insert(0, ROOT_DIR)

def draw_gear(surface, center, radius, teeth=8, color=(120,120,120,128)):
	import math
	points = []
	for i in range(teeth*2):
		angle = math.pi * 2 * i / (teeth*2)
		r = radius if i%2==0 else int(radius*0.78)
		x = int(center[0] + r * math.cos(angle))
		y = int(center[1] + r * math.sin(angle))
		points.append((x, y))
	gear_surf = pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA)
	pygame.draw.polygon(gear_surf, color, [(x-radius+2, y-radius+2) for (x,y) in points])
	pygame.draw.circle(gear_surf, (80,80,80,180), (radius+2, radius+2), int(radius*0.35))
	surface.blit(gear_surf, (center[0]-radius-2, center[1]-radius-2))

def run(screen):
	# State for gear target zones
	show_gear_targets = False
	gear_target_positions = []
	gear_target_radius = 108
	gear_target_teeth = 8
	gear_target_color = (120, 120, 120, 180)

	import pygame
	import traceback
	from src.tiled_loader import load_map, draw_map, extract_collision_rects
	from src.entities.player_map import MapPlayer
	from src.ui.dialog_box_notusing import SpeechBubble

	# Local set to track collected items since inventory system is removed
	collected_items = set()

	# Adjusted ROOT for testing folder (1 level deep)
	ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
	
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

	# Merge horizontally adjacent platform rects so we can trim them properly
	platforms.sort(key=lambda r: (r.y, r.x))
	merged_platforms = []
	if platforms:
		curr_p = platforms[0]
		for next_p in platforms[1:]:
			# Check if next_p is directly to the right of curr_p
			if (next_p.y == curr_p.y and 
				next_p.height == curr_p.height and 
				abs(next_p.x - curr_p.right) < 2): # Allow 1px slop just in case
				curr_p.width += next_p.width
			else:
				merged_platforms.append(curr_p)
				curr_p = next_p
		merged_platforms.append(curr_p)
	platforms = merged_platforms

	# Trim one tile column from the left side of each platform so collision
	# matches the grey platform area on the tilemap (fixes left-side overhang).
	try:
		trim_px = tile_w * scale_int
		trimmed = []
		for p in platforms:
			if p.width > trim_px:
				new_rect = pygame.Rect(p.left + trim_px, p.top, p.width - trim_px, p.height)
				trimmed.append(new_rect)
			# if platform is too narrow to trim safely, keep it as-is
			else:
				trimmed.append(p)
		platforms = trimmed
		print(f'[map01_scene DEBUG] trimmed {len(filtered_platforms)-len(trimmed)} platform columns on left')
	except Exception:
		# if pygame or rect operations fail, keep original platforms
		pass

	# --- place a single 'hourglass' item on the top-most platform ---
	items = []

	# --- Place hourglass and (delayed) lamp ---
	lamp_item_data = None
	try:
		if platforms:
			# ...existing code for platform selection...
			map_pixel_w = tile_w * width * scale_int
			map_pixel_h = tile_h * height * scale_int
			mid_left = map_pixel_w * 0.25
			mid_right = map_pixel_w * 0.75
			candidates = [p for p in platforms if p.width < (map_pixel_w * 0.9) and p.top > (tile_h * 1) and p.top < (map_pixel_h - tile_h * 4) and (p.left + p.width/2) >= mid_left and (p.left + p.width/2) <= mid_right]
			if not candidates:
				candidates = [p for p in platforms if p.width < (map_pixel_w * 0.99)]
			if not candidates:
				top_plat = min(platforms, key=lambda r: r.top)
			else:
				top_plat = min(candidates, key=lambda r: r.top)
			item_w = int(tile_w * scale_int)
			item_h = int(tile_h * scale_int)
			item_x = int(top_plat.left + (top_plat.width - item_w) // 2) - 48
			item_y = int(top_plat.top - item_h)

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
				surf = pygame.Surface((item_w, item_h), pygame.SRCALPHA)
				offx = (item_w - new_w) // 2
				offy = (item_h - new_h) // 2
				surf.blit(img_scaled, (offx, offy))
			else:
				surf = pygame.Surface((item_w, item_h), pygame.SRCALPHA)
				surf.fill((200, 180, 60))

			item_x = max(0, min(item_x, map_pixel_w - item_w))
			item_y = max(0, min(item_y, map_pixel_h - item_h))
			items.append({'id': 'hourglass', 'rect': pygame.Rect(item_x, item_y, item_w, item_h), 'sprite': surf})
			print('[map01_scene DEBUG] placed hourglass at', item_x, item_y, 'platform top', top_plat.top)

			# Prepare lamp item data, but do not add to items yet
			try:
				lamp_img_path = _find_asset('lamp.png')
				if lamp_img_path:
					lamp_img = pygame.image.load(lamp_img_path).convert_alpha()
					lamp_w, lamp_h = item_w * 2, item_h * 2
					lamp_img_scaled = pygame.transform.smoothscale(lamp_img, (lamp_w, lamp_h))
					lamp_surf = pygame.Surface((lamp_w, lamp_h), pygame.SRCALPHA)
					lamp_surf.blit(lamp_img_scaled, (0, 0))
					# Place lamp further to the right of the hourglass, with a larger gap
					lamp_gap = 60  # Reduced from 160 to keep it on platform
					lamp_x = item_x + item_w + lamp_gap
					# Clamp to map bounds
					lamp_x = max(0, min(lamp_x, map_pixel_w - lamp_w))
					# Align lamp's bottom with hourglass's bottom, then move it down a little
					lamp_y = item_y + item_h - lamp_h + 11  # Move lamp down by 11 pixels
					lamp_item_data = {'id': 'lamp', 'rect': pygame.Rect(lamp_x, lamp_y, lamp_w, lamp_h), 'sprite': lamp_surf}
					print('[map01_scene DEBUG] prepared lamp at', lamp_x, lamp_y, 'to the right of hourglass')
			except Exception as e:
				print('[map01_scene DEBUG] failed to prepare lamp:', e)

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

		# dialog = SpeechBubble(_anchor_static, size=(box_w, box_h), draw_background=False, face_offset=0.0, y_overlap=0, font_scale=0.72)
		# dialog.set_text('Hi~')
		# dialog.open()
		dialog = None
	except Exception:
		dialog = None


	# 在主循环前加载多张图片（brush.png, group.png）
	projected_imgs = []
	img_names = ['brush.png', 'group.png', 'chain.png']
	for name in img_names:
		try:
			img = pygame.image.load(os.path.join(ROOT, 'assets', name)).convert_alpha()
			img = pygame.transform.smoothscale(img, (200, 200))
			projected_imgs.append(img)
		except Exception as e:
			print(f"[map01_scene DEBUG] Failed to load {name}: {e}")
			projected_imgs.append(None)
	current_img_idx = -1  # Start with no image projected

	# 新增：沙漏拾取后只显示group.png
	group_img = None
	try:
		group_img = pygame.image.load(os.path.join(ROOT, 'assets', 'group.png')).convert_alpha()
		group_img = pygame.transform.smoothscale(group_img, (200, 200))
	except Exception as e:
		print(f"[map01_scene DEBUG] Failed to load group.png: {e}")
		group_img = None

	# Brush image for lamp projection
	brush_img = None
	try:
		brush_img = pygame.image.load(os.path.join(ROOT, 'assets', 'brush.png')).convert_alpha()
		brush_img = pygame.transform.smoothscale(brush_img, (200, 200))
	except Exception as e:
		print(f"[map01_scene DEBUG] Failed to load brush.png: {e}")
		brush_img = None

	show_only_group_img = False
	group_img_show_timer = 0.0  # 计时器，记录group.png和文字显示时长
	group_img_fadeout = False   # 是否进入淡出阶段
	group_img_fadeout_time = 1.5  # 淡出动画时长（秒）
	group_img_fadeout_progress = 0.0  # 当前淡出进度（秒）

	# Track whether each story window has completed showing (used to gate gear targets)
	group_story_completed = False
	
	# Story text state
	story_text_lines = [
		"Against the sand of time,",
		"we measure the weight of memory"
	]
	story_text_alpha = 0
	story_text_fadein = False
	story_text_fadeout = False
	story_text_fully_visible = False

	# Brush projection state
	show_brush_projection = False
	brush_img_alpha = 0
	brush_proj_timer = 0.0

	# Track brush story window completion
	brush_story_completed = False
	
	# Reward images state
	reward_img_clicked = False # For 1-1-1.png
	show_121_img = False
	img_121_clicked = False # For 1-2-1.png
	# Drag state for reward images
	drag_111 = False
	drag_121 = False
	drag_candidate_111 = False
	drag_candidate_121 = False
	drag_start_pos_111 = (0, 0)
	drag_start_pos_121 = (0, 0)
	drag_offset_111 = (0, 0)
	drag_offset_121 = (0, 0)
	# Positions for draggable images (default: bottom corners)
	reward_img_pos = None
	img_121_pos = None
	# Lock state for gears
	gear_111_locked = False
	gear_121_locked = False

	# Door shine effect state (used to visually highlight doors after gears placed)
	door_shine_timer = 0.0
	door_shine_period = 1.2
	show_door_shine = False

	# 图片淡入相关变量
	image_fadein = False  # 是否开始淡入
	image_alpha = 0       # 当前alpha值（0-255）
	image_fadein_speed = 180  # 每秒alpha增加量，可调整

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
		mouse_pos = pygame.mouse.get_pos()
		for ev in pygame.event.get():
			# Event-based click detection for reward / 1-2-1 images so clicks
			# are consumed by the event loop and won't cause instant lock on mouseup.
			if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
				# Pick up / start drag for 1-2-1 (right gear) if it's shown and not picked
				try:
					if show_121_img and not img_121_clicked and img_121_pos:
						r = pygame.Rect(img_121_pos[0], img_121_pos[1], 80, 80)
						if r.collidepoint(ev.pos):
							img_121_clicked = True
							drag_candidate_121 = True
							drag_start_pos_121 = ev.pos
				except Exception:
					pass
				# Pick up / start drag for 1-1-1 (left reward) if it's shown and not picked
				try:
					# reward image is only displayed after group fadeout
					if group_img_fadeout and group_img_alpha == 0 and not reward_img_clicked and reward_img_pos:
						r = pygame.Rect(reward_img_pos[0], reward_img_pos[1], 80, 80)
						if r.collidepoint(ev.pos):
							reward_img_clicked = True
							drag_candidate_111 = True
							drag_start_pos_111 = ev.pos
				except Exception:
					pass
			# Drag logic for reward images with locking
			if show_121_img and img_121_clicked and not gear_121_locked:
				if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
					if img_121_pos:
						img_121_rect = pygame.Rect(img_121_pos[0], img_121_pos[1], 80, 80)
						if img_121_rect.collidepoint(ev.pos):
							# start a drag candidate; only become an actual drag after movement
							drag_candidate_121 = True
							drag_start_pos_121 = ev.pos
				elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
					# Only consider dropping into the target if a drag actually happened
					if drag_121:
						drag_121 = False
						# Check if dropped in right target zone
						if show_gear_targets and len(gear_target_positions) == 2:
							target_rect = pygame.Rect(gear_target_positions[1][0] - gear_target_radius, gear_target_positions[1][1] - gear_target_radius, gear_target_radius*2, gear_target_radius*2)
							if img_121_pos and target_rect.collidepoint(img_121_pos[0] + 40, img_121_pos[1] + 40):
								gear_121_locked = True
								img_121_pos = (gear_target_positions[1][0] - 40, gear_target_positions[1][1] - 40)
								print('[DEBUG] gear_121_locked set ->', gear_121_locked)
					# clear candidate on mouseup regardless
					drag_candidate_121 = False
				elif ev.type == pygame.MOUSEMOTION:
					# If we have a drag candidate and movement exceeds threshold, start actual drag
					if drag_candidate_121 and not drag_121:
						dx = ev.pos[0] - drag_start_pos_121[0]
						dy = ev.pos[1] - drag_start_pos_121[1]
						if (dx*dx + dy*dy) >= (6*6):
							drag_121 = True
							# compute offset so the image sticks to cursor
							if img_121_pos:
								drag_offset_121 = (ev.pos[0] - img_121_pos[0], ev.pos[1] - img_121_pos[1])
							else:
								drag_offset_121 = (0, 0)
					# If actively dragging, update position
					if drag_121:
						img_121_pos = (ev.pos[0] - drag_offset_121[0], ev.pos[1] - drag_offset_121[1])
			# allow dragging the reward gear once it's been clicked, regardless of group fade flags
			if reward_img_clicked and not gear_111_locked:
				if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
					if reward_img_pos:
						reward_img_rect = pygame.Rect(reward_img_pos[0], reward_img_pos[1], 80, 80)
						if reward_img_rect.collidepoint(ev.pos):
							# start a drag candidate; only become an actual drag after movement
							drag_candidate_111 = True
							drag_start_pos_111 = ev.pos
				elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
					# Only consider dropping into the target if a drag actually happened
					if drag_111:
						drag_111 = False
						# Check if dropped in left target zone
						if show_gear_targets and len(gear_target_positions) == 2:
							target_rect = pygame.Rect(gear_target_positions[0][0] - gear_target_radius, gear_target_positions[0][1] - gear_target_radius, gear_target_radius*2, gear_target_radius*2)
							if reward_img_pos and target_rect.collidepoint(reward_img_pos[0] + 40, reward_img_pos[1] + 40):
								gear_111_locked = True
								reward_img_pos = (gear_target_positions[0][0] - 40, gear_target_positions[0][1] - 40)
								print('[DEBUG] gear_111_locked set ->', gear_111_locked)
					# clear candidate on mouseup regardless
					drag_candidate_111 = False
				elif ev.type == pygame.MOUSEMOTION:
					# If we have a drag candidate and movement exceeds threshold, start actual drag
					if drag_candidate_111 and not drag_111:
						dx = ev.pos[0] - drag_start_pos_111[0]
						dy = ev.pos[1] - drag_start_pos_111[1]
						if (dx*dx + dy*dy) >= (6*6):
							drag_111 = True
							# compute offset so the image sticks to cursor
							if reward_img_pos:
								drag_offset_111 = (ev.pos[0] - reward_img_pos[0], ev.pos[1] - reward_img_pos[1])
							else:
								drag_offset_111 = (0, 0)
					# If actively dragging, update position
					if drag_111:
						reward_img_pos = (ev.pos[0] - drag_offset_111[0], ev.pos[1] - drag_offset_111[1])
			if ev.type == pygame.QUIT:
				running = False
			elif ev.type == pygame.KEYDOWN:
				if ev.key == pygame.K_ESCAPE:
					running = False
				# Z 键跳过关卡
				elif ev.key == pygame.K_z:
					running = False
				elif ev.key == pygame.K_t:
					# 按T键切换下一张图片
					if projected_imgs:
						if current_img_idx == -1:
							current_img_idx = 0
						else:
							current_img_idx = (current_img_idx + 1) % len(projected_imgs)
				elif ev.key == pygame.K_SPACE:
					# Space bar now picks up items (was jump)
					px = int(player.x + player.cw // 2)
					py = int(player.y + player.ch // 2)
					from math import hypot
					print(f"[map01_scene DEBUG] Trying to pick up. Player at ({px}, {py}). Items: {len(items)}")
					for it in list(items):
						r = it['rect']
						dist = hypot(px - r.centerx, py - r.centery)
						print(f"[map01_scene DEBUG] Item {it.get('id')} at ({r.centerx}, {r.centery}), dist={dist:.1f}")
						if dist < max(tile_w * 6, 160):
							item_id = it.get('id')
							if item_id == 'lamp':
								items.remove(it)
								collected_items.add(item_id)
								print('Picked up', item_id)
								# DEBUG: show collected state after lamp pickup
								try:
									print(f"[DEBUG] collected_items={collected_items} show_brush_projection will be set")
								except Exception:
									pass
								show_brush_projection = True
								brush_img_alpha = 0
								brush_proj_timer = 0.0
								break
							elif item_id == 'hourglass':
								items.remove(it)
								collected_items.add(item_id)
								print('Picked up', item_id)
								# DEBUG: show collected state after hourglass pickup
								try:
									print(f"[DEBUG] collected_items={collected_items} image_fadein={image_fadein}")
								except Exception:
									pass
								image_fadein = True
								image_alpha = 0
								show_only_group_img = True
								group_img_show_timer = 0.0
								group_img_fadeout = False
								group_img_fadeout_progress = 0.0
								story_text_fadein = True
								story_text_alpha = 0
								story_text_fully_visible = False
								# Spawn the lamp immediately after hourglass pickup (if prepared)
								try:
									if lamp_item_data is not None and not any(x.get('id') == 'lamp' for x in items) and 'lamp' not in collected_items:
										items.append(lamp_item_data)
										print('[DEBUG] Lamp spawned after hourglass pickup')
								except Exception:
									pass
								break
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
							item_id = it.get('id')
							if item_id == 'lamp':
								items.remove(it)
								collected_items.add(item_id)
								print('Picked up', item_id)
								try:
									print(f"[DEBUG] collected_items={collected_items} show_brush_projection will be set (right-click)")
								except Exception:
									pass
								show_brush_projection = True
								brush_img_alpha = 0
								brush_proj_timer = 0.0
								break
							elif item_id == 'hourglass':
								items.remove(it)
								collected_items.add(item_id)
								print('Picked up', item_id)
								try:
									print(f"[DEBUG] collected_items={collected_items} image_fadein={image_fadein} (right-click)")
								except Exception:
									pass
								image_fadein = True
								image_alpha = 0
								show_only_group_img = True
								group_img_show_timer = 0.0
								group_img_fadeout = False
								group_img_fadeout_progress = 0.0
								story_text_fadein = True
								story_text_alpha = 0
								story_text_fully_visible = False
								# Spawn the lamp immediately after hourglass pickup (if prepared)
								try:
									if lamp_item_data is not None and not any(x.get('id') == 'lamp' for x in items) and 'lamp' not in collected_items:
										items.append(lamp_item_data)
										print('[DEBUG] Lamp spawned after hourglass pickup (right-click)')
								except Exception:
									pass
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
						if 'hourglass' in collected_items:
							print('[map01_scene DEBUG] player has hourglass - launching boss1')
							print(f"[DEBUG] door triggered; collected_items={collected_items}")
							# import here to avoid circular imports at module load time
							try:
								import main as main_mod
								boss_started = False
								# prefer run_boss_cli if present, fallback to legacy run_boss_test
								try:
									main_mod.run_boss_cli('hollow')
									boss_started = True
								except AttributeError:
									try:
										main_mod.run_boss_test('hollow')
										boss_started = True
									except Exception as e:
										print('[map01_scene DEBUG] failed to launch boss (fallback):', e)
								except Exception as e:
									print('[map01_scene DEBUG] failed to launch boss:', e)
								# if the boss actually started, exit the map immediately
								if boss_started:
									# return to avoid drawing to a closed display surface
									return
							except Exception as e:
								print('[map01_scene DEBUG] exception during boss launch:')
								traceback.print_exc()
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

		# Door arrow effect: minimalist white arrow pointing horizontally
		if show_door_shine:
			import math
			# Bobbing animation
			bob = 4 * math.sin(door_shine_timer * 4.0)
			map_center_x = map_pixel_w // 2
			# Group doors by left/right side and skip the uppermost (smallest top) on each side
			left_doors = [d for d in door_rects if d.centerx < map_center_x]
			right_doors = [d for d in door_rects if d.centerx >= map_center_x]
			skip_doors = []
			if left_doors:
				upper_left = min(left_doors, key=lambda r: r.top)
				skip_doors.append(upper_left)
			if right_doors:
				upper_right = min(right_doors, key=lambda r: r.top)
				skip_doors.append(upper_right)
			for d in door_rects:
				if d in skip_doors:
					continue
				# Move arrow down by one tile (map unit) to align with tile base
				cy = d.centery + (tile_h * scale_int)
				if d.centerx < map_center_x:
					# Left door: arrow on right, pointing left
					tip_x = d.right + 4 + bob
					p1 = (tip_x, cy)
					p2 = (tip_x + 8, cy - 6)
					p3 = (tip_x + 8, cy + 6)
				else:
					# Right door: arrow on left, pointing right
					tip_x = d.left - 4 - bob
					p1 = (tip_x, cy)
					p2 = (tip_x - 8, cy - 6)
					p3 = (tip_x - 8, cy + 6)
				pygame.draw.polygon(screen, (255, 255, 255), [p1, p2, p3])

		# 画面中央的半透明白色屏幕
		screen_w, screen_h = screen.get_size()
		rect_w, rect_h = 420, 320  # Wider popup (more horizontal) to fit image and text

		# Center overlay on the projected image (group.png/brush.png etc.)
		# If an image is present, center overlay on it; else, center on screen
		img_to_check = None
		if show_only_group_img and group_img:
			img_to_check = group_img
		elif show_brush_projection and brush_img:
			img_to_check = brush_img
		elif 0 <= current_img_idx < len(projected_imgs) and projected_imgs[current_img_idx]:
			img_to_check = projected_imgs[current_img_idx]

		vertical_offset = 40  # Move overlay down by 40 pixels
		if img_to_check:
			img_w, img_h = img_to_check.get_size()
			img_screen_x = (screen_w - img_w) // 2
			img_screen_y = (screen_h - img_h) // 2
			# Center overlay on the image, then move down
			rect_x = img_screen_x + (img_w - rect_w) // 2
			rect_y = img_screen_y + (img_h - rect_h) // 2 + vertical_offset
		else:
			# fallback: center on screen, then move down
			rect_x = (screen_w - rect_w) // 2
			rect_y = (screen_h - rect_h) // 2 + vertical_offset

		# 创建半透明白色surface
		overlay = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 0))  # Transparent base

		# Draw a lighter window with rounded corners and subtle border
		# Background (light neutral to contrast black edges)
		pygame.draw.rect(overlay, (245, 245, 250, 220), (0, 0, rect_w, rect_h), border_radius=12)
		# Border (soft gray)
		pygame.draw.rect(overlay, (120, 120, 130, 255), (0, 0, rect_w, rect_h), width=2, border_radius=12)

		# Update image_alpha for fade-in
		if image_fadein:
			image_alpha += int(image_fadein_speed * dt)
			if image_alpha >= 255:
				image_alpha = 255
				image_fadein = False

		# group.png和文字淡入/淡出控制
		group_img_alpha = image_alpha
		if show_only_group_img:
			group_img_show_timer += dt
			# 5秒后进入淡出
			if not group_img_fadeout and group_img_show_timer >= 5.0:
				group_img_fadeout = True
				group_img_fadeout_progress = 0.0
			# 淡出阶段，alpha逐渐减小
			if group_img_fadeout:
				group_img_fadeout_progress += dt
				fade = max(0.0, 1.0 - group_img_fadeout_progress / group_img_fadeout_time)
				group_img_alpha = int(image_alpha * fade)
				# Also fade the overlay background
				# For fadeout, we redraw the window with reduced alpha
				overlay.fill((0, 0, 0, 0))
				alpha_val = int(230 * fade)
				border_alpha = int(255 * fade)
				if alpha_val > 0:
					# Draw background with fade (lighter)
					bg_surf = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
					pygame.draw.rect(bg_surf, (245, 245, 250, alpha_val), (0, 0, rect_w, rect_h), border_radius=12)
					overlay.blit(bg_surf, (0, 0))
					# Draw border with fade (soft gray)
					border_surf = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
					pygame.draw.rect(border_surf, (120, 120, 130, border_alpha), (0, 0, rect_w, rect_h), width=2, border_radius=12)
					overlay.blit(border_surf, (0, 0))
				
				if group_img_fadeout_progress >= group_img_fadeout_time:
					group_img_alpha = 0
					show_only_group_img = False  # 完全消失后关闭group.png和文字
					current_img_idx = -1 # Reset to no image
					image_alpha = 0 # Reset alpha
					# Mark that the group story window completed its show+fade cycle
					group_story_completed = True
					print('[DEBUG] group_story_completed set')

		# 只显示group.png图片，不再切换
		if show_only_group_img:
			img = group_img
		else:
			img = projected_imgs[current_img_idx] if 0 <= current_img_idx < len(projected_imgs) else None

		if img:
			img_w, img_h = img.get_size()
			img_x = (rect_w - img_w) // 2
			img_y = 20 # Shifted up to make room for text
			# 创建带alpha的副本
			img_copy = img.copy()
			# group.png淡出时用group_img_alpha，否则用image_alpha
			img_copy.set_alpha(group_img_alpha if show_only_group_img else image_alpha)
			overlay.blit(img_copy, (img_x, img_y))
			
			# Only draw the overlay if there is an image to show
			screen.blit(overlay, (rect_x, rect_y))

		# 沙漏拾取后禁用T键切换
		if show_only_group_img:
			current_img_idx = img_names.index('group.png') if 'group.png' in img_names else 0


		# 把overlay贴到主屏幕中央
		# screen.blit(overlay, (rect_x, rect_y)) # Moved inside 'if img:' block

		# --- Brush projection after lamp is picked up ---
		# Fade in for 1.2s, hold for 5s, then fade out for 1.5s
		brush_fadeout_time = 1.5
		if show_brush_projection:
			brush_proj_timer += dt
			# Fade in
			if brush_img and brush_proj_timer <= 5.0:
				if brush_img_alpha < 255:
					brush_img_alpha += int(255 * dt / 1.2)
					if brush_img_alpha > 255:
						brush_img_alpha = 255
				brush_alpha_to_use = brush_img_alpha
			# Fade out
			elif brush_img and 5.0 < brush_proj_timer <= 5.0 + brush_fadeout_time:
				fade_progress = (brush_proj_timer - 5.0) / brush_fadeout_time
				brush_alpha_to_use = int(255 * (1.0 - fade_progress))
				if brush_alpha_to_use < 0:
					brush_alpha_to_use = 0
			else:
				brush_alpha_to_use = 0

			# Draw only if alpha > 0
			if brush_img and brush_alpha_to_use > 0:
				overlay.fill((0, 0, 0, 0)) # Clear/reset overlay
				# Draw lighter window background for better contrast with black edges
				pygame.draw.rect(overlay, (245, 245, 250, 220), (0, 0, rect_w, rect_h), border_radius=12)
				pygame.draw.rect(overlay, (120, 120, 130, 255), (0, 0, rect_w, rect_h), width=2, border_radius=12)
				
				img = brush_img.copy()
				img.set_alpha(brush_alpha_to_use)
				img_x = (rect_w - img.get_width()) // 2
				img_y = 20
				overlay.blit(img, (img_x, img_y))
				screen.blit(overlay, (rect_x, rect_y))

				# Draw text below the brush, with same alpha
				text_lines = ["To dwell in the light,", "with a brush, with a truth"]
				font = pygame.font.Font(os.path.join(ROOT, 'assets', 'Silver.ttf'), 22) if os.path.exists(os.path.join(ROOT, 'assets', 'Silver.ttf')) else pygame.font.SysFont('consolas', 22)
				total_height = 0
				text_surfs = []
				for line in text_lines:
					surf = font.render(line, True, (40, 40, 40))
					surf_alpha = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
					surf_alpha.blit(surf, (0, 0))
					surf_alpha.set_alpha(brush_alpha_to_use)
					text_surfs.append(surf_alpha)
					total_height += surf.get_height()
				spacing = 6
				y = rect_y + 230
				for surf in text_surfs:
					x = (screen_w - surf.get_width()) // 2
					screen.blit(surf, (x, y))
					y += surf.get_height() + spacing

			# After fadeout, stop showing brush and text
			if brush_proj_timer > 5.0 + brush_fadeout_time:
				show_brush_projection = False
				show_121_img = True
				# Mark that the brush story window completed
				brush_story_completed = True
				print('[DEBUG] brush_story_completed set')

		# --- Show 1-2-1.png after brush projection ---
		if show_121_img:
			try:
				img_121_path = os.path.join(ROOT, 'assets', '1-2-1.png')
				if os.path.exists(img_121_path):
					img_121 = pygame.image.load(img_121_path).convert_alpha()
					img_121 = pygame.transform.smoothscale(img_121, (80, 80))

					if not img_121_clicked:
						# Draw offset to right to avoid overlap
						img_x = rect_x + (rect_w // 2) + 20
						img_y = rect_y + (rect_h - 80) // 2
						img_121_pos = (img_x, img_y)
						screen.blit(img_121, img_121_pos)
						# Draw 'click' prompt
						prompt_font2 = pygame.font.Font(os.path.join(ROOT, 'assets', 'Silver.ttf'), 16) if os.path.exists(os.path.join(ROOT, 'assets', 'Silver.ttf')) else pygame.font.SysFont('consolas', 16)
						prompt_text2 = 'click-drag'
						prompt_surf2 = prompt_font2.render(prompt_text2, True, (255, 255, 255))
						prompt_bg2 = pygame.Surface((prompt_surf2.get_width()+6, prompt_surf2.get_height()+2), pygame.SRCALPHA)
						prompt_bg2.fill((0,0,0,180))
						prompt_bg2.blit(prompt_surf2, (3,1))
						prompt_x2 = img_x + 80 - prompt_bg2.get_width() + 8
						prompt_y2 = img_y - prompt_bg2.get_height() - 4
						screen.blit(prompt_bg2, (prompt_x2, prompt_y2))
						# Mouse click detection (left button)
						# Mouse click is handled in the event loop to avoid click->instant-lock
					else:
						# Draw gears first, then 1-2-1.png on top
						if img_121_pos is None:
							margin = 16
							img_121_pos = (screen.get_width() - 80 - margin, screen.get_height() - 80 - margin)
						# Draw 1-2-1.png on top
						screen.blit(img_121, img_121_pos)
			except Exception:
				pass

		# --- Show gear target zones after story windows shown ---
		# Show holes as soon as both story windows have completed, so the player
		# can drag the gears into them afterwards.
		if group_story_completed and brush_story_completed:
			if not show_gear_targets:
				show_gear_targets = True
				print('[DEBUG] show_gear_targets set -> drawing holes')
				# Calculate two positions centered horizontally, spaced apart
				sw, sh = screen.get_size()
				cx = sw // 2
				cy = sh // 2
				offset = 140
				gear_target_positions = [
					(cx - offset, cy),
					(cx + offset, cy)
				]
			# Draw gear targets above background, below draggable gears
			for pos in gear_target_positions:
				draw_gear(screen, pos, gear_target_radius, teeth=gear_target_teeth, color=gear_target_color)

			# Draw 1-2-1.png gear sprite above gray zones (if acquired)
			try:
				img_121_path = os.path.join(ROOT, 'assets', '1-2-1.png')
				if os.path.exists(img_121_path):
					img_121 = pygame.image.load(img_121_path).convert_alpha()
					img_121 = pygame.transform.smoothscale(img_121, (80, 80))
					if img_121_pos is None:
						margin = 16
						img_121_pos = (screen.get_width() - 80 - margin, screen.get_height() - 80 - margin)
					screen.blit(img_121, img_121_pos)
			except Exception:
				pass


		# 沙漏拾取后，在幕布下方显示指定文字，并支持淡出

		# Update door shine state and timer: show when both gears locked
		if gear_111_locked and gear_121_locked and show_gear_targets:
			show_door_shine = True
		else:
			show_door_shine = False
		door_shine_timer += dt
		# wrap timer
		if door_shine_timer > door_shine_period:
			door_shine_timer -= door_shine_period
		# Show story text if group.png is visible or fading
		if show_only_group_img or (group_img_fadeout and group_img_alpha > 0):
			font = None
			try:
				font = pygame.font.Font(os.path.join(ROOT, 'assets', 'Silver.ttf'), 22)
			except Exception:
				font = pygame.font.SysFont('consolas', 22)
			# Update text alpha based on fadein/fadeout
			if story_text_fadein and not story_text_fully_visible:
				story_text_alpha += int(255 * dt / 1.2)
				if story_text_alpha >= 255:
					story_text_alpha = 255
					story_text_fadein = False
					story_text_fully_visible = True
			if group_img_fadeout:
				story_text_alpha = group_img_alpha # Sync text fadeout with image
			if story_text_alpha > 0:
				total_height = 0
				text_surfs = []
				for line in story_text_lines:
					surf = font.render(line, True, (40, 40, 40))
					# Create alpha surface
					surf_alpha = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
					surf_alpha.blit(surf, (0, 0))
					surf_alpha.set_alpha(story_text_alpha)
					text_surfs.append(surf_alpha)
					total_height += surf.get_height()
				# Position: inside the white overlay, below the image
				spacing = 6
				y = rect_y + 230 # Positioned below the image (which ends at 220)
				for surf in text_surfs:
					x = (screen_w - surf.get_width()) // 2
					screen.blit(surf, (x, y))
					y += surf.get_height() + spacing

		# Show 1-1-1.png after group.png fades out
		if group_img_fadeout and group_img_alpha == 0:
			try:
				reward_img_path = os.path.join(ROOT, 'assets', '1-1-1.png')
				if os.path.exists(reward_img_path):
					reward_img = pygame.image.load(reward_img_path).convert_alpha()
					reward_img = pygame.transform.smoothscale(reward_img, (80, 80))
					if not reward_img_clicked:
						# Draw offset to left to avoid overlap
						img_w, img_h = reward_img.get_size()
						img_x = rect_x + (rect_w // 2) - img_w - 20
						img_y = rect_y + (rect_h - img_h) // 2
						reward_img_pos = (img_x, img_y)
						screen.blit(reward_img, reward_img_pos)
						# Draw 'click' prompt
						prompt_font2 = pygame.font.Font(os.path.join(ROOT, 'assets', 'Silver.ttf'), 16) if os.path.exists(os.path.join(ROOT, 'assets', 'Silver.ttf')) else pygame.font.SysFont('consolas', 16)
						prompt_text2 = 'click-drag'
						prompt_surf2 = prompt_font2.render(prompt_text2, True, (255, 255, 255))
						prompt_bg2 = pygame.Surface((prompt_surf2.get_width()+6, prompt_surf2.get_height()+2), pygame.SRCALPHA)
						prompt_bg2.fill((0,0,0,180))
						prompt_bg2.blit(prompt_surf2, (3,1))
						prompt_x2 = img_x + img_w - prompt_bg2.get_width() + 8
						prompt_y2 = img_y - prompt_bg2.get_height() - 4
						screen.blit(prompt_bg2, (prompt_x2, prompt_y2))
						# Mouse click detection (left button)
						# Mouse click is handled in the event loop to avoid click->instant-lock
					else:
						# Draggable: draw at current position
						if reward_img_pos is None:
							margin = 16
							reward_img_pos = (margin, screen.get_height() - reward_img.get_height() - margin)
						# If locked, draw at target
						if gear_111_locked and show_gear_targets and len(gear_target_positions) == 2:
							reward_img_pos = (gear_target_positions[0][0] - 40, gear_target_positions[0][1] - 40)
						screen.blit(reward_img, reward_img_pos)
			except Exception:
				pass

		# debug overlays removed so collision tiles are visible
		# (platform and door debug rectangles were here and have been disabled)


		# Add lamp to items only after reward_img_clicked is True
		if lamp_item_data is not None and reward_img_clicked and not any(it.get('id') == 'lamp' for it in items):
			items.append(lamp_item_data)

		# draw items, skip lamp if already collected
		for it in items:
			if it.get('id') == 'lamp' and 'lamp' in collected_items:
				continue
			try:
				screen.blit(it['sprite'], (it['rect'].x, it['rect'].y))
			except Exception:
				pygame.draw.rect(screen, (200, 180, 60), it['rect'])

		# Show 'Check (C)' prompt above hourglass if player is near and reward_img_clicked is False
		# Show 'Check (C)' prompt above lamp if player is near and reward_img_clicked is True
		prompt_font = None
		try:
			prompt_font = pygame.font.Font(os.path.join(ROOT, 'assets', 'Silver.ttf'), 18)
		except Exception:
			prompt_font = pygame.font.SysFont('consolas', 18)

		for it in items:
			# skip lamp prompt if lamp is collected
			if it.get('id') == 'lamp' and 'lamp' in collected_items:
				continue
			show_prompt = False
			if it.get('id') == 'hourglass':
				if reward_img_clicked:
					show_prompt = False
				else:
					show_prompt = True
			elif it.get('id') == 'lamp':
				if reward_img_clicked:
					show_prompt = True
				else:
					show_prompt = False
			if show_prompt:
				px = int(player.x + player.cw // 2)
				py = int(player.y + player.ch // 2)
				from math import hypot
				dist = hypot(px - it['rect'].centerx, py - it['rect'].centery)
				if dist < max(tile_w * 6, 160):
					prompt_text = 'Check'
					prompt_surf = prompt_font.render(prompt_text, True, (255, 255, 255))
					prompt_bg = pygame.Surface((prompt_surf.get_width()+8, prompt_surf.get_height()+4), pygame.SRCALPHA)
					prompt_bg.fill((0,0,0,180))
					prompt_bg.blit(prompt_surf, (4,2))
					prompt_x = it['rect'].centerx - prompt_bg.get_width()//2
					# Move the lamp's prompt down by 18 pixels if it's the lamp
					if it.get('id') == 'lamp':
						prompt_y = it['rect'].top - prompt_bg.get_height() - 8 + 18
					else:
						prompt_y = it['rect'].top - prompt_bg.get_height() - 8
					screen.blit(prompt_bg, (prompt_x, prompt_y))

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

		# draw speech bubble if present
		try:
			if dialog:
				dialog.draw(screen)
		except Exception:
			pass

		pygame.display.flip()

	return

if __name__ == '__main__':
	import pygame
	import globals as g
	pygame.init()
	screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
	run(screen)
	pygame.quit()
