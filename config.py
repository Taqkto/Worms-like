GRAVITY = 9.8
WIND = 15
GROUND_LEVEL = 400
SCREEN_WIDTH = 800

# Physics / projectile tuning
PROJECTILE_TIME_SCALE = 7.0    # >1 = projectiles traverse their path faster
SPEED_SCALE = 0.5              # used to convert force -> initial velocity

# Player / input / weapon UI
PLAYER_START_X = 100
PLAYER_START_Y = 350
MIN_FORCE = 0
MAX_FORCE = 150
CHARGE_RATE = 50.0             # units of force per second while holding fire

# UI / HUD
BAR_W = 120
BAR_H = 10
BAR_OFFSET_Y = 60              # vertical offset above player to draw bar

# Ground / colors
GROUND_HEIGHT = 50
GROUND_RECT_Y = GROUND_LEVEL - GROUND_HEIGHT

SKY_COLOR = (100, 149, 237)
GROUND_COLOR = (34, 139, 34)
BAR_BG_COLOR = (50, 50, 50)
BAR_FILL_COLOR = (200, 30, 30)
BAR_BORDER_COLOR = (0, 0, 0)
PROJECTILE_COLOR = (255, 120, 0)
TRAJECTORY_COLOR = (255, 255, 255)

# tuning for bounce behavior on shallow impacts
MIN_BOUNCE_SPEED = 5.0          # minimal upward speed applied when forcing a bounce
HORIZONTAL_BOUNCE_MIN_SPEED = 0.0  # minimum horizontal speed to allow a bounce instead of explode
HORIZONTAL_DAMP = 0.7            # horizontal speed retained after bounce
VERTICAL_DAMP = 0.4              # vertical damping factor on bounce