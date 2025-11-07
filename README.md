# Mind's Maze - Psychological 2D Platformer

A 2D pixel art puzzle-platformer game exploring psychological themes through metaphorical boss battles.

## Project Overview

**Genre:** 2D Side-scrolling Puzzle-Platformer  
**Engine:** Pygame  
**Art Style:** Pixel Art  
**Timeline:** 5-6 weeks (Deadline: December 1, 2025)  
**Team Size:** 4 developers  

### Game Concept

Players control a puppet figure representing "neglected self-awareness" within a chaotic mind landscape. The game features three metaphorical boss battles representing common psychological obstacles: perfectionism, procrastination, and nihilism.

### Core Features

- **Metaphorical Combat System:** Creative tools instead of traditional weapons
- **Progressive Difficulty:** Each boss requires different strategies
- **Pixel Art Aesthetic:** Retro-inspired visual design
- **Multimedia Integration:** Images, audio, narrative elements
- **Puzzle-Combat Hybrid:** Strategic thinking combined with action

### Boss Encounters

1. **Perfectionist** - "Self-Censorship/Fear of Action"
   - Entry boss, teaches baseline movement and dodge patterns
   - Standard bullet-hell patterns: spread, predictive, homing, sweep

2. **The Hollow (Nihilism)** - Black silhouette of emptiness
   - New Boss 3 (re-themed from Procrastinator mechanics)
   - Summons "Void Shards" (black squares) from above; touching hurts
   - Entry bubble: “You think words can scare me away?”
   - Player uses “Voidfire” (purple flame) as the primary attack in this fight
   - Victory bubble: “This is not a threat-it's my process”

### Technical Specifications

- **Resolution:** 1280x720
- **Frame Rate:** 60 FPS
- **Controls:** WASD + Mouse + Spacebar
- **Platform:** Windows (Primary)

## Project Structure

```
Mind's-Maze/
├── src/                    # Source code
│   ├── entities/          # Player, bosses, items
│   ├── scenes/            # Game states, levels
│   ├── systems/           # Combat, audio, input
│   └── utils/             # Helper functions
├── assets/                # Game resources
│   ├── images/           # Sprites, backgrounds, UI
│   ├── audio/            # Music and sound effects
│   └── fonts/            # Text rendering
├── config/               # Game configuration
├── docs/                 # Documentation
├── main.py              # Entry point
└── globals.py           # Global constants
```

## Development Setup

### Prerequisites

### Installation
1. Clone the repository:
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the game:
   ```bash
   python main.py
   ```

### Quick Boss Tests

- Perfectionist boss test:
   ```bash
   python main.py boss1
   ```

- The Hollow boss test (Boss 3):
   ```bash
   python main.py boss hollow
   # or
   python main.py boss3
   ```

Controls in boss tests:

- WASD / Arrow keys: Move
- Space / W / Up: Jump
- Mouse Left: Shoot (Perfectionist: normal bullets; The Hollow: Voidfire)
- R: Reset battle
- ESC: Exit

Idle penalty (anti-camping) in boss battles:

- If you stand still on the ground too long, punishment escalates:
   - Periodic “Void Shards” fall near you, count and speed scale with idle time
   - Continuous health drain while idle (tunable)
   - Tunables in `globals.py`:
      - `PLAYER_IDLE_THRESHOLD` (seconds)
      - `PLAYER_IDLE_SHARD_INTERVAL` (seconds)
      - `PLAYER_IDLE_HEALTH_DRAIN` (HP per second)

## Team Roles & Responsibilities

### Structure Developer
- **Responsibilities:** main loop, scene management, and overall integration
- **Files:** `main.py`, `src/scenes/`, `src/utils/`, project coordination

### Combat Systems Developer
- **Responsibilities:** Boss behaviors, combat mechanics, player controls, and balancing
- **Files:** `src/entities/`, `src/systems/combat.py`, `src/utils/collision.py`

### Visual & UI Developer
- **Responsibilities:** Map creation, camera movement, and basic UI design
- **Files:** `assets/` organization, `src/systems/renderer.py`, `src/systems/camera.py`, `src/scenes/`

### Content & Asset Integration Developer
- **Responsibilities:** Asset preparation (audio, images, sprites, animations), narrative text, and dialogue implementation
- **Files:** `assets/`, `src/systems/audio.py`, `config/`, `src/utils/dialogue.py`

## Development Guidelines

### Code Standards
- Pull lastest version everytime coding
- Use descriptive variable and function names
- Comment complex logic sections

### Asset Guidelines
- Pixel art sprites: 16x16 or 32x32 base size
- Audio files: MP3 or WAV format
- Consistent color palette across all art
- Organize assets by type and usage

### Git Workflow
- Create feature branches for major changes
- Commit frequently with descriptive messages
- Test before pushing to main branch
- Use pull requests for code review

## Third-party components / Attribution

- The project includes a vendored copy of `pygame_aseprite_animator` (used for loading Aseprite `.aseprite` animations) under `testing/pygame_aseprite_animator/`.
- Original upstream repository: https://github.com/ISebSej/pygame_aseprite_animator
- This copy was added as a vendor snapshot so the demo runner can parse `.aseprite` files without requiring an external install. The animator's original LICENSE file is included in `testing/pygame_aseprite_animator/LICENSE`.
- If you prefer to track upstream changes directly, we can convert this to a git submodule instead (ask me and I can set that up).

## Game Design Document

### Core Loop
1. **Exploration:** Navigate mind-scape environments
2. **Discovery:** Find creative tools and story elements  
3. **Challenge:** Face psychological boss battles
4. **Growth:** Overcome obstacles through strategy

### Progression System
- **Tools Acquisition:** Unlock new abilities
- **Knowledge Gain:** Learn boss patterns and strategies
- **Narrative Advancement:** Discover story through gameplay

## Current Development Status

**Phase 1: Foundation** (Weeks 1-2)
- [x] Project structure setup
- [ ] Core game engine implementation
- [ ] Basic player movement and controls

**Phase 2: Core Systems** (Weeks 3-4)  
- [ ] Boss battle framework
- [ ] Combat and puzzle mechanics
- [ ] Asset integration pipeline

**Phase 3: Content & Polish** (Weeks 5-6)
- [ ] Level design and balancing
- [ ] Audio implementation
- [ ] Testing and bug fixes

