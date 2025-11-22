import math
from Config import GRAVITY, WIND, GROUND_LEVEL, SCREEN_WIDTH


class PROJECTILE:
    def __init__(self, nom, x, y, angle, force):
        self.nom = nom
        self.x = x
        self.y = y

        self.angle = math.radians(angle)
        self.force = force

        # Convertir la force en vitesse réelle sinon c'est trop rapide
        SPEED_SCALE = 0.5
        v0 = force * SPEED_SCALE

        self.speedX = v0 * math.cos(self.angle)
        self.speedY = -v0 * math.sin(self.angle)

        self.radius = 5
        self.alive = True

    # ---------------------------------------------------------
    #  PHYSIQUE
    # ---------------------------------------------------------
    def apply_gravity(self, dt):
        self.speedY += GRAVITY * dt

    def update_position(self, dt):
        self.x += self.speedX * dt
        self.y += self.speedY * dt

    def check_ground_collision(self):
        if self.y >= GROUND_LEVEL - self.radius:
            self.alive = False

    # ---------------------------------------------------------
    #  EXPLOSION DU PROJECTILE
    # ---------------------------------------------------------
    def explode(self, characters=None):
        if characters is None:
            return
        for c in characters:
            dist = math.hypot(c.x - self.x, c.y - self.y)
            if dist <= self.radius:
                c.kill()

    # ---------------------------------------------------------
    #  DESSIN DU PROJECTILE
    # ---------------------------------------------------------
    def draw(self, screen):
        import pygame
        pygame.draw.circle(screen, (255, 120, 0), (int(self.x), int(self.y)), self.radius)

    # ---------------------------------------------------------
    #  TRAJECTOIRE AVANT TIR — VERSION PRO
    # ---------------------------------------------------------
    def simulate_trajectory(self, steps=80, dt=0.1, wind=0):
        """
        Retourne une liste de points simulés.
        La simulation est indépendante de la vraie position du projectile.
        """
        points = []

        # Copies locales (pour ne pas modifier l'état réel)
        px = self.x
        py = self.y
        vx = self.speedX
        vy = self.speedY

        for _ in range(steps):
            # appliquer la physique de manière stable
            vy += GRAVITY * dt
            vx += wind * dt

            px += vx * dt
            py += vy * dt

            if px < 0 or px > SCREEN_WIDTH:
                break
            if py >= GROUND_LEVEL:
                break

            points.append((int(px), int(py)))

        return points
