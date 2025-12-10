"""
Gestionnaire de rendu pour Worms Like.
Contient toutes les méthodes de dessin.
"""

import math
import pygame
from typing import Optional, TYPE_CHECKING

from config import (
    SKY_COLOR, BAR_W, BAR_H,
    BAR_BG_COLOR, BAR_FILL_COLOR, BAR_BORDER_COLOR, TRAJECTORY_COLOR
)

if TYPE_CHECKING:
    from Player.character import Character


class RendererMixin:
    """Mixin contenant toutes les méthodes de rendu."""

    def on_render(self) -> None:
        """Rendu principal."""
        if not self._display_surf:
            return

        self._display_surf.fill(SKY_COLOR)

        if self.terrain:
            self.terrain.draw(self._display_surf)

        if self.state == "menu":
            self._render_menu()
            return

        if self.state == "start":
            self._render_start()
            return

        if self.state == "settings":
            self._render_settings()
            return

        if self.state == "paused":
            self._render_paused()
            return

        if self.state == "game_over":
            self._render_game_over()
            return

        self._render_gameplay()

    def _render_menu(self) -> None:
        """Rendu du menu principal."""
        self.menu.draw(self._display_surf)
        pygame.display.flip()

    def _render_start(self) -> None:
        """Rendu de l'écran de configuration de partie."""
        self.start_menu.draw(self._display_surf)
        pygame.display.flip()

    def _render_settings(self) -> None:
        """Rendu du menu des paramètres."""
        self.settings_menu.draw(self._display_surf)
        pygame.display.flip()

    def _render_paused(self) -> None:
        """Rendu de l'écran de pause."""
        self._draw_game_scene()
        self.pause_menu.draw(self._display_surf)
        pygame.display.flip()

    def _render_game_over(self) -> None:
        """Rendu de l'écran de fin de partie."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self._display_surf.blit(overlay, (0, 0))

        if self.font:
            winner_txt = f"Player {self.winner_player_number} wins!"
            surf = self.font.render(winner_txt, True, (255, 255, 255))
            tx = int(self.width / 2 - surf.get_width() / 2)
            ty = int(self.height / 2 - 40)
            self._display_surf.blit(surf, (tx, ty))

            self._draw_home_button()

        pygame.display.flip()

    def _draw_home_button(self) -> None:
        """Dessine le bouton Home sur l'écran de game over."""
        btn_text = "Home"
        btn_surf = self.font.render(btn_text, True, (255, 255, 255))
        padding = (12, 8)
        btn_w = btn_surf.get_width() + padding[0] * 2
        btn_h = btn_surf.get_height() + padding[1] * 2
        btn_x = int(self.width / 2 - btn_w / 2)
        btn_y = int(self.height / 2 + 4)

        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(self._display_surf, (200, 30, 30), btn_rect)
        pygame.draw.rect(self._display_surf, (0, 0, 0), btn_rect, 2)
        self._display_surf.blit(btn_surf, (btn_x + padding[0], btn_y + padding[1]))

        self._game_over_button_rect = btn_rect

    def _render_gameplay(self) -> None:
        """Rendu principal du jeu en cours."""
        # Projectiles
        for p in self.projectiles:
            p.draw(self._display_surf)

        # Mines
        for m in self.mines:
            m.draw(self._display_surf)

        # Personnages
        self._draw_characters()

        # Grappin
        if self.grappin and self.grappin.is_active():
            self.grappin.draw(self._display_surf)

        # Explosions
        for explosion in self.explosions:
            explosion.draw(self._display_surf)

        # Preview de trajectoire
        if self.charging and self.current_weapon != "mine":
            self._draw_trajectory_preview()

        # UI
        self._draw_ui()

        pygame.display.flip()

    def _draw_characters(self) -> None:
        """Dessine tous les personnages avec leur nom et barre de vie."""
        for player in self.players:
            for c in player.characters:
                c.draw(self._display_surf)

                # Nom du personnage
                if c.name and self.font:
                    surf = self.font.render(str(c.name), True, (255, 255, 255))
                    shadow = self.font.render(str(c.name), True, (0, 0, 0))
                    tx = int(c.pos_x + c.width / 2 - surf.get_width() / 2)
                    ty = int(c.pos_y - 28)
                    self._display_surf.blit(shadow, (tx + 1, ty + 1))
                    self._display_surf.blit(surf, (tx, ty))

                # Barre de vie
                self._draw_health_bar(c)

    def _draw_health_bar(self, character: 'Character') -> None:
        """Dessine la barre de vie d'un personnage."""
        if character.pv is None:
            return

        max_hp = 100
        ratio = max(0.0, min(1.0, character.pv / max_hp))
        bar_width = 40
        bar_height = 4
        bar_x = int(character.pos_x + character.width / 2 - bar_width / 2)
        bar_y = int(character.pos_y - 10)

        # Fond rouge
        pygame.draw.rect(self._display_surf, (100, 0, 0),
                         (bar_x, bar_y, bar_width, bar_height))

        # Remplissage coloré selon la santé
        if ratio > 0.5:
            hp_color = (0, 255, 0)
        elif ratio > 0.25:
            hp_color = (255, 255, 0)
        else:
            hp_color = (255, 0, 0)

        pygame.draw.rect(self._display_surf, hp_color,
                         (bar_x, bar_y, int(bar_width * ratio), bar_height))

        # Bordure
        pygame.draw.rect(self._display_surf, (255, 255, 255),
                         (bar_x, bar_y, bar_width, bar_height), 1)

    def _draw_ui(self) -> None:
        """Dessine l'interface utilisateur du jeu."""
        if not self.font or self.state != "playing":
            return

        self._draw_turn_timer()
        self._draw_power_bar()
        self._draw_weapon_info()
        self._draw_wind_info()
        self._draw_grappin_instructions()

    def _draw_turn_timer(self) -> None:
        """Dessine le timer de tour."""
        secs = max(0, int(math.ceil(self.turn_time_remaining)))
        player_idx = self.turn_manager.current_player_index + 1
        timer_text = f"P{player_idx}  {secs}s"

        shadow = self.font.render(timer_text, True, (0, 0, 0))
        text_surf = self.font.render(timer_text, True, (250, 250, 250))
        tx = int(self.width / 2 - text_surf.get_width() / 2)
        ty = 6

        self._display_surf.blit(shadow, (tx + 1, ty + 1))
        self._display_surf.blit(text_surf, (tx, ty))

    def _draw_power_bar(self) -> None:
        """Dessine la barre de puissance pendant le chargement."""
        active_char = self._active_character()
        if not self.charging or not active_char:
            return

        name_surf = self.font.render(active_char.name, True, (255, 255, 255))
        name_y = active_char.pos_y - 20

        bar_x = active_char.pos_x + active_char.width / 2 - BAR_W / 2
        bar_y = name_y - 30

        # Fond
        pygame.draw.rect(self._display_surf, BAR_BG_COLOR,
                         (bar_x, bar_y, BAR_W, BAR_H))

        # Remplissage
        denom = max(1e-6, (self.max_force - self.min_force))
        ratio = (self.force - self.min_force) / denom
        fill_w = int(BAR_W * max(0.0, min(1.0, ratio)))
        pygame.draw.rect(self._display_surf, BAR_FILL_COLOR,
                         (bar_x, bar_y, fill_w, BAR_H))

        # Bordure
        pygame.draw.rect(self._display_surf, BAR_BORDER_COLOR,
                         (bar_x, bar_y, BAR_W, BAR_H), 1)

    def _draw_weapon_info(self) -> None:
        """Affiche l'arme actuelle."""
        weapon_names = {
            "roquette": "Roquette [R]",
            "grenade": "Grenade [G]",
            "grappin": "Grappin [H]",
            "mine": "Mines [M]"
        }
        weapon_text = weapon_names.get(self.current_weapon, self.current_weapon)
        weapon_surf = self.font.render(weapon_text, True, (255, 255, 255))
        self._display_surf.blit(weapon_surf, (10, 10))

    def _draw_wind_info(self) -> None:
        """Affiche les informations sur le vent."""
        wind_direction = "→" if self.wind > 0 else "←" if self.wind < 0 else ""
        wind_text = f"Vent: {self.wind:.1f} {wind_direction}"

        # Couleur selon l'intensité
        if abs(self.wind) < 10:
            wind_color = (200, 200, 255)
        elif abs(self.wind) < 15:
            wind_color = (255, 200, 100)
        else:
            wind_color = (255, 100, 100)

        wind_surf = self.font.render(wind_text, True, wind_color)
        self._display_surf.blit(wind_surf, (10, 30))

    def _draw_grappin_instructions(self) -> None:
        """Affiche les instructions du grappin si actif."""
        if self.grappin and self.grappin.is_swinging():
            instr = "A/D: Balancer | W/S: Corde | ESPACE: Lacher | Clic droit: Annuler"
            instr_surf = self.font.render(instr, True, (255, 255, 0))
            self._display_surf.blit(instr_surf, (10, self.height - 25))

    def _draw_trajectory_preview(self) -> None:
        """Dessine la prévisualisation de la trajectoire du projectile."""
        from Weapons.roquette import ROQUETTE
        from Weapons.grenade import GRENADE

        preview_char = self._active_character()

        if preview_char:
            preview_x = int(preview_char.pos_x + preview_char.width / 2)
            preview_y = int(preview_char.pos_y + preview_char.height / 4)
            facing_right = not preview_char.facing_left
            player_center_x = preview_x
            player_center_y = preview_char.pos_y + preview_char.height / 2
        else:
            preview_x = self.width // 2
            preview_y = self.height // 2
            facing_right = True
            player_center_x = preview_x
            player_center_y = preview_y

        # Calcul de l'angle
        mx, my = pygame.mouse.get_pos()
        dx = mx - player_center_x
        dy = player_center_y - my

        if dx != 0:
            raw_angle = max(5, min(85, math.degrees(math.atan2(dy, abs(dx)))))
        else:
            raw_angle = 45

        self.angle = raw_angle if facing_right else (180 - raw_angle)

        # Création du projectile de prévisualisation
        if self.current_weapon == "roquette":
            preview = ROQUETTE(preview_x, preview_y, self.angle, self.force,
                               terrain=self.terrain, wind=self.wind)
            wind = self.wind
        else:
            preview = GRENADE(preview_x, preview_y, self.angle, self.force,
                              terrain=self.terrain)
            wind = 0

        # Simulation de la trajectoire
        pts = preview.simulate_trajectory(wind=wind, time_scale=self.projectile_time_scale)

        # Dessin des points
        for (px, py) in pts:
            pygame.draw.circle(self._display_surf, TRAJECTORY_COLOR, (px, py), 2)

    def _draw_game_scene(self) -> None:
        """Dessine la scène de jeu (pour le menu pause)."""
        for p in self.projectiles:
            p.draw(self._display_surf)

        for player in self.players:
            for c in player.characters:
                c.draw(self._display_surf)

        for explosion in self.explosions:
            explosion.draw(self._display_surf)

