from .weapons_base import PROJECTILE
from config import GROUND_LEVEL, GROUND_RECT_Y, MIN_BOUNCE_SPEED, HORIZONTAL_BOUNCE_MIN_SPEED, HORIZONTAL_DAMP, VERTICAL_DAMP



class GRENADE(PROJECTILE):
    def __init__(self, x, y, angle, force):
        super().__init__("grenade", x, y, angle, force)
        self.timer = 3.0  # seconds before explosion

    def move(self, dt, real_dt=None):
        # use unscaled dt for the timer if provided so explosion timing stays real-time
        timer_dt = real_dt if real_dt is not None else dt
        self.timer -= timer_dt
        if self.timer <= 0:
            self.alive = False
            return

        # use scaled dt for movement so projectile traverses faster while preserving path
        self.apply_gravity(dt)
        self.update_position(dt)

        # bounce on visible ground top
        ground_top = GROUND_RECT_Y - self.radius
        if self.y >= ground_top:
            self.y = ground_top

            # compute post-impact candidate vertical speed (inverted & damped)
            post_vy = -abs(self.speedY) * VERTICAL_DAMP

            # If vertical component after inversion is too small:
            if abs(post_vy) < MIN_BOUNCE_SPEED:
                # if horizontal speed is large enough, force a small bounce upward
                if abs(self.speedX) >= HORIZONTAL_BOUNCE_MIN_SPEED:
                    self.speedY = -MIN_BOUNCE_SPEED
                    self.speedX *= HORIZONTAL_DAMP
                    # remain alive to continue sliding/bouncing
                else:
                    # otherwise explode / stop
                    self.alive = False
            else:
                # normal damped bounce
                self.speedY = post_vy
                self.speedX *= HORIZONTAL_DAMP

    def draw(self, screen):
        import pygame
        super().draw(screen)

        # draw timer above grenade while it's alive
        if self.alive:
            remaining = max(0.0, self.timer)
            text = f"{remaining:.1f}s"
            font = pygame.font.SysFont(None, 18)
            text_surf = font.render(text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(int(self.x), int(self.y - self.radius - 12)))
            bg_rect = text_rect.inflate(6, 4)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            screen.blit(text_surf, text_rect)