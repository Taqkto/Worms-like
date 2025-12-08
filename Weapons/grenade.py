# Weapons/grenade.py
from .weapons_base import PROJECTILE
from config import (
    GROUND_RECT_Y,
    MIN_BOUNCE_SPEED,
    HORIZONTAL_BOUNCE_MIN_SPEED,
    HORIZONTAL_DAMP,
    VERTICAL_DAMP,
    GRAVITY,
)
import pygame


class GRENADE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None):
        super().__init__("grenade", x, y, angle, force, terrain=terrain)
        self.timer = 3.0
        self.explosion_radius = 60

        self.sprite = pygame.image.load("Assets/projectiles/grenade.png").convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (14, 14))

    def _is_in_water(self) -> bool:
        """Vérifie si le centre de la grenade est dans un bloc d'eau."""
        if not self.terrain:
            return False
        from maps.map import WaterBlock
        block = self.terrain.block_at_pixel(self.x, self.y)
        return isinstance(block, WaterBlock)

    def _get_water_depth(self) -> float:
        """Retourne la profondeur d'immersion (0 = surface, plus = plus profond)."""
        if not self.terrain:
            return 0.0
        from maps.map import WaterBlock

        # Vérifie combien de la grenade est dans l'eau
        top = self.y - self.radius
        center = self.y
        bottom = self.y + self.radius

        in_water_count = 0
        for check_y in [top, center, bottom]:
            block = self.terrain.block_at_pixel(self.x, check_y)
            if isinstance(block, WaterBlock):
                in_water_count += 1

        return in_water_count / 3.0  # 0.0 à 1.0

    def apply_gravity(self, dt: float) -> None:
        water_depth = self._get_water_depth()

        if water_depth > 0:
            # Poussée d'Archimède : force vers le haut proportionnelle à l'immersion
            # buoyancy > 1.0 = flotte, < 1.0 = coule
            buoyancy_strength = 2.5  # Flotte fortement

            # Gravité normale - poussée d'Archimède
            net_gravity = GRAVITY * (1.0 - buoyancy_strength * water_depth)
            self.speedY += net_gravity * dt

            # Friction de l'eau (indépendante du framerate)
            drag_factor = 1.5 * water_depth  # Friction réduite pour plus de réactivité

            # Appliquer la friction : v = v * e^(-drag * dt)
            import math
            drag_multiplier = math.exp(-drag_factor * dt)
            self.speedX *= drag_multiplier
            self.speedY *= drag_multiplier

            # Limite de vitesse dans l'eau
            max_water_speed = 200.0
            if abs(self.speedX) > max_water_speed:
                self.speedX = max_water_speed if self.speedX > 0 else -max_water_speed
            if abs(self.speedY) > max_water_speed:
                self.speedY = max_water_speed if self.speedY > 0 else -max_water_speed
        else:
            # Pas dans l'eau : gravité normale
            self.speedY += GRAVITY * dt

    def _check_horizontal_collision(self, new_x: float, new_y: float) -> bool:
        """Vérifie collision avec un mur (pas le sol)."""
        if not self.terrain:
            return False

        # Vérifier seulement le centre et le haut, PAS le bas (évite confusion avec le sol)
        check_heights = [
            new_y - self.radius,  # haut
            new_y,                 # centre
        ]

        check_x = new_x + self.radius if self.speedX > 0 else new_x - self.radius

        for check_y in check_heights:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    def _check_vertical_collision(self, new_y: float, new_x: float) -> tuple[bool, float | None]:
        """Retourne (collision, ground_top_y) - position Y du centre après snap."""
        if not self.terrain:
            if new_y + self.radius >= GROUND_RECT_Y:
                return True, GROUND_RECT_Y - self.radius
            return False, None

        check_positions = [
            new_x - self.radius,
            new_x,
            new_x + self.radius,
        ]

        tile_size = self.terrain.tile_size

        if self.speedY > 0:
            # Chute : on vérifie le bas de la grenade
            check_y = new_y + self.radius
            for cx in check_positions:
                block = self.terrain.block_at_pixel(cx, check_y)
                if block and block.solid:
                    # Le bloc touché est à la ligne où check_y se trouve
                    block_row = int(check_y) // tile_size
                    # Le haut du bloc = block_row * tile_size
                    # Le centre de la grenade doit être au-dessus : haut_bloc - radius
                    ground_top = block_row * tile_size - self.radius
                    return True, ground_top
        else:
            # Montée : on vérifie le haut de la grenade (plafond)
            check_y = new_y - self.radius
            for cx in check_positions:
                block = self.terrain.block_at_pixel(cx, check_y)
                if block and block.solid:
                    block_row = int(check_y) // tile_size
                    # Le bas du bloc = (block_row + 1) * tile_size
                    # Le centre doit être en dessous : bas_bloc + radius
                    ceiling_bottom = (block_row + 1) * tile_size + self.radius
                    return True, ceiling_bottom

        return False, None

    def move(self, dt: float, real_dt: float | None = None) -> None:
        timer_dt = real_dt if real_dt is not None else dt
        self.timer -= timer_dt
        if self.timer <= 0:
            self.trigger_explosion()
            return

        self.apply_gravity(dt)

        new_x = self.x + self.speedX * dt
        new_y = self.y + self.speedY * dt

        # 1. Vérifier collision horizontale d'abord (pour savoir quel X utiliser)
        has_h_collision = self._check_horizontal_collision(new_x, new_y)

        # Si collision horizontale, on garde self.x pour la vérification verticale
        check_x = self.x if has_h_collision else new_x

        # 2. Collision verticale (sol/plafond) avec le bon X
        has_v_collision, snap_y = self._check_vertical_collision(new_y, check_x)
        if has_v_collision:
            if self.speedY > 0:  # chute -> sol
                self.y = snap_y

                post_vy = -abs(self.speedY) * VERTICAL_DAMP

                if abs(post_vy) < MIN_BOUNCE_SPEED:
                    if abs(self.speedX) >= HORIZONTAL_BOUNCE_MIN_SPEED:
                        self.speedY = -MIN_BOUNCE_SPEED
                    else:
                        self.speedY = 0
                        self.speedX = 0
                else:
                    self.speedY = post_vy
            else:
                # plafond
                self.y = snap_y
                self.speedY = abs(self.speedY) * VERTICAL_DAMP
        else:
            self.y = new_y

        # 3. Appliquer collision horizontale
        if has_h_collision:
            self.speedX = -self.speedX * HORIZONTAL_DAMP
        else:
            self.x = new_x

    def draw(self, screen) -> None:
        if not self.alive:
            return

        w, h = self.sprite.get_size()
        screen.blit(self.sprite, (int(self.x - w / 2), int(self.y - h / 2)))

        remaining = max(0.0, self.timer)
        text = f"{remaining:.1f}s"
        font = pygame.font.SysFont(None, 18)
        surf = font.render(text, True, (255, 255, 255))
        rect = surf.get_rect(center=(int(self.x), int(self.y - self.radius - 12)))

        pygame.draw.rect(screen, (0, 0, 0), rect.inflate(6, 4))
        screen.blit(surf, rect)
