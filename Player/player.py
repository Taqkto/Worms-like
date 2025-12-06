# python
from typing import List, Optional
from Player.character import Character


class Player:
    def __init__(self) -> None:
        self.characters: List[Character] = []
        self.current_character_index: int = 0

    def access_current_character(self) -> Optional[Character]:
        if not self.characters:
            return None
        self.current_character_index %= len(self.characters)
        return self.characters[self.current_character_index]

    def add_character(self, character: Character) -> None:
        self.characters.append(character)

    def remove_character(self, character_index: int) -> None:
        if not (0 <= character_index < len(self.characters)):
            return
        del self.characters[character_index]
        if not self.characters:
            self.current_character_index = 0
            return
        self.current_character_index %= len(self.characters)

    def switch_to_next_alive_character(self) -> None:
        if not self.characters or not self.has_alive_characters():
            return
        start = self.current_character_index
        n = len(self.characters)
        for i in range(1, n + 1):
            idx = (start + i) % n
            if self.characters[idx].is_alive():
                self.current_character_index = idx
                return

    def has_alive_characters(self) -> bool:
        return any(character.is_alive() for character in self.characters)

    def reset_characters(self) -> None:
        self.characters = []
        self.current_character_index = 0
