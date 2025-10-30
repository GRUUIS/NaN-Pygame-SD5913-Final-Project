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
BOSS_ATTACK_COOLDOWN_PHASE2 = 0.5  # Phase 2 more challenging
BOSS_TELEGRAPH_DURATION = 0.8  # Slightly reduce telegraph time
BOSS_MOVE_SPEED = 150  # Increase movement speed
BOSS_CHARGE_SPEED = 300

# Bullet Configuration
BULLET_SPEEDS = {
    'normal': 250,    # Slightly increase boss bullet speed
    'homing': 180,    # Homing bullets slower but more dangerous
    'laser': 350,     # Laser faster
    'player': 450     # Player bullets faster to maintain balance
}

BULLET_DAMAGE = {
    'normal': 15,     # Increase boss bullet damage
    'homing': 18,     # Homing bullets more dangerous
    'laser': 20,      # Laser high damage
    'player': 12      # Reduce player damage, requires more skill
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