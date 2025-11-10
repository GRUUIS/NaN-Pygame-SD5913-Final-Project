import json
import os
import glob
import xml.etree.ElementTree as ET
from pathlib import Path
import pygame


def _find_image_path(image_source, tsx_dir, map_dir):
    # Try several candidate locations for the image referenced by a .tsx
    candidates = []
    # If image_source is absolute, try it directly
    if os.path.isabs(image_source):
        candidates.append(image_source)
    # Relative to the tsx file
    candidates.append(os.path.normpath(os.path.join(tsx_dir, image_source)))
    # Relative to the map file
    candidates.append(os.path.normpath(os.path.join(map_dir, image_source)))
    # Just the basename under map_dir or workspace
    candidates.append(os.path.normpath(os.path.join(map_dir, os.path.basename(image_source))))
    # Search workspace for filename
    basename = os.path.basename(image_source)
    for p in glob.iglob(f"**/{basename}", recursive=True):
        candidates.append(os.path.abspath(p))

    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def load_map(map_json_path):
    """Load a Tiled JSON (.tmj) map and its tileset images.

    Returns a tuple: (map_dict, tiles_by_gid)
    - map_dict: the parsed JSON map (python dict)
    - tiles_by_gid: dict mapping gid (int) -> pygame.Surface
    """
    map_json_path = os.path.abspath(map_json_path)
    map_dir = os.path.dirname(map_json_path)

    with open(map_json_path, "r", encoding="utf-8") as f:
        m = json.load(f)

    # Build tiles_by_gid and tileset metadata
    tiles_by_gid = {}
    tileset_meta = {}

    for ts in m.get("tilesets", []):
        firstgid = ts.get("firstgid")
        source = ts.get("source")
        if not source:
            continue

        tsx_path = os.path.normpath(os.path.join(map_dir, source))
        if not os.path.exists(tsx_path):
            # try searching for source in workspace
            found = None
            for p in glob.iglob(f"**/{os.path.basename(source)}", recursive=True):
                found = p
                break
            if found:
                tsx_path = os.path.abspath(found)

        if not os.path.exists(tsx_path):
            print(f"Warning: tileset {source} not found for firstgid {firstgid}. Skipping.")
            continue

        tree = ET.parse(tsx_path)
        root = tree.getroot()
        tilewidth = int(root.attrib.get("tilewidth", m.get("tilewidth", 16)))
        tileheight = int(root.attrib.get("tileheight", m.get("tileheight", 16)))
        tilecount = int(root.attrib.get("tilecount", 0))
        columns = int(root.attrib.get("columns", 0))
        ts_name = root.attrib.get("name")
        tileset_meta[firstgid] = {
            "name": ts_name,
            "tilewidth": tilewidth,
            "tileheight": tileheight,
            "tilecount": tilecount,
            "columns": columns,
            "tsx_path": tsx_path,
        }

        image_elem = root.find("image")
        image_src = image_elem.attrib.get("source") if image_elem is not None else None

        img_path = None
        if image_src:
            img_path = _find_image_path(image_src, os.path.dirname(tsx_path), map_dir)

        if not img_path:
            print(f"Warning: image for tileset {source} (firstgid {firstgid}) not found (tried {image_src}). Using placeholders.")

        if img_path:
            try:
                img_surf = pygame.image.load(img_path).convert_alpha()
            except Exception as e:
                print(f"Failed to load image {img_path}: {e}")
                img_surf = None
        else:
            img_surf = None

        # If we have a tileset image, slice it
        if img_surf and columns > 0 and tilecount > 0:
            cols = columns
            rows = (tilecount + cols - 1) // cols
            for i in range(tilecount):
                local_id = i
                sx = (local_id % cols) * tilewidth
                sy = (local_id // cols) * tileheight
                try:
                    sub = img_surf.subsurface((sx, sy, tilewidth, tileheight)).copy()
                except Exception:
                    # create placeholder if slicing fails
                    sub = pygame.Surface((tilewidth, tileheight), pygame.SRCALPHA)
                    sub.fill((255, 0, 255, 255))
                tiles_by_gid[firstgid + i] = sub
        else:
            # No single-image tileset; try to load individual tile images (tile elements)
            tiles = root.findall("tile")
            for tile in tiles:
                id_attr = int(tile.attrib.get("id", 0))
                image = tile.find("image")
                if image is None:
                    # create placeholder
                    surf = pygame.Surface((tilewidth, tileheight), pygame.SRCALPHA)
                    surf.fill((255, 0, 255, 255))
                    tiles_by_gid[firstgid + id_attr] = surf
                    continue
                img_src2 = image.attrib.get("source")
                img_path2 = _find_image_path(img_src2, os.path.dirname(tsx_path), map_dir)
                if img_path2 and os.path.exists(img_path2):
                    try:
                        surf = pygame.image.load(img_path2).convert_alpha()
                    except Exception:
                        surf = pygame.Surface((tilewidth, tileheight), pygame.SRCALPHA)
                        surf.fill((255, 0, 255, 255))
                else:
                    surf = pygame.Surface((tilewidth, tileheight), pygame.SRCALPHA)
                    surf.fill((255, 0, 255, 255))
                tiles_by_gid[firstgid + id_attr] = surf

    return m, tiles_by_gid, tileset_meta


def get_tileset_for_gid(tileset_meta, gid):
    """Return tileset meta (firstgid, meta) for the tileset that contains gid, or (None, None)."""
    for firstgid in sorted(tileset_meta.keys(), reverse=True):
        meta = tileset_meta[firstgid]
        if gid >= firstgid and gid < firstgid + meta.get("tilecount", 0):
            return firstgid, meta
    return None, None


def extract_collision_rects(m, tileset_meta, collidable_gids=None, scale=1):
    """Return a list of pygame.Rect for tiles whose gid is in collidable_gids.

    If collidable_gids is None, returns empty list.
    Rects are in pixel coordinates (already scaled).
    """
    import pygame

    rects = []
    if not collidable_gids:
        return rects

    tile_w = m.get("tilewidth", 16)
    tile_h = m.get("tileheight", 16)
    width = m.get("width", 0)

    for layer in m.get("layers", []):
        if layer.get("type") != "tilelayer":
            continue
        data = layer.get("data", [])
        for idx, raw_gid in enumerate(data):
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0:
                continue
            if gid in collidable_gids:
                tx = idx % width
                ty = idx // width
                px = tx * tile_w * scale
                py = ty * tile_h * scale
                rects.append(pygame.Rect(px, py, tile_w * scale, tile_h * scale))
    return rects


def draw_map(surface, m, tiles_by_gid, camera_rect=None, scale=1):
    import pygame

    tile_w = m.get("tilewidth", 16)
    tile_h = m.get("tileheight", 16)
    width = m.get("width")
    height = m.get("height")

    layers = m.get("layers", [])

    # If we're scaling the whole map and no camera_rect is requested,
    # draw at native resolution then scale the final image once using
    # nearest-neighbour. This avoids per-tile rounding/seam artifacts
    # that produce thin black lines when scaling non-integer factors.
    if scale != 1 and camera_rect is None:
        nat_w = tile_w * width
        nat_h = tile_h * height
        nat_surf = pygame.Surface((nat_w, nat_h), pygame.SRCALPHA)

        for layer in layers:
            if not layer.get("visible", True):
                continue
            if layer.get("type") != "tilelayer":
                continue
            data = layer.get("data", [])
            for idx, raw_gid in enumerate(data):
                gid = raw_gid & 0x1FFFFFFF
                if gid == 0:
                    continue
                tx = idx % width
                ty = idx // width
                img = tiles_by_gid.get(gid)
                if img is None:
                    img = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
                    img.fill((255, 0, 255, 255))
                nat_surf.blit(img, (tx * tile_w, ty * tile_h))

        # Scale the full native surface to the requested size using
        # pygame.transform.scale (nearest-neighbour) to keep pixel art crisp
        target_w = max(1, int(nat_w * scale))
        target_h = max(1, int(nat_h * scale))
        try:
            scaled = pygame.transform.scale(nat_surf, (target_w, target_h))
        except Exception:
            # As a fallback, try smoothscale though for pixel art we prefer scale
            scaled = pygame.transform.smoothscale(nat_surf, (target_w, target_h))

        surface.blit(scaled, (0, 0))
        return

    # Fallback: per-tile drawing (used when a camera_rect is provided)
    scaled_cache = {}
    for layer in layers:
        if not layer.get("visible", True):
            continue
        if layer.get("type") != "tilelayer":
            continue
        data = layer.get("data", [])
        for idx, raw_gid in enumerate(data):
            # Mask out flip bits (Tiled uses high bits for flipping)
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0:
                continue
            tx = idx % width
            ty = idx // width
            img = tiles_by_gid.get(gid)
            if img is None:
                # draw a magenta placeholder for missing tiles
                img = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
                img.fill((255, 0, 255, 255))

            if scale != 1:
                target_w = max(1, int(tile_w * scale))
                target_h = max(1, int(tile_h * scale))
                cache_key = (gid, target_w, target_h)
                if cache_key in scaled_cache:
                    img2 = scaled_cache[cache_key]
                else:
                    img2 = pygame.transform.scale(img, (target_w, target_h))
                    scaled_cache[cache_key] = img2
            else:
                img2 = img

            px = tx * tile_w * scale
            py = ty * tile_h * scale
            if camera_rect:
                if not camera_rect.colliderect(pygame.Rect(px, py, tile_w * scale, tile_h * scale)):
                    continue
                surface.blit(img2, (px - camera_rect.x, py - camera_rect.y))
            else:
                surface.blit(img2, (px, py))

