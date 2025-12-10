"""
Fonctions et méthodes utilitaires pour Worms Like.
"""

import pygame
from typing import Optional

from Menu.Menu import Menu
from Menu.SettingsMenu import SettingsMenu
from Menu.StartMenu import StartMenu


class UtilsMixin:
    """Mixin contenant les méthodes utilitaires."""

    def _active_character(self) -> Optional['Character']:
        """Retourne le personnage actif du joueur courant."""
        if not self.turn_manager or not self.turn_manager.current_player:
            return None
        return self.turn_manager.current_player.access_current_character()

    def _restore_player_weapon(self) -> None:
        """Restaure l'arme mémorisée du joueur actuel."""
        if not self.turn_manager or not self.turn_manager.current_player:
            return

        current_player = self.turn_manager.current_player
        self.current_weapon = current_player.current_weapon

        # Mise à jour du sprite de l'arme tenue
        active_char = self._active_character()
        if active_char:
            weapon_to_item = {
                "roquette": "rocket",
                "grenade": "grenade",
                "grappin": "grappin",
                "mine": "mine"
            }
            active_char.current_hand_item = weapon_to_item.get(self.current_weapon)

    def _reset_game_state(self) -> None:
        """Réinitialise l'état du jeu."""
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

    def _reset_to_menu_layout(self) -> None:
        """Réinitialise l'affichage pour le menu principal."""
        # Réinitialisation de Pygame si nécessaire
        try:
            pygame.init()
        except Exception:
            pass

        try:
            pygame.font.init()
        except Exception:
            pass

        # Taille par défaut
        default_w, default_h = 800, 600
        self.size = (default_w, default_h)
        self.width, self.height = default_w, default_h

        # Recréation de la surface d'affichage
        self._display_surf = pygame.display.set_mode(
            self.size, pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.mouse.set_visible(True)

        # Recréation des menus
        self.menu = Menu(self.width, self.height, self.font)
        self.settings_menu = SettingsMenu(self.width, self.height, self.font)
        self.start_menu = StartMenu(self.width, self.height, self.font)
        self._game_over_button_rect = None

    def _resize_display_to_terrain(self) -> None:
        """Redimensionne la fenêtre selon la taille du terrain."""
        if self.terrain:
            self.size = self.width, self.height = self.terrain.width, self.terrain.height
            self._display_surf = pygame.display.set_mode(
                self.size, pygame.HWSURFACE | pygame.DOUBLEBUF
            )

