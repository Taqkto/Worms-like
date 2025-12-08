import pygame
import sys
from pathlib import Path

# Ajout du dossier courant au path pour les imports
sys.path.append(str(Path(__file__).parent))

from maps.map import BLOCK_TEXTURES, get_texture

# Configuration
TILE_SIZE = 32
SCREEN_WIDTH = 1380
SCREEN_HEIGHT = 820
SCROLL_SPEED = 15
DEFAULT_MAP_WIDTH = 40
DEFAULT_MAP_HEIGHT = 20

# Couleurs
BG_COLOR = (30, 30, 30)  # Gris foncé
GRID_COLOR = (200, 200, 200)
UI_BG_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 255, 0)

class LevelEditor:
    def __init__(self, width=DEFAULT_MAP_WIDTH, height=DEFAULT_MAP_HEIGHT):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Worms-like Level Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)

        self.map_width = width
        self.map_height = height
        # Initialisation de la grille avec de l'air '.'
        self.grid = [['.' for _ in range(width)] for _ in range(height)]
        
        self.camera_x = 0
        self.camera_y = 0

        # Définition des outils disponibles
        # Symboles correspondants à maps/map.py
        self.tools = [
            {'symbol': '#', 'name': 'Terre', 'color': (139, 90, 43), 'texture_key': 'dirt'},
            {'symbol': 'X', 'name': 'Pierre', 'color': (100, 100, 100), 'texture_key': 'stone'},
            {'symbol': 'W', 'name': 'Eau', 'color': (28, 107, 160), 'texture_key': 'water'},
            {'symbol': '!', 'name': 'NoSpawn', 'color': (255, 0, 0), 'texture_key': None},

            {'symbol': '.', 'name': 'Gomme', 'color': (255, 255, 255), 'texture_key': None},
        ]
        self.current_tool_index = 0
        self.running = True

        # État de l'éditeur
        self.state = "menu" # "menu", "editing", "saving"
        self.filename_input = "custom_map"
        
        self.file_list = []
        self.refresh_file_list()

        # Préchargement des textures pour l'éditeur
        self.textures = {}
        for tool in self.tools:
            key = tool['texture_key']
            if key and key in BLOCK_TEXTURES:
                try:
                    # On utilise get_texture de map.py pour la cohérence
                    self.textures[tool['symbol']] = get_texture(BLOCK_TEXTURES[key], TILE_SIZE)
                except Exception as e:
                    print(f"Erreur chargement texture {key}: {e}")

        # Liste des fichiers pour le menu
        self.file_list = []
        self.refresh_file_list()

    def refresh_file_list(self):
        directory = Path("maps/layouts")
        directory.mkdir(parents=True, exist_ok=True)
        self.file_list = [f.name for f in directory.glob("*.txt")]
        self.file_list.sort()

    def save_map(self, filename="custom_map.txt"):
        """Sauvegarde la grille actuelle dans un fichier texte."""
        directory = Path("maps/layouts")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                for row in self.grid:
                    f.write("".join(row) + "\n")
            print(f"✅ Map sauvegardée avec succès : {path}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")
            return False

    def load_map(self, filename):
        path = Path("maps/layouts") / filename
        if not path.exists():
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            
            if not lines:
                return
                
            self.map_height = len(lines)
            self.map_width = len(lines[0])
            self.grid = [list(line) for line in lines]
            self.filename_input = filename.replace(".txt", "")
            self.state = "editing"
            print(f"Chargé: {filename}")
        except Exception as e:
            print(f"Erreur chargement: {e}")

    def new_map(self):
        self.map_width = DEFAULT_MAP_WIDTH
        self.map_height = DEFAULT_MAP_HEIGHT
        self.grid = [['.' for _ in range(self.map_width)] for _ in range(self.map_height)]
        self.filename_input = "custom_map"
        self.state = "editing"

    def delete_map(self, filename):
        path = Path("maps/layouts") / filename
        if path.exists():
            try:
                path.unlink()
                print(f"Supprimé: {filename}")
            except Exception as e:
                print(f"Erreur suppression: {e}")
        self.refresh_file_list()

    def handle_input(self):
        if self.state == "editing":
            keys = pygame.key.get_pressed()
            
            # Déplacement Caméra
            if keys[pygame.K_RIGHT]:
                self.camera_x += SCROLL_SPEED
            if keys[pygame.K_LEFT]:
                self.camera_x -= SCROLL_SPEED
            if keys[pygame.K_DOWN]:
                self.camera_y += SCROLL_SPEED
            if keys[pygame.K_UP]:
                self.camera_y -= SCROLL_SPEED

            # Limites de la caméra (pour ne pas trop s'éloigner)
            max_cam_x = self.map_width * TILE_SIZE - SCREEN_WIDTH + 100
            max_cam_y = self.map_height * TILE_SIZE - SCREEN_HEIGHT + 100
            # On permet d'aller un peu dans le négatif ou au delà pour le confort
            
            # Interaction Souris
            mouse_buttons = pygame.mouse.get_pressed()
            mx, my = pygame.mouse.get_pos()
            
            # Si on est sur l'UI (en bas), on ignore le clic sur la grille
            if my > SCREEN_HEIGHT - 80:
                if mouse_buttons[0]: # Clic gauche sur l'UI pour changer d'outil
                    self._handle_ui_click(mx, my)
                return

            # Conversion coordonnées écran -> grille
            world_x = mx + self.camera_x
            world_y = my + self.camera_y
            
            grid_x = int(world_x // TILE_SIZE)
            grid_y = int(world_y // TILE_SIZE)

            if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                if mouse_buttons[0]: # Clic Gauche : Placer
                    self.grid[grid_y][grid_x] = self.tools[self.current_tool_index]['symbol']
                elif mouse_buttons[2]: # Clic Droit : Effacer (mettre de l'air)
                    self.grid[grid_y][grid_x] = '.'

        elif self.state == "saving":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.state = "editing"
            elif keys[pygame.K_RETURN]:
                # Valider la sauvegarde
                name = self.filename_input.strip()
                if name:
                    if not name.endswith(".txt"):
                        name += ".txt"
                    self.save_map(name)
                self.state = "editing"

    def _handle_ui_click(self, mx, my):
        # Logique simple pour cliquer sur les icônes en bas
        x_offset = 20
        for i, tool in enumerate(self.tools):
            rect = pygame.Rect(x_offset, SCREEN_HEIGHT - 60, 50, 50)
            if rect.collidepoint(mx, my):
                self.current_tool_index = i
                return
            x_offset += 70

    def draw_save_dialog(self):
        # Overlay semi-transparent
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Boite de dialogue
        dialog_width, dialog_height = 400, 200
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        
        pygame.draw.rect(self.screen, UI_BG_COLOR, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height), 2)
        
        # Titre
        title_surf = self.font.render("Sauvegarder le niveau", True, TEXT_COLOR)
        self.screen.blit(title_surf, (dialog_x + 20, dialog_y + 20))
        
        # Instruction
        instr_surf = self.font.render("Nom du fichier (.txt ajouté auto) :", True, (200, 200, 200))
        self.screen.blit(instr_surf, (dialog_x + 20, dialog_y + 60))
        
        # Champ texte
        input_bg_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 40)
        pygame.draw.rect(self.screen, (30, 30, 30), input_bg_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), input_bg_rect, 1)
        
        text_surf = self.font.render(self.filename_input, True, (255, 255, 255))
        self.screen.blit(text_surf, (input_bg_rect.x + 10, input_bg_rect.y + 10))
        
        # Boutons info
        help_surf = self.font.render("[Entrée] Valider   [Echap] Annuler", True, HIGHLIGHT_COLOR)
        self.screen.blit(help_surf, (dialog_x + 20, dialog_y + 150))

    def draw_menu(self):
        # Title
        title = self.font.render("Gestionnaire de Niveaux", True, TEXT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        # New Level Button
        new_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, 100, 200, 40)
        pygame.draw.rect(self.screen, UI_BG_COLOR, new_btn)
        pygame.draw.rect(self.screen, (200, 200, 200), new_btn, 2)
        new_txt = self.font.render("Nouveau Niveau", True, TEXT_COLOR)
        self.screen.blit(new_txt, (new_btn.centerx - new_txt.get_width()//2, new_btn.centery - new_txt.get_height()//2))
        
        # List
        y = 160
        for filename in self.file_list:
            # File name
            name_surf = self.font.render(filename, True, TEXT_COLOR)
            self.screen.blit(name_surf, (SCREEN_WIDTH//2 - 200, y + 10))
            
            # Edit Button
            edit_btn = pygame.Rect(SCREEN_WIDTH//2 + 50, y, 80, 30)
            pygame.draw.rect(self.screen, (0, 100, 0), edit_btn)
            edit_txt = self.font.render("Éditer", True, TEXT_COLOR)
            self.screen.blit(edit_txt, (edit_btn.centerx - edit_txt.get_width()//2, edit_btn.centery - edit_txt.get_height()//2))
            
            # Delete Button
            del_btn = pygame.Rect(SCREEN_WIDTH//2 + 140, y, 80, 30)
            pygame.draw.rect(self.screen, (100, 0, 0), del_btn)
            del_txt = self.font.render("Suppr", True, TEXT_COLOR)
            self.screen.blit(del_txt, (del_btn.centerx - del_txt.get_width()//2, del_btn.centery - del_txt.get_height()//2))
            
            y += 40

    def handle_menu_click(self, mx, my):
        # New Level Button
        new_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, 100, 200, 40)
        if new_btn.collidepoint(mx, my):
            self.new_map()
            return

        # List buttons
        y = 160
        for filename in self.file_list:
            edit_btn = pygame.Rect(SCREEN_WIDTH//2 + 50, y, 80, 30)
            del_btn = pygame.Rect(SCREEN_WIDTH//2 + 140, y, 80, 30)
            
            if edit_btn.collidepoint(mx, my):
                self.load_map(filename)
                return
            elif del_btn.collidepoint(mx, my):
                self.delete_map(filename)
                return
            
            y += 40

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # --- Dessin de la Grille ---
        # On calcule la plage visible pour optimiser
        start_col = int(self.camera_x // TILE_SIZE)
        end_col = start_col + (SCREEN_WIDTH // TILE_SIZE) + 2
        start_row = int(self.camera_y // TILE_SIZE)
        end_row = start_row + (SCREEN_HEIGHT // TILE_SIZE) + 2

        # Clamp values
        start_col = max(0, start_col)
        end_col = min(self.map_width, end_col)
        start_row = max(0, start_row)
        end_row = min(self.map_height, end_row)

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                symbol = self.grid[y][x]
                screen_x = x * TILE_SIZE - self.camera_x
                screen_y = y * TILE_SIZE - self.camera_y
                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)

                # Dessin du bloc
                if symbol in self.textures:
                    self.screen.blit(self.textures[symbol], rect)
                else:
                    # Fallback couleur si pas de texture ou symbole spécial
                    tool = next((t for t in self.tools if t['symbol'] == symbol), None)
                    if tool and symbol != '.':
                        pygame.draw.rect(self.screen, tool['color'], rect)
                        if symbol == 'S': # Marqueur Spawn
                            font_surf = self.font.render("S", True, (255, 255, 255))
                            self.screen.blit(font_surf, (rect.centerx - font_surf.get_width()//2, rect.centery - font_surf.get_height()//2))

                # Grille légère
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

        # --- Dessin de l'UI ---
        self.draw_ui()

        # --- Dessin du menu de sauvegarde ---
        if self.state == "saving":
            self.draw_save_dialog()
        elif self.state == "menu":
            self.draw_menu()
        
        pygame.display.flip()

    def draw_ui(self):
        # Fond du panneau
        ui_rect = pygame.Rect(0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 80)
        pygame.draw.rect(self.screen, UI_BG_COLOR, ui_rect)
        pygame.draw.line(self.screen, (100, 100, 100), (0, SCREEN_HEIGHT - 80), (SCREEN_WIDTH, SCREEN_HEIGHT - 80), 2)
        
        x_offset = 20
        for i, tool in enumerate(self.tools):
            rect = pygame.Rect(x_offset, SCREEN_HEIGHT - 60, 50, 50)
            
            # Surbrillance sélection
            if i == self.current_tool_index:
                pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect.inflate(6, 6), 3)
            
            # Dessin icône (texture ou couleur)
            if tool['symbol'] in self.textures:
                # On redimensionne un peu pour l'icone
                tex = pygame.transform.scale(self.textures[tool['symbol']], (50, 50))
                self.screen.blit(tex, rect)
            else:
                pygame.draw.rect(self.screen, tool['color'], rect)
                if tool['symbol'] == 'S':
                    font_surf = self.font.render("S", True, (255, 255, 255))
                    self.screen.blit(font_surf, (rect.centerx - font_surf.get_width()//2, rect.centery - font_surf.get_height()//2))
                elif tool['symbol'] == '.':
                    pygame.draw.rect(self.screen, (0,0,0), rect, 1) # Bordure pour la gomme blanche
            
            # Nom
            name_surf = self.font.render(f"{i+1}:{tool['name']}", True, TEXT_COLOR)
            self.screen.blit(name_surf, (x_offset, SCREEN_HEIGHT - 75))
            
            x_offset += 70
            
        # Instructions
        info_text = "Clic G: Placer | Clic D: Effacer | S: Sauvegarder | Flèches: Bouger"
        info_surf = self.font.render(info_text, True, TEXT_COLOR)
        self.screen.blit(info_surf, (SCREEN_WIDTH - info_surf.get_width() - 20, SCREEN_HEIGHT - 40))

    def run(self):
        print("Démarrage de l'éditeur de niveau...")
        print("Contrôles :")
        print(" - Clic Gauche : Placer un bloc")
        print(" - Clic Droit : Effacer")
        print(" - 1-6 : Choisir un outil")
        print(" - Flèches : Déplacer la caméra")
        print(" - S : Sauvegarder (Ouvre le menu)")
        print(" - Echap : Retour au menu principal")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # --- Gestion des événements en mode MENU ---
                if self.state == "menu":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_menu_click(event.pos[0], event.pos[1])

                # --- Gestion des événements en mode SAUVEGARDE ---
                elif self.state == "saving":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            # Valider la sauvegarde
                            name = self.filename_input.strip()
                            if name:
                                if not name.endswith(".txt"):
                                    name += ".txt"
                                self.save_map(name)
                            self.state = "editing"
                        elif event.key == pygame.K_ESCAPE:
                            # Annuler
                            self.state = "editing"
                        elif event.key == pygame.K_BACKSPACE:
                            self.filename_input = self.filename_input[:-1]
                        else:
                            # Saisie de texte
                            if event.unicode.isprintable() and len(self.filename_input) < 30:
                                self.filename_input += event.unicode

                # --- Gestion des événements en mode ÉDITION ---
                elif self.state == "editing":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s:
                            self.state = "saving"
                        elif event.key == pygame.K_ESCAPE:
                            # Retour au menu
                            self.state = "menu"
                            self.refresh_file_list()
                        # Raccourcis clavier 1-6
                        elif pygame.K_1 <= event.key <= pygame.K_6:
                            idx = event.key - pygame.K_1
                            if 0 <= idx < len(self.tools):
                                self.current_tool_index = idx
            
            self.handle_input()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()
