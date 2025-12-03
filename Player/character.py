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
        loaded_image = None
        try:
            loaded_image = pygame.image.load("assets/Worms/pngegg.png").convert_alpha()
        except Exception:
            loaded_image = None

        if loaded_image:
            try:
                self.image = pygame.transform.smoothscale(loaded_image, (int(width), int(height)))
            except Exception:
                try:
                    self.image = loaded_image
                except Exception:
                    self.image = pygame.Surface((width, height), pygame.SRCALPHA)
                    pygame.draw.circle(self.image, (200, 100, 50), (width // 2, height // 2), min(width, height) // 2)
        else:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 100, 50), (width // 2, height // 2), min(width, height) // 2)

        # store original and flipped versions
        self.image_right = self.image
        self.image_left = pygame.transform.flip(self.image, True, False)
        self.facing_right = True  # default facing direction

        self.player_number = player_number

        # optional terrain reference to compute per-x ground height and map width
        self.terrain = terrain

        # sprite size for ground collision (reflect actual image size)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # pixel positions
        self.pos_x = float(pos_x if pos_x is not None else PLAYER_START_X)
        # if pos_y not provided, place on terrain ground if available
        if pos_y is not None:
            self.pos_y = float(pos_y)
        else:
            if self.terrain:
                ground = self._sample_ground_height(self.pos_x)
                self.pos_y = float(ground - self.height)
            else:
                self.pos_y = float(PLAYER_START_Y)

        # conversion: how many pixels represent 1 meter in game world
        self.PIXELS_PER_METER = 40.0

        # physics (converted from config)
        self.gravity = float(GRAVITY) * self.PIXELS_PER_METER * max(0.01, float(SPEED_SCALE))
        self.jump_speed = float(jump_speed_m_s) * self.PIXELS_PER_METER * max(0.01, float(SPEED_SCALE))

        self.vy = 0.0
        self.is_jumping = False

        # gameplay
        self.pv = 100
        self.alive = True

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

    def _would_collide_horiz(self, new_x: float, max_step: float = 8.0) -> bool:
        """
        Check horizontal collision: allow small step-up (max_step pixels) but block vertical faces.
        Returns True if move is blocked, False if allowed.
        Only checks when on ground — allows free air movement.
        """
        if not self.terrain:
            return False

        # allow free horizontal movement while in air
        if self.is_jumping:
            return False

        # current ground height at player's feet
        current_ground = self._sample_ground_height(self.pos_x)
        # proposed ground height at new position
        new_ground = self._sample_ground_height(new_x)

        # height difference (positive = stepping up)
        height_diff = current_ground - new_ground

        # block if wall is too high (> max_step)
        if height_diff > max_step:
            return True

        return False

    def move_left(self, speed_pixels_per_s: float = 120.0, min_x: float = 0.0, dt: float = 1 / 60.0):
        """Move left with terrain collision checks. Allow small step-up but block vertical faces."""
        proposed = self.pos_x - speed_pixels_per_s * dt
        proposed = max(min_x, proposed)

        if not self._would_collide_horiz(proposed):
            self.pos_x = proposed
        else:
            # try incremental steps to find closest non-colliding position
            step_size = 1.0
            test_x = self.pos_x
            while test_x > proposed:
                test_x -= step_size
                if test_x < min_x:
                    test_x = min_x
                    break
                if not self._would_collide_horiz(test_x):
                    self.pos_x = test_x
                    break

        self.facing_right = False

    def move_right(self, speed_pixels_per_s: float = 120.0, max_x: Optional[float] = None, dt: float = 1 / 60.0):
        """Move right with terrain collision checks. Allow small step-up but block vertical faces."""
        if max_x is None:
            max_x = self._get_world_max_x()

        proposed = self.pos_x + speed_pixels_per_s * dt
        proposed = min(max_x, proposed)

        if not self._would_collide_horiz(proposed):
            self.pos_x = proposed
        else:
            # try incremental steps to find closest non-colliding position
            step_size = 1.0
            test_x = self.pos_x
            while test_x < proposed:
                test_x += step_size
                if test_x > max_x:
                    test_x = max_x
                    break
                if not self._would_collide_horiz(test_x):
                    self.pos_x = test_x
                    break

        self.facing_right = True

    def jump(self):
        if not self.is_jumping and self.alive:
            self.is_jumping = True
            self.vy = -abs(self.jump_speed)

    def update(self, dt: float):
        if not self.alive:
            return

        # apply gravity and vertical motion
        self.vy += self.gravity * dt
        self.pos_y += self.vy * dt

        # ground collision / landing: use sampled terrain height at current bounds if available
        if self.terrain:
            ground_top = float(self._sample_ground_height(self.pos_x) - self.height)
        else:
            ground_top = float(GROUND_RECT_Y) - float(self.height)

        # only check ground collision if moving downward (vy >= 0)
        if self.pos_y >= ground_top and self.vy >= 0:
            self.pos_y = ground_top
            self.vy = 0.0
            self.is_jumping = False

    def kill(self):
        self.pv = 0
        self.alive = False

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        img = self.image_right if self.facing_right else self.image_left
        surface.blit(img, (int(self.pos_x), int(self.pos_y)))
