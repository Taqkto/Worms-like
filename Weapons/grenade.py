# Weapons/grenade.py
from .weapons_base import PROJECTILE
from config import (
    GROUND_RECT_Y,
    MIN_BOUNCE_SPEED,
    HORIZONTAL_BOUNCE_MIN_SPEED,
    HORIZONTAL_DAMP,
    VERTICAL_DAMP,
)
import pygame


class GRENADE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None):
        super().__init__("grenade", x, y, angle, force, terrain=terrain)
        self.timer = 3.0
        self.explosion_radius = 60

        # Sprite grenade (14×14)
        self.sprite = pygame.image.load("Assets/projectiles/grenade.png").convert_alpha()
        self.sprite = pygame.transform.scale(self.sprite, (14, 14))

    # -------------------------------------------------------
    # COLLISIONS (basées sur grenade2.py — version stable)
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
    # PHYSIQUE DU GRENADE — version simple + stable
    # -------------------------------------------------------

    def move(self, dt: float, real_dt: float | None = None) -> None:
        # Timer (intégré dans les deux versions)
        timer_dt = real_dt if real_dt is not None else dt
        self.timer -= timer_dt
        if self.timer <= 0:
            self.trigger_explosion()
            return

        # Gravité
        self.apply_gravity(dt)

        # Nouveau déplacement
        new_x = self.x + self.speedX * dt
        new_y = self.y + self.speedY * dt

        # ----- Collision mur -----
        if self._check_horizontal_collision(new_x):
            self.speedX = -self.speedX * HORIZONTAL_DAMP
        else:
            self.x = new_x

        # ----- Collision sol / plafond -----
        if self._check_vertical_collision(new_y):
            if self.speedY > 0:  # chute -> sol
                if self.terrain:
                    ground_top = self.terrain.height_at(self.x) - self.radius
                else:
                    ground_top = GROUND_RECT_Y - self.radius
                self.y = ground_top

                # Rebond vertical
                post_vy = -abs(self.speedY) * VERTICAL_DAMP

                if abs(post_vy) < MIN_BOUNCE_SPEED:
                    if abs(self.speedX) >= HORIZONTAL_BOUNCE_MIN_SPEED:
                        self.speedY = -MIN_BOUNCE_SPEED
                        self.speedX *= HORIZONTAL_DAMP
                    else:
                        self.trigger_explosion()
                else:
                    self.speedY = post_vy
                    self.speedX *= HORIZONTAL_DAMP
            else:
                # plafond
                self.speedY = abs(self.speedY) * VERTICAL_DAMP
        else:
            self.y = new_y

    # -------------------------------------------------------
    # DESSIN AVEC SPRITE + TIMER
    # -------------------------------------------------------

    def draw(self, screen) -> None:
        if not self.alive:
            return

        w, h = self.sprite.get_size()
        screen.blit(self.sprite, (int(self.x - w / 2), int(self.y - h / 2)))

        # ----- Timer -----
        remaining = max(0.0, self.timer)
        text = f"{remaining:.1f}s"
        font = pygame.font.SysFont(None, 18)
        surf = font.render(text, True, (255, 255, 255))
        rect = surf.get_rect(center=(int(self.x), int(self.y - self.radius - 12)))

        pygame.draw.rect(screen, (0, 0, 0), rect.inflate(6, 4))
        screen.blit(surf, rect)
