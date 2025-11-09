import os
import pygame

def inspect(path):
    print(f"-- {path} --")
    if not os.path.exists(path):
        print("MISSING")
        return
    try:
        img = pygame.image.load(path)
        w,h = img.get_width(), img.get_height()
        print(f"size: {w}x{h}")
        candidates = []
        for s in (64,32,24,16,8):
            if w % s == 0 and h % s == 0:
                candidates.append(s)
        if candidates:
            print("possible tile sizes:", candidates)
            for s in candidates:
                cols = w // s
                rows = h // s
                print(f" tile {s}x{s} -> cols={cols}, rows={rows}")
        else:
            # fallback: gcd
            from math import gcd
            g = gcd(w,h)
            print(f"no clean divisions by common sizes; gcd(w,h)={g}")
            if g>1:
                cols = w//g
                rows = h//g
                print(f" fallback tile {g}x{g} -> cols={cols}, rows={rows}")
    except Exception as e:
        print("error loading:", e)

def main():
    pygame.init()
    base = os.path.join('assets','art')
    wall = os.path.join(base, 'tileset_corridor_wall.png')
    floor = os.path.join(base, 'tileset_corridor_floor.png')
    inspect(wall)
    print()
    inspect(floor)
    pygame.quit()

if __name__ == '__main__':
    main()
