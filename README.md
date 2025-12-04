# Mind's Maze - Psychological 2D Platformer

**Mind's Maze** is a 2D pixel art puzzle-platformer exploring psychological themes through metaphorical boss battles. 

It is developed by Team NaN. In programming, NotaNumber/NaN represents an undefined or unrepresentable value; in our project, this concept becomes a metaphor for the moments in life when our sense of self feels undefined, inconsistent, or lost. Mind’s Maze uses this idea as its narrative backbone—each level reflects cognitive states where clarity breaks down, and each boss symbolizes a psychological pattern that disrupts meaning or direction.

## Game Concept
 The game progresses through 10 integrated scenes, combining puzzle-solving with metaphorical boss battles:

1. **Menu Scene**: Main menu with settings (volume control, developer mode toggle)
2. **Puzzle Scene**: Top-down exploration requiring collection of 3 items to unlock exit door
3. **Dream Puzzle**: Yume Nikki-inspired surreal puzzle world with 4 sub-puzzles and effects
4. **Dream Transition**: Narrative transformation scene 
5. **Boss1 - The First Attack**: Scripted cinematic defeat by The Hollow (unavoidable ambush)
6. **Map01 Exploration**: Side-scrolling platformer exploration level
7. **Mirror Room Puzzle**: Environmental puzzle involving reflections
8. **Boss2 - The Sloth**: Procrastination battle with slime trails and area denial mechanics
9. **Painting Room Puzzle**: Art-themed environmental puzzle *(placeholder)*
10. **Boss3 - The Hollow**: Final survival battle against Nihilism with Void Shards and Voidfire

## Project Structure

```
Mind's-Maze/
├── assets/                    # Game resources
│   ├── backgrounds/           # Scene backgrounds  
│   ├── sfx/                   # Sound effects and music
│   ├── sprites/               # Character and enemy sprites
│   ├── tilemaps/              # Tiled map files (.tmj, .tsx)
│   └── 8Direction_TopDown.../  # Character sprite sheets
├── combine/                   # Menu system
│   └── meun.py                # Main menu implementation
├── config/                    # Configuration files
│   └── settings.py            # Game settings
├── src/                       # Core source code
│   ├── entities/              # Game entities
│   │   ├── player.py          # Player character (platformer + top-down)
│   │   ├── boss_the_hollow.py # Boss3 AI and state machine
│   │   ├── boss_sloth.py      # Boss2 AI and mechanics
│   │   ├── boss_battle_scene.py  # Boss3 battle scene
│   │   ├── sloth_battle_scene.py # Boss2 battle scene  
│   │   ├── bullets.py         # Bullet/projectile system
│   │   └── platform.py        # Platform physics
│   ├── scenes/                # Scene management
│   │   ├── base_scene.py      # Scene base class
│   │   ├── boss1_scripted_scene.py # Boss1 intro encounter
│   │   └── map01_scene.py     # Map01 exploration
│   ├── systems/               # Core game systems
│   │   └── ui.py              # HUD, health bars, dialogue boxes
│   └── utils/                 # Utilities
│       ├── logger.py          # Logging system
│       └── font.py            # Font management
├── testing/                   # Scene implementations
│   ├── game_flow_manager.py   # **Main game flow controller (10 scenes)**
│   ├── first_dream_puzzle.py  # Dream puzzle scene
│   ├── dream_transition_scene.py # Transformation scene
│   ├── map01_final.py         # Map exploration
│   ├── mirror_room_puzzle.py  # Mirror puzzle
│   └── painting_room_puzzle.py # Painting puzzle (placeholder)
├── globals.py                 # Global constants and configuration
└── main.py                    # Entry point + boss test modes

## Installation

1.  **Prerequisites**: Python 3.x
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## How to Play

### Run the Game
main.py

### Boss Battle Test Modes
You can directly test specific boss encounters:

```bash
# Intro/Boss1: The First Attack (Hollow ambush)
python main.py boss1

# Boss 2: The Sloth (Procrastination)
python main.py boss2

# Boss 3: The Hollow (Nihilism)
python main.py boss3
```

### Controls
- **WASD**: Move
- **W**: Jump (double jump available in boss battles)
- **Mouse**: Aim direction
- **Left Click**: Shoot (bullet type varies by boss)
- **R**: Restart (on defeat)d
- **SPACE**: Continue (on victory)



https://github.com/user-attachments/assets/8342c2e7-798e-4933-a2a0-3b14df6ebc09

## Game Flow Summary

The complete gameplay experience follows this progression:

1. **Menu** → Settings available (volume, developer mode)
2. **Puzzle Scene** → Collect 3 items, unlock door
3. **Dream Puzzle** → Complete 4 surreal mini-puzzles
4. **Dream Transition** → Narrative transformation
5. **Boss1 (Scripted)** → Unavoidable defeat by The Hollow
6. **Map01** → Side-scrolling exploration
7. **Mirror Room** → Reflection puzzle
8. **Boss2 (The Sloth)** → Combat with slime mechanics
9. **Painting Room** → Art puzzle *(placeholder)*
10. **Boss3 (The Hollow)** → Final boss battle

Press **Z** (when Developer Mode is enabled) to skip any scene.

### Individual Scene Tests
- Yume Nikki-style puzzle scene:
    ```bash
    python testing/first_dream_puzzle.py
    ```
    Notes: WASD/Arrows move; Space/Enter interact when prompted; onscreen hints included.

- Third Puzzle demo (top-down room, interactables):
    ```bash
    python testing/third_puzzle_demo.py
    ```

- Tiled map viewer (scales to window; optional Pymunk integration):
    ```bash
    python testing/run_map.py
    ```
    Controls: WASD pan, F fullscreen, ESC quit. Edit the `map_path` in-file to load other TMJ maps.

## Credits & Attribution

### Team NaN
- **Structure Developer**: Main loop, scene management
- **Combat Systems Developer**: Boss behaviors, combat mechanics
- **Visual & UI Developer**: Map creation, camera, UI
- **Content & Asset Integration**: Assets, narrative, dialogue

### Third-Party Assets
- **Map / Tileset**: [Cozy Room Library](https://rolff.itch.io/cozy-room-library-tilemap-16x16) by Rolff
- **Character Pack**: [Witches Pack](https://9e0.itch.io/witches-pack) by 9E0
- **Icon Pack**: [RPG IAB Icon Pack](https://zeromatrix.itch.io/rpgiab-icons) by ZeroMatrix
- **UI Styles**: [Complete UI Book Styles Pack](https://crusenho.itch.io/complete-ui-book-styles-pack) by Crusenho
- **Music**: [Essential Game Music Pack](https://bellkalengar.itch.io/essential-game-music-pack) by Bell Kalengar
- **Sound Effects**: OpenGameArt.org (Space Shoot Sounds, Spiritwatcher, Lurid Delusion)

### Libraries
- **PyTMX**: Map loading (MIT License)
- **Custom Sprite Loader**: Mask-based sprite strip slicing and animation (MIT)
 - **Pymunk**: Physics (optional; used in prototypes)

