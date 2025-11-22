import pygame
from pygame.locals import *


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.weight, self.height = 640, 400

        self.PROJECTILE = []

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        #test projectile creation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                from Weapons.weapons_base import PROJECTILE
                p = PROJECTILE("roquettes", 50, 300, 45, 50)
                self.PROJECTILE.append(p)

    def on_loop(self,dt):
        for p in self.PROJECTILE:
            p.move(dt)
        #retierer les projectiles morts
        self.PROJECTILE = [p for p in self.PROJECTILE if p.alive]

    def on_render(self):
        self._display_surf.fill((100, 149, 237))
        #afficher le sol
        pygame.draw.rect(self._display_surf, (34, 139, 34), (0, 350, self.weight, 50))
        #afficher les projectiles
        for p in self.PROJECTILE:
            p.draw(self._display_surf)
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        clock = pygame.time.Clock()

        if self.on_init() == False:
            self._running = False

        while (self._running):
            dt = clock.tick(60) / 1000

            for event in pygame.event.get():
                self.on_event(event)

            self.on_loop(dt)
            self.on_render()

        self.on_cleanup()


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()