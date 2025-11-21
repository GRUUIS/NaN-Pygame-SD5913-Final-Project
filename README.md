# Mind's Maze - Psychological 2D Platformer

**Mind's Maze** is a 2D pixel art puzzle-platformer exploring psychological themes through metaphorical boss battles. 

Developed by Team NaN. In programming, NaN represents an undefined or unrepresentable value; in our project, this concept becomes a metaphor for the moments in life when our sense of self feels undefined, inconsistent, or lost. Mind’s Maze uses this idea as its narrative backbone—each level reflects cognitive states where clarity breaks down, and each boss symbolizes a psychological pattern that disrupts meaning or direction.

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
│   ├── scenes/            # Game scenes (Menu, Gameplay, Bosses)
│   ├── systems/           # Core systems (Physics, Audio)
│   └── utils/             # Utilities (Logger, State Machine)
├── testing/               # Test scripts and flow managers
├── globals.py             # Global constants and configuration
└── main.py                # Main entry point
```

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
# Boss 2: The Sloth (Procrastination)
python main.py boss2

# Boss 3: The Hollow (Nihilism)
python main.py boss3
```

### Controls
- **WASD**: Move
- **Space**: Jump
- **Mouse**: Aim & Shoot
- **R**: Retry (in Boss Mode)

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
- **pygame_aseprite_animator**: Animation handling (MIT License)

