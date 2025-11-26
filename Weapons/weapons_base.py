from config import GRAVITY, WIND, GROUND_LEVEL, SCREEN_WIDTH, SPEED_SCALE, PROJECTILE_COLOR, GROUND_RECT_Y
import math

class PROJECTILE:
    def __init__(self, nom, x, y, angle, force):
        self.nom = nom
        self.x = x
        self.y = y

        self.angle = math.radians(angle)
        self.force = force

        # use SPEED_SCALE from config
        v0 = force * SPEED_SCALE

        self.speedX = v0 * math.cos(self.angle)
        self.speedY = -v0 * math.sin(self.angle)

        self.radius = 5
        self.alive = True

    def apply_gravity(self, dt):
        self.speedY += GRAVITY * dt

    def update_position(self, dt):
        self.x += self.speedX * dt
        self.y += self.speedY * dt

    def check_ground_collision(self):
        # Use top-of-visible-ground for physics collision
        ground_top = GROUND_RECT_Y - self.radius
        if self.y >= ground_top:
            self.y = ground_top
            self.alive = False

    def draw(self, screen):
        import pygame
        pygame.draw.circle(screen, PROJECTILE_COLOR, (int(self.x), int(self.y)), self.radius)

    def simulate_trajectory(self, steps=400, dt=0.02, wind=0, time_scale=1.0):
        """
        Return simulated points for preview. Start slightly above visible ground if the
        projectile spawn Y is on the ground to avoid an empty trajectory.
        """
        points = []

        px = self.x
        py = self.y
        vx = self.speedX
        vy = self.speedY

        effective_dt = dt * time_scale
        ground_top = GROUND_RECT_Y - self.radius

        # If preview starts on/under ground top (player stands on ground), nudge it up a bit
        if py >= ground_top:
            py = ground_top - 1.0

        for _ in range(steps):
            vy += GRAVITY * effective_dt
            vx += wind * effective_dt

            px += vx * effective_dt
            py += vy * effective_dt

            # stop when out of horizontal bounds or hitting visible ground top
            if px < 0 or px > SCREEN_WIDTH:
                break
            if py >= ground_top:
                break

            points.append((int(px), int(py)))

        return points