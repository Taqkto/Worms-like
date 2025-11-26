import math
import pygame

from config import (
    WIND,
    PROJECTILE_TIME_SCALE,
    PLAYER_START_X,
    PLAYER_START_Y,
    MIN_FORCE,
    MAX_FORCE,
    CHARGE_RATE,
    BAR_W,
    BAR_H,
    BAR_OFFSET_Y,
    SKY_COLOR,
    GROUND_COLOR,
    BAR_BG_COLOR,
    BAR_FILL_COLOR,
    BAR_BORDER_COLOR,
    GROUND_RECT_Y,
    TRAJECTORY_COLOR,
)
from Weapons.grenade import GRENADE
from Weapons.roquette import ROQUETTE


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None

        self.size = self.width, self.height = 1280, 800

        # Liste des projectiles en jeu
        self.projectiles = []

        # Charging (left click)
        self.charging = False
        self.min_force = MIN_FORCE
        self.max_force = MAX_FORCE
        self.charge_rate = CHARGE_RATE  # units of force per second while holding left click

        # Start with the bar empty
        self.force = self.min_force

        # Paramètres pour l'arme équipée
        self.current_weapon = "roquette"  # ou "grenade"
        self.angle = 80

        self.player_x = PLAYER_START_X
        self.player_y = min(PLAYER_START_Y, GROUND_RECT_Y - 20)  # fais en sorte que le joueur soit au-dessus du sol

        # use config time scale
        self.projectile_time_scale = PROJECTILE_TIME_SCALE

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

                # Nudge spawned projectile above visible ground so it doesn't instantly collide
                try:
                    ground_top = GROUND_RECT_Y - p.radius
                    if p.y >= ground_top:
                        p.y = ground_top - 1.0
                except Exception:
                    # safe fallback if p has no radius for some reason
                    pass

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

        # scale dt for projectile physics so trajectory shape is preserved but faster
        scaled_dt = dt * self.projectile_time_scale

        # --- physique des projectiles ---
        for p in self.projectiles:
            # Prefer weapon-specific move(dt) which handles timer, bounces, wind, etc.
            if hasattr(p, "move"):
                # keep grenade timer driven by real time (so explosion timing doesn't artificially speed up)
                if getattr(p, "nom", "") == "grenade":
                    # pass both scaled dt for movement and real dt for timer
                    p.move(scaled_dt, real_dt=dt)
                else:
                    p.move(scaled_dt)
            else:
                # fallback: keep previous behaviour for generic projectiles
                p.apply_gravity(dt)
                if getattr(p, "nom", "") == "roquette":
                    p.speedX += WIND * scaled_dt
                p.update_position(scaled_dt)
                p.check_ground_collision()

        # nettoyage
        self.projectiles = [p for p in self.projectiles if p.alive]

    # --------------------------------------------------------
    # AFFICHAGE
    # --------------------------------------------------------
    def on_render(self):
        self._display_surf.fill(SKY_COLOR)

        # ground
        pygame.draw.rect(self._display_surf, GROUND_COLOR, (0, GROUND_RECT_Y, self.width, self.height - GROUND_RECT_Y))

        # afficher trajectoire uniquement quand clic gauche est tenu
        if self.charging:
            preview = ROQUETTE(self.player_x, self.player_y, self.angle, self.force) \
                if self.current_weapon == "roquette" else \
                GRENADE(self.player_x, self.player_y, self.angle, self.force)

            points = preview.simulate_trajectory(
                wind=WIND if self.current_weapon == "roquette" else 0,
                time_scale=self.projectile_time_scale
            )

            for (px, py) in points:
                pygame.draw.circle(self._display_surf, TRAJECTORY_COLOR, (px, py), 2)

        # projectiles
        for p in self.projectiles:
            p.draw(self._display_surf)

        # draw charge bar above player
        bar_x = int(self.player_x - BAR_W / 2)
        bar_y = int(self.player_y - BAR_OFFSET_Y)
        # background
        pygame.draw.rect(self._display_surf, BAR_BG_COLOR, (bar_x, bar_y, BAR_W, BAR_H))
        # filled portion based on force (safe denominator)
        denom = max(1e-6, (self.max_force - self.min_force))
        ratio = (self.force - self.min_force) / denom
        ratio = max(0.0, min(1.0, ratio))
        fill_w = int(BAR_W * ratio)
        pygame.draw.rect(self._display_surf, BAR_FILL_COLOR, (bar_x, bar_y, fill_w, BAR_H))
        # thin border
        pygame.draw.rect(self._display_surf, BAR_BORDER_COLOR, (bar_x, bar_y, BAR_W, BAR_H), 1)

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