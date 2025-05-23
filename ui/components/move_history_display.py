import pygame
import config
from game_logic.chess_board import ChessBoardLogic

class MoveHistoryDisplay:
    def __init__(self, x, y, width, height, chess_logic: ChessBoardLogic, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.chess_logic = chess_logic
        self.font = font if font else config.MOVE_HISTORY_FONT
        self.text_color = config.COLOR_MOVE_HISTORY_TEXT
        self.bg_color = config.COLOR_MOVE_HISTORY_BG
        self.line_height = self.font.get_linesize() if self.font else 20
        self.max_lines_visible = self.rect.height // self.line_height
        self.scroll_offset = 0 # Nombre de lignes décalées vers le haut
        
        if not self.font:
            print("ATTENTION: MoveHistory font non initialisé dans config.py!")
            self.font = pygame.font.SysFont("arial", 16) # Fallback
            self.line_height = self.font.get_linesize()


    def handle_event(self, event):
        # Gérer le défilement avec la molette de la souris
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if event.button == 4:  # Molette vers le haut
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:  # Molette vers le bas
                total_moves = len(self.chess_logic.get_move_history_san())
                # Chaque coup prend une demi-ligne si on affiche "1. e4 e5"
                total_display_items = (total_moves + 1) // 2 
                if total_display_items > self.max_lines_visible:
                    self.scroll_offset = min(self.scroll_offset + 1, total_display_items - self.max_lines_visible)

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=5)
        
        move_history = self.chess_logic.get_move_history_san()
        
        # Créer une surface séparée pour l'historique pour le clipping
        history_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        history_surface.fill((0,0,0,0)) # Transparent

        y_pos = 5 # Petit padding en haut
        
        for i in range(0, len(move_history), 2):
            move_number = (i // 2) + 1
            line_text = f"{move_number}. {move_history[i]}"
            if i + 1 < len(move_history):
                line_text += f"  {move_history[i+1]}"
            
            # Afficher seulement si la ligne est dans la zone visible après défilement
            current_line_index = i // 2
            if current_line_index >= self.scroll_offset and current_line_index < self.scroll_offset + self.max_lines_visible:
                text_surface = self.font.render(line_text, True, self.text_color)
                history_surface.blit(text_surface, (5, y_pos))
                y_pos += self.line_height
        
        screen.blit(history_surface, self.rect.topleft)