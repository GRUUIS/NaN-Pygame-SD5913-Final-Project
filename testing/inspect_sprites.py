#!/usr/bin/env python3
"""
Inspect sprite-sheet PNGs and try to detect frame boxes.
Saves annotated images named inspect_<orig>.png next to each sprite.
"""
from PIL import Image, ImageDraw
import os
import sys

SPRITE_DIR = os.path.join(os.path.dirname(__file__), 'Blue_witch')
OUT_PREFIX = 'inspect_'


def load_mask(im):
    # return 2D list of booleans (h rows of w columns) where True == non-transparent
    im = im.convert('RGBA')
    w, h = im.size
    a = im.split()[-1]
    pixels = a.load()
    mask = [[pixels[x, y] > 0 for x in range(w)] for y in range(h)]
    return mask


def find_separator_ranges(sum_line):
    # Given a list of ints (sum per col/row), find contiguous ranges where sum>0
    ranges = []
    w = len(sum_line)
    i = 0
    while i < w:
        # skip zeros
        while i < w and sum_line[i] == 0:
            i += 1
        if i >= w:
            break
        start = i
        while i < w and sum_line[i] > 0:
            i += 1
        end = i  # exclusive
        ranges.append((start, end))
    return ranges


def detect_grid(mask):
    # mask: list of rows [[bool]] length h each of length w
    h = len(mask)
    w = len(mask[0]) if h else 0
    # compute column sums and row sums
    col_sums = [0] * w
    row_sums = [0] * h
    for y in range(h):
        row = mask[y]
        s = 0
        for x in range(w):
            if row[x]:
                col_sums[x] += 1
                s += 1
        row_sums[y] = s

    vertical_ranges = find_separator_ranges(col_sums)
    horizontal_ranges = find_separator_ranges(row_sums)

    # If there are multiple vertical and horizontal ranges, treat as grid
    if len(vertical_ranges) >= 2 or len(horizontal_ranges) >= 2:
        # Each cell is intersection of vertical_range x horizontal_range
        cells = []
        for vr in vertical_ranges:
            for hr in horizontal_ranges:
                x0, x1 = vr
                y0, y1 = hr
                cells.append((x0, y0, x1, y1))
        return cells
    return None


def connected_components(mask):
    h = len(mask)
    w = len(mask[0]) if h else 0
    visited = [[False]*w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if mask[y][x] and not visited[y][x]:
                # flood fill
                minx, miny, maxx, maxy = x, y, x, y
                stack = [(x,y)]
                visited[y][x] = True
                while stack:
                    cx, cy = stack.pop()
                    if cx < minx: minx = cx
                    if cy < miny: miny = cy
                    if cx > maxx: maxx = cx
                    if cy > maxy: maxy = cy
                    for nx, ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                        if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and mask[ny][nx]:
                            visited[ny][nx] = True
                            stack.append((nx, ny))
                # convert maxx,maxy to exclusive coordinates
                comps.append((minx, miny, maxx+1, maxy+1))
    return comps


def annotate_and_save(im, boxes, outpath):
    draw = ImageDraw.Draw(im, 'RGBA')
    colors = [(255,0,0,120), (0,255,0,120), (0,0,255,120), (255,255,0,120)]
    for i, box in enumerate(boxes):
        x0,y0,x1,y1 = box
        draw.rectangle([x0,y0,x1,y1], outline=(255,255,255,200), width=1)
        draw.rectangle([x0,y0,x1,y1], fill=colors[i%len(colors)])
    im.save(outpath)


def main():
    if not os.path.isdir(SPRITE_DIR):
        print('Sprite folder not found:', SPRITE_DIR)
        return 1
    files = [f for f in sorted(os.listdir(SPRITE_DIR)) if f.lower().endswith('.png')]
    if not files:
        print('No png files found in', SPRITE_DIR)
        return 1
    summary = []
    for fn in files:
        path = os.path.join(SPRITE_DIR, fn)
        try:
            im = Image.open(path)
        except Exception as e:
            print('Failed to open', fn, '->', e)
            continue
        w,h = im.size
        print(f'File: {fn} size={w}x{h}')
        mask = load_mask(im)
        cells = detect_grid(mask)
        if cells:
            print('  Detected grid-like layout: cells=', len(cells))
            boxes = cells
        else:
            comps = connected_components(mask)
            print('  Connected components detected:', len(comps))
            # Filter tiny components (noise)
            comps = [c for c in comps if (c[2]-c[0])>2 and (c[3]-c[1])>2]
            boxes = comps
        # Sort boxes left-to-right, top-to-bottom
        boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
        print('  Frames:')
        for i,b in enumerate(boxes):
            print(f'    {i}: {b} size={(b[2]-b[0])}x{(b[3]-b[1])}')
        # Save annotated image
        outname = OUT_PREFIX + fn
        outpath = os.path.join(SPRITE_DIR, outname)
        try:
            annotate_and_save(im.convert('RGBA'), boxes, outpath)
            print('  Wrote annotated image to', outname)
        except Exception as e:
            print('  Failed to write annotation for', fn, '->', e)
        summary.append((fn, w, h, len(boxes)))
    print('\nSummary:')
    for fn,w,h,count in summary:
        print(f'  {fn}: {w}x{h}, frames={count}')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except ImportError:
        print('Pillow is required. Install with: pip install pillow')
        raise
