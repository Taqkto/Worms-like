"""
Worms Like - Main Application
=============================
Point d'entrée principal du jeu. Utilise des mixins pour séparer les responsabilités.
"""

import random
import pygame
from typing import List, Optional, Sequence

# Menus
from Menu.Menu import Menu
from Menu.SettingsMenu import SettingsMenu
from Menu.StartMenu import StartMenu
from Menu.PauseMenu import PauseMenu

# Maps
from maps.map import load_default_map, load_map_from_txt, GridMap

# Configuration
from config import (
    WIND_MIN, WIND_MAX, PROJECTILE_TIME_SCALE,
    MIN_FORCE, MAX_FORCE, CHARGE_RATE,
)

# Armes
from Weapons.grappin import Grappin

# Joueurs
from Player.character import Character
from Player.player import Player
from Game.turn_manager import TurnManager

# Mixins (logique externalisée)
from Game.event_handler import EventHandlerMixin
from Game.game_loop import GameLoopMixin
from Game.renderer import RendererMixin
from Game.projectile_manager import ProjectileManagerMixin
from Game.utils import UtilsMixin


class App(EventHandlerMixin, GameLoopMixin, RendererMixin, ProjectileManagerMixin, UtilsMixin):
    """
    Classe principale de l'application Worms Like.
    Hérite des mixins pour la gestion des événements, la boucle de jeu,
    le rendu, les projectiles et les utilitaires.
    """

    def __init__(self) -> None:
        """Initialise l'application avec les valeurs par défaut."""
        # État de l'application
        self._running = True
        self._display_surf: Optional[pygame.Surface] = None
        self.size = self.width, self.height = 800, 600
        self.state = "menu"

        # Terrain
        self.terrain: Optional[GridMap] = None

        # Listes d'entités gameplay
        self.projectiles = []
        self.explosions = []
        self.mines = []

        # Système de tir / charge
        self.charging = False
        self.min_force = MIN_FORCE
        self.max_force = MAX_FORCE
        self.charge_rate = CHARGE_RATE
        self.force = self.min_force
        self.current_weapon = "roquette"
        self.angle = 80

        # Contrôles clavier
        self.key_bindings = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "jump": pygame.K_SPACE,
            "switch_grenade": pygame.K_g,
            "switch_rocket": pygame.K_r,
            "switch_grappin": pygame.K_h,
            "switch_mine": pygame.K_m,
        }

        # Physique des projectiles
        self.projectile_time_scale = PROJECTILE_TIME_SCALE

        # Grappin
        self.grappin: Optional[Grappin] = None

        # Environnement (vent)
        self.wind = random.uniform(WIND_MIN, WIND_MAX)

        # Gestion des tours
        self.turn_time_limit = 30.0
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index: Optional[int] = None

        # Menus / UI
        self.menu: Optional[Menu] = None
        self.start_menu: Optional[StartMenu] = None
        self.settings_menu: Optional[SettingsMenu] = None
        self.pause_menu: Optional[PauseMenu] = None
        self.font: Optional[pygame.font.Font] = None

        # Multijoueur
        self.players: List[Player] = []
        self.turn_manager: Optional[TurnManager] = None
        self._game_over_button_rect: Optional[pygame.Rect] = None
        self.winner_player_number: Optional[int] = None

        # États internes
        self._pending_game_over = False
        self._pending_winner = None
        self._pending_turn_switch = False
        self._has_fired_this_turn = False
        self._settings_from_pause = False
        self.mine_turn_delay = 0.0

    def on_init(self) -> bool:
        """Initialise Pygame et crée les menus."""
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 20)

        self._display_surf = pygame.display.set_mode(
            self.size, pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.mouse.set_visible(True)

        # Création des menus
        self.menu = Menu(self.width, self.height, self.font)
        self.settings_menu = SettingsMenu(self.width, self.height, self.font)
        self.start_menu = StartMenu(self.width, self.height, self.font)
        self.pause_menu = PauseMenu(self.width, self.height, self.font)

        # Synchronisation des bindings depuis les settings
        self.key_bindings = self.settings_menu.key_bindings.copy()
        self.key_bindings["switch_grappin"] = pygame.K_h
        self.key_bindings["switch_mine"] = pygame.K_m

        return True

    def create_players_and_turns(self, names: Sequence[Sequence[str] | str]) -> None:
        """Crée les joueurs et leurs personnages à partir des noms fournis."""
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

        # Normalisation des noms
        normalized: List[List[str]] = []
        if not names:
            normalized = [["Player1"]]
        elif isinstance(names[0], (list, tuple)):
            normalized = [list(p) for p in names]
        else:
            normalized = [[nm] for nm in names]

        # Création des joueurs et personnages
        for p_idx, char_names in enumerate(normalized):
            player = Player()
            for cname in char_names:
                left_x = spawn_left()
                char = Character(
                    player_number=p_idx + 1,
                    pos_x=int(left_x),
                    pos_y=None,
                    terrain=self.terrain
                )
                char._app_ref = self
                if cname:
                    char.rename(str(cname))
                player.add_character(char)
            self.players.append(player)

        # Initialisation du gestionnaire de tours
        self.turn_manager = TurnManager(self.players)
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index = self.turn_manager.current_player_index

    def start_game(self, config: dict) -> None:
        """Démarre une nouvelle partie avec la configuration fournie."""
        # Chargement de la carte
        map_path = config.get("map_path")
        try:
            self.terrain = load_map_from_txt(map_path) if map_path else load_default_map()
        except Exception:
            self.terrain = load_default_map()

        self._resize_display_to_terrain()

        # Création des joueurs
        names = config.get("names", []) or []
        self.create_players_and_turns(names)

        # Réinitialisation de l'état de jeu
        self.projectiles = []
        self.explosions = []
        self.mines = []
        self.force = self.min_force
        self.state = "playing"
        self.turn_time_remaining = self.turn_time_limit
        self._last_player_index = self.turn_manager.current_player_index
        self._pending_turn_switch = False
        self._has_fired_this_turn = False
        self.mine_turn_delay = 0.0

    def on_cleanup(self) -> None:
        """Nettoyage des ressources avant fermeture."""
        pygame.quit()

    def on_execute(self) -> None:
        """Point d'entrée principal de la boucle de jeu."""
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

