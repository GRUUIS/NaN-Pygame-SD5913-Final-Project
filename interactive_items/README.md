# Map01 Scene (map01_scene.py)

## Overview
This module implements a playable scene for a 2D platformer game using Pygame. It loads a map (Room1) from the assets, sets up platforms, doors, and interactive items, and manages a sequence of visual and interactive effects. The scene is designed for testing tile collisions, door teleporting, and scripted item-based interactions.

## Key Features
- Loads and renders a tiled map from the assets directory.
- Places interactive items (hourglass, lamp, brush, etc.) on platforms.
- Handles player movement, collision, and respawn logic.
- Implements a sequence of visual effects and overlays:
  - White translucent overlay for special events.
  - Fading in/out of images and text.
  - Interactive item prompts and click-based transitions.
- Manages a scripted sequence:
  1. Player picks up the hourglass, triggering a projection overlay with group.png and text.
  2. After the projection, 1-1-1.png appears, is clickable, and moves to the bottom left after click.
  3. Lamp appears and can be picked up, triggering a brush projection with brush.png and text.
  4. After the brush event, 1-2-1.png appears, is clickable, and moves to the bottom right after click.
- Prompts and overlays guide the player through the sequence.

## How to Use
- Run the scene as part of the main game or as a standalone test.
- Use the keyboard and mouse to interact with items as prompted.
- The code is self-contained and manages its own state and assets.

## File Location
- `map01_scene.py` (this directory)

## Requirements
- Python 3.x
- Pygame
- Assets in the expected directory structure (see project root)

## Note
This scene is intended for demonstration, testing, and as a template for more complex scripted interactions in Pygame-based games.
