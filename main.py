import math
import pygame

from Config import WIND
from Weapons.grenade import GRENADE
from Weapons.roquette import ROQUETTE


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None

        self.size = self.width, self.height = 1280, 800

        # Liste des projectiles en jeu
        self.projectiles = []

        # Paramètres pour l'arme équipée
        self.current_weapon = "roquette"  # ou "grenade"
        self.angle = 80
        self.force = 60

        # Charging (left click)
        self.charging = False
        self.min_force = 10
        self.max_force = 150
        self.charge_rate = 50.0  # units of force per second while holding left click

        self.player_x = 100
        self.player_y = 350


    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
        pygame.mouse.set_visible(True)


    # --------------------------------------------------------
    # GESTION DES INPUTS
    # --------------------------------------------------------
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        if event.type == pygame.KEYDOWN:

            # Changer d’arme
            if event.key == pygame.K_r:
                self.current_weapon = "roquette"
            if event.key == pygame.K_g:
                self.current_weapon = "grenade"

            # Ajuster la force
            if event.key == pygame.K_RIGHT:
                self.force = min(self.max_force, self.force + 2)
            if event.key == pygame.K_LEFT:
                self.force = max(self.min_force, self.force - 2)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # clic gauche -> start charging
                self.charging = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.charging:
                if self.current_weapon == "roquette":
                    p = ROQUETTE(self.player_x, self.player_y, self.angle, self.force)
                else:
                    p = GRENADE(self.player_x, self.player_y, self.angle, self.force)
                self.projectiles.append(p)
                self.charging = False
                # reset to minimum after firing so the bar shows empty
                self.force = self.min_force


    # --------------------------------------------------------
    # LOGIQUE / PHYSIQUE
    # --------------------------------------------------------
    def on_loop(self, dt):
        # --- Mise à jour de l'angle avec la souris ---
        mx, my = pygame.mouse.get_pos()
        dx = mx - self.player_x
        dy = self.player_y - my  # inversé car Pygame Y descend vers le bas
        if dx != 0:
            self.angle = math.degrees(math.atan2(dy, dx))
            self.angle = max(5, min(85, self.angle))

        # --- charging logic: increase force while holding left click ---
        if self.charging:
            self.force = min(self.max_force, self.force + self.charge_rate * dt)

        # --- physique des projectiles ---
        for p in self.projectiles:
            p.apply_gravity(dt)
            if p.nom == "roquette":
                p.speedX += WIND * dt
            p.update_position(dt)
            p.check_ground_collision()

        # nettoyage
        self.projectiles = [p for p in self.projectiles if p.alive]


    # --------------------------------------------------------
    # AFFICHAGE
    # --------------------------------------------------------
    def on_render(self):
        self._display_surf.fill((100, 149, 237))

        # sol
        pygame.draw.rect(self._display_surf, (34, 139, 34), (0, 350, self.width, 50))

        # afficher trajectoire uniquement quand clic gauche est tenu
        if self.charging:
            preview = ROQUETTE(self.player_x, self.player_y, self.angle, self.force) \
                      if self.current_weapon == "roquette" else \
                      GRENADE(self.player_x, self.player_y, self.angle, self.force)

            points = preview.simulate_trajectory(
                wind=WIND if self.current_weapon == "roquette" else 0
            )

            for (px, py) in points:
                pygame.draw.circle(self._display_surf, (255, 255, 255), (px, py), 2)

        # projectiles
        for p in self.projectiles:
            p.draw(self._display_surf)

        # draw charge bar above player
        bar_w = 120
        bar_h = 10
        bar_x = int(self.player_x - bar_w / 2)
        bar_y = int(self.player_y - 60)
        # background
        pygame.draw.rect(self._display_surf, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        # filled portion based on force
        ratio = (self.force - self.min_force) / (self.max_force - self.min_force)
        ratio = max(0.0, min(1.0, ratio))
        fill_w = int(bar_w * ratio)
        pygame.draw.rect(self._display_surf, (200, 30, 30), (bar_x, bar_y, fill_w, bar_h))
        # thin border
        pygame.draw.rect(self._display_surf, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), 1)

        pygame.display.flip()


    # --------------------------------------------------------
    # CLEANUP
    # --------------------------------------------------------
    def on_cleanup(self):
        pygame.quit()


    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------
    def on_execute(self):
        clock = pygame.time.Clock()

        if self.on_init() == False:
            self._running = False

        while self._running:
            dt = clock.tick(60) / 1000

            for event in pygame.event.get():
                self.on_event(event)

            self.on_loop(dt)
            self.on_render()

        self.on_cleanup()


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()