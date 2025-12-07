from pathlib import Path
import pygame
from typing import List


class StartMenu:

    def __init__(self, width: int, height: int, font: pygame.font.Font, player_count: int = 2):
        self.width = width
        self.height = height
        self.font = font
        self.player_count = player_count

        self.stage = 0
        self.num_chars = 1
        self.max_chars = 4

        # preparation of names storage (players x characters)
        self.names: List[List[str]] = [
            [f"Player{p+1}_C{i+1}" for i in range(self.num_chars)] for p in range(self.player_count)
        ]
        # ensure names length matches num_chars
        self.rebuild_names()

        # name input state
        self.current_input = ""
        self.cur_player = 0
        self.cur_char_idx = 0

        # maps list
        layout_dir = Path("maps/layouts")
        self.maps = sorted([path for path in layout_dir.glob("*.txt")])
        if not self.maps:
            self.maps = [Path("maps/layouts/default.txt")]
        self.selected_map_idx = 0

    def rebuild_names(self):
        """
        Ensure self.names has exactly self.player_count rows and each row has self.num_chars names.
        """
        # extend or trim player rows
        while len(self.names) < self.player_count:
            self.names.append([f"Player{len(self.names)+1}_C{i+1}" for i in range(self.num_chars)])
        if len(self.names) > self.player_count:
            self.names = self.names[: self.player_count]

        # for each player, ensure correct number of character names
        for p in range(self.player_count):
            cur = self.names[p] if p < len(self.names) else []
            if len(cur) < self.num_chars:
                cur += [f"Player{p + 1}_C{i + 1}" for i in range(len(cur), self.num_chars)]
            else:
                cur = cur[: self.num_chars]
            self.names[p] = cur

    # compatibility wrapper for older callers expecting _rebuild_names
    def _rebuild_names(self, *args, **kwargs):
        return self.rebuild_names(*args, **kwargs)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        # universal cancel
        if event.key == pygame.K_ESCAPE:
            return "back"

        if self.stage == 0:
            if event.key == pygame.K_LEFT:
                self.num_chars = max(1, self.num_chars - 1)
                self.rebuild_names()
            elif event.key == pygame.K_RIGHT:
                self.num_chars = min(self.max_chars, self.num_chars + 1)
                self.rebuild_names()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # go to naming stage
                self.stage = 1
                self.cur_player = 0
                self.cur_char_idx = 0
                self.current_input = self.names[0][0] if self.names and self.names[0] else ""
        elif self.stage == 1:
            if event.key == pygame.K_BACKSPACE:
                self.current_input = self.current_input[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # save current name and advance
                default_name = f"P{self.cur_player + 1}_C{self.cur_char_idx + 1}"
                self.names[self.cur_player][self.cur_char_idx] = self.current_input or default_name
                # advance indices
                if self.cur_player + 1 < self.player_count:
                    # next player same character index
                    self.cur_player += 1
                else:
                    # wrap players and advance char index
                    self.cur_player = 0
                    self.cur_char_idx += 1

                if self.cur_char_idx >= self.num_chars:
                    # done naming -> next stage
                    self.stage = 2
                    self.current_input = ""
                else:
                    # load next current input
                    self.current_input = self.names[self.cur_player][self.cur_char_idx]
            else:
                # add printable characters
                ch = event.unicode
                if ch and ord(ch) >= 32:
                    self.current_input += ch
        elif self.stage == 2:
            if event.key == pygame.K_LEFT:
                self.selected_map_idx = (self.selected_map_idx - 1) % len(self.maps)
            elif event.key == pygame.K_RIGHT:
                self.selected_map_idx = (self.selected_map_idx + 1) % len(self.maps)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                chosen = str(self.maps[self.selected_map_idx])
                config = {
                    "num_chars": self.num_chars,
                    "names": self.names,
                    "map_path": chosen,
                }
                return "start_game", config

        return None

    def draw(self, surface: pygame.Surface):
        surface.fill((30, 30, 30))
        white = (230, 230, 230)
        small = self.font

        def draw_text(text, y, color=white):
            surf = small.render(text, True, color)
            surface.blit(surf, (20, y))

        y = 20
        if self.stage == 0:
            draw_text("Choose characters per player: (LEFT / RIGHT)  ENTER to confirm", y)
            y += 40
            draw_text(f"Count: {self.num_chars}", y)
            y += 40
            # preview player rows
            for p in range(self.player_count):
                draw_text(f"P{p+1}: " + ", ".join(self.names[p]), y)
                y += 24
        elif self.stage == 1:
            draw_text("Enter names: press ENTER to accept each (Backspace to edit)", y)
            y += 36
            # show progress and current input
            draw_text(f"Player {self.cur_player+1} - Character {self.cur_char_idx+1}", y)
            y += 30
            draw_text(self.current_input or "<empty>", y, (200, 200, 120))
            y += 30
            # show preview of all names
            for p in range(self.player_count):
                draw_text(f"P{p+1}: " + ", ".join(self.names[p]), y)
                y += 24
        elif self.stage == 2:
            draw_text("Select map: (LEFT / RIGHT) ENTER to start", y)
            y += 36
            map_name = self.maps[self.selected_map_idx].name
            draw_text(f"Map: {map_name}", y, (180, 220, 180))
            y += 30
            # show neighbors
            left = self.maps[(self.selected_map_idx - 1) % len(self.maps)].name
            right = self.maps[(self.selected_map_idx + 1) % len(self.maps)].name
            draw_text(f"Prev: {left}", y)
            y += 22
            draw_text(f"Next: {right}", y)
            y += 22
        # small footer
        draw_text("ESC to cancel -> returns to main menu", self.height - 30)

    def reset(self):
        """Reset the menu to its initial state."""
        self.stage = 0
        self.num_chars = 1
        self.names = [
            [f"Player{p + 1}_C{i + 1}" for i in range(self.num_chars)] for p in range(self.player_count)
        ]
        self.rebuild_names()
        self.current_input = ""
        self.cur_player = 0
        self.cur_char_idx = 0
        self.selected_map_idx = 0