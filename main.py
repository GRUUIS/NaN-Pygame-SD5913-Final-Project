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
from src.utils.logger import setup_logger
logger = setup_logger()
logger.info("Game started!")
#endregion Imports

#region Game Flow Manager Bridge
def run_menu_and_flow():
    """Delegate to testing/game_flow_manager.py for menu + flow."""
    try:
        from testing.game_flow_manager import main as run_flow
        run_flow()
    except Exception as e:
        print(f"Failed to run game_flow_manager: {e}")
#endregion Game Flow Manager Bridge

#region Entry Point
def main():
    try:
        # Ensure global music_volume is set from config so scenes can read it
        try:
            from config import settings as cfg
            setattr(g, 'music_volume', getattr(cfg, 'MUSIC_VOLUME', 0.2))
        except Exception:
            try:
                setattr(g, 'music_volume', 0.2)
            except Exception:
                pass
        # Try to initialize the mixer and set the music default volume so
        # any later playback uses the configured value.
        try:
            try:
                pygame.mixer.get_init()
            except Exception:
                pygame.mixer.init()
            try:
                pygame.mixer.music.set_volume(getattr(g, 'music_volume', 0.2))
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
                bt = 'perfectionist'
                if len(sys.argv) > 2:
                    arg = (sys.argv[2] or '').lower()
                    if arg in ('sloth','the_sloth'): bt = 'sloth'
                    elif arg in ('hollow','the_hollow','nihilism','procrastinator','procrastination'): bt = 'hollow'
                    else: bt = 'perfectionist'
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
    """Run a boss scene directly from CLI: 'boss1' | 'sloth' | 'hollow' | 'perfectionist'."""
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
            from src.entities.boss_battle_scene import BossBattleScene
            scene = BossBattleScene(boss_type='perfectionist')
            title = 'Perfectionist'
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
    
    if hasattr(boss_scene, 'boss') and boss_scene.boss:
        draw_health_bar(screen, boss_scene.boss.health, boss_scene.boss.max_health,
                   g.SCREENWIDTH - 210, 10, 200, 20, "Boss")

    # Optional boss-specific overlays (Stress meter, Deadline timer)
    if hasattr(boss_scene, 'boss') and boss_scene.boss:
        boss = boss_scene.boss
        if hasattr(boss, 'max_stress') and hasattr(boss, 'stress'):
            # Draw Stress bar below boss HP
            stress_current = getattr(boss, 'stress', 0)
            stress_max = max(1, getattr(boss, 'max_stress', 100))
            draw_meter_bar(
                screen,
                current=stress_current,
                maximum=stress_max,
                x=g.SCREENWIDTH - 210,
                y=35,
                width=200,
                height=14,
                label="Stress",
                color_high=(220, 120, 120),
                color_mid=(230, 180, 80),
                color_low=(120, 200, 120)
            )

        if hasattr(boss, 'deadline_left') and hasattr(boss, 'deadline_total'):
            # Draw Deadline bar at top center
            d_left = max(0.0, float(getattr(boss, 'deadline_left', 0.0)))
            d_total = max(0.01, float(getattr(boss, 'deadline_total', 60.0)))
            center_x = g.SCREENWIDTH // 2 - 110
            draw_meter_bar(
                screen,
                current=d_left,
                maximum=d_total,
                x=center_x,
                y=10,
                width=220,
                height=14,
                label=f"Deadline: {int(d_left)}s",
                color_high=(120, 200, 120),
                color_mid=(230, 180, 80),
                color_low=(220, 120, 120)
            )
    
    # Debug info if enabled
    if g.SHOW_DEBUG_INFO:
        debug_info = [
            f"Player: ({int(boss_scene.player.x)}, {int(boss_scene.player.y)})",
            f"Bullets: {len(boss_scene.bullet_manager.bullets)}",
            f"FPS: {int(pygame.time.Clock().get_fps())}"
        ]
        if hasattr(boss_scene, 'boss') and boss_scene.boss:
            debug_info.insert(1, f"Boss State: {boss_scene.boss.current_state.__class__.__name__}")
        
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


def draw_meter_bar(screen, current, maximum, x, y, width, height, label,
                   color_high=(120, 200, 120), color_mid=(230, 180, 80), color_low=(220, 120, 120)):
    """Generic meter bar (e.g., Stress or Deadline) with label, colors based on percentage."""
    font = pygame.font.Font(None, 18)
    pct = max(0.0, min(1.0, float(current) / float(maximum))) if maximum else 0.0
    # For meters where "more is better" (e.g., time left), use high color when pct > .6
    if pct > 0.6:
        color = color_high
    elif pct > 0.3:
        color = color_mid
    else:
        color = color_low
    # background
    pygame.draw.rect(screen, (50, 50, 50), (x, y, width, height))
    # fill
    pygame.draw.rect(screen, color, (x, y, width * pct, height))
    # border
    pygame.draw.rect(screen, g.COLORS['ui_text'], (x, y, width, height), 2)
    # label
    label_text = font.render(str(label), True, g.COLORS['ui_text'])
    screen.blit(label_text, (x, y - 18))


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
        subtitle_text = None
    elif hasattr(boss_scene, 'boss') and boss_scene.boss and boss_scene.boss.health <= 0:
        title_text = font.render("VICTORY!", True, g.COLORS['ui_health_high'])
        subtitle_text = None
    else:
        # Fallback for scripted scenes where boss might not exist or be killable
        title_text = font.render("GAME OVER", True, g.COLORS['ui_text'])
        subtitle_text = small_font.render("Press R to restart", True, g.COLORS['ui_text'])
    
    # Center the text
    title_rect = title_text.get_rect(center=(g.SCREENWIDTH//2, g.SCREENHEIGHT//2))
    screen.blit(title_text, title_rect)
    if subtitle_text:
        subtitle_rect = subtitle_text.get_rect(center=(g.SCREENWIDTH//2, g.SCREENHEIGHT//2 + 30))
        screen.blit(subtitle_text, subtitle_rect)


def show_help():
    """Show help information"""
    print("\nMind's Maze")
    print("  python main.py                - Menu → First Dream → Transition → Third Puzzle")
    print("  python main.py boss1|boss2|boss3  - Direct boss test (boss2=Sloth, boss3=Hollow)")
    print("  python main.py boss [perfectionist|sloth|hollow] - Boss selector")
    print("  python main.py help           - Show this help")


if __name__ == "__main__":
    main()