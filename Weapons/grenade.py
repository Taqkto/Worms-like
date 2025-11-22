from .weapons_base import PROJECTILE
from Config import GRAVITY, GROUND_LEVEL


class GRENADE(PROJECTILE):
    def __init__(self,x, y, angle , force):
        super().__init__("grenade", x, y, angle, force)
        self.timer = 3.0  # seconds before explosion


    def move(self, dt):
        # tick du timer
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False
            return

        # gravité
        self.apply_gravity(dt)

        # mise à jour position
        self.update_position(dt)

        # rebond au sol
        if self.y >= GROUND_LEVEL:
            self.y = GROUND_LEVEL
            self.speedY *= -0.4  # rebond amorti
            self.speedX *= 0.7  # perte vitesse horizontale

            # si vitesse trop faible -> explosion
            if abs(self.speedY) < 20:
                self.alive = False
