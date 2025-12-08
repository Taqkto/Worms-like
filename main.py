import math
import pygame
from typing import List, Optional, Sequence

from Menu.Menu import Menu
from Menu.SettingsMenu import SettingsMenu
from Menu.StartMenu import StartMenu
from Menu.PauseMenu import PauseMenu
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
from Weapons.explosion import Explosion
from Player.character import Character
from Player.player import Player
from Game.turn_manager import TurnManager


def _calculate_explosion_damage(distance: float, radius: float, max_damage: int = 100) -> int:
    if distance >= radius:
        return 0
    distance_ratio = distance / radius
    damage = int(max_damage * (1.0 - distance_ratio))
    return max(0, damage)


class App:
    def __init__(self) -> None:
        self._running = True
        self._display_surf: Optional[pygame.Surface] = None
        self.terrain: Optional[GridMap] = None
        self.size = self.width, self.height = 800, 600

        # gameplay lists / state
        self.projectiles = []
        self.explosions = []

        # charge / firing
        self.charging = False
        self.min_force = MIN_FORCE
        self.max_force = MAX_FORCE
        self.charge_rate = CHARGE_RATE
        self.force = self.min_force
        self.current_weapon = "roquette"
        self.angle = 80

        self.key_bindings = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "jump": pygame.K_SPACE,
            "switch_grenade": pygame.K_g,
            "switch_rocket": pygame.K_r,
        }

        self.projectile_time_scale = PROJECTILE_TIME_SCALE

        # turn timer
        self.turn_time_limit = 30.0
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index: Optional[int] = None

        # menus / ui
        self.state = "menu"
        self.menu: Optional[Menu] = None
        self.start_menu: Optional[StartMenu] = None
        self.settings_menu: Optional[SettingsMenu] = None
        self.pause_menu: Optional[PauseMenu] = None
        self.font: Optional[pygame.font.Font] = None

        # multiplayer
        self.players: List[Player] = []
        self.turn_manager: Optional[TurnManager] = None
        self._game_over_button_rect: Optional[pygame.Rect] = None
        self.winner_player_number: Optional[int] = None

        self._pending_game_over = False
        self._pending_winner = None
        self._pending_turn_switch = False
        self._has_fired_this_turn = False
        self._settings_from_pause = False

    def on_init(self) -> bool:
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 20)

        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.mouse.set_visible(True)

        self.menu = Menu(self.width, self.height, self.font)
        self.settings_menu = SettingsMenu(self.width, self.height, self.font)
        self.start_menu = StartMenu(self.width, self.height, self.font)
        self.pause_menu = PauseMenu(self.width, self.height, self.font)

        self.key_bindings = self.settings_menu.key_bindings.copy()

        return True

    def create_players_and_turns(self, names: Sequence[Sequence[str] | str]) -> None:
        if not self.terrain:
            self.terrain = load_default_map()
            self._resize_display_to_terrain()

        char_w = 32
        self.players = []

        def spawn_left() -> int:
            try:
                left, _ = self.terrain.random_spawn_for_character(char_w)
                return left
            except Exception:
                span = max(1, self.terrain.width if self.terrain else self.width)
                return int(span * 0.1)

        normalized: List[List[str]] = []
        if not names:
            normalized = [["Player1"]]
        elif isinstance(names[0], (list, tuple)):
            normalized = [list(p) for p in names]
        else:
            normalized = [[nm] for nm in names]

        for p_idx, char_names in enumerate(normalized):
            player = Player()
            for cname in char_names:
                left_x = spawn_left()
                char = Character(player_number=p_idx + 1, pos_x=int(left_x), pos_y=None, terrain=self.terrain)
                char._app_ref = self
                if cname:
                    char.rename(str(cname))
                player.add_character(char)
            self.players.append(player)

        self.turn_manager = TurnManager(self.players)
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index = self.turn_manager.current_player_index

    def start_game(self, config: dict) -> None:
        map_path = config.get("map_path")
        try:
            self.terrain = load_map_from_txt(map_path) if map_path else load_default_map()
        except Exception:
            self.terrain = load_default_map()

        self._resize_display_to_terrain()

        names = config.get("names", []) or []
        self.create_players_and_turns(names)
        self.projectiles = []
        self.explosions = []
        self.force = self.min_force
        self.state = "playing"
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index = self.turn_manager.current_player_index
        self._pending_turn_switch = False
        self._has_fired_this_turn = False

    def _resize_display_to_terrain(self) -> None:
        if self.terrain:
            self.size = self.width, self.height = self.terrain.width, self.terrain.height
            self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)

    def _can_end_turn(self) -> bool:
        if self.explosions:
            return False
        if self.projectiles:
            return False
        active_char = self._active_character()
        if active_char and active_char.is_jumping:
            return False
        return True

    def on_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self._running = False
            return

        if self.state == "game_over":
            self._handle_game_over_event(event)
            return

        if self.state == "paused":
            self._handle_pause_event(event)
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

        self._handle_play_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        action = self.menu.handle_event(event)
        if action == "play":
            self.start_menu.reset()
            self.state = "start"
        elif action == "editor":
            # Launch the level editor (modal). Import inside to avoid top-level coupling.
            try:
                from level_editor import LevelEditor
                editor = LevelEditor()
                editor.run()
            except Exception as e:
                print(f"Could not start editor: {e}")
            # After editor exits, restore the game's menu/display
            self._reset_to_menu_layout()
            self.state = "menu"
        elif action == "settings":
            self._settings_from_pause = False
            self.state = "settings"
        elif action == "quit":
            self._running = False

    def _handle_start_event(self, event: pygame.event.Event) -> None:
        result = self.start_menu.handle_event(event)
        if result is None:
            return

        if isinstance(result, tuple) and len(result) == 2 and result[0] in ("start", "start_game"):
            _, cfg = result
            self.start_game(cfg)
        elif isinstance(result, dict):
            if result.get("action") in (None, "start", "start_game"):
                cfg = {"names": result.get("names", []), "map_path": result.get("map_path")}
                self.start_game(cfg)
        elif result == "back":
            self.state = "menu"

    def _handle_settings_event(self, event: pygame.event.Event) -> None:
        result = self.settings_menu.handle_event(event)
        if isinstance(result, dict):
            if "key_bindings" in result:
                self.key_bindings.update(result["key_bindings"])
            if result.get("action") == "back":
                if self._settings_from_pause:
                    self.state = "paused"
                else:
                    self.state = "menu"
                self._settings_from_pause = False
        elif result == "back":
            self.state = "menu"

    def _handle_play_event(self, event: pygame.event.Event) -> None:
        active_char = self._active_character()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.pause_menu.resize(self.width, self.height)
                self.state = "paused"
                return

            if event.key == self.key_bindings["switch_rocket"]:
                self.current_weapon = "roquette"
                self.force = self.min_force
                self.charging = False
                if active_char:
                    active_char.current_hand_item = "rocket"


            elif event.key == self.key_bindings["switch_grenade"]:
                self.current_weapon = "grenade"
                self.force = self.min_force
                self.charging = False
                if active_char:
                    active_char.current_hand_item = "grenade"


            elif event.key == pygame.K_RIGHT:
                self.force = min(self.max_force, self.force + 2)

            elif event.key == pygame.K_LEFT:
                self.force = max(self.min_force, self.force - 2)

            elif event.key in (self.key_bindings["jump"], pygame.K_UP):
                if active_char:
                    active_char.jump()

        # Début tir
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self._has_fired_this_turn:
                self.charging = True

        # Fin tir
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.charging:
            self._spawn_current_projectile(active_char)
            self.charging = False
            self.force = self.min_force
            self._pending_turn_switch = True
            self._has_fired_this_turn = True

    def _handle_pause_event(self, event: pygame.event.Event) -> None:
        result = self.pause_menu.handle_event(event)
        if result == "resume":
            self.state = "playing"
        elif result == "settings":
            self._settings_from_pause = True
            self.settings_menu.resize(self.width, self.height)
            self.state = "settings"
        elif result == "home":
            self.players = []
            self.turn_manager = None
            self.projectiles = []
            self.explosions = []
            self._pending_game_over = False
            self._pending_winner = None
            self._pending_turn_switch = False
            self._last_player_index = None
            self._has_fired_this_turn = False
            self._settings_from_pause = False
            self._reset_to_menu_layout()
            self.state = "menu"

    def _active_character(self) -> Optional[Character]:
        if not self.turn_manager or not self.turn_manager.current_player:
            return None
        return self.turn_manager.current_player.access_current_character()

    def _spawn_current_projectile(self, active_char: Optional[Character]) -> None:
        if active_char:
            spawn_x = int(active_char.pos_x + active_char.width / 2)
            spawn_y = int(active_char.pos_y + active_char.height / 4)
        else:
            spawn_x = self.width // 2
            spawn_y = self.height // 2

        all_characters = [
            c for player in self.players
            for c in player.characters
            if c != active_char
        ]

        if self.current_weapon == "roquette":
            p = ROQUETTE(spawn_x, spawn_y, self.angle, self.force, terrain=self.terrain, characters=all_characters)
        else:
            p = GRENADE(spawn_x, spawn_y, self.angle, self.force, terrain=self.terrain)


        if self.terrain:
            block = self.terrain.block_at_pixel(p.x, p.y)
            if block and block.solid:
                ground_top = self.terrain.height_at(p.x)
                p.y = ground_top - p.radius - 1

        self.projectiles.append(p)

    def on_loop(self, dt: float) -> None:
        if self.state != "playing":
            return

        # Turn manager
        if self.turn_manager:
            if self._last_player_index is None:
                self._last_player_index = self.turn_manager.current_player_index
            elif self._last_player_index != self.turn_manager.current_player_index:
                self.turn_time_remaining = self.turn_time_limit
                self._last_player_index = self.turn_manager.current_player_index
                self._has_fired_this_turn = False

        # Update explosions
        for explosion in self.explosions:
            explosion.update(dt)
        self.explosions = [e for e in self.explosions if e.alive]

        # Remove dead characters
        for player in self.players:
            player.characters = [c for c in player.characters if c.alive]
        self.players = [pl for pl in self.players if pl.has_alive_characters()]

        # Update turn manager
        if self.turn_manager and self.players:
            self.turn_manager.players = self.players
            if self.turn_manager.current_player_index >= len(self.players):
                self.turn_manager.current_player_index = 0

        # Pending turn switch ?
        if self._pending_turn_switch and self._can_end_turn():
            self.turn_manager.next_turn()
            self._last_player_index = self.turn_manager.current_player_index
            self._has_fired_this_turn = False
            self.turn_time_remaining = self.turn_time_limit
            self._pending_turn_switch = False

        # Timer turn switch
        self.turn_time_remaining -= dt
        if self.turn_time_remaining <= 0 and self._can_end_turn():
            self.turn_manager.next_turn()
            self._last_player_index = self.turn_manager.current_player_index
            self._has_fired_this_turn = False
            self.turn_time_remaining = self.turn_time_limit

        # Victory detection
        alive_players = [pl for pl in self.players if pl.has_alive_characters()]
        if len(alive_players) == 1:
            try:
                winner_num = alive_players[0].characters[0].player_number
            except Exception:
                winner_num = 1
            self._pending_game_over = True
            self._pending_winner = winner_num

        # If pending game over : finish projectiles + explosions
        if self._pending_game_over:
            scaled_dt = dt * self.projectile_time_scale
            self._update_projectiles(scaled_dt, dt)

            if len(self.explosions) == 0:
                self.winner_player_number = self._pending_winner
                self.state = "game_over"
                self.turn_manager = None
                self.projectiles = []
                self._last_player_index = None
                self._pending_game_over = False
                self._pending_winner = None
            return

        # ==== MAIN GAME PROCESSING =====

        active_char = self._active_character()
        if active_char:
            px = active_char.pos_x
            pw = active_char.width
            facing_right = not active_char.facing_left
        else:
            px, pw, facing_right = 0.0, 32, True

        mx, my = pygame.mouse.get_pos()
        player_center_x = px + pw / 2.0
        player_center_y = active_char.pos_y + active_char.height / 2.0 if active_char else self.height / 2.0

        dx = mx - player_center_x
        dy = player_center_y - my

        if dx != 0:
            raw_angle = math.degrees(math.atan2(dy, abs(dx)))
            raw_angle = max(5, min(85, raw_angle))
            self.angle = raw_angle if facing_right else (180 - raw_angle)

        # Charging
        if self.charging:
            self.force = min(self.max_force, self.force + self.charge_rate * dt)

        scaled_dt = dt * self.projectile_time_scale
        self._update_projectiles(scaled_dt, dt)

        # Movement logic (corrected order)
        if active_char:
            # Reset movement state
            active_char.update(dt)

            keys = pygame.key.get_pressed()
            moved = False

            if keys[self.key_bindings["move_left"]] or keys[pygame.K_LEFT]:
                active_char.move_left(dt=dt)
                moved = True

            if keys[self.key_bindings["move_right"]] or keys[pygame.K_RIGHT]:
                active_char.move_right(dt=dt)
                moved = True

            if not moved:
                active_char.is_moving = False

    def _update_projectiles(self, scaled_dt: float, real_dt: float) -> None:
        for p in list(self.projectiles):
            if hasattr(p, "move"):
                if p.nom == "grenade":
                    try:
                        p.move(scaled_dt, real_dt)
                    except TypeError:
                        p.move(scaled_dt)
                else:
                    try:
                        p.move(scaled_dt)
                    except TypeError:
                        p.move(real_dt)
            else:
                p.apply_gravity(real_dt)
                if p.nom == "roquette":
                    try:
                        p.speedX += WIND * real_dt
                    except Exception:
                        pass
                p.update_position(scaled_dt)
                try:
                    p.check_ground_collision()
                except Exception:
                    pass

            if p.exploded:
                self._handle_explosion(p)

        self.projectiles = [p for p in self.projectiles if p.alive and not p.exploded]

    def _handle_explosion(self, p) -> None:
        try:
            cx = p.x
            cy = p.y
            radius = getattr(p, "explosion_radius", 40)
        except Exception:
            return

        explosion = Explosion(cx, cy, radius)
        self.explosions.append(explosion)

        # Damage
        for player in self.players:
            for c in list(player.characters):
                char_cx = c.pos_x + c.width / 2
                char_cy = c.pos_y + c.height / 2
                dist = math.dist((char_cx, char_cy), (cx, cy))
                dmg = _calculate_explosion_damage(dist, radius)
                if dmg > 0:
                    c.damage(dmg)

            player.characters = [c for c in player.characters if c.alive]

        self.projectiles = [pp for pp in self.projectiles if pp.alive and not pp.exploded]

        # Victory re-eval but don't switch immediately
        alive_players = [pl for pl in self.players if pl.has_alive_characters()]
        if len(alive_players) == 1:
            try:
                winner_num = alive_players[0].characters[0].player_number
            except Exception:
                winner_num = 1
            self._pending_game_over = True
            self._pending_winner = winner_num

    def _handle_game_over_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if not self._game_over_button_rect:
            return
        mx, my = event.pos
        if self._game_over_button_rect.collidepoint(mx, my):
            self.players = []
            self.turn_manager = None
            self.projectiles = []
            self.explosions = []
            self._pending_game_over = False
            self._pending_winner = None
            self._pending_turn_switch = False
            self._last_player_index = None
            self._has_fired_this_turn = False
            self._reset_to_menu_layout()
            self.state = "menu"

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

        if self.state == "paused":
            self._draw_game_scene()
            self.pause_menu.draw(self._display_surf)
            pygame.display.flip()
            return

        # PROJECTILES
        for p in self.projectiles:
            p.draw(self._display_surf)

        # CHARACTERS
        for player in self.players:
            for c in player.characters:
                c.draw(self._display_surf)

                # Name
                if c.name and self.font:
                    surf = self.font.render(str(c.name), True, (255, 255, 255))
                    shadow = self.font.render(str(c.name), True, (0, 0, 0))
                    tx = int(c.pos_x + c.width/2 - surf.get_width()/2)
                    ty = int(c.pos_y - 28)
                    self._display_surf.blit(shadow, (tx+1, ty+1))
                    self._display_surf.blit(surf, (tx, ty))

                # HP bar
                if c.pv is not None:
                    max_hp = 100
                    ratio = max(0.0, min(1.0, c.pv/max_hp))
                    bar_width = 40
                    bar_height = 4
                    bar_x = int(c.pos_x + c.width/2 - bar_width/2)
                    bar_y = int(c.pos_y - 10)
                    pygame.draw.rect(self._display_surf, (100,0,0), (bar_x, bar_y, bar_width, bar_height))
                    hp_color = (0,255,0) if ratio>0.5 else (255,255,0) if ratio>0.25 else (255,0,0)
                    pygame.draw.rect(self._display_surf, hp_color, (bar_x, bar_y, int(bar_width*ratio), bar_height))
                    pygame.draw.rect(self._display_surf, (255,255,255), (bar_x, bar_y, bar_width, bar_height), 1)

        # EXPLOSIONS
        for explosion in self.explosions:
            explosion.draw(self._display_surf)

        # GAME OVER SCREEN
        if self.state == "game_over":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self._display_surf.blit(overlay, (0,0))

            if self.font:
                winner_txt = f"Player {self.winner_player_number} wins!"
                surf = self.font.render(winner_txt, True, (255,255,255))
                tx = int(self.width/2 - surf.get_width()/2)
                ty = int(self.height/2 - 40)
                self._display_surf.blit(surf, (tx,ty))

                btn_text = "Home"
                btn_surf = self.font.render(btn_text, True, (255,255,255))
                padding = (12,8)
                btn_w = btn_surf.get_width() + padding[0]*2
                btn_h = btn_surf.get_height() + padding[1]*2
                btn_x = int(self.width/2 - btn_w/2)
                btn_y = int(self.height/2 + 4)
                btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                pygame.draw.rect(self._display_surf, (200,30,30), btn_rect)
                pygame.draw.rect(self._display_surf, (0,0,0), btn_rect, 2)
                self._display_surf.blit(btn_surf, (btn_x+padding[0], btn_y+padding[1]))
                self._game_over_button_rect = btn_rect

            pygame.display.flip()
            return

        # If charging → preview trajectory
        if self.charging:
            self._draw_trajectory_preview()

        # Turn timer text
        if self.font and self.state == "playing":
            secs = max(0, int(math.ceil(self.turn_time_remaining)))
            player_idx = self.turn_manager.current_player_index + 1
            timer_text = f"P{player_idx}  {secs}s"
            shadow = self.font.render(timer_text, True, (0,0,0))
            text_surf = self.font.render(timer_text, True, (250,250,250))
            tx = int(self.width/2 - text_surf.get_width()/2)
            ty = 6
            self._display_surf.blit(shadow, (tx+1, ty+1))
            self._display_surf.blit(text_surf, (tx, ty))

        # Power bar
        bar_x = int(self.width/2 - BAR_W/2)
        bar_y = 20
        pygame.draw.rect(self._display_surf, BAR_BG_COLOR, (bar_x, bar_y, BAR_W, BAR_H))
        denom = max(1e-6, (self.max_force - self.min_force))
        ratio = (self.force - self.min_force) / denom
        fill_w = int(BAR_W * max(0.0, min(1.0, ratio)))
        pygame.draw.rect(self._display_surf, BAR_FILL_COLOR, (bar_x, bar_y, fill_w, BAR_H))
        pygame.draw.rect(self._display_surf, BAR_BORDER_COLOR, (bar_x, bar_y, BAR_W, BAR_H), 1)

        pygame.display.flip()

    def _reset_to_menu_layout(self) -> None:
        # Ensure pygame and font subsystem are initialized (editor may have quit them)
        try:
            pygame.init()
        except Exception:
            pass
        try:
            pygame.font.init()
        except Exception:
            pass

        default_w, default_h = 800, 600
        self.size = (default_w, default_h)
        self.width, self.height = default_w, default_h
        # recreate display surface after reinitializing pygame
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.mouse.set_visible(True)

        # Recreate menus that rely on pygame.font
        self.menu = Menu(self.width, self.height, self.font)
        self.settings_menu = SettingsMenu(self.width, self.height, self.font)
        self.start_menu = StartMenu(self.width, self.height, self.font)
        self._game_over_button_rect = None

    def _draw_game_scene(self):
        for p in self.projectiles:
            p.draw(self._display_surf)
        for player in self.players:
            for c in player.characters:
                c.draw(self._display_surf)
        for explosion in self.explosions:
            explosion.draw(self._display_surf)

    def _draw_trajectory_preview(self) -> None:
        preview_char = self._active_character()
        if preview_char:
            preview_x = int(preview_char.pos_x + preview_char.width/2)
            preview_y = int(preview_char.pos_y + preview_char.height/4)
            facing_right = not preview_char.facing_left
            player_center_x = preview_x
            player_center_y = preview_char.pos_y + preview_char.height/2
        else:
            preview_x = self.width//2
            preview_y = self.height//2
            facing_right = True
            player_center_x = preview_x
            player_center_y = preview_y

        mx, my = pygame.mouse.get_pos()
        dx = mx - player_center_x
        dy = player_center_y - my

        if dx != 0:
            raw_angle = max(5, min(85, math.degrees(math.atan2(dy, abs(dx)))))
        else:
            raw_angle = 45

        self.angle = raw_angle if facing_right else (180 - raw_angle)

        preview = (
            ROQUETTE(preview_x, preview_y, self.angle, self.force, terrain=self.terrain)
            if self.current_weapon == "roquette"
            else GRENADE(preview_x, preview_y, self.angle, self.force, terrain=self.terrain)
        )

        pts = preview.simulate_trajectory(
            wind=WIND if self.current_weapon == "roquette" else 0,
            time_scale=self.projectile_time_scale
        )

        for (px, py) in pts:
            pygame.draw.circle(self._display_surf, TRAJECTORY_COLOR, (px, py), 2)

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
