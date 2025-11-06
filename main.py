"""
Mind's Maze - Main Entry Point

A 2D psychological puzzle-platformer game built with Pygame.
This is the main entry point for the game.

Author: Team NaN
Course: Creative Programming SD5913

Usage:
    python main.py                              # Normal game mode
    python main.py boss [perfectionist|hollow]  # Boss battle test mode (default: perfectionist)
    python main.py test [perfectionist|hollow]  # Same as boss mode
    python main.py boss1                        # Shortcut: Perfectionist boss test
    python main.py boss3                        # Shortcut: The Hollow boss test
"""

import pygame
import sys
import os
import globals as g
from src.scenes.game_manager import GameManager
from src.entities.boss_battle_scene import BossBattleScene
from src.utils.logger import setup_logger
logger = setup_logger()
logger.info("Game started!")

def main():
    """
    Main game entry point.
    Initializes Pygame and starts the appropriate game mode.
    """
    try:
        # Initialize Pygame
        pygame.init()
        
        # Check for command line arguments
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode in ['boss1', 'perfectionist']:
                print("Starting Boss Battle Test Mode... (Perfectionist)")
                run_boss_test('perfectionist')
                return
            if mode in ['boss2', 'procrastinator', 'procrastination', 'boss3', 'hollow', 'the_hollow', 'nihilism']:
                print("Starting Boss Battle Test Mode... (The Hollow)")
                run_boss_test('hollow')
                return
            if mode in ['boss', 'test']:
                # Direct boss battle test mode
                boss_type = 'perfectionist'
                if len(sys.argv) > 2:
                    arg = (sys.argv[2] or '').lower()
                    if arg in ('perfectionist', 'procrastinator', 'procrastination', 'hollow', 'the_hollow', 'nihilism'):
                        boss_type = 'hollow' if (arg in ('hollow','the_hollow','nihilism') or arg.startswith('procrast')) else 'perfectionist'
                display_name = 'The Hollow' if boss_type == 'hollow' else 'Perfectionist'
                print(f"Starting Boss Battle Test Mode... ({display_name})")
                run_boss_test(boss_type)
                return
            elif mode == 'help':
                show_help()
                return
        
        # Normal game mode
        print("Starting Normal Game Mode...")
        
        # Set up the game window
        screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
        pygame.display.set_caption("Mind's Maze - Psychological Platformer")
        
        # Initialize game manager
        game_manager = GameManager(screen)
        
        # Start the game
        game_manager.run()
        
    except Exception as e:
        print(f"Error starting game: {e}")
        sys.exit(1)
    
    finally:
        pygame.quit()
        sys.exit()


def run_boss_test(boss_type: str = 'perfectionist'):
    """
    Direct boss battle test without menu navigation.
    Tests the Perfectionist boss with full 2D platformer mechanics.
    """
    # Initialize display
    screen = pygame.display.set_mode((g.SCREENWIDTH, g.SCREENHEIGHT))
    # Title mapping: show The Hollow when using the new boss aliases or legacy procrastinator alias
    bt = (boss_type or 'perfectionist').lower()
    title = "The Hollow" if bt in ('hollow','the_hollow','nihilism','procrastinator','procrastination') else "Perfectionist"
    pygame.display.set_caption(f"Boss Battle Test - {title}")
    clock = pygame.time.Clock()
    
    # Initialize boss battle scene
    boss_scene = BossBattleScene(boss_type=boss_type)
    
    print("Boss Battle Controls:")
    print("  WASD: Move")
    print("  Space: Jump")
    print("  Mouse: Aim and Shoot")
    print("  R: Reset Battle")
    print("  ESC: Exit")
    print(f"  Boss: {title}")
    
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

    # Optional boss-specific overlays (Stress meter, Deadline timer)
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
    print("  python main.py                              - Start normal game")
    print("  python main.py boss [perfectionist|hollow]  - Boss battle test mode (default: perfectionist)")
    print("  python main.py test [perfectionist|hollow]  - Same as boss mode") 
    print("  python main.py boss1                        - Shortcut: Perfectionist boss test")
    print("  python main.py boss3                        - Shortcut: The Hollow boss test")
    print("  python main.py help   - Show this help")
    print("\nBoss Battle Controls:")
    print("  WASD: Move player")
    print("  Space: Jump")
    print("  Mouse: Aim and shoot")
    print("  R: Reset battle")
    print("  ESC: Exit")


if __name__ == "__main__":
    main()