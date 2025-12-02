# python
# File: `Player/character.py`
import pygame
from typing import Optional

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
        jump_speed_m_s: float = 6.0,  # default jump speed in meters/sec
        width: int = 32,
        height: int = 32,
    ):
        # try load asset and scale it to requested size; fallback to a simple circle surface
        loaded_image = None
        try:
            loaded_image = pygame.image.load("assets/Worms/pngegg.png").convert_alpha()
        except Exception:
            loaded_image = None

        if loaded_image:
            # scale loaded image to requested sprite size
            try:
                self.image = pygame.transform.smoothscale(loaded_image, (int(width), int(height)))
            except Exception:
                # if scaling fails, fall back to original loaded image or fallback surface
                try:
                    self.image = loaded_image
                except Exception:
                    self.image = pygame.Surface((width, height), pygame.SRCALPHA)
                    pygame.draw.circle(self.image, (200, 100, 50), (width // 2, height // 2), min(width, height) // 2)
        else:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 100, 50), (width // 2, height // 2), min(width, height) // 2)

        self.player_number = player_number

        # pixel positions
        self.pos_x = float(pos_x if pos_x is not None else PLAYER_START_X)
        self.pos_y = float(pos_y if pos_y is not None else PLAYER_START_Y)

        # conversion: how many pixels represent 1 meter in game world
        self.PIXELS_PER_METER = 40.0

        # physics (converted from config)
        # gravity in pixels/sec^2 (config GRAVITY is m/s^2)
        self.gravity = float(GRAVITY) * self.PIXELS_PER_METER * max(0.01, float(SPEED_SCALE))
        # jump speed: input in m/s, converted to pixels/sec
        self.jump_speed = float(jump_speed_m_s) * self.PIXELS_PER_METER * max(0.01, float(SPEED_SCALE))

        self.vy = 0.0
        self.is_jumping = False

        # gameplay
        self.pv = 100
        self.alive = True

        # sprite size for ground collision (reflect actual image size)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def move_left(self, speed_pixels_per_s: float = 120.0, min_x: float = 0.0, dt: float = 1 / 60.0):
        self.pos_x -= speed_pixels_per_s * dt
        self.pos_x = max(min_x, self.pos_x)

    def move_right(self, speed_pixels_per_s: float = 120.0, max_x: Optional[float] = None, dt: float = 1 / 60.0):
        self.pos_x += speed_pixels_per_s * dt
        if max_x is None:
            max_x = max(0.0, SCREEN_WIDTH - self.width)
        self.pos_x = min(max_x, self.pos_x)

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

        # ground collision / landing (use current sprite height)
        ground_y = float(GROUND_RECT_Y) - float(self.height)
        if self.pos_y >= ground_y:
            self.pos_y = ground_y
            self.vy = 0.0
            self.is_jumping = False

    def kill(self):
        self.pv = 0
        self.alive = False

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        surface.blit(self.image, (int(self.pos_x), int(self.pos_y)))
