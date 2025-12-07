from .weapons_base import PROJECTILE
from config import WIND, SCREEN_WIDTH, GROUND_RECT_Y

class ROQUETTE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None):
        super().__init__("roquette", x, y, angle, force, terrain=terrain)

    def move(self, dt: float) -> None:
        self.apply_gravity(dt)
        self.speedX += WIND * dt
        self.update_position(dt)

        if self.terrain:
            ground_top = self.terrain.height_at(self.x) - self.radius
            if self.y >= ground_top:
                self.y = ground_top
                self.trigger_explosion()
        else:
            if self.y >= (GROUND_RECT_Y - self.radius):
                self.y = GROUND_RECT_Y - self.radius
                self.trigger_explosion()

        max_x = self.terrain.width if self.terrain else SCREEN_WIDTH
        if self.x <= self.radius or self.x >= max_x - self.radius:
            self.trigger_explosion()