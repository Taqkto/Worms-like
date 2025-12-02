import pygame

class character:
    
    
    def __init__(self, player_number, pos_x, pos_y, pos_z):


        self.image = pygame.image.load("assets/Worms/pngegg.png").convert_alpha()
        #self.skin = skin
        self.player_number = player_number

        self.pos_x = pos_x
        self.pos_y = pos_y
        self.pos_z = pos_z

        self.is_jumping = False
        self.jump_height = 60 
        self.jump_speed = 4   
        self.jump_origin = pos_y

        self.pv = 100
        self.alive = True

    def move_left(self):
        self.x -= 3

    def move_right(self):
        self.x += 3

    #appeler en 1er pui update jump a chaque frame
    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_origin = self.pos_y

    def update_jump(self):
        if self.is_jumping:
            #montée
            if self.y > self.jump_origin - self.jump_height and not hasattr(self, 'jump_peak'):
                self.y -= self.jump_speed
                if self.y <= self.jump_origin - self.jump_height:
                    self.jump_peak = True

            #descente
            elif hasattr(self, 'jump_peak'):
                self.y += self.jump_speed
                if self.y >= self.jump_origin:
                    self.y = self.jump_origin
                    self.is_jumping = False
                    del self.jump_peak

    def kill(self):
        self.pv = 0
        self.alive = False

    def draw(self, surface):
        surface.blit(self.image, (self.pos_x, self.pos_y))

            
