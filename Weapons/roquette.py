from .weapons_base import PROJECTILE
from Config import WIND

GROUND_Y = 350

class ROQUETTE(PROJECTILE):
    def __init__(self, x, y, angle, force):
        super().__init__("roquette", x, y, angle, force)

    def move(self, dt):
        # gravité
        self.apply_gravity(dt)

        # vent (spécifique roquette)
        self.speedX += WIND * dt

        # mise à jour position
        self.update_position(dt)

        # collision sol == explosion
        if self.y >= GROUND_Y:
            self.alive = False

        # bord écran
        if self.x <= self.radius or self.x >= 640 - self.radius:
            self.alive = False