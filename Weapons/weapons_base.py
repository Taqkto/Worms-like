# Weapons/weapons_base.py
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

        # optional GridMap instance
        self.terrain = terrain

    def ground_top_at(self, x: float | None = None) -> float:
        px = self.x if x is None else x
        if self.terrain:
            return self.terrain.height_at(px) - self.radius
        return GROUND_RECT_Y - self.radius

    def apply_gravity(self, dt: float) -> None:
        self.speedY += GRAVITY * dt

    def update_position(self, dt: float) -> None:
        self.x += self.speedX * dt
        self.y += self.speedY * dt

    def check_ground_collision(self) -> bool:
        if self.terrain:
            ground_top = self.terrain.height_at(self.x) - self.radius
            if self.y >= ground_top:
                self.y = ground_top
                self.alive = False
                return True
            return False
        else:
            ground_top = GROUND_RECT_Y - self.radius
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
        ground_top_start = (self.terrain.height_at(px) - self.radius) if self.terrain else (GROUND_RECT_Y - self.radius)
        if py >= ground_top_start:
            py = ground_top_start - 1.0

        for _ in range(steps):
            vy += GRAVITY * effective_dt
            vx += wind * effective_dt

            px += vx * effective_dt
            py += vy * effective_dt

            if px < 0 or px > max_x:
                break

            ground_top = (self.terrain.height_at(px) - self.radius) if self.terrain else (GROUND_RECT_Y - self.radius)
            if py >= ground_top:
                break

            points.append((int(px), int(py)))

        return points
