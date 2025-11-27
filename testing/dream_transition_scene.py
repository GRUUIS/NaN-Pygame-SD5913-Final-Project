"""
梦境过渡场景 - 主角梦见自己变成小女巫
用于解谜关卡和战斗关卡之间的剧情衔接
"""
import pygame
import sys
import math
import random
from pathlib import Path
import globals as g

# 路径设置
REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = REPO_ROOT / "assets"

def run_dream_transition(screen):
    """
    运行梦境过渡场景
    返回: 'next' 继续到战斗关卡, 'quit' 退出游戏
    """
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    
    pygame.font.init()
    try:
        font_large = pygame.font.Font(str(ASSETS_PATH / "Silver.ttf"), 48)
        font_text = pygame.font.Font(str(ASSETS_PATH / "Silver.ttf"), 32)
    except:
        font_large = pygame.font.Font(None, 48)
        font_text = pygame.font.Font(None, 32)
    
    # 加载角色精灵
    player_sprite_path = ASSETS_PATH / "8Direction_TopDown_Character Sprites_ByBossNelNel" / "SpriteSheet.png"
    witch_sprite_path = ASSETS_PATH / "sprites" / "Blue_witch"
    
    # 加载普通主角（朝下idle）
    try:
        player_sheet = pygame.image.load(str(player_sprite_path)).convert_alpha()
        player_sprite = player_sheet.subsurface(pygame.Rect(0, 0, 23, 36))
        player_sprite = pygame.transform.scale(player_sprite, (92, 144))  # 放大4倍
    except Exception as e:
        print(f"无法加载主角精灵: {e}")
        player_sprite = pygame.Surface((92, 144), pygame.SRCALPHA)
        player_sprite.fill((100, 150, 200))
    
    # 加载小女巫精灵（idle）
    try:
        witch_idle_path = ASSETS_PATH / "sprites" / "Blue_witch" / "B_witch_idle.png"
        witch_sheet = pygame.image.load(str(witch_idle_path)).convert_alpha()
        # 精灵条是 32x288，每帧 32x32，取第一帧
        frame_size = 32
        witch_frame = witch_sheet.subsurface(pygame.Rect(0, 0, frame_size, frame_size))
        # 放大到合适尺寸
        witch_sprite = pygame.transform.scale(witch_frame, (128, 128))
    except Exception as e:
        print(f"无法加载女巫精灵: {e}")
        witch_sprite = pygame.Surface((128, 128), pygame.SRCALPHA)
        witch_sprite.fill((100, 50, 150))
    
    # 剧情文本（分段）
    story_segments = [
        "I was trapped in this gray mist again.",
        "The road under my feet was as soft as cotton,",
        "and I could never step firmly on it.",
        "",
        "Suddenly, my body felt heavy—",
        "the fabric of a black cloak clung to my skin,",
        "and a broom had appeared by my hand,",
        "its wooden handle as cold as my trembling fingertips.",
        "",
        "A low growl came from the mist—",
        "it was the dark shadow that always clung to me.",
        "It surrounded me like a tide,",
        "blurring the line between the sky and the ground.",
        "",
        "I had to count the beats of my breath",
        "to keep from being swallowed by fear."
    ]
    
    # 场景状态
    phase = 0  # 0: 开始淡入, 1: 显示主角, 2: 变身, 3: 女巫形态, 4: 淡出
    phase_timer = 0
    text_index = 0
    text_timer = 0
    TEXT_SPEED = 1.5  # 每1.5秒一行
    
    # 视觉效果参数
    mist_particles = []
    for _ in range(50):
        mist_particles.append({
            'x': pygame.math.Vector2(
                random.random() * SCREEN_WIDTH,
                random.random() * SCREEN_HEIGHT
            ),
            'speed': pygame.math.Vector2(
                (random.random() - 0.5) * 20,
                (random.random() - 0.5) * 10
            ),
            'size': int(30 + random.random() * 50),
            'alpha': int(20 + random.random() * 40)
        })
    
    shadow_particles = []
    shadow_active = False
    
    alpha = 0  # 淡入淡出透明度
    transform_progress = 0  # 变身进度 0-1
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and getattr(g, 'DEVELOPER_MODE', False):
                    print("Developer Mode: Skipping transition...")
                    return 'next'
                if event.key == pygame.K_ESCAPE:
                    return 'quit'
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    # 快进到下一阶段
                    if phase < 4:
                        phase += 1
                        phase_timer = 0
        
        # 更新阶段
        phase_timer += dt
        
        if phase == 0:  # 淡入
            alpha = min(255, alpha + 100 * dt)
            if phase_timer > 2.0:
                phase = 1
                phase_timer = 0
        
        elif phase == 1:  # 显示主角和前半段文本
            text_timer += dt
            if text_timer > TEXT_SPEED and text_index < 8:
                text_index += 1
                text_timer = 0
            
            if phase_timer > 8.0:  # 前半段显示8秒
                phase = 2
                phase_timer = 0
        
        elif phase == 2:  # 变身过程
            transform_progress = min(1.0, phase_timer / 3.0)  # 3秒变身
            
            # 继续显示文本
            text_timer += dt
            if text_timer > TEXT_SPEED and text_index < len(story_segments):
                text_index += 1
                text_timer = 0
            
            # 激活阴影效果
            if phase_timer > 1.5:
                shadow_active = True
            
            if phase_timer > 3.0:
                phase = 3
                phase_timer = 0
                transform_progress = 1.0
        
        elif phase == 3:  # 女巫形态和后半段文本
            text_timer += dt
            if text_timer > TEXT_SPEED and text_index < len(story_segments):
                text_index += 1
                text_timer = 0
            
            shadow_active = True
            
            if phase_timer > 6.0:  # 后半段显示6秒
                phase = 4
                phase_timer = 0
        
        elif phase == 4:  # 淡出
            alpha = max(0, alpha - 100 * dt)
            if alpha <= 0:
                return 'next'
        
        # 更新迷雾粒子
        for p in mist_particles:
            p['x'] += p['speed'] * dt
            if p['x'][0] < -50:
                p['x'][0] = SCREEN_WIDTH + 50
            elif p['x'][0] > SCREEN_WIDTH + 50:
                p['x'][0] = -50
            if p['x'][1] < -50:
                p['x'][1] = SCREEN_HEIGHT + 50
            elif p['x'][1] > SCREEN_HEIGHT + 50:
                p['x'][1] = -50
        
        # 更新阴影粒子
        if shadow_active:
            if len(shadow_particles) < 30 and random.random() < 0.3:
                angle = random.random() * math.pi * 2
                distance = 200 + random.random() * 150
                shadow_particles.append({
                    'pos': pygame.math.Vector2(
                        SCREEN_WIDTH // 2 + math.cos(angle) * distance,
                        SCREEN_HEIGHT // 2 + math.sin(angle) * distance
                    ),
                    'vel': pygame.math.Vector2(
                        math.cos(angle + math.pi) * 50,
                        math.sin(angle + math.pi) * 50
                    ),
                    'life': 2.0,
                    'max_life': 2.0
                })
            
            for s in shadow_particles[:]:
                s['pos'] += s['vel'] * dt
                s['life'] -= dt
                if s['life'] <= 0:
                    shadow_particles.remove(s)
        
        # ===== 渲染 =====
        # 背景渐变（灰色迷雾）
        for y in range(SCREEN_HEIGHT):
            gray = int(60 + 30 * math.sin(y / SCREEN_HEIGHT * math.pi))
            pygame.draw.line(screen, (gray, gray, gray + 10), (0, y), (SCREEN_WIDTH, y))
        
        # 绘制迷雾粒子
        mist_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for p in mist_particles:
            pygame.draw.circle(mist_surface, (200, 200, 210, p['alpha']), 
                             (int(p['x'][0]), int(p['x'][1])), p['size'])
        screen.blit(mist_surface, (0, 0))
        
        # 绘制角色（变身效果）
        char_x = SCREEN_WIDTH // 2
        char_y = SCREEN_HEIGHT // 2 - 50
        
        if phase < 2:
            # 只显示主角
            char_surface = player_sprite.copy()
            char_surface.set_alpha(int(alpha))
            screen.blit(char_surface, 
                       (char_x - char_surface.get_width() // 2, 
                        char_y - char_surface.get_height() // 2))
        
        elif phase == 2:
            # 变身中：混合两个精灵
            player_alpha = int((1 - transform_progress) * 255)
            witch_alpha = int(transform_progress * 255)
            
            player_surface = player_sprite.copy()
            player_surface.set_alpha(player_alpha)
            screen.blit(player_surface,
                       (char_x - player_surface.get_width() // 2,
                        char_y - player_surface.get_height() // 2))
            
            witch_surface = witch_sprite.copy()
            witch_surface.set_alpha(witch_alpha)
            screen.blit(witch_surface,
                       (char_x - witch_surface.get_width() // 2,
                        char_y - witch_surface.get_height() // 2))
        
        else:
            # 只显示女巫
            char_surface = witch_sprite.copy()
            char_surface.set_alpha(int(alpha))
            screen.blit(char_surface,
                       (char_x - char_surface.get_width() // 2,
                        char_y - char_surface.get_height() // 2))
        
        # 绘制阴影粒子
        if shadow_active:
            shadow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for s in shadow_particles:
                life_ratio = s['life'] / s['max_life']
                alpha_val = int(life_ratio * 150)
                size = int(20 + (1 - life_ratio) * 30)
                pygame.draw.circle(shadow_surface, (20, 10, 30, alpha_val),
                                 (int(s['pos'][0]), int(s['pos'][1])), size)
            screen.blit(shadow_surface, (0, 0))
        
        # 绘制文本
        text_y = SCREEN_HEIGHT - 250
        for i in range(min(text_index + 1, len(story_segments))):
            if i < len(story_segments):
                line = story_segments[i]
                if line:  # 跳过空行
                    text_surf = font_text.render(line, True, (220, 220, 230))
                    text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, text_y))
                    
                    # 文本阴影
                    shadow_surf = font_text.render(line, True, (30, 30, 40))
                    shadow_rect = shadow_surf.get_rect(center=(SCREEN_WIDTH // 2 + 2, text_y + 2))
                    screen.blit(shadow_surf, shadow_rect)
                    screen.blit(text_surf, text_rect)
                    
                    text_y += 35
        
        # 提示文本
        if phase < 4:
            hint = font_text.render("Press SPACE to continue", True, (150, 150, 160))
            hint_alpha_pulse = int(100 + 55 * math.sin(phase_timer * 3))
            hint.set_alpha(hint_alpha_pulse)
            screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 50))
        
        pygame.display.flip()
    
    return 'quit'


def main():
    """测试梦境过渡场景"""
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Dream Transition Scene")
    
    result = run_dream_transition(screen)
    print(f"场景结束，返回: {result}")
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
