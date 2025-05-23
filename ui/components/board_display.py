import pygame
import chess
import config 
from game_logic.chess_board import ChessBoardLogic
import math

class BoardDisplay:
    def __init__(self, x_offset, y_offset, chess_logic: ChessBoardLogic):
        self.x_offset = x_offset # Offset global où le plateau (les 64 cases) commence à être dessiné
        self.y_offset = y_offset
        self.chess_logic = chess_logic
        
        self.selected_pygame_square = None 
        self.legal_moves_for_selected_piece = []

        self.arrow_color = pygame.Color(255, 100, 0, 180) # Orange semi-transparent
        self.arrow_thickness = 8 # Un peu plus épais
        self.arrow_head_size_factor = 0.05 # Ratio de la taille de la case pour la tête de flèche
                                         # Augmenter pour une tête plus grande

    def _pygame_coords_to_board_square(self, pos):
        # Vérifier si le clic est DANS la zone des 64 cases
        if not (self.x_offset <= pos[0] < self.x_offset + config.BOARD_SIZE_PX and \
                self.y_offset <= pos[1] < self.y_offset + config.BOARD_SIZE_PX):
            return None 
        
        col = (pos[0] - self.x_offset) // config.SQUARE_SIZE
        row = (pos[1] - self.y_offset) // config.SQUARE_SIZE
        return row, col

    def _board_square_to_chess_square(self, board_row, board_col):
        return chess.square(file_index=board_col, rank_index=7 - board_row)

    def _chess_square_to_board_square(self, chess_square_index: chess.Square):
        file_index = chess.square_file(chess_square_index)
        rank_index = chess.square_rank(chess_square_index)
        return (7 - rank_index, file_index)

    def handle_click(self, mouse_pos):
        if self.chess_logic.is_game_over():
            return False 

        board_coords = self._pygame_coords_to_board_square(mouse_pos)
        if board_coords is None:
            if self.selected_pygame_square: # Si on clique en dehors pour désélectionner
                 self.selected_pygame_square = None
                 self.legal_moves_for_selected_piece = []
            return False

        clicked_row, clicked_col = board_coords
        clicked_chess_square = self._board_square_to_chess_square(clicked_row, clicked_col)
        
        current_player_color = self.chess_logic.get_current_player_color()
        piece_at_click = self.chess_logic.get_board_state().piece_at(clicked_chess_square)
        
        played_a_move_this_click = False

        if self.selected_pygame_square:
            selected_r, selected_c = self.selected_pygame_square
            from_chess_square = self._board_square_to_chess_square(selected_r, selected_c)
            
            promotion_choice = None
            piece_type = self.chess_logic.get_board_state().piece_type_at(from_chess_square)
            
            if piece_type == chess.PAWN:
                if (current_player_color == chess.WHITE and chess.square_rank(clicked_chess_square) == 7) or \
                   (current_player_color == chess.BLACK and chess.square_rank(clicked_chess_square) == 0):
                    promotion_choice = chess.QUEEN
            
            move_to_try = chess.Move(from_chess_square, clicked_chess_square, promotion=promotion_choice)

            if move_to_try in self.legal_moves_for_selected_piece:
                is_capture = self.chess_logic.get_board_state().is_capture(move_to_try)
                is_castling = self.chess_logic.get_board_state().is_castling(move_to_try)
                
                if self.chess_logic.apply_move(move_to_try):
                    played_a_move_this_click = True
                    if promotion_choice: config.play_sound("promote")
                    elif is_castling: config.play_sound("castle")
                    elif is_capture: config.play_sound("capture")
                    else: config.play_sound("move_self")
                    
                    if self.chess_logic.is_in_check():
                        config.play_sound("check")
                    
                    # La vérification de fin de partie et les sons associés sont gérés par GameScreen après le retour
                else: 
                    config.play_sound("illegal_move") # Ne devrait pas arriver si legal_moves est correct

                self.selected_pygame_square = None
                self.legal_moves_for_selected_piece = []
            
            elif piece_at_click and piece_at_click.color == current_player_color:
                self.selected_pygame_square = (clicked_row, clicked_col)
                self.legal_moves_for_selected_piece = self.chess_logic.get_legal_moves_from_square(clicked_chess_square)
            else: 
                self.selected_pygame_square = None
                self.legal_moves_for_selected_piece = []
                if not played_a_move_this_click : config.play_sound("illegal_move") # Si on clique ailleurs qu'un coup légal
        else: 
            if piece_at_click and piece_at_click.color == current_player_color:
                self.selected_pygame_square = (clicked_row, clicked_col)
                self.legal_moves_for_selected_piece = self.chess_logic.get_legal_moves_from_square(clicked_chess_square)
            else: 
                config.play_sound("illegal_move")
        
        return played_a_move_this_click # Indique si un coup a été appliqué

    def _draw_arrow(self, screen, start_pos_px, end_pos_px):
        pygame.draw.line(screen, self.arrow_color, start_pos_px, end_pos_px, self.arrow_thickness)
        angle = math.atan2(start_pos_px[1] - end_pos_px[1], start_pos_px[0] - end_pos_px[0])
        
        # Longueur de la tête de flèche proportionnelle à la taille de la case
        arrow_head_length = config.SQUARE_SIZE * self.arrow_head_size_factor * 2.5 # Ajustez le multiplicateur
        arrow_head_angle_degrees = 30
        arrow_head_angle_rad = math.radians(arrow_head_angle_degrees)

        x1 = end_pos_px[0] + arrow_head_length * math.cos(angle + arrow_head_angle_rad)
        y1 = end_pos_px[1] + arrow_head_length * math.sin(angle + arrow_head_angle_rad)
        x2 = end_pos_px[0] + arrow_head_length * math.cos(angle - arrow_head_angle_rad)
        y2 = end_pos_px[1] + arrow_head_length * math.sin(angle - arrow_head_angle_rad)

        # Créer une surface pour la tête de flèche pour la transparence
        # Cela nécessite de dessiner le polygone avec des coordonnées relatives à cette surface.
        # Ou plus simple, si arrow_color a déjà une composante alpha, pygame.draw.polygon la gère.
        pygame.draw.polygon(screen, self.arrow_color, [end_pos_px, (x1, y1), (x2, y2)])

    def draw(self, screen, best_move_to_show: chess.Move | None = None):
        # 1. Cases
        for r in range(8):
            for c in range(8):
                color = config.COLOR_LIGHT_SQUARE if (r + c) % 2 == 0 else config.COLOR_DARK_SQUARE
                pygame.draw.rect(screen, color, 
                                 (self.x_offset + c * config.SQUARE_SIZE, 
                                  self.y_offset + r * config.SQUARE_SIZE, 
                                  config.SQUARE_SIZE, config.SQUARE_SIZE))

        # 2. Highlights (échec, sélection, coups légaux)
        # Roi en échec (du joueur actuel)
        current_player_color_for_check = self.chess_logic.get_current_player_color() # Le roi qui PEUT être en échec est celui dont c'est le tour
        if self.chess_logic.is_in_check(): 
            king_sq = self.chess_logic.get_king_square(current_player_color_for_check)
            if king_sq is not None:
                r_k, c_k = self._chess_square_to_board_square(king_sq)
                s_check = pygame.Surface((config.SQUARE_SIZE, config.SQUARE_SIZE), pygame.SRCALPHA)
                s_check.fill(config.COLOR_CHECK)
                screen.blit(s_check, (self.x_offset + c_k * config.SQUARE_SIZE, self.y_offset + r_k * config.SQUARE_SIZE))
        
        # Dernier coup joué
        last_move = self.chess_logic.get_last_move()
        if last_move:
            from_r, from_c = self._chess_square_to_board_square(last_move.from_square)
            to_r, to_c = self._chess_square_to_board_square(last_move.to_square)
            highlight_color_last_move = (200, 200, 0, 90) 
            
            s_last = pygame.Surface((config.SQUARE_SIZE, config.SQUARE_SIZE), pygame.SRCALPHA)
            s_last.fill(highlight_color_last_move)
            screen.blit(s_last, (self.x_offset + from_c * config.SQUARE_SIZE, self.y_offset + from_r * config.SQUARE_SIZE))
            screen.blit(s_last, (self.x_offset + to_c * config.SQUARE_SIZE, self.y_offset + to_r * config.SQUARE_SIZE))

        # Case sélectionnée
        if self.selected_pygame_square:
            r_s, c_s = self.selected_pygame_square
            s_sel = pygame.Surface((config.SQUARE_SIZE, config.SQUARE_SIZE), pygame.SRCALPHA)
            s_sel.fill(config.COLOR_SELECTED_SQUARE)
            screen.blit(s_sel, (self.x_offset + c_s * config.SQUARE_SIZE, self.y_offset + r_s * config.SQUARE_SIZE))

        # Mouvements légaux (points et anneaux)
        for move in self.legal_moves_for_selected_piece:
            to_r_lm, to_c_lm = self._chess_square_to_board_square(move.to_square)
            center_x_lm = self.x_offset + to_c_lm * config.SQUARE_SIZE + config.SQUARE_SIZE // 2
            center_y_lm = self.y_offset + to_r_lm * config.SQUARE_SIZE + config.SQUARE_SIZE // 2
            
            if self.chess_logic.get_board_state().is_capture(move):
                pygame.draw.circle(screen, config.COLOR_LEGAL_CAPTURE_RING, (center_x_lm, center_y_lm), 
                                   config.SQUARE_SIZE * 0.45, width=max(2, config.SQUARE_SIZE // 12))
            else:
                pygame.draw.circle(screen, config.COLOR_LEGAL_MOVE_DOT, (center_x_lm, center_y_lm), 
                                   config.SQUARE_SIZE // 7)
        
        # --- FLÈCHE DU MEILLEUR COUP DE STOCKFISH --- (Dessinée avant les pièces)
        if best_move_to_show:
            from_r_bm, from_c_bm = self._chess_square_to_board_square(best_move_to_show.from_square)
            to_r_bm, to_c_bm = self._chess_square_to_board_square(best_move_to_show.to_square)

            start_pos_px = (self.x_offset + from_c_bm * config.SQUARE_SIZE + config.SQUARE_SIZE // 2,
                            self.y_offset + from_r_bm * config.SQUARE_SIZE + config.SQUARE_SIZE // 2)
            end_pos_px = (self.x_offset + to_c_bm * config.SQUARE_SIZE + config.SQUARE_SIZE // 2,
                          self.y_offset + to_r_bm * config.SQUARE_SIZE + config.SQUARE_SIZE // 2)
            
            self._draw_arrow(screen, start_pos_px, end_pos_px)

        # 3. Pièces (dessinées par-dessus tout le reste sur le plateau)
        board_state = self.chess_logic.get_board_state()
        for r_board in range(8):
            for c_board in range(8):
                chess_sq = self._board_square_to_chess_square(r_board, c_board)
                piece = board_state.piece_at(chess_sq)
                if piece:
                    color_char = 'w' if piece.color == chess.WHITE else 'b'
                    image_key = f"{color_char}{piece.symbol().upper()}"
                    image_to_draw = config.PIECE_IMAGES.get(image_key)
                    if image_to_draw:
                        screen.blit(image_to_draw, 
                                    (self.x_offset + c_board * config.SQUARE_SIZE, 
                                     self.y_offset + r_board * config.SQUARE_SIZE))