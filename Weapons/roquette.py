# Weapons/roquette.py
from .weapons_base import PROJECTILE
from config import WIND, SCREEN_WIDTH, GROUND_RECT_Y
import pygame


class ROQUETTE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None, characters=None):
        super().__init__("roquette", x, y, angle, force, terrain=terrain)
        self.explosion_radius = 50
        self.characters = characters or []

        # Sprite de la roquette
        self.sprite = pygame.image.load("Assets/projectiles/rocket.png").convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (18, 8))

    # -------------------------------------------------------
    # COLLISIONS SOL / MURS — version stable comme grenade2
    # -------------------------------------------------------

    def _check_horizontal_collision(self, new_x: float) -> bool:
        if not self.terrain:
            return False

        check_heights = [
            self.y - self.radius,
            self.y,
            self.y + self.radius,
        ]

        check_x = new_x + self.radius if new_x > self.x else new_x - self.radius

        for check_y in check_heights:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    def _check_vertical_collision(self, new_y: float) -> bool:
        if not self.terrain:
            return new_y + self.radius >= GROUND_RECT_Y

        check_positions = [
            self.x - self.radius,
            self.x,
            self.x + self.radius,
        ]

        check_y = new_y + self.radius if self.speedY > 0 else new_y - self.radius

        for check_x in check_positions:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    # -------------------------------------------------------
    # COLLISION AVEC LES PERSONNAGES
    # -------------------------------------------------------

    def _check_character_collision(self) -> bool:
        for char in self.characters:
            if not char.alive:
                continue

            char_left = char.pos_x
            char_right = char.pos_x + char.width
            char_top = char.pos_y
            char_bottom = char.pos_y + char.height

            closest_x = max(char_left, min(self.x, char_right))
            closest_y = max(char_top, min(self.y, char_bottom))

            dist_x = self.x - closest_x
            dist_y = self.y - closest_y
            distance = (dist_x ** 2 + dist_y ** 2) ** 0.5

            if distance <= self.radius:
                return True

        return False

    # -------------------------------------------------------
    # PHYSIQUE PRINCIPALE DE LA ROQUETTE
    # -------------------------------------------------------

    def move(self, dt: float) -> None:
        # Gravité normale
        self.apply_gravity(dt)

        # Vent
        self.speedX += WIND * dt

        # Nouveau mouvement
        new_x = self.x + self.speedX * dt
        new_y = self.y + self.speedY * dt

        # Collision mur
        if self._check_horizontal_collision(new_x):
            self.trigger_explosion()
            return
        else:
            self.x = new_x

        # Collision sol/plafond
        if self._check_vertical_collision(new_y):
            self.trigger_explosion()
            return
        else:
            self.y = new_y

        # Collision personnage
        if self._check_character_collision():
            self.trigger_explosion()
            return

        # Sortie écran horizontale
        max_x = self.terrain.width if self.terrain else SCREEN_WIDTH
        if self.x <= self.radius or self.x >= max_x - self.radius:
            self.trigger_explosion()

        # Sortie écran verticale (sécurité)
        max_y = self.terrain.height if self.terrain else 600
        if self.y >= max_y:
            self.trigger_explosion()

    # -------------------------------------------------------
    # DESSIN AVEC SPRITE
    # -------------------------------------------------------

    def draw(self, screen):
        if not self.alive:
            return

        w, h = self.sprite.get_size()
        screen.blit(self.sprite, (int(self.x - w / 2), int(self.y - h / 2)))
