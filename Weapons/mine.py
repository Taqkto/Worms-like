import pygame
import math

class Mine:
    def __init__(self, x, y, facing_left, terrain, characters):
        self.nom = "mine"
        self.x = float(x)
        self.y = float(y)
        self.facing_left = facing_left
        self.terrain = terrain
        self.characters = characters  # alliés + ennemis

        self.radius = 8  # rayon collision/placement
        self.explosion_radius = 40 
        self.armed = False
        self.arm_time = 5.0  # secondes pour armer

        # Sprites
        self.sprite_off = pygame.image.load("Assets/projectiles/mine_off.png").convert_alpha()
        self.sprite_on  = pygame.image.load("Assets/projectiles/mine_on.png").convert_alpha()

        self.sprite_off = pygame.transform.scale(self.sprite_off, (20,20))
        self.sprite_on  = pygame.transform.scale(self.sprite_on,  (20,20))

        self.exploded = False
        self.alive = True

    def move(self, dt):
        
        if not self.alive:
            return

        # armement
        if not self.armed:
            self.arm_time -= dt
            if self.arm_time <= 0:
                self.armed = True

        # détection contact seulement si armée
        if self.armed:
            for c in self.characters:
                if not c.alive:
                    continue
                cx = c.pos_x + c.width/2
                cy = c.pos_y + c.height/2
                dist = math.hypot(cx - self.x, cy - self.y)
                if dist <= 25: 
                    self.exploded = True
                    self.alive = False
                    return

    def draw(self, screen):
        if not self.alive:
            return

        sprite = self.sprite_on if self.armed else self.sprite_off
        w, h = sprite.get_size()
        screen.blit(sprite, (int(self.x - w/2), int(self.y - h/2)))
