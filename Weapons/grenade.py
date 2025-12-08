from .weapons_base import PROJECTILE
from config import GROUND_RECT_Y, MIN_BOUNCE_SPEED, HORIZONTAL_BOUNCE_MIN_SPEED, HORIZONTAL_DAMP, VERTICAL_DAMP, GRAVITY
import math


class GRENADE(PROJECTILE):
    def __init__(self, x, y, angle, force, terrain=None):
        super().__init__("grenade", x, y, angle, force, terrain=terrain)
        self.timer = 3.0
        self.explosion_radius = 60

    def _is_in_water(self) -> bool:
        """Vérifie si le projectile est dans l'eau."""
        if not self.terrain:
            return False
        block = self.terrain.block_at_pixel(int(self.x), int(self.y))
        return block and hasattr(block, 'stats') and block.stats.name == 'water'

    def _check_horizontal_collision(self, new_x: float) -> bool:
        if not self.terrain:
            return False
        check_heights = [self.y - self.radius, self.y, self.y + self.radius]
        check_x = new_x + self.radius if new_x > self.x else new_x - self.radius
        for check_y in check_heights:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True
        return False

    def _check_vertical_collision(self, new_y: float) -> bool:
        if not self.terrain:
            return new_y + self.radius >= GROUND_RECT_Y
        check_positions = [self.x - self.radius, self.x, self.x + self.radius]
        check_y = new_y + self.radius if self.speedY > 0 else new_y - self.radius
        for check_x in check_positions:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True
        return False

    def _find_ground_y(self) -> float:
        """Trouve la position Y du sol sous le projectile."""
        if not self.terrain:
            return GROUND_RECT_Y - self.radius

        # Cherche le premier bloc solide en dessous
        tile_size = self.terrain.tile_size
        start_row = int(self.y) // tile_size
        col = int(self.x) // tile_size

        for row in range(start_row, self.terrain.rows_count()):
            block = self.terrain.block_at_pixel(self.x, row * tile_size)
            if block and block.solid:
                return row * tile_size - self.radius

        return self.terrain.height - self.radius

    def move(self, dt: float, real_dt: float | None = None) -> None:
        timer_dt = real_dt if real_dt is not None else dt
        self.timer -= timer_dt
        if self.timer <= 0:
            self.trigger_explosion()
            return

        in_water = self._is_in_water()

        # === PHYSIQUE ===
        if in_water:
            # Frottements aqueux : réduction progressive de la vitesse
            # Utilisation d'une formule indépendante du framerate
            drag_coefficient = 3.0  # Plus c'est grand, plus ça freine
            drag_factor = math.exp(-drag_coefficient * dt)
            self.speedX *= drag_factor
            self.speedY *= drag_factor

            # Poussée d'Archimède (force vers le haut)
            buoyancy = 150  # Force de flottaison modérée
            self.speedY -= buoyancy * dt

            # Gravité réduite dans l'eau
            self.speedY += GRAVITY * dt * 0.4
        else:
            # Gravité normale hors de l'eau
            self.apply_gravity(dt)

        # === MOUVEMENT ===
        new_x = self.x + self.speedX * dt
        new_y = self.y + self.speedY * dt

        # === COLLISION HORIZONTALE ===
        if self._check_horizontal_collision(new_x):
            if in_water:
                # Dans l'eau : quasi pas de rebond, juste un arrêt
                self.speedX = -self.speedX * 0.1
            else:
                # Hors de l'eau : rebond normal
                self.speedX = -self.speedX * HORIZONTAL_DAMP
        else:
            self.x = new_x

        # === COLLISION VERTICALE ===
        if self._check_vertical_collision(new_y):
            # Collision avec le sol (chute)
            if self.speedY > 0:
                # Repositionner sur le sol
                self.y = self._find_ground_y()

                if in_water:
                    # Dans l'eau : absorption quasi-totale du rebond
                    if abs(self.speedY) < 20:
                        # Vitesse trop faible -> on arrête le rebond
                        self.speedY = 0
                        self.speedX *= 0.5
                    else:
                        # Rebond très faible
                        self.speedY = -abs(self.speedY) * 0.1
                        self.speedX *= 0.5
                else:
                    # Hors de l'eau : rebond classique
                    post_vy = -abs(self.speedY) * VERTICAL_DAMP

                    if abs(post_vy) < MIN_BOUNCE_SPEED:
                        if abs(self.speedX) >= HORIZONTAL_BOUNCE_MIN_SPEED:
                            # Encore assez de vitesse horizontale -> petit rebond
                            self.speedY = -MIN_BOUNCE_SPEED
                            self.speedX *= HORIZONTAL_DAMP
                        else:
                            # Plus de vitesse -> explosion
                            self.trigger_explosion()
                            return
                    else:
                        self.speedY = post_vy
                        self.speedX *= HORIZONTAL_DAMP
            else:
                # Collision avec le plafond
                if in_water:
                    self.speedY = abs(self.speedY) * 0.1
                else:
                    self.speedY = abs(self.speedY) * VERTICAL_DAMP
        else:
            self.y = new_y

        # === SÉCURITÉ : vitesses minimales ===
        # Évite les micro-mouvements infinis
        if abs(self.speedX) < 0.5:
            self.speedX = 0
        if abs(self.speedY) < 0.5 and in_water:
            self.speedY = 0

    def draw(self, screen) -> None:
        import pygame
        super().draw(screen)
        if self.alive:
            remaining = max(0.0, self.timer)
            text = f"{remaining:.1f}s"
            font = pygame.font.SysFont(None, 18)
            text_surf = font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(int(self.x), int(self.y - self.radius - 12)))
            bg_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            screen.blit(text_surf, text_rect)
