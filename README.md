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
   - Initial defeat teaches importance of preparation
   - Victory requires creative tools acquisition

2. **Procrastination** - "Laziness Ghost/Creative Drought"  
   - Slow but wide-range attacks
   - Requires constant movement and positioning

3. **Nihilism** - "Meaninglessness/Futility"
   - Cannot be attacked directly  
   - Must clear environmental puzzle elements

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

## Team Roles & Responsibilities

### Lead Developer
- **Responsibilities:** Core game architecture, scene management, integration
- **Files:** `main.py`, `src/scenes/`, project coordination

### Combat Systems Developer  
- **Responsibilities:** Boss behaviors, combat mechanics, player controls
- **Files:** `src/entities/`, `src/systems/combat.py`

### Level Design & Assets Integration
- **Responsibilities:** Map creation, asset implementation, UI design
- **Files:** `assets/` organization, `src/systems/renderer.py`

### Content Text & Audio & Polish Developer
- **Responsibilities:** Texts, Sound system, game balance, bug fixes
- **Files:** `src/systems/audio.py`, `config/`, testing

## Development Guidelines

### Code Standards
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Comment complex logic sections
- Keep functions small and focused

### Asset Guidelines
- Pixel art sprites: 16x16 or 32x32 base size
- Audio files: OGG or WAV format
- Consistent color palette across all art
- Organize assets by type and usage

### Git Workflow
- Create feature branches for major changes
- Commit frequently with descriptive messages
- Test before pushing to main branch
- Use pull requests for code review

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

