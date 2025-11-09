from PIL import Image
import os
paths=[r'assets/art/tileset_corridor_wall.png', r'assets/art/tileset_corridor_floor.png']
for p in paths:
    if os.path.exists(p):
        try:
            im=Image.open(p)
            w,h=im.size
            print(f"{p}: {w}x{h}")
        except Exception as e:
            print(f"{p}: ERROR open - {e}")
    else:
        print(f"{p}: NOT FOUND")
