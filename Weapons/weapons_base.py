import math
from Config import GRAVITY

class projectiles:
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

        #taille du projectile
        self.radius = 5
        #savoir si le projectile est toujours présent
        self.alive = True

    # a faire quand character existe
    #def explode(self):
        #explosion simple kill no matter what dans la zone d'explosion
        #for c in characters:
            #dist = ((C.x - self.x)**2 + (c.y - self.y)**2)**0.5 #
            #if dist <= self.radius:
                #c.kill()

    def move(self, dt):
        self.speedY = self.speedY + GRAVITY * dt


    def draw(self,screen):
        import pygame
        pygame.draw.circle(screen,(255,120,0),(int(self.x),int(self.y)),int(self.force),self.radius)










