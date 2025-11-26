from .weapons_base import PROJECTILE
from config import WIND, GROUND_LEVEL, SCREEN_WIDTH, GROUND_RECT_Y

class ROQUETTE(PROJECTILE):
    def __init__(self, x, y, angle, force):
        super().__init__("roquette", x, y, angle, force)

    def move(self, dt):
        # gravity
        self.apply_gravity(dt)

        # wind
        self.speedX += WIND * dt

        # update position
        self.update_position(dt)

        # collision with visible ground top
        if self.y >= (GROUND_RECT_Y - self.radius):
            self.alive = False

        # screen bounds (use SCREEN_WIDTH)
        if self.x <= self.radius or self.x >= SCREEN_WIDTH - self.radius:
            self.alive = False