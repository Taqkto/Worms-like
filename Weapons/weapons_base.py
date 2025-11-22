import math
from Config import GRAVITY, WIND, GROUND_LEVEL, SCREEN_WIDTH


class PROJECTILE:
    #constructeur
    def __init__(self, nom, x, y, angle , force):
        self.nom = nom
        self.x = x
        self.y = y
        self.angle = math.radians(angle)
        self.force = force

        #déterminer la vitesse initiale
        self.speedX = force * math.cos(self.angle)
        self.speedY = -force * math.sin(self.angle)

        #taille de l'explosion du projectile
        self.radius = 5
        #savoir si le projectile est toujours présent
        self.alive = True

    # a faire quand character existe
    def explode(self, characters=None):
        #explosion simple kill no matter what dans la zone d'explosion
        for c in characters:
            dist = ((c.x - self.x)**2 + (c.y - self.y)**2)**0.5 #
            if dist <= self.radius:
                c.kill()

    def move(self, dt):
        #appliquer la gravité
        self.speedY = self.speedY + GRAVITY * dt

        #appliquer la force du vent sur les roquettes
        if self.nom  == "roquette":
            self.x += WIND * dt

        #mettre à jour la position
        self.x += self.speedX * dt
        self.y += self.speedY * dt

        # Collision sol
        if self.y >= GROUND_LEVEL:
            self.alive = False

        # Collision bords écran
        if self.x <= self.radius or self.x >= SCREEN_WIDTH - self.radius:
            self.alive = False

    def draw(self,screen):
        import pygame
        pygame.draw.circle(screen, (255, 120, 0), (int(self.x), int(self.y)), self.radius)









