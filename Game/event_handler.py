"""
Gestionnaire d'événements pour le jeu Worms Like.
Contient les mixins pour gérer tous les types d'événements.
"""

import pygame
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Player.character import Character
    from Player.player import Player


class EventHandlerMixin:
    """Mixin contenant tous les gestionnaires d'événements."""

    def on_event(self, event: pygame.event.Event) -> None:
        """Dispatcher principal des événements."""
        if event.type == pygame.QUIT:
            self._running = False
            return

        state_handlers = {
            "game_over": self._handle_game_over_event,
            "paused": self._handle_pause_event,
            "menu": self._handle_menu_event,
            "start": self._handle_start_event,
            "settings": self._handle_settings_event,
        }

        handler = state_handlers.get(self.state)
        if handler:
            handler(event)
        else:
            self._handle_play_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        """Gère les événements du menu principal."""
        action = self.menu.handle_event(event)
        if action == "play":
            self.start_menu.reset()
            self.state = "start"
        elif action == "editor":
            try:
                from level_editor import LevelEditor
                editor = LevelEditor()
                editor.run()
            except Exception as e:
                print(f"Could not start editor: {e}")
            self._reset_to_menu_layout()
            self.state = "menu"
        elif action == "settings":
            self._settings_from_pause = False
            self.state = "settings"
        elif action == "quit":
            self._running = False

    def _handle_start_event(self, event: pygame.event.Event) -> None:
        """Gère les événements de l'écran de configuration de partie."""
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
        """Gère les événements du menu des paramètres."""
        result = self.settings_menu.handle_event(event)
        if isinstance(result, dict):
            if "key_bindings" in result:
                self.key_bindings.update(result["key_bindings"])
            if result.get("action") == "back":
                self.state = "paused" if self._settings_from_pause else "menu"
                self._settings_from_pause = False
        elif result == "back":
            self.state = "menu"

    def _handle_pause_event(self, event: pygame.event.Event) -> None:
        """Gère les événements du menu pause."""
        result = self.pause_menu.handle_event(event)
        if result == "resume":
            self.state = "playing"
        elif result == "settings":
            self._settings_from_pause = True
            self.settings_menu.resize(self.width, self.height)
            self.state = "settings"
        elif result == "home":
            self._reset_game_state()
            self._reset_to_menu_layout()
            self.state = "menu"

    def _handle_game_over_event(self, event: pygame.event.Event) -> None:
        """Gère les événements de l'écran de fin de partie."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if not self._game_over_button_rect:
            return
        mx, my = event.pos
        if self._game_over_button_rect.collidepoint(mx, my):
            self._reset_game_state()
            self._reset_to_menu_layout()
            self.state = "menu"

    def _handle_play_event(self, event: pygame.event.Event) -> None:
        """Gère les événements pendant le jeu."""
        active_char = self._active_character()
        current_player = self.turn_manager.current_player if self.turn_manager else None

        if event.type == pygame.KEYDOWN:
            self._handle_play_keydown(event, active_char, current_player)

        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_play_mousedown(event, active_char)

        if event.type == pygame.MOUSEBUTTONUP:
            self._handle_play_mouseup(event, active_char)

    def _handle_play_keydown(self, event: pygame.event.Event,
                             active_char: Optional['Character'],
                             current_player: Optional['Player']) -> None:
        """Gère les touches pressées pendant le jeu."""
        # Pause
        if event.key == pygame.K_ESCAPE:
            self.pause_menu.resize(self.width, self.height)
            self.state = "paused"
            return

        # Changement d'arme
        weapon_keys = {
            self.key_bindings["switch_rocket"]: ("roquette", "rocket"),
            self.key_bindings["switch_grenade"]: ("grenade", "grenade"),
            self.key_bindings["switch_mine"]: ("mine", "mine"),
            self.key_bindings["switch_grappin"]: ("grappin", "grappin"),
        }

        if event.key in weapon_keys:
            weapon, hand_item = weapon_keys[event.key]
            self._switch_weapon(weapon, hand_item, active_char, current_player)
            return

        # Ajustement de la force
        if event.key == pygame.K_RIGHT:
            self.force = min(self.max_force, self.force + 2)
        elif event.key == pygame.K_LEFT:
            self.force = max(self.min_force, self.force - 2)

        # Saut / Relâchement du grappin
        elif event.key in (self.key_bindings["jump"], pygame.K_UP):
            if self.grappin and self.grappin.is_swinging():
                self.grappin.release()
                self.grappin = None
                self._pending_turn_switch = True
                self._has_fired_this_turn = True
            elif active_char:
                active_char.jump()

    def _handle_play_mousedown(self, event: pygame.event.Event,
                               active_char: Optional['Character']) -> None:
        """Gère les clics souris pendant le jeu."""
        from Weapons.grappin import Grappin

        # Clic gauche - Tir
        if event.button == 1:
            if self.current_weapon == "grappin":
                if not self._has_fired_this_turn and active_char:
                    if self.grappin is None or not self.grappin.is_active():
                        self.grappin = Grappin(active_char, self.terrain)
                        self.grappin.fire(self.angle)

            elif self.current_weapon == "mine" and not self._has_fired_this_turn:
                if active_char:
                    self._spawn_current_projectile(active_char)

            elif not self._has_fired_this_turn and self.current_weapon != "mine":
                self.charging = True

        # Clic droit - Annuler le grappin
        elif event.button == 3:
            if self.grappin and self.grappin.is_active():
                self.grappin.cancel()
                self.grappin = None
                self._pending_turn_switch = True
                self._has_fired_this_turn = True

    def _handle_play_mouseup(self, event: pygame.event.Event,
                             active_char: Optional['Character']) -> None:
        """Gère le relâchement des boutons souris pendant le jeu."""
        if event.button == 1 and self.charging:
            if self.current_weapon != "grappin":
                self._spawn_current_projectile(active_char)
                self.charging = False
                self.force = self.min_force
                self._pending_turn_switch = True
                self._has_fired_this_turn = True

                # Cas spécial grenade
                if active_char and self.current_weapon == "grenade":
                    active_char.current_hand_item = None
                    self.current_weapon = None

    def _switch_weapon(self, weapon: str, hand_item: str,
                       active_char: Optional['Character'],
                       current_player: Optional['Player']) -> None:
        """Change l'arme actuelle."""
        self.current_weapon = weapon
        self.force = self.min_force
        self.charging = False

        if current_player:
            current_player.current_weapon = weapon
        if active_char:
            active_char.current_hand_item = hand_item

