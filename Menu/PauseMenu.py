import pygame
from typing import Optional, Tuple


class PauseMenu:
    def __init__(self, width: int, height: int, font: pygame.font.Font):
        self.width = width
        self.height = height
        self.font = font

        # Dimensions des boutons
        self.button_width = 200
        self.button_height = 50
        self.button_spacing = 20

        # Créer les boutons
        self.buttons = []
        self._create_buttons()

    def resize(self, width: int, height: int):
        """Redimensionne le menu pause"""
        self.width = width
        self.height = height
        self._create_buttons()

    def _create_buttons(self):
        center_x = self.width // 2
        start_y = self.height // 2 - 100

        self.buttons = [
            {
                "text": "Resume",
                "action": "resume",
                "rect": pygame.Rect(
                    center_x - self.button_width // 2,
                    start_y,
                    self.button_width,
                    self.button_height
                )
            },
            {
                "text": "Settings",
                "action": "settings",
                "rect": pygame.Rect(
                    center_x - self.button_width // 2,
                    start_y + self.button_height + self.button_spacing,
                    self.button_width,
                    self.button_height
                )
            },
            {
                "text": "Home",
                "action": "home",
                "rect": pygame.Rect(
                    center_x - self.button_width // 2,
                    start_y + 2 * (self.button_height + self.button_spacing),
                    self.button_width,
                    self.button_height
                )
            }
        ]

    def handle_event(self, event) -> Optional[str]:
        """Gère les événements du menu pause"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "resume"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for button in self.buttons:
                if button["rect"].collidepoint(mx, my):
                    return button["action"]

        return None

    def draw(self, surface: pygame.Surface):
        """Dessine le menu pause avec overlay semi-transparent"""
        # Overlay semi-transparent
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Titre "PAUSED"
        title_text = "PAUSED"
        title_surf = self.font.render(title_text, True, (255, 255, 255))
        title_x = self.width // 2 - title_surf.get_width() // 2
        title_y = self.height // 2 - 180
        surface.blit(title_surf, (title_x, title_y))

        # Dessiner les boutons
        mx, my = pygame.mouse.get_pos()
        for button in self.buttons:
            rect = button["rect"]
            is_hovered = rect.collidepoint(mx, my)

            # Couleur du bouton (plus clair si survolé)
            btn_color = (100, 100, 200) if is_hovered else (60, 60, 150)
            pygame.draw.rect(surface, btn_color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 2)

            # Texte du bouton
            text_surf = self.font.render(button["text"], True, (255, 255, 255))
            text_x = rect.centerx - text_surf.get_width() // 2
            text_y = rect.centery - text_surf.get_height() // 2
            surface.blit(text_surf, (text_x, text_y))