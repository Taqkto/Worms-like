# python
import math
import pygame
from Menu.Menu import Menu
from Menu.SettingsMenu import SettingsMenu
from maps.map import load_default_map

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
    BAR_BG_COLOR,
    BAR_FILL_COLOR,
    BAR_BORDER_COLOR,
    GROUND_RECT_Y,
    TRAJECTORY_COLOR,
)
from Weapons.grenade import GRENADE
from Weapons.roquette import ROQUETTE

from Player.character import Character


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None

        self.terrain = load_default_map()
        self.size = self.width, self.height = self.terrain.width, self.terrain.height

        # Liste des projectiles en jeu
        self.projectiles = []

        # Charging (left click)
        self.charging = False
        self.min_force = MIN_FORCE
        self.max_force = MAX_FORCE
        self.charge_rate = CHARGE_RATE

        # Start with the bar empty
        self.force = self.min_force

        # Paramètres pour l'arme équipée
        self.current_weapon = "roquette"
        self.angle = 80

        try:
            spawn_x, spawn_y = self.terrain.get_spawn_point()
            self.player_x = spawn_x
            self.player_y = spawn_y
        except ValueError:
            self.player_x = PLAYER_START_X
            # fallback to legacy flat ground height if map has no spawn
            self.player_y = min(PLAYER_START_Y, GROUND_RECT_Y - 20)

        self.projectile_time_scale = PROJECTILE_TIME_SCALE

        # Menu / state
        self.state = "menu"  # "menu", "playing", "settings"
        self.menu = None
        self.settings_menu = None
        self.font = None

        # player will be created in on_init (after pygame.init)
        self.player = None

    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    def on_init(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 36)
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
        pygame.mouse.set_visible(True)
        self.menu = Menu(self.width, self.height, self.font)
        self.settings_menu = SettingsMenu(self.width, self.height, self.font)

        # instantiate Character now that pygame is initialized
        self.player = Character(1, int(self.player_x), int(self.player_y))

    # --------------------------------------------------------
    # GESTION DES INPUTS
    # --------------------------------------------------------
    def on_event(self, event):
        # global quit
        if event.type == pygame.QUIT:
            self._running = False
            return

        # When in main menu, send events to the Menu and act on its return value
        if self.state == "menu":
            action = self.menu.handle_event(event)
            if action == "play":
                self.state = "playing"
            elif action == "settings":
                self.state = "settings"
            elif action == "quit":
                self._running = False
            return

        # When in settings, send events to SettingsMenu
        if self.state == "settings":
            action = self.settings_menu.handle_event(event)
            if action == "back":
                self.state = "menu"
            return

        # Playing-state input handling
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.current_weapon = "roquette"
            if event.key == pygame.K_g:
                self.current_weapon = "grenade"
            if event.key == pygame.K_RIGHT:
                self.force = min(self.max_force, self.force + 2)
            if event.key == pygame.K_LEFT:
                self.force = max(self.min_force, self.force - 2)
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                if self.player:
                    self.player.jump()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # left click -> start charging
                self.charging = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.charging:
                # spawn from player top-center
                if self.player:
                    spawn_x = int(self.player.pos_x + self.player.width / 2)
                    spawn_y = int(self.player.pos_y)
                else:
                    spawn_x = int(self.player_x)
                    spawn_y = int(self.player_y)

                if self.current_weapon == "roquette":
                    p = ROQUETTE(self.player_x, self.player_y, self.angle, self.force, terrain=self.terrain)
                else:
                    p = GRENADE(self.player_x, self.player_y, self.angle, self.force, terrain=self.terrain)

                # Nudge spawned projectile above visible ground so it doesn't instantly collide
                try:
                    ground_top = p.ground_top_at()
                    if p.y >= ground_top:
                        p.y = ground_top - 1.0
                except Exception:
                    pass

                self.projectiles.append(p)
                self.charging = False
                self.force = self.min_force

    # --------------------------------------------------------
    # LOGIQUE / PHYSIQUE
    # --------------------------------------------------------
    def on_loop(self, dt):
        if self.state != "playing":
            return

        # Use player position for aim computation (fallback to stored spawn if player missing)
        if self.player:
            px = self.player.pos_x
            py = self.player.pos_y
            pw = self.player.width
            ph = self.player.height
        else:
            px = float(self.player_x)
            py = float(self.player_y)
            pw = ph = 32

        mx, my = pygame.mouse.get_pos()
        player_center_x = px + pw / 2.0
        player_center_y = py + ph / 2.0
        dx = mx - player_center_x
        dy = player_center_y - my
        if dx != 0:
            self.angle = math.degrees(math.atan2(dy, dx))
            self.angle = max(5, min(85, self.angle))

        if self.charging:
            self.force = min(self.max_force, self.force + self.charge_rate * dt)

        scaled_dt = dt * self.projectile_time_scale

        for p in self.projectiles:
            if hasattr(p, "move"):
                if getattr(p, "nom", "") == "grenade":
                    p.move(scaled_dt, real_dt=dt)
                else:
                    p.move(scaled_dt)
            else:
                p.apply_gravity(dt)
                if getattr(p, "nom", "") == "roquette":
                    p.speedX += WIND * scaled_dt
                p.update_position(scaled_dt)
                p.check_ground_collision()

        self.projectiles = [p for p in self.projectiles if p.alive]

        # player movement (hold keys)
        if self.player:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.player.move_left(dt=dt)
            if keys[pygame.K_RIGHT]:
                self.player.move_right(dt=dt)

            # update player physics
            self.player.update(dt)

    # --------------------------------------------------------
    # AFFICHAGE
    # --------------------------------------------------------
    def on_render(self):
        self._display_surf.fill(SKY_COLOR)

        self.terrain.draw(self._display_surf)

        if self.state == "menu":
            self.menu.draw(self._display_surf)
            pygame.display.flip()
            return

        if self.state == "settings":
            self.settings_menu.draw(self._display_surf)
            pygame.display.flip()
            return

        # afficher trajectoire uniquement quand clic gauche est tenu
        if self.charging:
            preview = (
                ROQUETTE(self.player_x, self.player_y, self.angle, self.force, terrain=self.terrain)
                if self.current_weapon == "roquette"
                else GRENADE(self.player_x, self.player_y, self.angle, self.force, terrain=self.terrain)
            )

            points = preview.simulate_trajectory(
                wind=WIND if self.current_weapon == "roquette" else 0,
                time_scale=self.projectile_time_scale
            )

            for (px, py) in points:
                pygame.draw.circle(self._display_surf, TRAJECTORY_COLOR, (px, py), 2)

        # projectiles
        for p in self.projectiles:
            p.draw(self._display_surf)

        # draw player
        if self.player:
            self.player.draw(self._display_surf)

            # draw charge bar above player (use player center)
            bar_x = int(self.player.pos_x + self.player.width / 2 - BAR_W / 2)
            bar_y = int(self.player.pos_y - BAR_OFFSET_Y)
        else:
            bar_x = int(self.player_x - BAR_W / 2)
            bar_y = int(self.player_y - BAR_OFFSET_Y)

        pygame.draw.rect(self._display_surf, BAR_BG_COLOR, (bar_x, bar_y, BAR_W, BAR_H))
        denom = max(1e-6, (self.max_force - self.min_force))
        ratio = (self.force - self.min_force) / denom
        ratio = max(0.0, min(1.0, ratio))
        fill_w = int(BAR_W * ratio)
        pygame.draw.rect(self._display_surf, BAR_FILL_COLOR, (bar_x, bar_y, fill_w, BAR_H))
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
