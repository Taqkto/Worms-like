# python
from typing import List, Optional
from Player.player import Player


class TurnManager:
    def __init__(self, players: List[Player]):
        self.players = players
        self.current_player_index = 0
        # choose a starting player that has alive characters (allow staying on index 0)
        self._advance_to_next_player_with_alive_characters(allow_same_player=True)

    @property
    def current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        return self.players[self.current_player_index]

    def _advance_to_next_player_with_alive_characters(self, allow_same_player: bool = False) -> None:
        if not self.players:
            return
        n = len(self.players)
        start_index = self.current_player_index if allow_same_player else (self.current_player_index + 1) % n
        for i in range(n):
            idx = (start_index + i) % n
            if self.players[idx].has_alive_characters():
                self.current_player_index = idx
                return
        # no alive players -> keep index (game over handled elsewhere)

    def next_turn(self) -> None:
        player = self.current_player
        if player is None:
            return
        # advance this player's active character (one character per player per turn)
        player.switch_to_next_alive_character()
        # then move to the next player who still has alive characters
        self._advance_to_next_player_with_alive_characters(allow_same_player=False)
