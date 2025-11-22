import math
import pygame

from Config import WIND
from Weapons.grenade import GRENADE
from Weapons.roquette import ROQUETTE


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None

        self.size = self.width, self.height = 640, 400

        # Liste des projectiles en jeu
        self.projectiles = []

        # Paramètres pour l'arme équipée
        self.current_weapon = "roquette"  # ou "grenade"
        self.angle = 45
        self.force = 60

        self.show_aim = True  # pour afficher la trajectoire
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

            # TIR
            if event.key == pygame.K_SPACE:
                if self.current_weapon == "roquette":
                    p = ROQUETTE(self.player_x, self.player_y, self.angle, self.force)
                else:
                    p = GRENADE(self.player_x, self.player_y, self.angle, self.force)
                self.projectiles.append(p)

            # Ajuster la force
            if event.key == pygame.K_RIGHT:
                self.force = min(150, self.force + 2)
            if event.key == pygame.K_LEFT:
                self.force = max(10, self.force - 2)


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

        # afficher trajectoire de l’arme
        if self.show_aim:
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
