import pygame
import pickle
import os


class SettingsMenu:
    SETTINGS_FILE = "settings.bin"

    def __init__(self, width, height, font=None):
        self.width = width
        self.height = height
        self.font = font or pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 28)

        # Touches par défaut
        self.default_key_bindings = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "jump": pygame.K_SPACE,
            "switch_grenade": pygame.K_g,
            "switch_rocket": pygame.K_r,
        }

        # Charger les touches sauvegardées ou utiliser les valeurs par défaut
        self.key_bindings = self.load_settings()

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

    def save_settings(self):
        """Sauvegarde les touches dans un fichier binaire"""
        try:
            with open(self.SETTINGS_FILE, 'wb') as f:
                pickle.dump(self.key_bindings, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres: {e}")

    def load_settings(self):
        """Charge les touches depuis le fichier binaire"""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'rb') as f:
                    loaded = pickle.load(f)
                    # Vérifier que toutes les touches par défaut sont présentes
                    for key in self.default_key_bindings:
                        if key not in loaded:
                            loaded[key] = self.default_key_bindings[key]
                    return loaded
            except Exception as e:
                print(f"Erreur lors du chargement des paramètres: {e}")
        return self.default_key_bindings.copy()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Clic sur retour
            if self.back_button.collidepoint(mx, my):
                # Sauvegarder avant de retourner
                self.save_settings()
                return {"action": "back", "key_bindings": self.key_bindings}

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

        return None

    def draw(self, screen):
        """Affiche le menu des paramètres"""
        screen.fill(self.bg_color)

        # Titre
        title = self.font.render("Settings", True, self.text_color)
        title_rect = title.get_rect(center=(self.width // 2, 80))
        screen.blit(title, title_rect)

        # Afficher chaque touche configurable
        start_y = self.height // 3
        spacing = 70

        for i, (key_name, label) in enumerate(self.key_labels.items()):
            y_pos = start_y + i * spacing

            # Label de la touche (ex: "Move Left")
            label_surf = self.small_font.render(label + ":", True, self.text_color)
            screen.blit(label_surf, (self.width // 2 - 250, y_pos + 8))

            # Rectangle de la touche
            rect = self.key_rects[key_name]
            color = self.highlight_color if self.waiting_for_key == key_name else self.btn_color
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, self.text_color, rect, 2)

            # Texte de la touche actuelle
            if self.waiting_for_key == key_name:
                key_text = "Press a key..."
            else:
                key_code = self.key_bindings[key_name]
                key_text = pygame.key.name(key_code).upper()

            key_surf = self.small_font.render(key_text, True, self.text_color)
            key_rect = key_surf.get_rect(center=rect.center)
            screen.blit(key_surf, key_rect)

        # Bouton retour
        pygame.draw.rect(screen, self.btn_color, self.back_button)
        pygame.draw.rect(screen, self.text_color, self.back_button, 2)
        back_text = self.font.render("Back", True, self.text_color)
        back_rect = back_text.get_rect(center=self.back_button.center)
        screen.blit(back_text, back_rect)

