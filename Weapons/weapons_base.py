# python
# File: Weapons/weapons_base.py
from typing import Optional
import math
from config import GRAVITY, WIND, GROUND_RECT_Y, SCREEN_WIDTH, SPEED_SCALE, PROJECTILE_COLOR

class PROJECTILE:
    def __init__(self, nom: str, x: float, y: float, angle: float, force: float, terrain: Optional[object] = None):
        self.nom = nom
        self.x = float(x)
        self.y = float(y)
        self.angle = math.radians(angle)
        self.force = force

        v0 = force * SPEED_SCALE
        self.speedX = v0 * math.cos(self.angle)
        self.speedY = -v0 * math.sin(self.angle)

        self.radius = 5
        self.alive = True
        self.exploded = False

        # optional GridMap instance
        self.terrain = terrain

    def trigger_explosion(self) -> None:
        self.alive = False
        self.exploded = True

    def _ground_top_for_px(self, px: float) -> float:
        if self.terrain:
            try:
                return float(self.terrain.height_at(px)) - self.radius
            except Exception:
                return float(GROUND_RECT_Y) - self.radius
        return GROUND_RECT_Y - self.radius

    def ground_top_at(self, x: float | None = None) -> float:
        px = self.x if x is None else x
        return self._ground_top_for_px(px)

    def apply_gravity(self, dt: float) -> None:
        self.speedY += GRAVITY * dt

    def update_position(self, dt: float) -> None:
        self.x += self.speedX * dt
        self.y += self.speedY * dt

    def check_ground_collision(self) -> bool:
        """
        Check collision against terrain by sampling across projectile diameter (left, center, right).
        If any sampled column has ground that intersects the projectile, snap it to that ground_top and mark dead.
        """
        samples = [self.x - self.radius, self.x, self.x + self.radius]
        for sx in samples:
            ground_top = self._ground_top_for_px(sx)
            if self.y >= ground_top:
                self.y = ground_top
                self.alive = False
                return True
        return False

    def draw(self, screen) -> None:
        import pygame
        pygame.draw.circle(screen, PROJECTILE_COLOR, (int(self.x), int(self.y)), self.radius)

    def simulate_trajectory(self, steps: int = 400, dt: float = 0.02, wind: float = 0, time_scale: float = 1.0):
        points = []
        px = self.x
        py = self.y
        vx = self.speedX
        vy = self.speedY
        effective_dt = dt * time_scale

        max_x = self.terrain.width if self.terrain else SCREEN_WIDTH

        for _ in range(steps):
            vy += GRAVITY * effective_dt
            vx += wind * effective_dt

            new_px = px + vx * effective_dt
            new_py = py + vy * effective_dt

            # Screen bounds check
            if new_px < self.radius or new_px > max_x - self.radius:
                break

            # Check collision using block_at_pixel like actual projectiles
            if self.terrain:
                # Check horizontal collision
                check_x = new_px + self.radius if vx > 0 else new_px - self.radius
                for check_y in [py - self.radius, py, py + self.radius]:
                    block = self.terrain.block_at_pixel(check_x, check_y)
                    if block and block.solid:
                        return points

                # Check vertical collision
                check_y = new_py + self.radius if vy > 0 else new_py - self.radius
                for check_x in [px - self.radius, px, px + self.radius]:
                    block = self.terrain.block_at_pixel(check_x, check_y)
                    if block and block.solid:
                        return points
            else:
                # Fallback without terrain
                if new_py + self.radius >= GROUND_RECT_Y:
                    break

            px = new_px
            py = new_py
            points.append((int(px), int(py)))

        return points

