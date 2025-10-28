# Asset Directory Structure

This directory contains all game assets organized by type and usage.

## Directory Structure

### images/
- **characters/** - Player character sprites and animations
- **bosses/** - Boss character sprites and animations  
- **backgrounds/** - Level backgrounds and environment art
- **ui/** - User interface elements, menus, HUD

### audio/
- **bgm/** - Background music tracks for different scenes
- **sfx/** - Sound effects for actions, combat, environment

### fonts/
- Custom fonts for UI and text rendering
- Keep font files small for performance

## Asset Guidelines

### Images
- **Format:** PNG with transparency support
- **Pixel Art:** 16x16 or 32x32 base tile size
- **Color Palette:** Consistent across all sprites
- **Naming:** Descriptive names with type suffix
  - Example: `player_idle_01.png`, `boss_perfectionist_attack.png`

### Audio
- **Music Format:** OGG Vorbis (smaller file size)
- **SFX Format:** WAV (low latency)
- **Sample Rate:** 44.1kHz
- **Bit Depth:** 16-bit minimum
- **Volume:** Normalized to prevent clipping

### Organization Tips
- Group related assets in subfolders
- Use consistent naming conventions
- Include asset source files in .gitignore
- Document asset sources and licenses

## Placeholder Assets

During development, use simple colored rectangles or basic shapes as placeholders. This allows development to continue while art assets are being created.

## Asset Integration

Team Member 3 (Level Design & Visual Systems) is responsible for:
- Organizing this directory structure
- Implementing asset loading pipeline
- Ensuring consistent visual style
- Performance optimization of assets