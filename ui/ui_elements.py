import pygame
import config # Pour les couleurs et polices

class Button:
    def __init__(self, x, y, width, height, text, action=None, 
                 font=None, 
                 color_normal=None, color_hover=None, color_text=None,
                 border_radius=5):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_hovered = False

        self.font = font if font else config.BUTTON_FONT
        self.color_normal = color_normal if color_normal else config.COLOR_BUTTON_NORMAL
        self.color_hover = color_hover if color_hover else config.COLOR_BUTTON_HOVER
        self.color_text = color_text if color_text else config.COLOR_BUTTON_TEXT
        self.border_radius = border_radius
        
        if not self.font:
            print("ATTENTION: Button font non initialisé dans config.py!")
            # Fallback très basique
            self.font = pygame.font.SysFont("arial", 20)


    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                if self.action:
                    self.action() # Exécute l'action associée
                return True # Indique que le bouton a géré l'événement
        return False

    def draw(self, screen):
        color = self.color_hover if self.is_hovered else self.color_normal
        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        
        if self.text:
            text_surface = self.font.render(self.text, True, self.color_text)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)

class Label:
    def __init__(self, x, y, text, font=None, color=None, anchor="topleft"):
        self.text = text
        self.font = font if font else config.INFO_FONT
        self.color = color if color else config.COLOR_TEXT
        self.anchor = anchor # "topleft", "center", "midtop", etc.
        self.x = x
        self.y = y
        
        if not self.font:
            print("ATTENTION: Label font non initialisé dans config.py!")
            self.font = pygame.font.SysFont("arial", 18) # Fallback

        self.surface = self.font.render(self.text, True, self.color)
        self.rect = self.surface.get_rect()
        self._update_position()

    def _update_position(self):
        if self.anchor == "topleft":
            self.rect.topleft = (self.x, self.y)
        elif self.anchor == "center":
            self.rect.center = (self.x, self.y)
        elif self.anchor == "midtop":
            self.rect.midtop = (self.x, self.y)
        # Ajoutez d'autres ancres si nécessaire

    def set_text(self, new_text):
        if new_text != self.text:
            self.text = new_text
            self.surface = self.font.render(self.text, True, self.color)
            old_center = self.rect.center # Conserver le centre si l'ancre est centrée
            self.rect = self.surface.get_rect()
            self._update_position() # Réappliquer l'ancre

    def draw(self, screen):
        screen.blit(self.surface, self.rect)

class OptionSelector:
    """Un groupe de boutons où un seul peut être sélectionné."""
    def __init__(self, x, y, options: list[tuple[str, any]], default_value: any, 
                 on_select_action=None, button_width=120, button_height=40, spacing=10,
                 font=None, orientation="horizontal"):
        self.options = options # liste de (texte_display, valeur_reelle)
        self.selected_value = default_value
        self.on_select_action = on_select_action # Fonction à appeler avec la nouvelle valeur
        self.buttons = []
        self.font = font if font else config.BUTTON_FONT # Réutiliser BUTTON_FONT ou un autre
        self.orientation = orientation

        current_x, current_y = x, y
        for text, value in self.options:
            button = Button(current_x, current_y, button_width, button_height, text,
                            action=lambda v=value: self._select_option(v), # Passer la valeur via lambda
                            font=self.font,
                            # Les couleurs seront gérées dans draw pour montrer la sélection
                            )
            self.buttons.append(button)
            if self.orientation == "horizontal":
                current_x += button_width + spacing
            else: # vertical
                current_y += button_height + spacing
        
        if not self.font:
            print("ATTENTION: OptionSelector font non initialisé!")


    def _select_option(self, value):
        if self.selected_value != value:
            self.selected_value = value
            if self.on_select_action:
                self.on_select_action(self.selected_value)
        # print(f"OptionSelector: Selected {self.selected_value}") # Debug

    def get_selected_value(self):
        return self.selected_value
    
    def set_selected_value(self, value): # Pour un contrôle externe si besoin
        if value in [opt_val for _, opt_val in self.options]:
            self.selected_value = value

    def handle_event(self, event):
        for button in self.buttons:
            # L'action du bouton est gérée par son propre handle_event
            if button.handle_event(event): 
                return True # Un bouton a été cliqué
        return False

    def draw(self, screen):
        for i, button in enumerate(self.buttons):
            text, value = self.options[i]
            if value == self.selected_value:
                button.color_normal = config.COLOR_OPTION_SELECTED # Couleur pour l'option active
                button.color_hover = config.COLOR_OPTION_SELECTED # Garder la couleur si survolé
            else:
                button.color_normal = config.COLOR_BUTTON_NORMAL # Couleur par défaut
                button.color_hover = config.COLOR_BUTTON_HOVER
            button.draw(screen)