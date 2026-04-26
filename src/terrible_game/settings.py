WIDTH = 1280
HEIGHT = 720
FPS = 60
TITLE = "Mario's All-Nighter: Survivors"

# Player default properties
PLAYER_SPEED = 5
PROJECTILE_SPEED = 15
FIRE_RATE = 500 # ms between shots
PROJECTILE_DAMAGE = 1

# Balance: passive energy drain and incoming damage to the player
ENERGY_DRAIN_PER_FRAME = 0.01
PLAYER_ENEMY_TOUCH_DAMAGE = 6
ENEMY_BULLET_DAMAGE = 4

# Physics: knockback (on hit from player), projectiles, bombs
KNOCKBACK_BASE = 5.0
KNOCKBACK_FRICTION = 0.86
PENCIL_GRAVITY = 0.11  # top-down: pulls projectiles in +world Y
BOMB_TOSS_MAX_SPEED = 3.2
BOMB_DRAG = 0.985
BOMB_KNOCKBACK = 2.0
ENEMY_BULLET_HOMING = 0.14  # 0 = straight, higher = more curve toward player
MAX_WEAPON_SLOTS = 9

# Linked teleporter pads: pair members are this far apart; hop uses cooldown + nudge
TELEPORT_PAIR_SPACING = 260
TELEPORT_NUDGE = 48
TELEPORT_COOLDOWN_MS = 700

# Minimap (player-centered; world radius maps to edge of inner circle)
MINIMAP_SIZE = 200
MINIMAP_MARGIN = 14
MINIMAP_WORLD_RADIUS = 880.0

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
BGCOLOR = (30, 30, 40)

# Metaprogression shop (max level per upgrade, cost = SHOP_BASE_COST * (1 + current_level))
SHOP_MAX_LEVEL = 20
SHOP_BASE_COST = 50

SHOP_UPGRADES = (
    ("damage", "Global Damage", "+1 to all attack damage per level"),
    ("speed", "Global Speed", "+10% move speed per level"),
    ("energy", "Starting Energy", "+20 max energy per level"),
)

# Zones Config (Time-based progression)
# Swarms are massive, spawn rate is incredibly low.
ZONES = [
    {
        "name": "Evening",
        "bg_color": (30, 30, 40),
        "time_thresh": 0,
        "enemy_spawn_rate": 800, 
        "drink_chance": 0.05,
    },
    {
        "name": "Midnight",
        "bg_color": (20, 10, 40),
        "time_thresh": 60000, 
        "enemy_spawn_rate": 300,
        "drink_chance": 0.03,
    },
    {
        "name": "3 AM",
        "bg_color": (10, 5, 20),
        "time_thresh": 120000, 
        "enemy_spawn_rate": 100,
        "drink_chance": 0.01,
    },
    {
        "name": "The Grind",
        "bg_color": (0, 0, 0),
        "time_thresh": 180000, 
        "enemy_spawn_rate": 40,
        "drink_chance": 0.005,
    }
]
