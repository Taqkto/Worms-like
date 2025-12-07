# Weapons/grenade.py
from .weapons_base import PROJECTILE
from config import GROUND_RECT_Y, MIN_BOUNCE_SPEED, HORIZONTAL_BOUNCE_MIN_SPEED, HORIZONTAL_DAMP, VERTICAL_DAMP


class GRENADE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None):
        super().__init__("grenade", x, y, angle, force, terrain=terrain)
        self.timer = 3.0
        self.explosion_radius = 60

    def _check_horizontal_collision(self, new_x: float) -> bool:
        """Check if moving to new_x would hit a solid block."""
        if not self.terrain:
            return False

        # Check at multiple heights around the projectile
        check_heights = [
            self.y - self.radius,
            self.y,
            self.y + self.radius,
        ]

        # Determine which edge to check based on direction
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

        if self.speedY > 0:  # Falling - check bottom edge
            check_y = new_y + self.radius
        else:  # Rising - check top edge
            check_y = new_y - self.radius

        for check_x in check_positions:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    def move(self, dt: float, real_dt: float | None = None) -> None:
        timer_dt = real_dt if real_dt is not None else dt
        self.timer -= timer_dt
        if self.timer <= 0:
            self.trigger_explosion()
            return

        self.apply_gravity(dt)

        new_x = self.x + self.speedX * dt
        new_y = self.y + self.speedY * dt

        # Check horizontal collision (walls)
        if self._check_horizontal_collision(new_x):
            self.speedX = -self.speedX * HORIZONTAL_DAMP
        else:
            self.x = new_x

        # Check vertical collision (ground/ceiling)
        if self._check_vertical_collision(new_y):
            if self.speedY > 0:  # Falling - hit ground
                if self.terrain:
                    ground_top = self.terrain.height_at(self.x) - self.radius
                else:
                    ground_top = GROUND_RECT_Y - self.radius
                self.y = ground_top

                post_vy = -abs(self.speedY) * VERTICAL_DAMP

                if abs(post_vy) < MIN_BOUNCE_SPEED:
                    if abs(self.speedX) >= HORIZONTAL_BOUNCE_MIN_SPEED:
                        self.speedY = -MIN_BOUNCE_SPEED
                        self.speedX *= HORIZONTAL_DAMP
                    else:
                        self.trigger_explosion()
                else:
                    self.speedY = post_vy
                    self.speedX *= HORIZONTAL_DAMP
            else:  # Rising - hit ceiling
                # Find ceiling and snap below it
                self.speedY = abs(self.speedY) * VERTICAL_DAMP
                # Don't update y - stay at current position
        else:
            self.y = new_y

    def draw(self, screen) -> None:
        import pygame
        super().draw(screen)
        if self.alive:
            remaining = max(0.0, self.timer)
            text = f"{remaining:.1f}s"
            font = pygame.font.SysFont(None, 18)
            text_surf = font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(int(self.x), int(self.y - self.radius - 12)))
            bg_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            screen.blit(text_surf, text_rect)
