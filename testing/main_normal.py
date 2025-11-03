"""
Mind's Maze - Normal Game Mode (test copy)

This file is a disposable copy of `main.py` that always starts the
"Normal Game Mode" (menu -> gameplay) for testing purposes.

Usage:
    python main_normal.py    # Start normal mode
    python main_normal.py help  # Print help and exit quickly (smoke test)
"""

import pygame
import sys
import os

# When running this test script directly, Python's import path (sys.path[0]) is
# the `testing/` directory. Ensure the project root is on sys.path so imports
# like `src.scenes...` work consistently.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.scenes.game_manager import GameManager
import globals as g
from src.entities.boss_battle_scene import BossBattleScene
from src.utils.logger import setup_logger
logger = setup_logger()
logger.info("Game (normal copy) started!")


def main():
    """
    Start normal game mode unconditionally (for testing).
    """
    try:
        # Initialize Pygame
        pygame.init()

        # Quick-help mode: if 'help' passed, print help and return.
        if len(sys.argv) > 1 and sys.argv[1].lower() == 'help':
            show_help()
            return

        # Normal game mode
        print("Starting Normal Game Mode (test copy)...")

        # Set up the game window
        screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
        pygame.display.set_caption("Mind's Maze - Psychological Platformer (test)")

        # Initialize game manager
        game_manager = GameManager(screen)

        # Skip menu and start directly in the richer example gameplay scene
        # which includes platforms and notes. Load it via importlib from the
        # testing/ folder so we don't need to change src files.
        try:
            import importlib.util
            example_path = os.path.join(project_root, 'testing', 'gameplay_scene_example.py')
            spec = importlib.util.spec_from_file_location('gameplay_scene_example', example_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            GameplayExample = getattr(mod, 'GameplayScene', None)
            if GameplayExample:
                game_manager.state_machine.change_state(GameplayExample(game_manager))
            else:
                # Fallback to built-in gameplay scene
                game_manager.change_scene('gameplay')
        except Exception as e:
            print(f"Warning: couldn't load testing gameplay example, falling back to 'gameplay': {e}")
            try:
                game_manager.change_scene('gameplay')
            except Exception:
                pass

        # Start the game
        game_manager.run()

    except Exception as e:
        print(f"Error starting game: {e}")
        sys.exit(1)

    finally:
        pygame.quit()
        sys.exit()


def run_boss_test():
    """
    Direct boss battle test without menu navigation.
    (Copied from original main.py)
    """
    # Initialize display
    screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
    pygame.display.set_caption("Boss Battle Test - Perfectionist")
    clock = pygame.time.Clock()

    # Initialize boss battle scene
    boss_scene = BossBattleScene()

    print("Boss Battle Controls:")
    print("  WASD: Move")
    print("  Space: Jump")
    print("  Mouse: Aim and Shoot")
    print("  R: Reset Battle")
    print("  ESC: Exit")

    # Game loop
    running = True
    show_game_over_timer = 0

    while running:
        dt = clock.tick(g.FPS) / 1000.0

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Reset boss battle using new method
                    boss_scene.reset_battle()
                    show_game_over_timer = 0
                    print("Boss battle reset!")

        # Update and draw
        if not boss_scene.is_game_over() or show_game_over_timer > 0:
            boss_scene.update(dt)

        boss_scene.draw(screen)

        # Show instructions and debug info
        draw_ui_overlay(screen, boss_scene)

        # Handle game over state
        if boss_scene.is_game_over():
            if show_game_over_timer <= 0:
                show_game_over_timer = 3.0  # Show for 3 seconds
                if boss_scene.player.health <= 0:
                    print("DEFEAT! Press R to retry")
                elif boss_scene.boss.health <= 0:
                    print("VICTORY! Press R for new battle")
            else:
                show_game_over_timer -= dt
                draw_game_over_screen(screen, boss_scene)

        pygame.display.flip()

    pygame.quit()


def draw_ui_overlay(screen, boss_scene):
    """Draw UI overlay with instructions and debug info"""
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)

    # Instructions
    instructions = [
        "WASD: Move",
        "Space: Jump",
        "Mouse: Aim/Shoot",
        "R: Reset",
        "ESC: Exit"
    ]

    for i, instruction in enumerate(instructions):
        text = small_font.render(instruction, True, g.COLORS['ui_text'])
        screen.blit(text, (10, 10 + i * 20))

    # Health bars
    draw_health_bar(screen, boss_scene.player.health, boss_scene.player.max_health,
                   10, g.SCREENHEIGHT - 40, 200, 20, "Player")

    draw_health_bar(screen, boss_scene.boss.health, boss_scene.boss.max_health,
                   g.SCREENWIDTH - 210, 10, 200, 20, "Boss")

    # Debug info if enabled
    if g.SHOW_DEBUG_INFO:
        debug_info = [
            f"Player: ({int(boss_scene.player.x)}, {int(boss_scene.player.y)})",
            f"Boss State: {boss_scene.boss.current_state.__class__.__name__}",
            f"Bullets: {len(boss_scene.bullet_manager.bullets)}",
            f"FPS: {int(pygame.time.Clock().get_fps())}"
        ]

        for i, info in enumerate(debug_info):
            text = small_font.render(info, True, g.COLORS['ui_text'])
            screen.blit(text, (g.SCREENWIDTH - 250, g.SCREENHEIGHT - 100 + i * 20))


def draw_health_bar(screen, current, maximum, x, y, width, height, label):
    """Draw a health bar with label"""
    font = pygame.font.Font(None, 18)

    # Calculate health percentage
    health_percent = max(0, current / maximum)

    # Choose color based on health
    if health_percent > 0.6:
        color = g.COLORS['ui_health_high']
    elif health_percent > 0.3:
        color = g.COLORS['ui_health_medium']
    else:
        color = g.COLORS['ui_health_low']

    # Draw background
    pygame.draw.rect(screen, (50, 50, 50), (x, y, width, height))

    # Draw health bar
    pygame.draw.rect(screen, color, (x, y, width * health_percent, height))

    # Draw border
    pygame.draw.rect(screen, g.COLORS['ui_text'], (x, y, width, height), 2)

    # Draw label and value
    label_text = font.render(f"{label}: {int(current)}/{int(maximum)}", True, g.COLORS['ui_text'])
    screen.blit(label_text, (x, y - 20))


def draw_game_over_screen(screen, boss_scene):
    """Draw game over overlay"""
    # Semi-transparent overlay
    overlay = pygame.Surface((g.SCREENWIDTH, g.SCREENHEIGHT))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Game over text
    font = pygame.font.Font(None, 72)
    small_font = pygame.font.Font(None, 36)

    if boss_scene.player.health <= 0:
        title_text = font.render("DEFEAT", True, g.COLORS['ui_health_low'])
        subtitle_text = small_font.render("Press R to retry", True, g.COLORS['ui_text'])
    else:
        title_text = font.render("VICTORY!", True, g.COLORS['ui_health_high'])
        subtitle_text = small_font.render("Press R for new battle", True, g.COLORS['ui_text'])

    # Center the text
    title_rect = title_text.get_rect(center=(g.SCREENWIDTH//2, g.SCREENHEIGHT//2 - 30))
    subtitle_rect = subtitle_text.get_rect(center=(g.SCREENWIDTH//2, g.SCREENHEIGHT//2 + 30))

    screen.blit(title_text, title_rect)
    screen.blit(subtitle_text, subtitle_rect)


def show_help():
    """Show help information"""
    print("\nMind's Maze - Game Modes:")
    print("  python main_normal.py        - Start normal game")
    print("  python main_normal.py boss   - Boss battle test mode")
    print("  python main_normal.py test   - Same as boss mode")
    print("  python main_normal.py help   - Show this help")
    print("\nBoss Battle Controls:")
    print("  WASD: Move player")
    print("  Space: Jump")
    print("  Mouse: Aim and shoot")
    print("  R: Reset battle")
    print("  ESC: Exit")


if __name__ == "__main__":
    main()
