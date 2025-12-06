import math
import pygame
from Menu.Menu import Menu
from Menu.SettingsMenu import SettingsMenu
from maps.map import load_default_map

from config import (
    WIND,
    PROJECTILE_TIME_SCALE,
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
    TRAJECTORY_COLOR,
)
from Weapons.grenade import GRENADE
from Weapons.roquette import ROQUETTE

from Player.character import Character
from Player.player import Player
from Game.turn_manager import TurnManager


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None

        self.terrain = load_default_map()
        self.size = self.width, self.height = self.terrain.width, self.terrain.height

        self.projectiles = []

        # charging
        self.charging = False
        self.min_force = MIN_FORCE
        self.max_force = MAX_FORCE
        self.charge_rate = CHARGE_RATE
        self.force = self.min_force
        self.current_weapon = "roquette"
        self.angle = 80

        self.projectile_time_scale = PROJECTILE_TIME_SCALE

        self.state = "menu"
        self.menu = None
        self.settings_menu = None
        self.font = None

        # multiplayer
        self.players = []
        self.turn_manager = None

    def on_init(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 36)
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
        pygame.mouse.set_visible(True)
        self.menu = Menu(self.width, self.height, self.font)
        self.settings_menu = SettingsMenu(self.width, self.height, self.font)

        # create two players and characters with spawn points if available
        spawns = []
        try:
            # try common API returning list of spawn points
            spawns = list(self.terrain.get_spawn_points())
        except Exception:
            try:
                # fallback single spawn
                sp = self.terrain.get_spawn_point()
                spawns = [sp, (sp[0] + 120, sp[1])]
            except Exception:
                spawns = [(100, 100), (self.width - 200, 100)]

        # ensure two spawn tuples
        if len(spawns) < 2:
            spawns = [spawns[0], (spawns[0][0] + 120, spawns[0][1])]

        # create players with one character each (can add more later)
        p1 = Player()
        p1.add_character(Character(1, int(spawns[0][0]), int(spawns[0][1]), terrain=self.terrain))
        p2 = Player()
        p2.add_character(Character(2, int(spawns[1][0]), int(spawns[1][1]), terrain=self.terrain))

        self.players = [p1, p2]
        self.turn_manager = TurnManager(self.players)

    # event handling
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
            return

        if self.state == "menu":
            action = self.menu.handle_event(event)
            if action == "play":
                self.state = "playing"
            elif action == "settings":
                self.state = "settings"
            elif action == "quit":
                self._running = False
            return

        if self.state == "settings":
            action = self.settings_menu.handle_event(event)
            if action == "back":
                self.state = "menu"
            return

        active_char = None
        if self.turn_manager and self.turn_manager.current_player:
            active_char = self.turn_manager.current_player.access_current_character()

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
                if active_char:
                    active_char.jump()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.charging = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.charging:
                # spawn projectile from active character (top-center)
                if active_char:
                    spawn_x = int(active_char.pos_x + active_char.width / 2)
                    spawn_y = int(active_char.pos_y)
                else:
                    # fallback center of screen
                    spawn_x = self.width // 2
                    spawn_y = self.height // 2

                if self.current_weapon == "roquette":
                    p = ROQUETTE(spawn_x, spawn_y, self.angle, self.force, terrain=self.terrain)
                else:
                    p = GRENADE(spawn_x, spawn_y, self.angle, self.force, terrain=self.terrain)

                try:
                    ground_top = p.ground_top_at()
                    if p.y >= ground_top:
                        p.y = ground_top - 1.0
                except Exception:
                    pass

                self.projectiles.append(p)
                self.charging = False
                self.force = self.min_force

                # advance turn: current player's character cycling then next player
                if self.turn_manager:
                    self.turn_manager.next_turn()

    def on_loop(self, dt):
        if self.state != "playing":
            return

        active_char = None
        if self.turn_manager and self.turn_manager.current_player:
            active_char = self.turn_manager.current_player.access_current_character()

        # aiming: use active character center for angle when present
        if active_char:
            px = active_char.pos_x
            py = active_char.pos_y
            pw = active_char.width
            ph = active_char.height
            facing_right = active_char.facing_right
        else:
            px = py = 0.0
            pw = ph = 32
            facing_right = True

        mx, my = pygame.mouse.get_pos()
        player_center_x = px + pw / 2.0
        player_center_y = py + ph / 2.0
        dx = mx - player_center_x
        dy = player_center_y - my

        if dx != 0:
            # match preview behaviour: use abs(dx) base angle
            raw_angle = math.degrees(math.atan2(dy, abs(dx)))
            raw_angle = max(5, min(85, raw_angle))
            self.angle = raw_angle if facing_right else (180 - raw_angle)
        else:
            # keep existing angle or default
            pass

        if self.charging:
            self.force = min(self.max_force, self.force + self.charge_rate * dt)

        scaled_dt = dt * self.projectile_time_scale

        for p in list(self.projectiles):
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

        # player controls apply only to active character
        if active_char:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                active_char.move_left(dt=dt)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                active_char.move_right(dt=dt)
            active_char.update(dt)

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

        # trajectory preview based on active character
        if self.charging:
            if self.turn_manager and self.turn_manager.current_player:
                preview_char = self.turn_manager.current_player.access_current_character()
            else:
                preview_char = None

            if preview_char:
                preview_x = int(preview_char.pos_x + preview_char.width / 2)
                preview_y = int(preview_char.pos_y)
                facing_right = preview_char.facing_right
                player_center_x = preview_x
                player_center_y = preview_y + preview_char.height / 2.0
            else:
                preview_x = self.width // 2
                preview_y = self.height // 2
                facing_right = True
                player_center_x = preview_x
                player_center_y = preview_y

            mx, my = pygame.mouse.get_pos()
            dx = mx - player_center_x
            dy = player_center_y - my

            if dx != 0:
                raw_angle = math.degrees(math.atan2(dy, abs(dx)))
                raw_angle = max(5, min(85, raw_angle))
            else:
                raw_angle = 45

            self.angle = raw_angle if facing_right else (180 - raw_angle)

            preview = (
                ROQUETTE(preview_x, preview_y, self.angle, self.force, terrain=self.terrain)
                if self.current_weapon == "roquette"
                else GRENADE(preview_x, preview_y, self.angle, self.force, terrain=self.terrain)
            )

            points = preview.simulate_trajectory(
                wind=WIND if self.current_weapon == "roquette" else 0,
                time_scale=self.projectile_time_scale
            )

            for (px, py) in points:
                pygame.draw.circle(self._display_surf, TRAJECTORY_COLOR, (px, py), 2)

        # draw projectiles
        for p in self.projectiles:
            p.draw(self._display_surf)

        # draw all players' characters and highlight active
        active_char = None
        if self.turn_manager and self.turn_manager.current_player:
            active_char = self.turn_manager.current_player.access_current_character()

        for player in self.players:
            for c in player.characters:
                c.draw(self._display_surf)

        # highlight active character with simple rect
        if active_char:
            rect = pygame.Rect(int(active_char.pos_x), int(active_char.pos_y), active_char.width, active_char.height)
            pygame.draw.rect(self._display_surf, (255, 255, 0), rect, 2)

            bar_x = int(active_char.pos_x + active_char.width / 2 - BAR_W / 2)
            bar_y = int(active_char.pos_y - BAR_OFFSET_Y)
        else:
            bar_x = int(self.width / 2 - BAR_W / 2)
            bar_y = 20

        pygame.draw.rect(self._display_surf, BAR_BG_COLOR, (bar_x, bar_y, BAR_W, BAR_H))
        denom = max(1e-6, (self.max_force - self.min_force))
        ratio = (self.force - self.min_force) / denom
        ratio = max(0.0, min(1.0, ratio))
        fill_w = int(BAR_W * ratio)
        pygame.draw.rect(self._display_surf, BAR_FILL_COLOR, (bar_x, bar_y, fill_w, BAR_H))
        pygame.draw.rect(self._display_surf, BAR_BORDER_COLOR, (bar_x, bar_y, BAR_W, BAR_H), 1)

        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

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
