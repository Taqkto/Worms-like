from .weapons_base import PROJECTILE
from config import WIND, SCREEN_WIDTH, GROUND_RECT_Y, GRAVITY


class ROQUETTE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None, characters=None):
        super().__init__("roquette", x, y, angle, force, terrain=terrain)
        self.explosion_radius = 50
        self.characters = characters or []

    def _check_horizontal_collision(self, new_x: float) -> bool:
        if not self.terrain:
            return False
        check_heights = [self.y - self.radius, self.y, self.y + self.radius]
        check_x = new_x + self.radius if new_x > self.x else new_x - self.radius
        for check_y in check_heights:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True
        return False

    def _check_vertical_collision(self, new_y: float) -> bool:
        if not self.terrain:
            return new_y + self.radius >= GROUND_RECT_Y
        check_positions = [self.x - self.radius, self.x, self.x + self.radius]
        check_y = new_y + self.radius if self.speedY > 0 else new_y - self.radius
        for check_x in check_positions:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True
        return False

    def _check_character_collision(self) -> bool:
        for char in self.characters:
            if not char.alive:
                continue
            char_left, char_right = char.pos_x, char.pos_x + char.width
            char_top, char_bottom = char.pos_y, char.pos_y + char.height
            closest_x = max(char_left, min(self.x, char_right))
            closest_y = max(char_top, min(self.y, char_bottom))
            distance = ((self.x - closest_x) ** 2 + (self.y - closest_y) ** 2) ** 0.5
            if distance <= self.radius:
                return True
        return False

    def move(self, dt: float) -> None:
        # Vent (sans effet de l'eau)
        self.speedX += WIND * dt

        # Gravité normale
        self.apply_gravity(dt)

        # === MOUVEMENT ===
        new_x = self.x + self.speedX * dt
        new_y = self.y + self.speedY * dt

        # === COLLISIONS ===
        if self._check_horizontal_collision(new_x):
            self.trigger_explosion()
            return
        self.x = new_x

        if self._check_vertical_collision(new_y):
            self.trigger_explosion()
            return
        self.y = new_y

        if self._check_character_collision():
            self.trigger_explosion()
            return

        # Sortie de l'écran
        max_x = self.terrain.width if self.terrain else SCREEN_WIDTH
        if self.x <= self.radius or self.x >= max_x - self.radius:
            self.trigger_explosion()

        # Sortie par le bas de l'écran
        max_y = self.terrain.height if self.terrain else 600
        if self.y >= max_y:
            self.trigger_explosion()
