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
BOSS3_MAX_HEALTH = 1320
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

# Boss #3 Sprite / Animation
# Walk and Attack spritesheets and meta.
BOSS3_SPRITE_WALK_PATH = 'assets/sprites/boss/boss_hollow_walk.png'
BOSS3_WALK_FRAME_COUNT = 15
BOSS3_WALK_ANIM_FPS = 8
BOSS3_SPRITE_ATTACK_PATH = 'assets/sprites/boss/boss_hollow_attack.png'
BOSS3_ATTACK_FRAME_COUNT = 12
BOSS3_ATTACK_ANIM_FPS = 10
BOSS3_SPRITE_MARGIN_X = 0
BOSS3_SPRITE_MARGIN_Y = 0
BOSS3_SPRITE_SPACING_X = 0
BOSS3_SPRITE_SPACING_Y = 0
# Explicit frame size from provided resolution 3360x240 with 15 frames => 224x240
BOSS3_FRAME_W = 224
BOSS3_FRAME_H = 240

# Hollow direct chase tuning (enables stronger pursuit toward player center)
BOSS3_DIRECT_CHASE_ENABLE = True
BOSS3_DIRECT_CHASE_MIN_APPROACH = 0.88  # minimum mix toward player when enabled
BOSS3_DIRECT_CHASE_RATE = 5.0           # how fast center tracks desired position
BOSS3_DIRECT_CHASE_MIN_SEP = 120.0      # clamp on closest allowed distance

# Boss #2 (Sloth) – persistent ground zoning snail (balance pass v2, English comments)
# --- Sloth Difficulty Overhaul (v3) ---
# Increased durability & aggression
BOSS2_MAX_HEALTH = 920            # Much higher durability for extended pressure
BOSS2_MOVE_SPEED = 60              # Faster crawl encourages wider trail coverage
BOSS2_SLIME_COOLDOWN = 1         # Phase 1 base slime volley rate (was 2.0)
BOSS2_SLIME_COOLDOWN_P2 = 0.85     # Phase 2 faster slime volley rate (was 1.0)
BOSS2_PHASE2_HP_RATIO = 0.65       # Transition later to sustain P1 pressure longer (was 0.55)
BOSS2_SLIME_POOL_LIFETIME = 13.0   # Pools persist longer (was 11.0)
BOSS2_SLIME_TICK_DAMAGE = 80       # Pool tick damage increased (was 10)
BOSS2_SLIME_TICK_INTERVAL = 0.1   # Slightly faster ticking (was 0.45)
BOSS2_BODY_W = 160                 # Same sprite width
BOSS2_BODY_H = 110

# Sloth slime trail mechanics (forces constant player movement)
BOSS2_SLIME_TRAIL_SEG_W = 30       # Slightly wider segments for fewer safe gaps
BOSS2_SLIME_TRAIL_SEG_H = 20       # Slightly taller for clearer hazard
BOSS2_SLIME_TRAIL_DROP_DIST = 26   # Drops trail more frequently (was 30)
BOSS2_SLIME_TRAIL_LIFETIME = 18.0  # Trail persists longer (was 15.0)
BOSS2_SLIME_TRAIL_DPS = 20.0       # Baseline DPS up (was 16.0)
BOSS2_SLIME_TRAIL_IDLE_MULT = 3.4  # Idle punish stronger (was 2.8)
BOSS2_SLIME_TRAIL_SLOW = 0.30      # Slightly less slow so player can attempt escape (was 0.35)

# Sloth advanced difficulty tuning
BOSS2_ENRAGE_HP_RATIO = 0.5        # Enrage earlier (was 0.25) for longer high pressure end-phase
BOSS2_DASH_SPEED = 320              # Faster horizontal dash (was 260)
BOSS2_DASH_DURATION = 0.60          # Slightly longer dash presence (was 0.55)
BOSS2_DASH_COOLDOWN_P1 = 5.5        # More frequent dash phase 1 (was 7.0)
BOSS2_DASH_COOLDOWN_P2 = 3.6        # More frequent dash phase 2 (was 4.2)
BOSS2_DASH_COOLDOWN_ENRAGE = 2.2    # Enrage cadence (was 2.8)
BOSS2_ERUPTION_INTERVAL_P1 = 8.0    # Eruptions sooner (was 9.0)
BOSS2_ERUPTION_INTERVAL_P2 = 5.0    # Phase 2 (was 6.0)
BOSS2_ERUPTION_INTERVAL_ENRAGE = 3.2 # Enraged (was 4.0)
BOSS2_SPORE_COOLDOWN_P1 = 7.0       # Spore faster P1 (was 8.0)
BOSS2_SPORE_COOLDOWN_P2 = 4.6       # Phase 2 faster (was 5.5)
BOSS2_SPORE_COOLDOWN_ENRAGE = 3.0   # Enrage faster (was 3.5)
BOSS2_SPORE_FLOAT_TIME = 1.1        # Less hang time (was 1.3) to drop sooner
BOSS2_SPORE_COUNT_P1 = 4            # More spores P1 (was 3)
BOSS2_SPORE_COUNT_P2 = 6            # Phase 2 (was 5)
BOSS2_SPORE_COUNT_ENRAGE = 9        # Enrage burst (was 7)
BOSS2_ERUPTION_BURST_DAMAGE = 18    # Burst damage increased (was 12)
BOSS2_SLIME_VOLLEY_P1 = 7           # Slime globs phase 1 (was 6)
BOSS2_SLIME_VOLLEY_P2 = 11          # Phase 2 (was 9)
BOSS2_SLIME_VOLLEY_ENRAGE = 15      # Enrage volley size (was 12)

# Sloth per-attack fine tuning (extracted for data cleanliness)
# Slime Volley
BOSS2_SLIME_BASE_SPEED_P1 = 205      # Base horizontal projectile speed phase 1
BOSS2_SLIME_BASE_SPEED_P2 = 230      # Base horizontal projectile speed phase 2
BOSS2_SLIME_ENRAGE_SPEED_MULT = 1.12 # Multiplier when enraged
BOSS2_SLIME_SPEED_JITTER_LOW = -28   # Random add low
BOSS2_SLIME_SPEED_JITTER_HIGH = 42   # Random add high
BOSS2_SLIME_SPREAD_P1 = 0.90         # Horizontal spread angle span phase 1
BOSS2_SLIME_SPREAD_P2 = 1.10         # Spread angle span phase 2
BOSS2_SLIME_BASE_ANGLE = -1.05       # Central firing angle (radians)

# Dash
BOSS2_DASH_ENRAGE_SPEED_MULT = 1.25  # Additional speed multiplier while enraged

# Spore Attack
BOSS2_SPORE_SPREAD_P1 = 60           # Horizontal velocity range half-span phase 1/2
BOSS2_SPORE_SPREAD_ENRAGE = 80       # Wider spread when enraged
BOSS2_SPORE_VX_SLOW_DECAY = 0.98     # Horizontal decay while ascending (see bullets logic)
BOSS2_SPORE_VY_MIN = -65             # Upward velocity min
BOSS2_SPORE_VY_MAX = -40             # Upward velocity max
BOSS2_SPORE_POOL_TICK_INTERVAL = 0.3  # Seconds between spore pool damage ticks
BOSS2_SPORE_POOL_TICK_DAMAGE = 80      # Damage per tick for spore-derived pools

# Trail / Eruption & Enrage scaling
BOSS2_TRAIL_ENRAGE_DPS_MULT = 1.30   # Trail DPS multiplier when enraged
BOSS2_ERUPTION_TRAIL_AGE_ADD = 0.60  # Additional age added to segments on eruption burst

# Crush (Overhead Lazy Collapse) Attack
# The Sloth phases in above player then slams down, applying heavy burst damage and leaving a toxic pressure pool.
BOSS2_CRUSH_COOLDOWN = 11.0           # Base cooldown P1
BOSS2_CRUSH_COOLDOWN_P2 = 8.5         # Faster in phase 2
BOSS2_CRUSH_COOLDOWN_ENRAGE_MULT = 0.55  # Enrage reduces cooldown further
BOSS2_CRUSH_TELEGRAPH_TIME = 1.2      # Shadow warning duration before descent
BOSS2_CRUSH_HEIGHT = 320              # Vertical offset above ground before drop
BOSS2_CRUSH_IMPACT_DAMAGE_RATIO = 0.15  # % of player max HP on direct impact (lowered from 0.33)
BOSS2_CRUSH_IMPACT_RADIUS = 140       # Additional radius for shock damage (slightly less than full screen pressure)
BOSS2_CRUSH_POOL_WIDTH = 170          # Width of residual pressure pool
BOSS2_CRUSH_POOL_HEIGHT = 38          # Height of residual pool
BOSS2_CRUSH_POOL_LIFETIME = 11.0      # Duration of residual pool
BOSS2_CRUSH_POOL_DPS = 26.0           # Damage per second if player stands inside
BOSS2_CRUSH_POOL_IDLE_MULT = 1.9      # Idle multiplier (standing still inside pool)
BOSS2_GROUND_HEIGHT = 78              # Sloth battle ground platform height (for projectile pooling heuristics)

# Boss #2 Sprite sheets (generated by generate_sloth_sprites_v2.py)
BOSS2_SPRITE_WALK_PATH = 'assets/sprites/boss/boss_sloth_walk.png'
BOSS2_WALK_FRAME_COUNT = 8
BOSS2_WALK_ANIM_FPS = 7
BOSS2_SPRITE_ATTACK_PATH = 'assets/sprites/boss/boss_sloth_attack.png'
BOSS2_ATTACK_FRAME_COUNT = 6
BOSS2_ATTACK_ANIM_FPS = 8
BOSS2_SPRITE_FADE_PATH = 'assets/sprites/boss/boss_sloth_fade.png'
BOSS2_FADE_FRAME_COUNT = 6
BOSS2_FADE_ANIM_FPS = 6
BOSS2_FRAME_W = 160
BOSS2_FRAME_H = 110

# Bullet Configuration
BULLET_SPEEDS = {
    'normal': 250,    # Slightly increase boss bullet speed
    'homing': 180,    # Homing bullets slower but more dangerous
    'laser': 350,     # Laser faster
    'player': 450,    # Player bullets faster to maintain balance
    'void_shard': 320,
    'voidfire': 420,
    'slime': 120      # Sloth 粘液抛射速度较慢
}

BULLET_DAMAGE = {
    'normal': 15,     # Increase boss bullet damage
    'homing': 18,     # Homing bullets more dangerous
    'laser': 20,      # Laser high damage
    'player': 12,     # Reduce player damage, requires more skill
    'void_shard': 16,
    'voidfire': 18,
    'slime': 4        # 初次接触伤害较低，后续由池子持续 DOT（独立计算）
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
    'bullet_slime': (120, 200, 120),
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

# Hollow Battle Spike Configuration
HOLLOW_SPIKE_INTERVAL_P1 = 6.0   # seconds between spike waves phase 1
HOLLOW_SPIKE_INTERVAL_P2 = 4.5   # phase 2 faster
HOLLOW_SPIKE_INTERVAL_P3 = 3.2   # phase 3 fastest
HOLLOW_SPIKE_DURATION = 3.0      # duration for spikes to remain active
HOLLOW_SPIKE_WIDTH = 28          # spike base width
HOLLOW_SPIKE_GAP_MIN = 90        # minimum gap between spikes for player passage
HOLLOW_SPIKE_GAP_MAX = 140       # maximum gap size
HOLLOW_SPIKE_TOP_HEIGHT = 260    # top spikes hanging length
HOLLOW_SPIKE_BOTTOM_HEIGHT = 320 # bottom spikes rising length
HOLLOW_SPIKE_DAMAGE = 18         # damage if player overlaps