# python
from .weapons_base import PROJECTILE
from Config import GRAVITY, GROUND_LEVEL


class GRENADE(PROJECTILE):
    def __init__(self, x, y, angle, force):
        super().__init__("grenade", x, y, angle, force)
        self.timer = 3.0  # seconds before explosion

    def move(self, dt):
        # tick du timer
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False
            return

        # gravité
        self.apply_gravity(dt)

        # mise à jour position
        self.update_position(dt)

        # rebond au sol
        if self.y >= GROUND_LEVEL:
            self.y = GROUND_LEVEL
            self.speedY *= -0.4  # rebond amorti
            self.speedX *= 0.7  # perte vitesse horizontale

            # si vitesse trop faible -> explosion
            if abs(self.speedY) < 20:
                self.alive = False

    def draw(self, screen):
        import pygame
        # draw base projectile
        super().draw(screen)

        # draw timer above grenade while it's alive (before explosion)
        if self.alive:
            remaining = max(0.0, self.timer)
            text = f"{remaining:.1f}s"
            font = pygame.font.SysFont(None, 18)
            text_surf = font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(int(self.x), int(self.y - self.radius - 12)))
            bg_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            screen.blit(text_surf, text_rect)
