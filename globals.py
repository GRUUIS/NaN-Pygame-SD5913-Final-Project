# Screen Configuration
SCREENWIDTH = 1280
SCREENHEIGHT = 720
FPS = 60

# Game Physics Constants
GRAVITY = 800  # pixels per second squared
MAX_FALL_SPEED = 600  # terminal velocity
JUMP_STRENGTH = 500  # initial jump velocity
PLAYER_MOVE_SPEED = 100  # horizontal movement speed
GROUND_FRICTION = 0.8  # friction when on ground
AIR_RESISTANCE = 0.98  # air resistance

# Player Configuration
PLAYER_SIZE = 16
PLAYER_MAX_HEALTH = 100
PLAYER_ATTACK_COOLDOWN = 0.5
PLAYER_INVINCIBLE_DURATION = 1.0

# Boss Configuration - Perfectionist
BOSS_MAX_HEALTH = 500 
BOSS_ATTACK_COOLDOWN_PHASE1 = 2
BOSS_ATTACK_COOLDOWN_PHASE2 = 0.5  # Phase 2更具挑战性
BOSS_TELEGRAPH_DURATION = 0.8  # 稍微减少预告时间
BOSS_MOVE_SPEED = 150  # 增加移动速度
BOSS_CHARGE_SPEED = 300

# Bullet Configuration
BULLET_SPEEDS = {
    'normal': 250,    # 稍微加快boss子弹速度
    'homing': 180,    # 追踪弹稍慢但更危险
    'laser': 350,     # 激光更快
    'player': 450     # 玩家子弹更快以保持平衡
}

BULLET_DAMAGE = {
    'normal': 15,     # 增加boss子弹伤害
    'homing': 18,     # 追踪弹更危险
    'laser': 20,      # 激光高伤害
    'player': 12      # 降低玩家伤害，需要更多技巧
}

# Colors
COLORS = {
    'background': (20, 20, 40),
    'player': (100, 150, 255),
    'player_jumping': (255, 200, 200),
    'player_invincible': (255, 255, 255),
    'platform': (100, 100, 100),
    'ground': (80, 80, 80),
    'boss': (150, 50, 50),
    'boss_telegraph': (255, 100, 100),
    'bullet_normal': (255, 100, 100),
    'bullet_homing': (255, 150, 50),
    'bullet_laser': (255, 255, 100),
    'bullet_player': (100, 200, 255),
    'ui_text': (255, 255, 255),
    'ui_health_high': (50, 255, 50),
    'ui_health_medium': (255, 255, 50),
    'ui_health_low': (255, 50, 50)
}

# Game States
GAME_STATES = {
    'MENU': 'menu',
    'GAMEPLAY': 'gameplay', 
    'BOSS_BATTLE': 'boss_battle',
    'GAME_OVER': 'game_over',
    'VICTORY': 'victory',
    'PAUSED': 'paused'
}

# Debug Mode
DEBUG_MODE = True
SHOW_DEBUG_INFO = True
SHOW_COLLISION_BOXES = False