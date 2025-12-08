from typing import Optional
import pygame

from config import (
    GRAVITY,
    SPEED_SCALE,
    PLAYER_START_X,
    PLAYER_START_Y,
    GROUND_RECT_Y,
    SCREEN_WIDTH,
)


class Character:
    def __init__(
            self,
            player_number: int,
            pos_x: Optional[int] = None,
            pos_y: Optional[int] = None,
            jump_speed_m_s: float = 6.0,
            width: int = 32,
            height: int = 32,
            terrain: Optional[object] = None,
    ):

        self.name = None
        self.player_number = player_number
        self.terrain = terrain

        # -----------------------------------
        # SPRITES : idle, walk, jump
        # -----------------------------------
        self.sprite_idle = pygame.image.load("Assets/characters/worm_idle.png").convert_alpha()
        self.sprite_walk = pygame.image.load("Assets/characters/worm_walk.png").convert_alpha()
        self.sprite_jump = pygame.image.load("Assets/characters/worm_jump.png").convert_alpha()

        # weapon (static, no rotation)
        self.weapon_sprite = pygame.image.load("Assets/weapons/rocket_launcher.png").convert_alpha()

        # Resize sprites
        self.sprite_idle = pygame.transform.scale(self.sprite_idle, (width, height))
        self.sprite_walk = pygame.transform.scale(self.sprite_walk, (width, height))
        self.sprite_jump = pygame.transform.scale(self.sprite_jump, (width, height))

        self.weapon_sprite = pygame.transform.scale(self.weapon_sprite, (28, 14))

        # Grenade tenue en main
        self.held_grenade_sprite = pygame.image.load("Assets/projectiles/grenade.png").convert_alpha()
        self.held_grenade_sprite = pygame.transform.scale(self.held_grenade_sprite, (14, 14))

        # L’arme actuellement affichée (sera changée par main.py)
        self.current_hand_item = "rocket"  # "rocket" ou "grenade"


        # Movement states
        self.is_moving = False
        self.on_ground = True
        self.facing_left = False  # False = regarde droite si on flip, True = gauche

        self.width = width
        self.height = height

        # Position init
        self.pos_x = float(pos_x if pos_x is not None else PLAYER_START_X)

        if pos_y is not None:
            self.pos_y = float(pos_y)
        else:
            if self.terrain:
                ground = self._sample_ground_height(self.pos_x)
                self.pos_y = float(ground - self.height)
            else:
                self.pos_y = float(PLAYER_START_Y)

        # Physics
        self.PIXELS_PER_METER = 40.0
        self.gravity = float(GRAVITY) * self.PIXELS_PER_METER * max(0.01, float(SPEED_SCALE))
        self.jump_speed = float(jump_speed_m_s) * self.PIXELS_PER_METER * max(0.01, float(SPEED_SCALE))

        self.vy = 0.0
        self.is_jumping = False

        # Momentum horizontal (pour le grappin)
        self._release_vx = 0.0
        self._has_release_momentum = False

        # Gameplay
        self.pv = 100
        self.alive = True

    # -------------------------------------------------------------------
    # INTERNAL COLLISION HELPERS
    # -------------------------------------------------------------------

    def _get_world_max_x(self) -> float:
        if self.terrain and hasattr(self.terrain, "width"):
            return max(0.0, float(self.terrain.width) - self.width)
        return max(0.0, float(SCREEN_WIDTH) - self.width)

    def _sample_ground_height(self, x: float) -> float:
        """
        Sample ground height under the sprite across left, center and right columns.
        Return the smallest y (i.e. the highest ground) so the player cannot sink into cliffs.
        """
        if not self.terrain:
            return float(GROUND_RECT_Y)
        samples = [x, x + self.width / 2.0, x + max(0.0, self.width - 1)]
        heights = []
        for sx in samples:
            try:
                heights.append(float(self.terrain.height_at(sx)))
            except Exception:
                heights.append(float(GROUND_RECT_Y))
        return min(heights)

    def _would_collide_horiz(self, new_x: float) -> bool:
        """
        Check if moving to new_x would collide with solid blocks.
        Returns True if blocked, False if allowed.
        """
        if not self.terrain:
            return False

        check_heights = [
            self.pos_y + 2,                    # near top
            self.pos_y + self.height / 2,      # middle
            self.pos_y + self.height - 2,      # near bottom
        ]

        if new_x > self.pos_x:
            check_x = new_x + self.width      # moving right: check right edge
        else:
            check_x = new_x                   # moving left: check left edge

        for check_y in check_heights:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    def _find_ground_below(self, x: float, start_y: float) -> float:
        """Find the Y position of the ground below the given point."""
        if not self.terrain:
            return float(GROUND_RECT_Y)

        samples = [x, x + self.width / 2, x + self.width - 1]
        min_ground = float(self.terrain.height)

        for sx in samples:
            for test_y in range(int(start_y), int(self.terrain.height)):
                block = self.terrain.block_at_pixel(sx, test_y)
                if block and block.solid:
                    min_ground = min(min_ground, float(test_y))
                    break

        return min_ground

    # -------------------------------------------------------------------
    # MOVEMENT
    # -------------------------------------------------------------------

    def move_left(self, speed_pixels_per_s: float = 120.0, min_x: float = 0.0, dt: float = 1 / 60.0):
        """Move left with terrain collision checks."""
        step = speed_pixels_per_s * dt
        proposed = max(min_x, self.pos_x - step)

        if not self._would_collide_horiz(proposed):
            self.pos_x = proposed
        else:
            for _ in range(int(step)):
                test_x = self.pos_x - 1
                if test_x < min_x:
                    break
                if self._would_collide_horiz(test_x):
                    break
                self.pos_x = test_x

        self.facing_left = True
        self.is_moving = True

    def move_right(self, speed_pixels_per_s: float = 120.0, max_x: Optional[float] = None, dt: float = 1 / 60.0):
        """Move right with terrain collision checks."""
        if max_x is None:
            max_x = self._get_world_max_x()

        step = speed_pixels_per_s * dt
        proposed = min(max_x, self.pos_x + step)

        if not self._would_collide_horiz(proposed):
            self.pos_x = proposed
        else:
            for _ in range(int(step)):
                test_x = self.pos_x + 1
                if test_x > max_x:
                    break
                if self._would_collide_horiz(test_x):
                    break
                self.pos_x = test_x

        self.facing_left = False
        self.is_moving = True

    # -------------------------------------------------------------------
    # UPDATE (PHYSICS)
    # -------------------------------------------------------------------

    def update(self, dt: float):
        if not self.alive:
            return

        # Reset mouvement pour la frame (sera remis à True si move_left/right est appelé dans main)
        self.is_moving = False

        # Check water collision
        if self.terrain:
            check_points = [
                (self.pos_x, self.pos_y + self.height),
                (self.pos_x + self.width, self.pos_y + self.height),
                (self.pos_x + self.width / 2, self.pos_y + self.height),
            ]

            for px, py in check_points:
                block = self.terrain.block_at_pixel(px, py)
                if block and hasattr(block, 'stats') and block.stats.name == "water":
                    self.kill()
                    # Informer l'App pour passer le tour si besoin (comme dans la version 1)
                    if hasattr(self, "_app_ref") and self._app_ref:
                        self._app_ref._pending_turn_switch = True
                    return

        # Appliquer le momentum horizontal (propulsion du grappin)
        if self._has_release_momentum and abs(self._release_vx) > 0.1:
            # Déplacer horizontalement
            new_x = self.pos_x + self._release_vx * dt

            # Vérifier collision horizontale
            if not self._would_collide_horiz(new_x):
                self.pos_x = new_x
                # Mettre à jour la direction du regard
                if self._release_vx > 0:
                    self.facing_left = False
                elif self._release_vx < 0:
                    self.facing_left = True
            else:
                # Collision : arrêter le momentum
                self._release_vx = 0

            # Friction aérienne pour ralentir progressivement
            self._release_vx *= 0.98

            # Arrêter le momentum quand on touche le sol
            if self.on_ground:
                self._release_vx *= 0.8  # Friction au sol plus forte
                if abs(self._release_vx) < 5:
                    self._release_vx = 0
                    self._has_release_momentum = False

        # Gravity
        self.vy += self.gravity * dt
        new_y = self.pos_y + self.vy * dt

        # Falling
        if self.vy > 0:
            ground_y = self._find_ground_below(self.pos_x, self.pos_y + self.height)
            feet_y = new_y + self.height

            if feet_y >= ground_y:
                self.pos_y = ground_y - self.height
                self.vy = 0.0
                self.is_jumping = False
                self.on_ground = True
            else:
                self.pos_y = new_y
                self.on_ground = False

        # Rising
        elif self.vy < 0:
            blocked = False
            head_y = new_y
            for check_x in [self.pos_x + 4, self.pos_x + self.width / 2, self.pos_x + self.width - 4]:
                block = self.terrain.block_at_pixel(check_x, head_y) if self.terrain else None
                if block and block.solid:
                    blocked = True
                    break

            if blocked:
                self.vy = 0
            else:
                self.pos_y = new_y

            self.on_ground = False

        else:
            # vy == 0 : on ne change pas on_ground, on garde l'état précédent
            self.pos_y = new_y

    # -------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------

    def jump(self):
        """Make the character jump if on the ground."""
        if not self.alive:
            return
        if not self.is_jumping and self.on_ground:
            self.vy = -self.jump_speed
            self.is_jumping = True
            self.on_ground = False

    # -------------------------------------------------------------------
    # DRAW
    # -------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return

        # Choix du sprite
        if not self.on_ground:
            sprite = self.sprite_jump
        elif self.is_moving:
            sprite = self.sprite_walk
        else:
            sprite = self.sprite_idle

        # Flip horizontal : tes sprites de base regardent à gauche
        # donc on les flip quand il regarde à droite
        if not self.facing_left:
            sprite = pygame.transform.flip(sprite, True, False)

        surface.blit(sprite, (int(self.pos_x), int(self.pos_y)))

        # ------- Arme tenue en main (selon l'arme sélectionnée) ------
        if self.current_hand_item == "rocket":
            weapon = self.weapon_sprite
        else:
            weapon = self.held_grenade_sprite

        # flip horizontal si besoin
        if not self.facing_left:
            weapon = pygame.transform.flip(weapon, True, False)

        # Position de l’arme
        wx = self.pos_x + (-10 if self.facing_left else self.width - 5)
        wy = self.pos_y + 6

        # On affiche l’arme uniquement si elle n'a pas encore été jetée
        surface.blit(weapon, (int(wx), int(wy)))


    # -------------------------------------------------------------------
    # MISC
    # -------------------------------------------------------------------

    def rename(self, new_name: str):
        self.name = new_name

    def is_alive(self) -> bool:
        return self.alive

    def damage(self, amount: int):
        self.pv -= amount
        if self.pv <= 0:
            self.kill()

    def kill(self):
        self.pv = 0
        self.alive = False
