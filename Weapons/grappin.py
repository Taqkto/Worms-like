# Weapons/grappin.py
import pygame
import math
from config import GRAVITY


class Grappin:
    """
    Grappin : arme de mobilité permettant de se balancer et atteindre de nouvelles zones.

    Fonctionnement :
    1. Le joueur tire le grappin vers un point
    2. Si le grappin touche un bloc solide, il s'accroche
    3. Le joueur se balance comme un pendule
    4. Le joueur peut se relâcher pour être propulsé
    """

    def __init__(self, character, terrain=None):
        self.character = character
        self.terrain = terrain

        # États du grappin
        self.state = "idle"  # idle, flying, attached, swinging

        # Position du grappin (pointe)
        self.hook_x = 0.0
        self.hook_y = 0.0

        # Vitesse du grappin en vol
        self.hook_vx = 0.0
        self.hook_vy = 0.0

        # Point d'ancrage (où le grappin s'est accroché)
        self.anchor_x = 0.0
        self.anchor_y = 0.0

        # Paramètres du grappin
        self.hook_speed = 800.0  # Vitesse de tir du grappin
        self.max_range = 400.0   # Portée maximale
        self.rope_length = 0.0   # Longueur de la corde une fois accroché
        self.min_rope_length = 50.0  # Longueur minimale de la corde

        # Physique du balancement (pendule)
        self.swing_angle = 0.0      # Angle actuel du pendule
        self.swing_velocity = 0.0   # Vitesse angulaire
        self.swing_damping = 0.995  # Amortissement léger

        # Contrôle du joueur pendant le swing
        self.swing_force = 5.0  # Force que le joueur peut appliquer pour se balancer

        # Visuel
        self.rope_color = (139, 90, 43)  # Couleur corde (marron)
        self.hook_color = (100, 100, 100)  # Couleur grappin (gris)
        self.hook_radius = 5

        # Pour le calcul de la distance parcourue
        self.start_x = 0.0
        self.start_y = 0.0

    def fire(self, angle_deg: float):
        """Tire le grappin dans la direction donnée."""
        if self.state != "idle":
            return

        self.state = "flying"

        # Position de départ (centre du personnage)
        self.start_x = self.character.pos_x + self.character.width / 2
        self.start_y = self.character.pos_y + self.character.height / 2

        self.hook_x = self.start_x
        self.hook_y = self.start_y

        # Convertir l'angle en radians et calculer la vitesse
        angle_rad = math.radians(angle_deg)
        self.hook_vx = self.hook_speed * math.cos(angle_rad)
        self.hook_vy = -self.hook_speed * math.sin(angle_rad)  # Négatif car Y vers le bas

    def update(self, dt: float, keys_pressed=None):
        """Met à jour l'état du grappin."""
        if self.state == "idle":
            return

        elif self.state == "flying":
            self._update_flying(dt)

        elif self.state == "attached":
            self._start_swinging()

        elif self.state == "swinging":
            self._update_swinging(dt, keys_pressed)

    def _update_flying(self, dt: float):
        """Met à jour le grappin en vol."""
        # Appliquer une légère gravité au grappin
        self.hook_vy += GRAVITY * 0.3 * dt

        # Déplacer le grappin
        new_x = self.hook_x + self.hook_vx * dt
        new_y = self.hook_y + self.hook_vy * dt

        # Vérifier la collision avec le terrain
        if self._check_hook_collision(new_x, new_y):
            self._attach_hook()
            return

        self.hook_x = new_x
        self.hook_y = new_y

        # Vérifier si le grappin a dépassé sa portée maximale
        dist = math.sqrt((self.hook_x - self.start_x)**2 + (self.hook_y - self.start_y)**2)
        if dist > self.max_range:
            self.cancel()

    def _check_hook_collision(self, x: float, y: float) -> bool:
        """Vérifie si le grappin touche un bloc solide."""
        if not self.terrain:
            return False

        block = self.terrain.block_at_pixel(x, y)
        return block and block.solid

    def _attach_hook(self):
        """Accroche le grappin au point actuel."""
        self.state = "attached"
        self.anchor_x = self.hook_x
        self.anchor_y = self.hook_y

        # Calculer la longueur de corde initiale
        char_x = self.character.pos_x + self.character.width / 2
        char_y = self.character.pos_y + self.character.height / 2

        self.rope_length = math.sqrt(
            (self.anchor_x - char_x)**2 +
            (self.anchor_y - char_y)**2
        )
        self.rope_length = max(self.rope_length, self.min_rope_length)

    def _start_swinging(self):
        """Initialise le balancement."""
        self.state = "swinging"

        # Calculer l'angle initial du pendule
        char_x = self.character.pos_x + self.character.width / 2
        char_y = self.character.pos_y + self.character.height / 2

        dx = char_x - self.anchor_x
        dy = char_y - self.anchor_y

        # Angle par rapport à la verticale (0 = en dessous du point d'ancrage)
        self.swing_angle = math.atan2(dx, dy)

        # Vitesse angulaire initiale basée sur le mouvement du personnage
        # Convertir la vitesse linéaire en vitesse angulaire
        if hasattr(self.character, 'vx'):
            self.swing_velocity = self.character.vx / self.rope_length * 0.5
        else:
            self.swing_velocity = 0.0

    def _update_swinging(self, dt: float, keys_pressed=None):
        """Met à jour la physique du balancement (pendule)."""
        # Accélération angulaire due à la gravité
        # Pour un pendule : α = -(g/L) * sin(θ)
        g = GRAVITY * 40  # Ajuster pour le feeling
        angular_accel = -(g / self.rope_length) * math.sin(self.swing_angle)

        # Contrôle du joueur pour se balancer
        if keys_pressed:
            if keys_pressed.get(pygame.K_a) or keys_pressed.get(pygame.K_LEFT):
                angular_accel -= self.swing_force
            if keys_pressed.get(pygame.K_d) or keys_pressed.get(pygame.K_RIGHT):
                angular_accel += self.swing_force

            # Raccourcir/allonger la corde
            if keys_pressed.get(pygame.K_w) or keys_pressed.get(pygame.K_UP):
                self.rope_length = max(self.min_rope_length, self.rope_length - 100 * dt)
            if keys_pressed.get(pygame.K_s) or keys_pressed.get(pygame.K_DOWN):
                self.rope_length = min(self.max_range, self.rope_length + 100 * dt)

        # Intégrer la vitesse angulaire
        self.swing_velocity += angular_accel * dt
        self.swing_velocity *= self.swing_damping  # Amortissement

        # Limiter la vitesse angulaire
        max_angular_velocity = 8.0
        self.swing_velocity = max(-max_angular_velocity, min(max_angular_velocity, self.swing_velocity))

        # Intégrer l'angle
        new_angle = self.swing_angle + self.swing_velocity * dt

        # LIMITE : Le joueur ne peut pas dépasser le point d'ancrage en Y
        # Angle = 0 signifie directement en dessous, angle = ±π/2 signifie au niveau horizontal
        # On limite à un peu moins de π/2 (environ 85 degrés) pour ne jamais dépasser
        max_swing_angle = math.pi / 2 - 0.1  # ~85 degrés

        if new_angle > max_swing_angle:
            new_angle = max_swing_angle
            self.swing_velocity = -abs(self.swing_velocity) * 0.3  # Rebondir doucement
        elif new_angle < -max_swing_angle:
            new_angle = -max_swing_angle
            self.swing_velocity = abs(self.swing_velocity) * 0.3  # Rebondir doucement

        self.swing_angle = new_angle

        # Calculer la nouvelle position du personnage
        new_char_x = self.anchor_x + self.rope_length * math.sin(self.swing_angle)
        new_char_y = self.anchor_y + self.rope_length * math.cos(self.swing_angle)

        # Vérifier collision avec le terrain pour le personnage
        test_x = new_char_x - self.character.width / 2
        test_y = new_char_y - self.character.height / 2

        if not self._character_would_collide(test_x, test_y):
            self.character.pos_x = test_x
            self.character.pos_y = test_y
        else:
            # Collision : réduire la vitesse
            self.swing_velocity *= 0.5

        # Mettre à jour l'état du personnage
        self.character.on_ground = False
        self.character.is_jumping = True

    def _character_would_collide(self, x: float, y: float) -> bool:
        """Vérifie si le personnage collerait à cette position."""
        if not self.terrain:
            return False

        # Vérifier plusieurs points du personnage
        check_points = [
            (x + 5, y + 5),
            (x + self.character.width - 5, y + 5),
            (x + 5, y + self.character.height - 5),
            (x + self.character.width - 5, y + self.character.height - 5),
            (x + self.character.width / 2, y + self.character.height / 2),
        ]

        for px, py in check_points:
            block = self.terrain.block_at_pixel(px, py)
            if block and block.solid:
                return True
        return False

    def release(self):
        """Relâche le grappin et propulse le personnage."""
        if self.state != "swinging":
            self.cancel()
            return

        # Calculer la vitesse tangentielle = ω * r
        tangent_speed = self.swing_velocity * self.rope_length

        # Direction tangentielle (perpendiculaire à la corde)
        # La corde fait un angle swing_angle par rapport à la verticale
        # La tangente est perpendiculaire à la corde
        # Si swing_angle > 0 (à droite) et swing_velocity > 0, on va vers la droite et vers le haut

        # Vecteur de la corde : (sin(θ), cos(θ)) pointe du anchor vers le joueur
        # Vecteur tangent (perpendiculaire, dans le sens du mouvement) : (cos(θ), -sin(θ)) * signe(velocity)

        # Vitesse tangentielle en X et Y
        release_vx = tangent_speed * math.cos(self.swing_angle)
        release_vy = -tangent_speed * math.sin(self.swing_angle)

        # Facteur de projection (plus élevé = plus de propulsion)
        projection_factor = 0.5

        # Appliquer la vitesse au personnage
        self.character.vy = release_vy * projection_factor

        # Ajouter un boost vertical si on lâche en montant
        if release_vy < 0:  # Monte
            self.character.vy *= 1.2  # Bonus de 20% vers le haut

        # Stocker la vitesse horizontale
        # Le personnage n'a pas de vx par défaut, on doit gérer ça différemment
        # On va stocker la vitesse pour que le main.py puisse l'utiliser
        self.character._release_vx = release_vx * projection_factor
        self.character._has_release_momentum = True

        # Le personnage n'est plus au sol
        self.character.on_ground = False
        self.character.is_jumping = True

        self.cancel()

    def cancel(self):
        """Annule/réinitialise le grappin."""
        self.state = "idle"
        self.hook_x = 0
        self.hook_y = 0
        self.hook_vx = 0
        self.hook_vy = 0
        self.anchor_x = 0
        self.anchor_y = 0
        self.swing_angle = 0
        self.swing_velocity = 0

    def draw(self, screen: pygame.Surface):
        """Dessine le grappin et la corde."""
        if self.state == "idle":
            return

        # Position du personnage (centre)
        char_x = self.character.pos_x + self.character.width / 2
        char_y = self.character.pos_y + self.character.height / 2

        if self.state == "flying":
            # Dessiner la corde vers le grappin en vol
            pygame.draw.line(
                screen,
                self.rope_color,
                (int(char_x), int(char_y)),
                (int(self.hook_x), int(self.hook_y)),
                2
            )
            # Dessiner le grappin
            pygame.draw.circle(
                screen,
                self.hook_color,
                (int(self.hook_x), int(self.hook_y)),
                self.hook_radius
            )

        elif self.state in ("attached", "swinging"):
            # Dessiner la corde vers le point d'ancrage
            pygame.draw.line(
                screen,
                self.rope_color,
                (int(char_x), int(char_y)),
                (int(self.anchor_x), int(self.anchor_y)),
                3
            )
            # Dessiner le point d'ancrage
            pygame.draw.circle(
                screen,
                self.hook_color,
                (int(self.anchor_x), int(self.anchor_y)),
                self.hook_radius + 2
            )
            # Petit indicateur visuel
            pygame.draw.circle(
                screen,
                (255, 200, 0),
                (int(self.anchor_x), int(self.anchor_y)),
                self.hook_radius - 1
            )

    def is_active(self) -> bool:
        """Retourne True si le grappin est en cours d'utilisation."""
        return self.state != "idle"

    def is_swinging(self) -> bool:
        """Retourne True si le joueur est en train de se balancer."""
        return self.state == "swinging"

