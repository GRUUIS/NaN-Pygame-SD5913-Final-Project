# Mind's Maze - Psychological 2D Platformer

**Mind's Maze** is a 2D pixel art puzzle-platformer exploring psychological themes through metaphorical boss battles. 

It is developed by Team NaN. In programming, NotaNumber/NaN represents an undefined or unrepresentable value; in our project, this concept becomes a metaphor for the moments in life when our sense of self feels undefined, inconsistent, or lost. Mind’s Maze uses this idea as its narrative backbone—each level reflects cognitive states where clarity breaks down, and each boss symbolizes a psychological pattern that disrupts meaning or direction.

## Game Concept

Players control a puppet figure representing "neglected self-awareness" within a chaotic mind landscape. The game features metaphorical boss battles representing common psychological obstacles:

1.  **The First Attack**: Player couldn't react but being defeated by the hollow.
2.  **The Sloth**: A zoning-heavy battle representing procrastination, featuring persistent slime trails and area denial.
3.  **The Hollow**: A survival battle against Nihilism, featuring "Void Shards" and "Voidfire" mechanics.

## Project Structure

```
Mind's-Maze/
├── assets/                # Game resources (sprites, audio, maps)
├── config/                # Configuration files
├── src/                   # Source code
│   ├── entities/          # Player, bosses, platforms
│   ├── scenes/            # Game scenes (Menu, Gameplay, Bosses, Puzzles)
│   ├── systems/           # Core systems (Physics, Audio)
│   └── utils/             # Utilities (Logger, State Machine)
├── testing/               # Test scripts and flow managers
├── globals.py             # Global constants and configuration
└── main.py                # Main entry point
```
Key scenes and prototypes (non-exhaustive):
- `src/scenes/menu_scene.py`: Start menu; routes to `GameplayScene`.
- `src/scenes/gameplay_scene.py`: Core gameplay placeholder (integrates later systems).
- `src/scenes/game_over_scene.py`: End screen scaffold for loop completion.
- `src/scenes/boss1_scripted_scene.py`: Intro/Boss1 Hollow ambush (cinematic defeat; Space to continue).
- `src/scenes/third_puzzle_scene.py`: Top-down room puzzle scene (used by demo below).
- `testing/first_dream_puzzle.py`: Yume Nikki-style multi-puzzle prototype (4 puzzles + effects).
- `testing/third_puzzle_demo.py`: Minimal runner for the third puzzle scene.
- `testing/run_map.py`: Tiled map viewer with scaling and optional physics.
- `testing/game_flow_manager.py`: Prototype flow: menu → puzzle → dream transition → combat.

## Installation

1.  **Prerequisites**: Python 3.x
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## How to Play

### Run the Game
game_flow_manager.py

### Boss Battle Test Modes
You can directly test specific boss encounters:

```bash
# Intro/Boss1: The First Attack (Hollow ambush)
python main.py boss1
python main.py intro

# Boss 2: The Sloth (Procrastination)
python main.py boss2

# Boss 3: The Hollow (Nihilism)
python main.py boss3
```

### Controls
- **WASD**: Move
- **Space**: Jump
- **Mouse**: Aim & Shoot
- **R**: Reset (during battle in Boss Test Mode)
- **Space (Game Over)**: Continue (Boss Test Mode)

### Puzzle Prototypes & Tools
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

