import pygame


class SettingsMenu:
    def __init__(self, width, height, font=None):
        self.width = width
        self.height = height
        self.font = font or pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 28)

        # Touches par défaut (adaptées au jeu)
        self.key_bindings = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "jump": pygame.K_SPACE,
            "switch_grenade": pygame.K_g,
            "switch_rocket": pygame.K_r,
        }

        self.key_labels = {
            "move_left": "Move Left",
            "move_right": "Move Right",
            "jump": "Jump",
            "switch_grenade": "Switch to Grenade",
            "switch_rocket": "Switch to Rocket",
        }

        self.waiting_for_key = None
        self.bg_color = (10, 10, 30)
        self.btn_color = (70, 130, 180)
        self.btn_hover = (100, 160, 210)
        self.text_color = (255, 255, 255)
        self.highlight_color = (255, 200, 0)

        # Bouton retour
        btn_w, btn_h = 200, 50
        self.back_button = pygame.Rect(
            width // 2 - btn_w // 2,
            height - 100,
            btn_w,
            btn_h
        )

        # Zones cliquables pour chaque touche
        self.key_rects = {}
        start_y = height // 3
        spacing = 70
        for i, key_name in enumerate(self.key_labels.keys()):
            self.key_rects[key_name] = pygame.Rect(
                width // 2 + 50,
                start_y + i * spacing,
                200,
                40
            )

    def draw(self, surf):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(self.bg_color)
        surf.blit(overlay, (0, 0))

        # Titre
        title = self.font.render("Settings - Key Bindings", True, self.text_color)
        surf.blit(title, ((self.width - title.get_width()) // 2, 50))

        # Afficher les touches
        for key_name, rect in self.key_rects.items():
            # Label
            label = self.small_font.render(
                self.key_labels[key_name] + ":",
                True,
                self.text_color
            )
            surf.blit(label, (rect.x - label.get_width() - 20, rect.y + 5))

            # Zone de touche
            mx, my = pygame.mouse.get_pos()
            if self.waiting_for_key == key_name:
                color = self.highlight_color
                key_text = "Press a key..."
            else:
                color = self.btn_hover if rect.collidepoint(mx, my) else self.btn_color
                key_text = pygame.key.name(self.key_bindings[key_name]).upper()

            pygame.draw.rect(surf, color, rect, border_radius=4)
            txt = self.small_font.render(key_text, True, self.text_color)
            surf.blit(txt, (
                rect.x + (rect.width - txt.get_width()) // 2,
                rect.y + (rect.height - txt.get_height()) // 2
            ))

        # Bouton retour
        mx, my = pygame.mouse.get_pos()
        color = self.btn_hover if self.back_button.collidepoint(mx, my) else self.btn_color
        pygame.draw.rect(surf, color, self.back_button, border_radius=6)
        txt = self.font.render("Back", True, self.text_color)
        surf.blit(txt, (
            self.back_button.x + (self.back_button.width - txt.get_width()) // 2,
            self.back_button.y + (self.back_button.height - txt.get_height()) // 2
        ))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Clic sur retour
            if self.back_button.collidepoint(mx, my):
                return "back"

            # Clic sur une touche à configurer
            if not self.waiting_for_key:
                for key_name, rect in self.key_rects.items():
                    if rect.collidepoint(mx, my):
                        self.waiting_for_key = key_name
                        return None

        # Capture de la nouvelle touche
        if event.type == pygame.KEYDOWN and self.waiting_for_key:
            if event.key != pygame.K_ESCAPE:
                self.key_bindings[self.waiting_for_key] = event.key
            self.waiting_for_key = None

        return None
