"""
Mind's Maze - Main Entry Point

Menu → First Dream Puzzle → Dream Transition → Third Puzzle.
"""

#region Imports
import pygame
import sys
import os
import subprocess
import globals as g
import traceback
from src.utils.logger import setup_logger
logger = setup_logger()
logger.info("Game started!")
# Expose centralized font path helper to the global namespace so other
# modules can find the Silver.ttf (or fallback) consistently. Prefer
# the `globals` resolution (set in `globals.py`) first, then fall back
# to the compatibility shim at `src.utils.font` if needed.
try:
    # `globals` already defines `get_font_path()` and `FONT_PATH` (see
    # `globals.py`), so prefer those values when available.
    setattr(g, 'FONT_PATH', g.get_font_path())
    setattr(g, 'get_font_path', g.get_font_path)
except Exception:
    try:
        from src.utils.font import get_font_path as _get_font_path
        setattr(g, 'FONT_PATH', _get_font_path())
        setattr(g, 'get_font_path', _get_font_path)
    except Exception:
        # If fonts are unavailable, ensure attributes exist but set to None
        setattr(g, 'FONT_PATH', None)
        setattr(g, 'get_font_path', lambda: None)
# Centralized UI utilities
try:
    from src.systems.ui import draw_ui_overlay, draw_game_over_screen
except Exception:
    # fallback if module import fails during early development
    draw_ui_overlay = None
    draw_game_over_screen = None
#endregion Imports
#region Game Flow Manager Bridge
def run_menu_and_flow():
    """Delegate to testing/game_flow_manager.py for menu + flow."""
    try:
        from testing.game_flow_manager import main as run_flow
        try:
            run_flow()
        except Exception:
            print("Unhandled exception in game_flow_manager:")
            traceback.print_exc()
            raise
    except Exception as e:
        print(f"Failed to run game_flow_manager: {e}")


# Ensure any uncaught exceptions print a full traceback to the terminal
def _print_unhandled(exc_type, exc_value, exc_tb):
    print("Uncaught exception:")
    traceback.print_exception(exc_type, exc_value, exc_tb)

sys.excepthook = _print_unhandled
#endregion Game Flow Manager Bridge

#region Entry Point
def main():
    try:
        # Set music volume attribute for runtime access
        try:
            setattr(g, 'music_volume', g.MUSIC_VOLUME)
        except Exception:
            setattr(g, 'music_volume', 0.25)
        # Try to initialize the mixer and set the music default volume so
        # any later playback uses the configured value.
        try:
            try:
                pygame.mixer.get_init()
            except Exception:
                pygame.mixer.init()
            try:
                pygame.mixer.music.set_volume(getattr(g, 'music_volume', 0.25))
            except Exception:
                # ignore if mixer not fully ready
                pass
        except Exception:
            pass
        # CLI shortcuts: support boss1/2/3 direct tests and help
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            if mode in ('help', '--help', '-h'):
                show_help()
                return
            if mode in ('boss1','intro'):
                return run_boss_cli('boss1')
            if mode in ('boss2','sloth','the_sloth'):
                return run_boss_cli('sloth')
            if mode in ('boss3','hollow','the_hollow'):
                return run_boss_cli('hollow')
            if mode == 'boss':
                bt = 'hollow'
                if len(sys.argv) > 2:
                    arg = (sys.argv[2] or '').lower()
                    if arg in ('sloth','the_sloth'): bt = 'sloth'
                    elif arg in ('hollow','the_hollow','nihilism','procrastinator','procrastination'): bt = 'hollow'
                return run_boss_cli(bt)
        # Normal: menu + flow
        run_menu_and_flow()
    except Exception as e:
        print(f"Error starting game: {e}")
        sys.exit(1)
    finally:
        pygame.quit()
        sys.exit()
#endregion Entry Point

#region Boss CLI Runner
def run_boss_cli(which: str):
    """Run a boss scene directly from CLI: 'boss1' | 'sloth' | 'hollow'."""
    pygame.init()
    screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
    clock = pygame.time.Clock()
    # Construct scene
    scene = None
    title = ''
    try:
        if which == 'boss1':
            from src.scenes.boss1_scripted_scene import Boss1ScriptedScene
            scene = Boss1ScriptedScene(game_manager=None)
            title = 'Boss1 Intro'
        elif which == 'sloth':
            from src.entities.sloth_battle_scene import SlothBattleScene
            scene = SlothBattleScene()
            title = 'The Sloth'
        elif which == 'hollow':
            from src.entities.boss_battle_scene import BossBattleScene
            scene = BossBattleScene(boss_type='hollow')
            title = 'The Hollow'
        else:
            # Default to Hollow
            from src.entities.boss_battle_scene import BossBattleScene
            scene = BossBattleScene(boss_type='hollow')
            title = 'The Hollow'
    except Exception as e:
        print(f"Failed to initialize boss scene: {e}")
        pygame.quit(); return
    if hasattr(scene, 'enter'):
        try: scene.enter()
        except Exception: pass
    pygame.display.set_caption(f"Boss Test - {title}")
    running = True
    while running:
        dt = clock.tick(g.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    if hasattr(scene, 'is_game_over') and callable(scene.is_game_over) and not scene.is_game_over():
                        if hasattr(scene, 'reset_battle') and callable(scene.reset_battle):
                            scene.reset_battle()
                        elif hasattr(scene, 'enter') and callable(scene.enter):
                            scene.enter()
                elif event.key == pygame.K_SPACE:
                    # Allow space to exit on victory; scripted boss1 allows space after over
                    boss = getattr(scene, 'boss', None)
                    is_over = hasattr(scene, 'is_game_over') and scene.is_game_over()
                    victory = False
                    if boss is not None and hasattr(boss, 'health'):
                        victory = getattr(boss, 'health', 1) <= 0
                    else:
                        victory = is_over and boss is None
                    if is_over and victory:
                        running = False
            try:
                scene.handle_event(event)
            except Exception:
                pass
        try:
            scene.update(dt)
        except Exception:
            pass
        try:
            scene.draw(screen)
        except Exception:
            pass
        pygame.display.flip()
    pygame.quit()
#endregion Boss CLI Runner


# Boss battle test code removed per new flow requirements


# UI rendering moved to `src.systems.ui`. If import failed earlier, ensure
# a minimal fallback that won't crash the CLI runner.
if draw_ui_overlay is None:
    def draw_ui_overlay(screen, boss_scene):
        # minimal placeholder: don't draw anything
        return

if draw_game_over_screen is None:
    def draw_game_over_screen(screen, boss_scene):
        return


def show_help():
    """Show help information"""
    print("\nMind's Maze")
    print("  python main.py                - Menu → First Dream → Transition → Third Puzzle")
    print("  python main.py boss1|boss2|boss3  - Direct boss test (boss2=Sloth, boss3=Hollow)")
    print("  python main.py boss [sloth|hollow] - Boss selector")
    print("  python main.py help           - Show this help")


if __name__ == "__main__":
    main()