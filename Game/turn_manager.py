from typing import List, Optional
from Player.player import Player


class TurnManager:
    """
    Manage turn order between Player instances.
    Keeps self.current_player_index pointing to the next player who has alive characters.
    """

    def __init__(self, players: List[Player]) -> None:
        self.players: List[Player] = players or []
        self.current_player_index: int = 0
        # ensure index points to a valid player with alive characters if possible
        self._ensure_valid_index()

    @property
    def current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        # guard index range
        if not (0 <= self.current_player_index < len(self.players)):
            return None
        return self.players[self.current_player_index]

    def _find_next_alive(self, start_index: int = 0) -> Optional[int]:
        """
        Return the index of the next player (starting from start_index) that has alive characters.
        Returns None if none found.
        """
        n = len(self.players)
        if n == 0:
            return None
        for i in range(n):
            idx = (start_index + i) % n
            try:
                if self.players[idx].has_alive_characters():
                    return idx
            except Exception:
                # if player object is malformed, skip it
                continue
        return None

    def _ensure_valid_index(self) -> None:
        """
        Make sure current_player_index points to a player with alive characters if any exist.
        If no players have alive characters, index remains 0 (or clamped).
        """
        if not self.players:
            self.current_player_index = 0
            return
        next_idx = self._find_next_alive(self.current_player_index)
        if next_idx is None:
            # no alive players; clamp index to valid range
            self.current_player_index = max(0, min(self.current_player_index, len(self.players) - 1))
        else:
            self.current_player_index = next_idx
            # ensure the player's active character is an alive one
            try:
                self.current_player.switch_to_next_alive_character()
            except Exception:
                pass

    def next_turn(self) -> Optional[int]:
        """
        Advance to the next player with alive characters.
        Returns the new current_player_index, or None if no eligible players exist.
        """
        if not self.players:
            return None
        start = (self.current_player_index + 1) % len(self.players)
        next_idx = self._find_next_alive(start)
        if next_idx is None:
            # if nobody alive, do not change index (game over handled by caller)
            return None
        self.current_player_index = next_idx
        # ensure the player's active character is alive
        try:
            self.current_player.switch_to_next_alive_character()
        except Exception:
            pass
        return self.current_player_index
