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

# Phase thresholds (ratios of max HP)
PERFECTIONIST_PHASE2_HP_RATIO = 0.5  # Phase 2 when HP <= 50%

# Boss Configuration - The Hollow (Boss #3)
# Tunable knobs for the Hollow (previously the Procrastinator design). These
# are named BOSS3_* so we can reserve BOSS2_* for a future different Boss #2.
BOSS3_MAX_HEALTH = 520
BOSS3_MOVE_SPEED = 150
BOSS3_COOLDOWN_P1 = 1.5
BOSS3_COOLDOWN_P2 = 1.0
BOSS3_COOLDOWN_P3 = 0.5
BOSS3_TELEGRAPH_BASE = 1.1
BOSS3_HOMING_BASE_SPEED = 250
BOSS3_LASER_BASE_SPEED = 500
DEADLINE_SECONDS = 100

# The Hollow (Boss #3) phase thresholds (ratios of max HP)
HOLLOW_PHASE2_HP_RATIO = 0.8   # Phase 2 when HP <= 80%
HOLLOW_PHASE3_HP_RATIO = 0.6   # Phase 3 when HP <= 60%

# Boss #3 Advanced Tuning (all optional; safe defaults provided in code)
# Drift/Approach behavior
BOSS3_DRIFT_BLEND_TIME = 0.25
BOSS3_BASE_CY = 120.0
BOSS3_CHASE_RATE = 10.0
BOSS3_AMPLITUDE_SHRINK = 0.52
BOSS3_APPROACH_MIN = 0.05
BOSS3_APPROACH_MAX = 0.92
BOSS3_APPROACH_BASE = 0.22
BOSS3_APPROACH_PHASE = 0.38
BOSS3_APPROACH_DEADLINE = 0.38
BOSS3_APPROACH_STRESS = 0.18

# Safe radius (min separation) shrink
BOSS3_MIN_SEP_BASE = 260.0
BOSS3_MIN_SEP_PHASE = 160.0
BOSS3_MIN_SEP_DEADLINE = 140.0
BOSS3_MIN_SEP_STRESS = 80.0
BOSS3_MIN_SEP_MIN = 80.0
BOSS3_MIN_SEP_MAX = 260.0

# Vertical clamp dynamics
BOSS3_Y_MAX_BASE = 220.0
BOSS3_Y_MAX_DEADLINE_ADD = 160.0
BOSS3_Y_MAX_PHASE_ADD = 60.0
BOSS3_Y_MAX_MARGIN = 100.0  # bottom margin to keep boss above ground

# Calendar checkpoint drop impulse
BOSS3_DROP_IMPULSE_BASE = 160.0
BOSS3_DROP_IMPULSE_STEP = 60.0
BOSS3_DROP_DECAY = 220.0

# Backlog/procrastination boost
BOSS3_BACKLOG_BOOST_MULT = 1.5
BOSS3_BACKLOG_DURATION = 4.0

# Distraction Field (Poisson around player)
BOSS3_DISTRACTION_LAMBDA0 = 10.0
BOSS3_DISTRACTION_BOOST_FACTOR = 0.5

# Predictive Barrage (interception + homing)
BOSS3_PRED_FAKE_STRESS_T = 0.3
BOSS3_PRED_FAKE_PROB = 0.25
BOSS3_PRED_INTERVAL_BASE = 0.35
BOSS3_PRED_INTERVAL_BOOST = 0.32
BOSS3_PRED_EXTRA_SALVO = 1

# Log Spiral Burst
BOSS3_SPIRAL_OMEGA_BASE = 2.6
BOSS3_SPIRAL_OMEGA_DEADLINE = 1.6
BOSS3_SPIRAL_OMEGA_BOOST = 0.12
BOSS3_SPIRAL_K_BASE = 0.14
BOSS3_SPIRAL_K_STRESS = 0.10
BOSS3_SPIRAL_K_BOOST = 0.18
BOSS3_SPIRAL_BASE_SPEED_MULT = 0.55
BOSS3_SPIRAL_SPAWN_INTERVAL = 0.05
BOSS3_SPIRAL_DURATION = 1.8

# Rain Barrage
BOSS3_RAIN_LAMBDA0 = 22.0
BOSS3_RAIN_LAMBDA_DEADLINE = 0.8
BOSS3_RAIN_LAMBDA_STRESS = 0.6
BOSS3_RAIN_LAMBDA_BOOST = 0.4
BOSS3_RAIN_BIAS_PLAYER_MIX = 0.6
BOSS3_RAIN_BIAS_PLAYER_SIGMA = 120.0
BOSS3_RAIN_VX_JITTER = 40.0
BOSS3_RAIN_VY_BASE_MULT = 0.8
BOSS3_RAIN_VY_DEADLINE = 0.4
BOSS3_RAIN_DURATION_BASE = 1.6
BOSS3_RAIN_DURATION_STRESS = 0.3

# Bullet Configuration
BULLET_SPEEDS = {
    'normal': 250,    # Slightly increase boss bullet speed
    'homing': 180,    # Homing bullets slower but more dangerous
    'laser': 350,     # Laser faster
    'player': 450,    # Player bullets faster to maintain balance
    'void_shard': 320,
    'voidfire': 420
}

BULLET_DAMAGE = {
    'normal': 15,     # Increase boss bullet damage
    'homing': 18,     # Homing bullets more dangerous
    'laser': 20,      # Laser high damage
    'player': 12,     # Reduce player damage, requires more skill
    'void_shard': 16,
    'voidfire': 18
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
    'bullet_void_shard': (10, 10, 10),
    'bullet_voidfire': (170, 80, 255),
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

# Player idle penalty (anti-camping)
PLAYER_IDLE_THRESHOLD = 1.8  # seconds before penalty starts
PLAYER_IDLE_SHARD_INTERVAL = 0.5  # spawn shards this often while idle
PLAYER_IDLE_HEALTH_DRAIN = 4  # per second when idle; set to 0 to disable drain