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

    def _would_collide_horiz(self, new_x: float) -> bool:
        """
        Check if moving to new_x would collide with solid blocks.
        Returns True if blocked, False if allowed.
        """
        if not self.terrain:
            return False

        # Check multiple points along the character's height
        check_heights = [
            self.pos_y + 2,  # near top
            self.pos_y + self.height / 2,  # middle
            self.pos_y + self.height - 2,  # near bottom (but not feet)
        ]

        # Determine which side to check based on direction
        if new_x > self.pos_x:
            # Moving right, check right edge
            check_x = new_x + self.width
        else:
            # Moving left, check left edge
            check_x = new_x

        for check_y in check_heights:
            block = self.terrain.block_at_pixel(check_x, check_y)
            if block and block.solid:
                return True

        return False

    def _find_ground_below(self, x: float, start_y: float) -> float:
        """Find the Y position of the ground below the given point."""
        if not self.terrain:
            return float(GROUND_RECT_Y)

        # Sample across the character's width
        samples = [x, x + self.width / 2, x + self.width - 1]
        min_ground = float(self.terrain.height)

        for sx in samples:
            # Scan downward from current position
            for test_y in range(int(start_y), int(self.terrain.height)):
                block = self.terrain.block_at_pixel(sx, test_y)
                if block and block.solid:
                    min_ground = min(min_ground, float(test_y))
                    break

        return min_ground

    def move_left(self, speed_pixels_per_s: float = 120.0, min_x: float = 0.0, dt: float = 1 / 60.0):
        """Move left with terrain collision checks."""
        step = speed_pixels_per_s * dt
        proposed = max(min_x, self.pos_x - step)

        # Check collision at proposed position
        if not self._would_collide_horiz(proposed):
            self.pos_x = proposed
        else:
            # Try smaller steps to get as close as possible
            for i in range(int(step)):
                test_x = self.pos_x - 1
                if test_x < min_x:
                    break
                if self._would_collide_horiz(test_x):
                    break
                self.pos_x = test_x

        self.facing_right = False

    def move_right(self, speed_pixels_per_s: float = 120.0, max_x: Optional[float] = None, dt: float = 1 / 60.0):
        """Move right with terrain collision checks."""
        if max_x is None:
            max_x = self._get_world_max_x()

        step = speed_pixels_per_s * dt
        proposed = min(max_x, self.pos_x + step)

        # Check collision at proposed position
        if not self._would_collide_horiz(proposed):
            self.pos_x = proposed
        else:
            # Try smaller steps to get as close as possible
            for i in range(int(step)):
                test_x = self.pos_x + 1
                if test_x > max_x:
                    break
                if self._would_collide_horiz(test_x):
                    break
                self.pos_x = test_x

        self.facing_right = True

    def update(self, dt: float):
        if not self.alive:
            return

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
                    if hasattr(self, '_app_ref') and self._app_ref:
                        self._app_ref._pending_turn_switch = True
                    return

        # Apply gravity
        self.vy += self.gravity * dt
        new_y = self.pos_y + self.vy * dt

        # Vertical collision - check if falling into solid block
        if self.vy > 0:  # Falling
            ground_y = self._find_ground_below(self.pos_x, self.pos_y + self.height)
            feet_y = new_y + self.height

            if feet_y >= ground_y:
                self.pos_y = ground_y - self.height
                self.vy = 0.0
                self.is_jumping = False
            else:
                self.pos_y = new_y
        elif self.vy < 0:  # Rising
            # Check ceiling collision
            head_y = new_y
            blocked = False
            for check_x in [self.pos_x + 4, self.pos_x + self.width / 2, self.pos_x + self.width - 4]:
                block = self.terrain.block_at_pixel(check_x, head_y) if self.terrain else None
                if block and block.solid:
                    blocked = True
                    break

            if blocked:
                self.vy = 0
            else:
                self.pos_y = new_y
        else:
            self.pos_y = new_y

    def jump(self):
        """Make the character jump if on the ground."""
        if not self.alive:
            return
        if not self.is_jumping:
            self.vy = -self.jump_speed
            self.is_jumping = True

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        img = self.image_right if self.facing_right else self.image_left
        surface.blit(img, (int(self.pos_x), int(self.pos_y)))

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

