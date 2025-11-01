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

# Boss Configuration - Procrastinator (Boss #2)
# Tunable knobs for stress/deadline-driven boss
BOSS2_MAX_HEALTH = 520
BOSS2_MOVE_SPEED = 110
BOSS2_COOLDOWN_P1 = 1.8
BOSS2_COOLDOWN_P2 = 1.2
BOSS2_COOLDOWN_P3 = 0.9
BOSS2_TELEGRAPH_BASE = 1.1
BOSS2_HOMING_BASE_SPEED = 200
BOSS2_LASER_BASE_SPEED = 360
DEADLINE_SECONDS = 120

# Boss #2 Advanced Tuning (all optional; safe defaults provided in code)
# Drift/Approach behavior
BOSS2_DRIFT_BLEND_TIME = 0.25
BOSS2_BASE_CY = 120.0
BOSS2_CHASE_RATE = 3.0
BOSS2_AMPLITUDE_SHRINK = 0.52
BOSS2_APPROACH_MIN = 0.05
BOSS2_APPROACH_MAX = 0.92
BOSS2_APPROACH_BASE = 0.22
BOSS2_APPROACH_PHASE = 0.38
BOSS2_APPROACH_DEADLINE = 0.38
BOSS2_APPROACH_STRESS = 0.18

# Safe radius (min separation) shrink
BOSS2_MIN_SEP_BASE = 260.0
BOSS2_MIN_SEP_PHASE = 160.0
BOSS2_MIN_SEP_DEADLINE = 140.0
BOSS2_MIN_SEP_STRESS = 80.0
BOSS2_MIN_SEP_MIN = 80.0
BOSS2_MIN_SEP_MAX = 260.0

# Vertical clamp dynamics
BOSS2_Y_MAX_BASE = 220.0
BOSS2_Y_MAX_DEADLINE_ADD = 160.0
BOSS2_Y_MAX_PHASE_ADD = 60.0
BOSS2_Y_MAX_MARGIN = 100.0  # bottom margin to keep boss above ground

# Calendar checkpoint drop impulse
BOSS2_DROP_IMPULSE_BASE = 160.0
BOSS2_DROP_IMPULSE_STEP = 60.0
BOSS2_DROP_DECAY = 220.0

# Procrastination backlog boost
BOSS2_BACKLOG_BOOST_MULT = 1.5
BOSS2_BACKLOG_DURATION = 4.0

# Distraction Field (Poisson around player)
BOSS2_DISTRACTION_LAMBDA0 = 10.0
BOSS2_DISTRACTION_BOOST_FACTOR = 0.5

# Predictive Barrage (interception + homing)
BOSS2_PRED_FAKE_STRESS_T = 0.3
BOSS2_PRED_FAKE_PROB = 0.25
BOSS2_PRED_INTERVAL_BASE = 0.35
BOSS2_PRED_INTERVAL_BOOST = 0.32
BOSS2_PRED_EXTRA_SALVO = 1

# Log Spiral Burst
BOSS2_SPIRAL_OMEGA_BASE = 2.6
BOSS2_SPIRAL_OMEGA_DEADLINE = 1.6
BOSS2_SPIRAL_OMEGA_BOOST = 0.12
BOSS2_SPIRAL_K_BASE = 0.14
BOSS2_SPIRAL_K_STRESS = 0.10
BOSS2_SPIRAL_K_BOOST = 0.18
BOSS2_SPIRAL_BASE_SPEED_MULT = 0.55
BOSS2_SPIRAL_SPAWN_INTERVAL = 0.05
BOSS2_SPIRAL_DURATION = 1.8

# Rain Barrage
BOSS2_RAIN_LAMBDA0 = 22.0
BOSS2_RAIN_LAMBDA_DEADLINE = 0.8
BOSS2_RAIN_LAMBDA_STRESS = 0.6
BOSS2_RAIN_LAMBDA_BOOST = 0.4
BOSS2_RAIN_BIAS_PLAYER_MIX = 0.6
BOSS2_RAIN_BIAS_PLAYER_SIGMA = 120.0
BOSS2_RAIN_VX_JITTER = 40.0
BOSS2_RAIN_VY_BASE_MULT = 0.8
BOSS2_RAIN_VY_DEADLINE = 0.4
BOSS2_RAIN_DURATION_BASE = 1.6
BOSS2_RAIN_DURATION_STRESS = 0.3

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