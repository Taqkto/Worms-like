import pygame


class Menu:
    def __init__(self, width, height, font=None):
        self.width = width
        self.height = height
        self.font = font or pygame.font.SysFont(None, 36)
        btn_w, btn_h = 300, 60
        cx, cy = width // 2, height // 2
        spacing = 20
        self.buttons = {
            "play": pygame.Rect(cx - btn_w // 2, cy - btn_h - spacing, btn_w, btn_h),
            "editor": pygame.Rect(cx - btn_w // 2, cy - btn_h // 2, btn_w, btn_h),  # new Editor button
            "settings": pygame.Rect(cx - btn_w // 2, cy + btn_h // 2, btn_w, btn_h),
            "quit": pygame.Rect(cx - btn_w // 2, cy + btn_h + spacing, btn_w, btn_h),
        }
        self.bg_color = (10, 10, 30)
        self.btn_color = (70, 130, 180)
        self.btn_hover = (100, 160, 210)
        self.text_color = (255, 255, 255)

    def draw_button(self, surf, rect, label):
        mx, my = pygame.mouse.get_pos()
        color = self.btn_hover if rect.collidepoint(mx, my) else self.btn_color
        pygame.draw.rect(surf, color, rect, border_radius=6)
        txt = self.font.render(label, True, self.text_color)
        tx = rect.x + (rect.width - txt.get_width()) // 2
        ty = rect.y + (rect.height - txt.get_height()) // 2
        surf.blit(txt, (tx, ty))

    def draw(self, surf):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(self.bg_color)
        surf.blit(overlay, (0, 0))

        title = self.font.render("Worms Like", True, self.text_color)
        surf.blit(title, ((self.width - title.get_width()) // 2, self.height // 4))

        self.draw_button(surf, self.buttons["play"], "Play")
        self.draw_button(surf, self.buttons["editor"], "Editor")      # draw Editor
        self.draw_button(surf, self.buttons["settings"], "Settings")
        self.draw_button(surf, self.buttons["quit"], "Quit")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for name, rect in self.buttons.items():
                if rect.collidepoint(mx, my):
                    return name
        return None
