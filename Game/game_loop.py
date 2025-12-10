"""
Boucle de jeu pour Worms Like.
Contient la logique de mise à jour du jeu.
"""

import math
import random
import pygame
from typing import Optional, TYPE_CHECKING

from config import WIND_MIN, WIND_MAX

if TYPE_CHECKING:
    from Player.character import Character


class GameLoopMixin:
    """Mixin contenant la logique de la boucle de jeu."""

    def on_loop(self, dt: float) -> None:
        """Boucle principale de mise à jour du jeu."""
        if self.state != "playing":
            return

        self._update_turn_manager()
        self._update_explosions(dt)
        self._cleanup_dead_entities()
        self._update_turn_manager_players()
        self._update_mine_delay(dt)
        self._check_turn_switch()
        self._update_turn_timer(dt)
        self._check_victory()

        if self._pending_game_over:
            self._handle_pending_game_over(dt)
            return

        self._process_gameplay(dt)

    def _update_turn_manager(self) -> None:
        """Met à jour le gestionnaire de tours au début du tour."""
        if not self.turn_manager:
            return

        if self._last_player_index is None:
            self._last_player_index = self.turn_manager.current_player_index
            self._restore_player_weapon()
        elif self._last_player_index != self.turn_manager.current_player_index:
            self.turn_time_remaining = self.turn_time_limit
            self._last_player_index = self.turn_manager.current_player_index
            self._has_fired_this_turn = False
            self._restore_player_weapon()

    def _update_explosions(self, dt: float) -> None:
        """Met à jour et nettoie les explosions."""
        for explosion in self.explosions:
            explosion.update(dt)
        self.explosions = [e for e in self.explosions if e.alive]

    def _cleanup_dead_entities(self) -> None:
        """Supprime les personnages et joueurs morts."""
        for player in self.players:
            player.characters = [c for c in player.characters if c.alive]
        self.players = [pl for pl in self.players if pl.has_alive_characters()]

    def _update_turn_manager_players(self) -> None:
        """Met à jour la liste des joueurs dans le gestionnaire de tours."""
        if self.turn_manager and self.players:
            self.turn_manager.players = self.players
            if self.turn_manager.current_player_index >= len(self.players):
                self.turn_manager.current_player_index = 0

    def _update_mine_delay(self, dt: float) -> None:
        """Met à jour le délai après pose de mine."""
        if self.mine_turn_delay > 0:
            self.mine_turn_delay -= dt
            if self.mine_turn_delay <= 0:
                self.mine_turn_delay = 0
                self._pending_turn_switch = True

    def _check_turn_switch(self) -> None:
        """Vérifie et effectue le changement de tour si nécessaire."""
        if self._pending_turn_switch and self._can_end_turn():
            self._execute_turn_switch()

    def _execute_turn_switch(self) -> None:
        """Exécute le changement de tour."""
        self.turn_manager.next_turn()
        self._last_player_index = self.turn_manager.current_player_index
        self._has_fired_this_turn = False
        self.turn_time_remaining = self.turn_time_limit
        self._pending_turn_switch = False
        self.mine_turn_delay = 0.0
        self._restore_player_weapon()
        self._randomize_wind()

    def _update_turn_timer(self, dt: float) -> None:
        """Met à jour le timer de tour et change de tour si expiré."""
        self.turn_time_remaining -= dt
        if self.turn_time_remaining <= 0 and self._can_end_turn():
            self._execute_turn_switch()

    def _check_victory(self) -> None:
        """Vérifie si un joueur a gagné."""
        alive_players = [pl for pl in self.players if pl.has_alive_characters()]
        if len(alive_players) == 1:
            try:
                winner_num = alive_players[0].characters[0].player_number
            except Exception:
                winner_num = 1
            self._pending_game_over = True
            self._pending_winner = winner_num

    def _handle_pending_game_over(self, dt: float) -> None:
        """Gère la fin de partie en attente."""
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

    def _process_gameplay(self, dt: float) -> None:
        """Traitement principal du gameplay à chaque frame."""
        active_char = self._active_character()

        self._update_aim_angle(active_char)

        if self.charging:
            self.force = min(self.max_force, self.force + self.charge_rate * dt)

        self._update_grappin(dt)

        scaled_dt = dt * self.projectile_time_scale
        self._update_projectiles(scaled_dt, dt)
        self._update_mines(dt)
        self._update_inactive_characters(dt, active_char)
        self._update_active_character_movement(dt, active_char)

    def _update_aim_angle(self, active_char: Optional['Character']) -> None:
        """Met à jour l'angle de visée basé sur la position de la souris."""
        if active_char:
            px = active_char.pos_x
            pw = active_char.width
            facing_right = not active_char.facing_left
            player_center_y = active_char.pos_y + active_char.height / 2.0
        else:
            px, pw, facing_right = 0.0, 32, True
            player_center_y = self.height / 2.0

        mx, my = pygame.mouse.get_pos()
        player_center_x = px + pw / 2.0

        dx = mx - player_center_x
        dy = player_center_y - my

        if dx != 0:
            raw_angle = math.degrees(math.atan2(dy, abs(dx)))
            raw_angle = max(5, min(85, raw_angle))
            self.angle = raw_angle if facing_right else (180 - raw_angle)

    def _update_grappin(self, dt: float) -> None:
        """Met à jour le grappin si actif."""
        if self.grappin and self.grappin.is_active():
            keys = pygame.key.get_pressed()
            keys_dict = {
                pygame.K_a: keys[pygame.K_a],
                pygame.K_d: keys[pygame.K_d],
                pygame.K_w: keys[pygame.K_w],
                pygame.K_s: keys[pygame.K_s],
                pygame.K_LEFT: keys[pygame.K_LEFT],
                pygame.K_RIGHT: keys[pygame.K_RIGHT],
                pygame.K_UP: keys[pygame.K_UP],
                pygame.K_DOWN: keys[pygame.K_DOWN],
            }
            self.grappin.update(dt, keys_dict)

    def _update_mines(self, dt: float) -> None:
        """Met à jour les mines."""
        for m in list(self.mines):
            m.move(dt)
            if m.y > self.height:
                m.exploded = True
            if m.exploded:
                self._handle_explosion(m)
                m.alive = False

        self.mines = [m for m in self.mines if m.alive]

    def _update_inactive_characters(self, dt: float, active_char: Optional['Character']) -> None:
        """Met à jour les personnages non actifs."""
        for player in self.players:
            for c in player.characters:
                if c is not active_char:
                    c.update(dt)

    def _update_active_character_movement(self, dt: float, active_char: Optional['Character']) -> None:
        """Gère le mouvement du personnage actif."""
        if not active_char:
            return

        if self.grappin and self.grappin.is_swinging():
            return

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

    def _can_end_turn(self) -> bool:
        """Vérifie si le tour peut se terminer."""
        if self.explosions:
            return False
        if self.projectiles:
            return False
        if self.grappin and self.grappin.is_active():
            return False

        active_char = self._active_character()
        if active_char and active_char.alive and not active_char.on_ground:
            return False

        return True

    def _randomize_wind(self) -> None:
        """Change le vent aléatoirement."""
        self.wind = random.uniform(WIND_MIN, WIND_MAX)

