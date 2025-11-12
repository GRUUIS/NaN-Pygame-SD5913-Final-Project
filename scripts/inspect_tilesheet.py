import os
import json
import pygame

TMJ = 'assets/tilemaps/test puzzle scene.tmj'
IMG = 'assets/tilemaps/test scene2.png'

pygame.init()
print('cwd:', os.getcwd())

if not os.path.exists(IMG):
    print('Image not found:', IMG)
else:
    try:
        surf = pygame.image.load(IMG)
        w,h = surf.get_width(), surf.get_height()
        print('Image size:', w, 'x', h)
    except Exception as e:
        print('Failed to load image:', e)

if not os.path.exists(TMJ):
    print('TMJ not found:', TMJ)
else:
    with open(TMJ, 'r', encoding='utf-8') as f:
        m = json.load(f)
    tile_w = m.get('tilewidth', 16)
    tile_h = m.get('tileheight', 16)
    map_w = m.get('width', 0) * tile_w
    map_h = m.get('height', 0) * tile_h
    print('TMJ map pixel size:', map_w, 'x', map_h)

print('Done')
