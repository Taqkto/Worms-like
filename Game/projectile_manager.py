"""
Gestionnaire de projectiles et explosions pour Worms Like.
"""

import math
from typing import Optional, TYPE_CHECKING

from Weapons.grenade import GRENADE
from Weapons.roquette import ROQUETTE
from Weapons.explosion import Explosion
from Weapons.mine import Mine

if TYPE_CHECKING:
    from Player.character import Character


def calculate_explosion_damage(distance: float, radius: float, max_damage: int = 100) -> int:
    """
    Calcule les dégâts d'une explosion en fonction de la distance.
    Décroissance linéaire : plus on est proche, plus on prend de dégâts.
    """
    if distance >= radius:
        return 0
    distance_ratio = distance / radius
    damage = int(max_damage * (1.0 - distance_ratio))
    return max(0, damage)


class ProjectileManagerMixin:
    """Mixin contenant la gestion des projectiles et explosions."""

    def _spawn_current_projectile(self, active_char: Optional['Character']) -> None:
        """Crée et lance le projectile de l'arme actuelle."""
        # Position de spawn
        if active_char:
            spawn_x = int(active_char.pos_x + active_char.width / 2)
            spawn_y = int(active_char.pos_y + active_char.height / 4)
        else:
            spawn_x = self.width // 2
            spawn_y = self.height // 2

        # Liste des autres personnages (pour les collisions)
        all_characters = [
            c for player in self.players
            for c in player.characters
            if c != active_char
        ]

        # Création du projectile selon l'arme
        if self.current_weapon == "roquette":
            p = ROQUETTE(
                spawn_x, spawn_y, self.angle, self.force,
                terrain=self.terrain, characters=all_characters, wind=self.wind
            )

        elif self.current_weapon == "grenade":
            p = GRENADE(
                spawn_x, spawn_y, self.angle, self.force,
                terrain=self.terrain
            )

        elif self.current_weapon == "mine":
            self._spawn_mine(active_char, spawn_x)
            return

        else:
            return

        # Vérification collision initiale
        if self.terrain:
            block = self.terrain.block_at_pixel(p.x, p.y)
            if block and block.solid:
                ground_top = self.terrain.height_at(p.x)
                p.y = ground_top - p.radius - 1

        self.projectiles.append(p)

    def _spawn_mine(self, active_char: 'Character', spawn_x: int) -> None:
        """Pose une mine au sol devant le personnage."""
        facing_left = active_char.facing_left
        offset = -30 if facing_left else 30
        spawn_x = int(active_char.pos_x + active_char.width / 2 + offset)

        spawn_y = int(active_char.pos_y + active_char.height)
        while spawn_y < self.terrain.height - 1:
            block = self.terrain.block_at_pixel(spawn_x, spawn_y)
            if block and block.solid:
                spawn_y -= 8
                break
            spawn_y += 1

        mine = Mine(
            spawn_x, spawn_y, facing_left,
            terrain=self.terrain,
            characters=[c for pl in self.players for c in pl.characters]
        )

        self.mines.append(mine)
        active_char.current_hand_item = None
        self._has_fired_this_turn = True
        self.mine_turn_delay = 2.0

    def _update_projectiles(self, scaled_dt: float, real_dt: float) -> None:
        """Met à jour tous les projectiles."""
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
                        p.speedX += self.wind * real_dt
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
        """Gère une explosion : dégâts, destruction du terrain, effets."""
        try:
            cx = p.x
            cy = p.y
            radius = getattr(p, "explosion_radius", 40)
        except Exception:
            return

        # Création de l'effet visuel
        explosion = Explosion(cx, cy, radius)
        self.explosions.append(explosion)

        # Destruction du terrain
        if self.terrain:
            self.terrain.destroy_circle(cx, cy, radius)

            # Mise à jour de l'état au sol des personnages
            for player in self.players:
                for c in player.characters:
                    under = self.terrain.block_at_pixel(
                        int(c.pos_x + c.width / 2),
                        int(c.pos_y + c.height + 1)
                    )
                    if not under or not under.solid:
                        c.on_ground = False

        # Application des dégâts
        for player in self.players:
            for c in list(player.characters):
                char_cx = c.pos_x + c.width / 2
                char_cy = c.pos_y + c.height / 2
                dist = math.dist((char_cx, char_cy), (cx, cy))
                dmg = calculate_explosion_damage(dist, radius)
                if dmg > 0:
                    c.damage(dmg)

            player.characters = [c for c in player.characters if c.alive]

        # Nettoyage des projectiles
        self.projectiles = [pp for pp in self.projectiles if pp.alive and not pp.exploded]

        # Vérification de victoire
        alive_players = [pl for pl in self.players if pl.has_alive_characters()]
        if len(alive_players) == 1:
            try:
                winner_num = alive_players[0].characters[0].player_number
            except Exception:
                winner_num = 1
            self._pending_game_over = True
            self._pending_winner = winner_num

