import pygame
import chess
import chess.engine 
import config
import math
# import math # Pas directement besoin de math ici si _eval_to_bar_ratio est ici
from game_logic.chess_board import ChessBoardLogic
from game_logic.player import Player
from .clock_display import ClockDisplay
from .move_history_display import MoveHistoryDisplay
from ui.ui_elements import Button
from engine.stockfish_adapter import StockfishAdapter # Assurez-vous que cet import est correct

class Sidebar:
    def __init__(self, x, y, width, height, 
                 chess_logic: ChessBoardLogic, 
                 player_white: Player, player_black: Player, 
                 game_screen_ref, stockfish_adapter: StockfishAdapter | None):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.chess_logic = chess_logic
        self.player_white = player_white
        self.player_black = player_black
        self.game_screen_ref = game_screen_ref
        self.stockfish_adapter = stockfish_adapter
        
        self.current_stockfish_eval_obj = None # Pour PovScore
        self.current_stockfish_eval_str = "Analyse..." 
        self.best_move_str = "" # Pour la version SAN/UCI du meilleur coup
        self.best_move_object = None # Pour l'objet chess.Move du meilleur coup (pour les flèches)
        
        self.thinking_dots = ""
        self.last_dot_update = pygame.time.get_ticks()

        self.padding = 20 
        clock_height = 60
        buttons_row_height = 50
        
        current_y_pos_relative = self.padding 

        self.clock_black = ClockDisplay(
            self.rect.x + self.padding, self.rect.top + current_y_pos_relative, 
            self.rect.width - 2 * self.padding, clock_height, 
            self.player_black
        )
        current_y_pos_relative += clock_height + self.padding

        self.stockfish_info_y_abs = self.rect.top + current_y_pos_relative
        self.stockfish_info_height = (config.INFO_FONT.get_height() if config.INFO_FONT else 20) * 2 + 10
        current_y_pos_relative += self.stockfish_info_height + self.padding
        
        space_for_bottom_elements = clock_height + buttons_row_height + (2 * self.padding)
        history_height = self.rect.height - current_y_pos_relative - space_for_bottom_elements - self.padding
        history_height = max(50, history_height)

        self.move_history = MoveHistoryDisplay(
            self.rect.x + self.padding, self.rect.top + current_y_pos_relative,
            self.rect.width - 2 * self.padding, history_height,
            self.chess_logic
        )
        current_y_pos_relative += history_height + self.padding
        
        self.clock_white = ClockDisplay(
            self.rect.x + self.padding, self.rect.top + current_y_pos_relative, 
            self.rect.width - 2 * self.padding, clock_height, 
            self.player_white
        )
        
        self.buttons = []
        btn_width = (self.rect.width - 3 * self.padding) // 2 
        
        self.buttons.append(Button(
            self.rect.x + self.padding, 
            self.rect.bottom - self.padding - buttons_row_height, 
            btn_width, buttons_row_height, 
            "Abandonner", 
            action=self.game_screen_ref.handle_resign_button 
        ))
        
        self.buttons.append(Button(
            self.rect.x + self.padding + btn_width + self.padding, 
            self.rect.bottom - self.padding - buttons_row_height, 
            btn_width, buttons_row_height, 
            "Nulle", 
            action=self.game_screen_ref.handle_draw_offer_button
        ))

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if self.move_history.rect.collidepoint(mouse_pos):
            if event.type == pygame.MOUSEBUTTONDOWN and (event.button == 4 or event.button == 5):
                self.move_history.handle_event(event)
                return True

        for button in self.buttons:
            if button.handle_event(event):
                return True
        return False

    def update(self):
        if self.stockfish_adapter and self.stockfish_adapter.engine:
            new_analysis_info = self.stockfish_adapter.get_latest_analysis_info()
            is_analyzing = self.stockfish_adapter.analysis_thread and self.stockfish_adapter.analysis_thread.is_alive()

            if new_analysis_info:
                self.current_stockfish_eval_obj = new_analysis_info.get("score")
                if self.current_stockfish_eval_obj:
                    pov_score = self.current_stockfish_eval_obj.white()
                    if pov_score.is_mate():
                        mate_in = pov_score.mate()
                        self.current_stockfish_eval_str = f"M{'+' if mate_in > 0 else ''}{mate_in}"
                    else:
                        self.current_stockfish_eval_str = f"{pov_score.score(mate_score=10000) / 100.0:+.2f}"
                else:
                    self.current_stockfish_eval_str = "Calcul" + self._get_thinking_dots()

                pv = new_analysis_info.get("pv")
                if pv and self.chess_logic:
                    self.best_move_object = pv[0] # Stocker l'objet chess.Move
                    temp_board = self.chess_logic.get_board_state().copy()
                    try:
                        if pv[0] in temp_board.legal_moves:
                             self.best_move_str = temp_board.san(pv[0])
                        else:
                            self.best_move_str = pv[0].uci() + "?"
                    except Exception:
                        self.best_move_str = pv[0].uci()
                else:
                    self.best_move_str = ""
                    self.best_move_object = None 
            
            elif is_analyzing:
                self.current_stockfish_eval_str = "Analyse" + self._get_thinking_dots()
                # Ne pas effacer self.best_move_object ici, garder le dernier connu
                if not self.best_move_object : self.best_move_str = "..." # Si on n'a jamais eu de best_move
                
        elif self.stockfish_adapter and not self.stockfish_adapter.engine:
             self.current_stockfish_eval_str = "Stockfish ERR"
             self.best_move_str = ""
             self.best_move_object = None
        else:
            self.current_stockfish_eval_str = "Stockfish N/A"
            self.best_move_str = ""
            self.best_move_object = None

    def _get_thinking_dots(self):
        now = pygame.time.get_ticks()
        if now - self.last_dot_update > 300: 
            self.last_dot_update = now
            self.thinking_dots = "." * ((len(self.thinking_dots) % 3) + 1)
        return self.thinking_dots

    def draw(self, screen):
        pygame.draw.rect(screen, config.COLOR_SIDEBAR_BACKGROUND, self.rect)
        current_player_turn = self.chess_logic.get_current_player_color()
        
        self.clock_black.draw(screen, current_player_turn == chess.BLACK)

        if self.stockfish_adapter and config.INFO_FONT:
            eval_surf = config.INFO_FONT.render(self.current_stockfish_eval_str, True, config.COLOR_TEXT)
            eval_rect = eval_surf.get_rect(left=self.rect.x + self.padding, top=self.stockfish_info_y_abs)
            screen.blit(eval_surf, eval_rect)

            if self.best_move_str:
                best_move_surf = config.INFO_FONT.render(f"Meilleur: {self.best_move_str}", True, config.COLOR_TEXT)
                best_move_rect = best_move_surf.get_rect(
                    left=self.rect.x + self.padding, 
                    top=self.stockfish_info_y_abs + config.INFO_FONT.get_height() + 5
                )
                screen.blit(best_move_surf, best_move_rect)
        
        self.move_history.draw(screen)
        self.clock_white.draw(screen, current_player_turn == chess.WHITE)
        
        for button in self.buttons:
            button.draw(screen)

    def get_white_bar_ratio(self) -> float:
        if self.current_stockfish_eval_obj:
            # Utiliser math.tanh pour une courbe plus "standard" pour la barre d'évaluation
            # PovScore.score() donne des centipions. Mate est géré séparément.
            score = self.current_stockfish_eval_obj.white()
            if score.is_mate():
                return 1.0 if score.mate() > 0 else 0.0 # Blanc matant ou maté
            
            # On veut que le score soit normalisé. Par exemple, un score de X donne un avantage Y.
            # Un score de 200cp (2 pions) est souvent un avantage significatif.
            # k * score_cp. 
            # tanh(k * score_cp) varie de -1 à 1. On veut ramener ça à [0, 1].
            # (tanh(k * score_cp) + 1) / 2
            k = 0.0027 # Facteur pour que +/-200cp soit ~75%/25% (tanh(0.54) ~ 0.5)
                      # tanh(1) ~ 0.76. Si on veut que 500cp soit 0.9 (tanh(X)=0.8 => X=1.09)
                      # k = 1.09 / 500 = 0.00218
            k_factor = 0.0025 # Ajustez ce facteur
            normalized_score = k_factor * score.score(mate_score=10000) # mate_score pour éviter crash si mate est proche
            
            # Utilisation de tanh pour une courbe en S
            # tanh varie entre -1 et 1. On la mappe sur [0, 1]
            # (tanh(x) + 1) / 2
            try:
                # math.tanh a été introduit en Python 3. Pour compatibilité plus large,
                # on peut l'implémenter avec exp ou utiliser une approximation.
                # Pour Python 3.x standard, math.tanh est disponible.
                ratio = (math.tanh(normalized_score) + 1) / 2.0
            except AttributeError: # Si math.tanh n'existe pas (vieux Python, peu probable)
                # Approximation simple de tanh pour des petites valeurs : x - x^3/3 ...
                # Ou fallback à la méthode linéaire précédente
                max_visible_advantage_cp = 600 
                clamped_score_cp = max(-max_visible_advantage_cp, min(max_visible_advantage_cp, score.score(mate_score=10000)))
                ratio = (clamped_score_cp / max_visible_advantage_cp) * 0.5 + 0.5
            
            return max(0.0, min(1.0, ratio))
        return 0.5

    def _eval_to_bar_ratio(self, pov_score: chess.engine.PovScore | None) -> float:
        # Cette méthode est maintenant un wrapper si on veut garder l'ancien nom,
        # mais get_white_bar_ratio est plus spécifique.
        # Ou on peut simplement supprimer _eval_to_bar_ratio et renommer get_white_bar_ratio
        if pov_score is None:
            return 0.5 
        # ... (ancienne logique linéaire si vous préférez la garder comme option)
        # Pour utiliser la nouvelle logique tanh, assurez-vous que get_white_bar_ratio est appelée.
        # Pour cet exemple, je vais supposer que get_white_bar_ratio est la méthode principale.
        # Si vous appelez _eval_to_bar_ratio, elle doit contenir la logique de conversion.
        # Par souci de clarté, je vais mettre la logique tanh dans get_white_bar_ratio.
        # Cette fonction devient donc redondante si get_white_bar_ratio fait le travail.
        # Pour l'instant, laissons get_white_bar_ratio faire le travail.
        # Si vous aviez une raison de garder les deux, il faudrait clarifier leur usage.
        print("ATTENTION: _eval_to_bar_ratio est appelée, préférez get_white_bar_ratio")
        return self.get_white_bar_ratio() # Délégué pour l'instant