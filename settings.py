WIDTH = 1280
HEIGHT = 720
FPS = 60
TITLE = "Mario's All-Nighter: Survivors"

# Player default properties
PLAYER_SPEED = 5
PROJECTILE_SPEED = 15
FIRE_RATE = 500 # ms between shots
PROJECTILE_DAMAGE = 1

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
BGCOLOR = (30, 30, 40)

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
