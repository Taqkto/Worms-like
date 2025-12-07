import pygame


class Explosion:
    def __init__(self, x: float, y: float, radius: float = 60):
        self.x = x
        self.y = y
        self.max_radius = radius
        self.current_radius = 5.0  # Commencer avec un rayon visible
        self.duration = 0.5
        self.elapsed = 0.0
        self.alive = True

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.alive = False
            return
        self.current_radius = self.max_radius * (self.elapsed / self.duration)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.alive:
            return

        rad = max(3, int(self.current_radius))

        # Cercle extérieur rouge
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), rad)
        # Cercle moyen orange
        pygame.draw.circle(screen, (255, 128, 0), (int(self.x), int(self.y)), max(2, rad * 2 // 3))
        # Cercle intérieur jaune
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), max(1, rad // 3))