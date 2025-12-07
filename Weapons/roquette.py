from .weapons_base import PROJECTILE
from config import WIND, SCREEN_WIDTH, GROUND_RECT_Y


class ROQUETTE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None, characters=None):
        super().__init__("roquette", x, y, angle, force, terrain=terrain)
        self.explosion_radius = 50
        self.characters = characters or []

    def _check_horizontal_collision(self, new_x: float) -> bool:
        """Check if moving to new_x would hit a solid block."""
        if not self.terrain:
            return False

        check_heights = [
            self.y - self.radius,
            self.y,
            self.y + self.radius,
        ]

        if new_x > self.x:
            check_x = new_x + self.radius
        else:
            check_x = new_x - self.radius

        for check_y in check_heights:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    def _check_vertical_collision(self, new_y: float) -> bool:
        """Check if moving to new_y would hit a solid block (ground or ceiling)."""
        if not self.terrain:
            return new_y + self.radius >= GROUND_RECT_Y

        check_positions = [
            self.x - self.radius,
            self.x,
            self.x + self.radius,
        ]

        if self.speedY > 0:
            check_y = new_y + self.radius
        else:
            check_y = new_y - self.radius

        for check_x in check_positions:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    def _check_character_collision(self) -> bool:
        """Check if rocket hits any character."""
        for char in self.characters:
            if not char.alive:
                continue
            # Character bounding box
            char_left = char.pos_x
            char_right = char.pos_x + char.width
            char_top = char.pos_y
            char_bottom = char.pos_y + char.height

            # Check if projectile circle intersects character rectangle
            closest_x = max(char_left, min(self.x, char_right))
            closest_y = max(char_top, min(self.y, char_bottom))

            dist_x = self.x - closest_x
            dist_y = self.y - closest_y
            distance = (dist_x ** 2 + dist_y ** 2) ** 0.5

            if distance <= self.radius:
                return True

        return False

    def move(self, dt: float) -> None:
        self.apply_gravity(dt)
        self.speedX += WIND * dt

        new_x = self.x + self.speedX * dt
        new_y = self.y + self.speedY * dt

        if self._check_horizontal_collision(new_x):
            self.trigger_explosion()
            return
        else:
            self.x = new_x

        if self._check_vertical_collision(new_y):
            self.trigger_explosion()
            return
        else:
            self.y = new_y

        # Check character collision after position update
        if self._check_character_collision():
            self.trigger_explosion()
            return

        max_x = self.terrain.width if self.terrain else SCREEN_WIDTH
        if self.x <= self.radius or self.x >= max_x - self.radius:
            self.trigger_explosion()