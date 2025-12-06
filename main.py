import math
import pygame
from typing import List, Optional, Sequence

from Menu.Menu import Menu
from Menu.SettingsMenu import SettingsMenu
from Menu.StartMenu import StartMenu
from maps.map import load_default_map, load_map_from_txt, GridMap

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
    def __init__(self) -> None:
        self._running = True
        self._display_surf: Optional[pygame.Surface] = None
        self.terrain: Optional[GridMap] = None
        self.size = self.width, self.height = 800, 600

        # gameplay lists / state
        self.projectiles = []

        # charge / firing
        self.charging = False
        self.min_force = MIN_FORCE
        self.max_force = MAX_FORCE
        self.charge_rate = CHARGE_RATE
        self.force = self.min_force
        self.current_weapon = "roquette"
        self.angle = 80
        self.projectile_time_scale = PROJECTILE_TIME_SCALE

        # turn timer (seconds)
        self.turn_time_limit = 30.0
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index: Optional[int] = None

        # menus / ui
        self.state = "menu"
        self.menu: Optional[Menu] = None
        self.start_menu: Optional[StartMenu] = None
        self.settings_menu: Optional[SettingsMenu] = None
        self.font: Optional[pygame.font.Font] = None

        # multiplayer
        self.players: List[Player] = []
        self.turn_manager: Optional[TurnManager] = None

    # ---------- init / menus ----------
    def on_init(self) -> bool:
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 20)

        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.mouse.set_visible(True)

        self.menu = Menu(self.width, self.height, self.font)
        self.settings_menu = SettingsMenu(self.width, self.height, self.font)
        self.start_menu = StartMenu(self.width, self.height, self.font)

        return True

    # ---------- game start / player creation ----------
    def create_players_and_turns(self, names: Sequence[Sequence[str] | str]) -> None:
        """
        names: can be
          - list of lists: names_per_player -> create one Player with multiple Characters
          - list of strings: create one Player per name (backwards compatible)
        """
        # ensure map loaded
        if not self.terrain:
            self.terrain = load_default_map()
            self._resize_display_to_terrain()

        char_w = 32
        self.players = []

        # helper to get spawn left_x
        def spawn_left() -> int:
            try:
                left, _ = self.terrain.random_spawn_for_character(char_w)
                return left
            except Exception:
                # fallback: distribute across width
                span = max(1, self.terrain.width if self.terrain else self.width)
                return int(span * 0.1)

        # normalize names input
        normalized: List[List[str]] = []
        if not names:
            normalized = [["Player1"]]
        elif isinstance(names[0], (list, tuple)):
            for p in names:
                normalized.append(list(p))
        else:
            # flat list: one character per player
            for nm in names:
                normalized.append([nm])

        for p_idx, char_names in enumerate(normalized):
            player = Player()
            for c_idx, cname in enumerate(char_names):
                left_x = spawn_left()
                # Character constructor doesn't accept name param -> set with rename
                char = Character(player_number=p_idx + 1, pos_x=int(left_x), pos_y=None, terrain=self.terrain)
                if cname:
                    char.rename(str(cname))
                player.add_character(char)
            self.players.append(player)

        self.turn_manager = TurnManager(self.players)
        # reset timer when new turns created
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index = self.turn_manager.current_player_index if self.turn_manager else None

    def start_game(self, config: dict) -> None:
        """
        config expected keys:
         - names: list[list[str]] or list[str]
         - map_path: optional path to .txt map
        """
        map_path = config.get("map_path")
        try:
            self.terrain = load_map_from_txt(map_path) if map_path else load_default_map()
        except Exception:
            self.terrain = load_default_map()

        self._resize_display_to_terrain()

        names = config.get("names", []) or []
        self.create_players_and_turns(names)
        self.projectiles = []
        self.force = self.min_force
        self.state = "playing"
        # ensure timer starts fresh
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index = self.turn_manager.current_player_index if self.turn_manager else None

    def _resize_display_to_terrain(self) -> None:
        if self.terrain:
            self.size = self.width, self.height = self.terrain.width, self.terrain.height
            self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)

    # ---------- event dispatch ----------
    def on_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self._running = False
            return

        if self.state == "menu":
            self._handle_menu_event(event)
            return

        if self.state == "start":
            self._handle_start_event(event)
            return

        if self.state == "settings":
            self._handle_settings_event(event)
            return

        # playing
        self._handle_play_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        action = self.menu.handle_event(event) if self.menu else None
        if action == "play":
            self.state = "start"
        elif action == "settings":
            self.state = "settings"
        elif action == "quit":
            self._running = False

    def _handle_start_event(self, event: pygame.event.Event) -> None:
        if not self.start_menu:
            return
        result = self.start_menu.handle_event(event)
        if result is None:
            return

        # Normalize possible return forms:
        # - StartMenu currently returns ("start_game", config)
        # - other implementations might return dict with "action"
        if isinstance(result, tuple) and len(result) == 2 and result[0] in ("start_game", "start"):
            _, cfg = result
            self.start_game(cfg)
        elif isinstance(result, dict):
            # support {"action": "start", ...} or direct config
            if result.get("action") in (None, "start", "start_game"):
                # if it's a full config, pass; else extract needed fields
                if "names" in result or "map_path" in result:
                    self.start_game(result)
                else:
                    # fallback: build config
                    cfg = {
                        "names": result.get("names", []),
                        "map_path": result.get("map_path"),
                    }
                    self.start_game(cfg)
        elif result == "back":
            self.state = "menu"

    def _handle_settings_event(self, event: pygame.event.Event) -> None:
        action = self.settings_menu.handle_event(event) if self.settings_menu else None
        if action == "back":
            self.state = "menu"

    def _handle_play_event(self, event: pygame.event.Event) -> None:
        active_char = self._active_character()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.current_weapon = "roquette"
            elif event.key == pygame.K_g:
                self.current_weapon = "grenade"
            elif event.key == pygame.K_RIGHT:
                self.force = min(self.max_force, self.force + 2)
            elif event.key == pygame.K_LEFT:
                self.force = max(self.min_force, self.force - 2)
            elif event.key in (pygame.K_SPACE, pygame.K_UP):
                if active_char:
                    active_char.jump()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.charging = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.charging:
            self._spawn_current_projectile(active_char)
            self.charging = False
            self.force = self.min_force
            if self.turn_manager:
                self.turn_manager.next_turn()
                # reset timer when player ends turn
                self.turn_time_remaining = self.turn_time_limit
                self._last_player_index = self.turn_manager.current_player_index

    def _active_character(self) -> Optional[Character]:
        if not self.turn_manager or not self.turn_manager.current_player:
            return None
        return self.turn_manager.current_player.access_current_character()

    def _spawn_current_projectile(self, active_char: Optional[Character]) -> None:
        if active_char:
            spawn_x = int(active_char.pos_x + active_char.width / 2)
            spawn_y = int(active_char.pos_y)
        else:
            spawn_x = self.width // 2
            spawn_y = self.height // 2

        if self.current_weapon == "roquette":
            p = ROQUETTE(spawn_x, spawn_y, self.angle, self.force, terrain=self.terrain)
        else:
            p = GRENADE(spawn_x, spawn_y, self.angle, self.force, terrain=self.terrain)

        # make sure not starting buried
        try:
            ground_top = p.ground_top_at()
            if p.y >= ground_top:
                p.y = ground_top - 1.0
        except Exception:
            pass

        self.projectiles.append(p)

    # ---------- main loop pieces ----------
    def on_loop(self, dt: float) -> None:
        if self.state != "playing":
            return

        # detect if turn changed externally and reset timer
        if self.turn_manager:
            if self._last_player_index is None:
                self._last_player_index = self.turn_manager.current_player_index
            elif self._last_player_index != self.turn_manager.current_player_index:
                self.turn_time_remaining = self.turn_time_limit
                self._last_player_index = self.turn_manager.current_player_index

        # decrement timer
        self.turn_time_remaining -= dt
        if self.turn_time_remaining <= 0:
            # auto end turn
            if self.turn_manager:
                self.turn_manager.next_turn()
                self._last_player_index = self.turn_manager.current_player_index
            self.turn_time_remaining = self.turn_time_limit

        active_char = self._active_character()
        if active_char:
            px = active_char.pos_x
            pw = active_char.width
            facing_right = active_char.facing_right
        else:
            px = 0.0
            pw = 32
            facing_right = True

        mx, my = pygame.mouse.get_pos()
        player_center_x = px + pw / 2.0
        player_center_y = (active_char.pos_y + active_char.height / 2.0) if active_char else self.height / 2.0
        dx = mx - player_center_x
        dy = player_center_y - my

        if dx != 0:
            raw_angle = math.degrees(math.atan2(dy, abs(dx)))
            raw_angle = max(5, min(85, raw_angle))
            self.angle = raw_angle if facing_right else (180 - raw_angle)

        if self.charging:
            self.force = min(self.max_force, self.force + self.charge_rate * dt)

        scaled_dt = dt * self.projectile_time_scale
        self._update_projectiles(scaled_dt, dt)

        if active_char:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                active_char.move_left(dt=dt)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                active_char.move_right(dt=dt)
            active_char.update(dt)

    def _update_projectiles(self, scaled_dt: float, real_dt: float) -> None:
        for p in list(self.projectiles):
            if hasattr(p, "move"):
                if getattr(p, "nom", "") == "grenade":
                    p.move(scaled_dt, real_dt=real_dt)
                else:
                    p.move(scaled_dt)
            else:
                p.apply_gravity(real_dt)
                if getattr(p, "nom", "") == "roquette":
                    p.speedX += WIND * scaled_dt
                p.update_position(scaled_dt)
                p.check_ground_collision()
        self.projectiles = [p for p in self.projectiles if p.alive]

    # ---------- rendering ----------
    def on_render(self) -> None:
        if not self._display_surf:
            return
        self._display_surf.fill(SKY_COLOR)
        if self.terrain:
            self.terrain.draw(self._display_surf)

        if self.state == "menu":
            self.menu.draw(self._display_surf)
            pygame.display.flip()
            return

        if self.state == "start":
            self.start_menu.draw(self._display_surf)
            pygame.display.flip()
            return

        if self.state == "settings":
            self.settings_menu.draw(self._display_surf)
            pygame.display.flip()
            return

        # charging preview trajectory
        if self.charging:
            self._draw_trajectory_preview()

        for p in self.projectiles:
            p.draw(self._display_surf)

        # draw characters and their names
        for player in self.players:
            for c in player.characters:
                c.draw(self._display_surf)
                # draw name above head if available
                if c.name and self.font:
                    name_text = str(c.name)
                    surf = self.font.render(name_text, True, (255, 255, 255))
                    shadow = self.font.render(name_text, True, (0, 0, 0))
                    tx = int(c.pos_x + c.width / 2 - surf.get_width() / 2)
                    ty = int(c.pos_y - 18)
                    # shadow
                    self._display_surf.blit(shadow, (tx + 1, ty + 1))
                    self._display_surf.blit(surf, (tx, ty))

        active_char = self._active_character()
        if active_char:
            rect = pygame.Rect(int(active_char.pos_x), int(active_char.pos_y), active_char.width, active_char.height)
            pygame.draw.rect(self._display_surf, (255, 255, 0), rect, 2)
            bar_x = int(active_char.pos_x + active_char.width / 2 - BAR_W / 2)
            bar_y = int(active_char.pos_y - BAR_OFFSET_Y)
        else:
            bar_x = int(self.width / 2 - BAR_W / 2)
            bar_y = 20

        # draw turn timer at top center
        if self.font and self.state == "playing":
            secs = max(0, int(math.ceil(self.turn_time_remaining)))
            # show current player index if available
            if self.turn_manager:
                player_idx = self.turn_manager.current_player_index + 1
                timer_text = f"P{player_idx}  {secs}s"
            else:
                timer_text = f"{secs}s"
            shadow = self.font.render(timer_text, True, (0, 0, 0))
            text_surf = self.font.render(timer_text, True, (250, 250, 250))
            tx = int(self.width / 2 - text_surf.get_width() / 2)
            ty = 6
            self._display_surf.blit(shadow, (tx + 1, ty + 1))
            self._display_surf.blit(text_surf, (tx, ty))

        # force bar
        pygame.draw.rect(self._display_surf, BAR_BG_COLOR, (bar_x, bar_y, BAR_W, BAR_H))
        denom = max(1e-6, (self.max_force - self.min_force))
        ratio = (self.force - self.min_force) / denom
        ratio = max(0.0, min(1.0, ratio))
        fill_w = int(BAR_W * ratio)
        pygame.draw.rect(self._display_surf, BAR_FILL_COLOR, (bar_x, bar_y, fill_w, BAR_H))
        pygame.draw.rect(self._display_surf, BAR_BORDER_COLOR, (bar_x, bar_y, BAR_W, BAR_H), 1)

        pygame.display.flip()

    def _draw_trajectory_preview(self) -> None:
        preview_char = self._active_character()
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
            time_scale=self.projectile_time_scale,
        )
        for (px, py) in points:
            pygame.draw.circle(self._display_surf, TRAJECTORY_COLOR, (px, py), 2)

    # ---------- cleanup / run ----------
    def on_cleanup(self) -> None:
        pygame.quit()

    def on_execute(self) -> None:
        clock = pygame.time.Clock()
        if not self.on_init():
            self._running = False

        while self._running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop(dt)
            self.on_render()

        self.on_cleanup()


if __name__ == "__main__":
    app = App()
    app.on_execute()