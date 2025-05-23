import pygame
import config
import chess
from game_logic.player import Player


class ClockDisplay:
    def __init__(self, x, y, width, height, player: Player, font=None, text_color_override=None, bg_color_override=None): # Changé les noms
        self.rect = pygame.Rect(x, y, width, height)
        self.player = player
        self.font = font if font else config.STATUS_FONT
        
        # Déterminer les couleurs en fonction de la couleur du joueur
        if self.player.color == chess.WHITE:
            self.actual_bg_color = bg_color_override if bg_color_override else pygame.Color(220, 220, 220) # Fond clair pour joueur blanc
            self.actual_text_color = text_color_override if text_color_override else pygame.Color(20, 20, 20)   # Texte foncé
        else: # Joueur Noir
            self.actual_bg_color = bg_color_override if bg_color_override else pygame.Color(50, 50, 50)    # Fond foncé pour joueur noir
            self.actual_text_color = text_color_override if text_color_override else pygame.Color(200, 200, 200) # Texte clair
        
        if not self.font: # Fallback
            self.font = pygame.font.SysFont("arial", 30)

    def draw(self, screen, is_current_player: bool):
        # Dessiner le fond de l'horloge
        pygame.draw.rect(screen, self.actual_bg_color, self.rect, border_radius=8) # Coins arrondis
        
        time_str = self.player.get_time_left_formatted()
        text_surface = self.font.render(time_str, True, self.actual_text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        
        if is_current_player and not self.player.is_timed_out:
            # Highlight plus subtil, peut-être une bordure plus épaisse ou d'une couleur vive
            pygame.draw.rect(screen, config.COLOR_SELECTED_SQUARE, self.rect, border_radius=8, width=4) # Bordure de 4px
            
        screen.blit(text_surface, text_rect)