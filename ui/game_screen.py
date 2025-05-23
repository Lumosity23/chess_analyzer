import pygame
import chess
import config 
from game_logic.chess_board import ChessBoardLogic
from game_logic.player import Player
from .components.board_display import BoardDisplay
from .components.sidebar import Sidebar
from engine.stockfish_adapter import StockfishAdapter
from .ui_elements import Button

class GameScreen:
    def __init__(self, screen_surface, game_config: dict):
        # ... (votre __init__ existant et correct) ...
        self.screen = screen_surface
        self.game_config = game_config 
        self.chess_logic = ChessBoardLogic()
        
        time_minutes = self.game_config.get("time_minutes", config.DEFAULT_GAME_TIME_MINUTES)
        initial_time_ms = time_minutes * 60 * 1000 if time_minutes > 0 else float('inf')

        self.player_white_type = self.game_config.get("white_player_type", config.OPPONENT_HUMAN)
        self.player_black_type = self.game_config.get("black_player_type", config.OPPONENT_HUMAN)

        self.player_white = Player(chess.WHITE, "Blancs", initial_time_ms, is_human=(self.player_white_type == config.OPPONENT_HUMAN))
        self.player_black = Player(chess.BLACK, "Noirs", initial_time_ms, is_human=(self.player_black_type == config.OPPONENT_HUMAN))
        self.current_active_player_object = self.player_white

        self.stockfish_adapter = StockfishAdapter()

        self.eval_bar_x = config.MAIN_PADDING
        self.eval_bar_y = config.MAIN_PADDING + config.COORDINATE_SPACE 
        self.eval_bar_height = config.BOARD_SIZE_PX 
        
        board_x_offset_for_coords = self.eval_bar_x + config.EVAL_BAR_WIDTH + config.MAIN_PADDING
        board_y_offset_for_coords = self.eval_bar_y 
        
        self.board_display_x_offset = board_x_offset_for_coords + config.COORDINATE_SPACE
        self.board_display_y_offset = board_y_offset_for_coords
        
        self.board_display = BoardDisplay(
            self.board_display_x_offset, 
            self.board_display_y_offset, 
            self.chess_logic
        )

        sidebar_x_offset = self.board_display_x_offset + config.BOARD_SIZE_PX + config.COORDINATE_SPACE + config.MAIN_PADDING
        sidebar_y_offset = config.MAIN_PADDING
        sidebar_height = config.TOTAL_HEIGHT - (2 * config.MAIN_PADDING)
        
        self.sidebar = Sidebar(sidebar_x_offset, sidebar_y_offset, 
                               config.SIDEBAR_WIDTH, sidebar_height, 
                               self.chess_logic, self.player_white, self.player_black, 
                               self, self.stockfish_adapter)
        
        self.last_tick_time = pygame.time.get_ticks()
        if self.stockfish_adapter and self.stockfish_adapter.engine:
            self.stockfish_adapter.start_analysis(self.chess_logic.get_board_state())

        self.game_over_popup_active = False
        self.game_over_message_text = ""
        self.popup_buttons = []
        self.main_app_ref = None

    def set_main_app_ref(self, main_app_ref):
        self.main_app_ref = main_app_ref

    # --- MÉTHODE _draw_board_coordinates À AJOUTER/REMPLACER ---
    def _draw_board_coordinates(self):
        """Dessine les lettres (A-H) et les chiffres (1-8) autour du plateau."""
        if not config.COORDINATE_FONT:
            print("ATTENTION: COORDINATE_FONT non chargé, impossible de dessiner les coordonnées.")
            return

        files = "ABCDEFGH"
        # Coordonnées X et Y où le dessin des 64 cases du plateau commence effectivement
        board_actual_draw_x = self.board_display_x_offset
        board_actual_draw_y = self.board_display_y_offset

        # Lettres (A-H)
        for i, letter in enumerate(files):
            # Couleur en fonction de la case adjacente pour un meilleur contraste/style
            # Lettres en bas
            text_color_bottom = config.COLOR_COORDINATES_LIGHT if (i % 2 == 0) else config.COLOR_COORDINATES_DARK 
            text_surface_bottom = config.COORDINATE_FONT.render(letter, True, text_color_bottom)
            text_rect_bottom = text_surface_bottom.get_rect(
                centerx = board_actual_draw_x + i * config.SQUARE_SIZE + config.SQUARE_SIZE // 2,
                centery = board_actual_draw_y + config.BOARD_SIZE_PX + config.COORDINATE_SPACE // 2
            )
            self.screen.blit(text_surface_bottom, text_rect_bottom)
            
            # Lettres en haut
            # La case (0,0) du plateau (A8) est claire si (0+0)%2 == 0. La couleur de la coordonnée sera foncée.
            # Pour A (i=0), la case H8 (i=7, r=0) (7+0)%2 !=0 -> foncée -> coord claire
            # Pour H (i=7), la case A8 (i=0, r=0) (0+0)%2 ==0 -> claire -> coord foncée
            # La couleur de la case (col, row) est claire si (col+row)%2==0
            # Pour les lettres en haut, la rangée de référence est la 8ème (index 0 pour le calcul de couleur de case)
            # Case A8 (col=0, row=0) -> claire. Lettre A -> couleur foncée
            text_color_top = config.COLOR_COORDINATES_DARK if (i % 2 == 0) else config.COLOR_COORDINATES_LIGHT
            text_surface_top = config.COORDINATE_FONT.render(letter, True, text_color_top)
            text_rect_top = text_surface_top.get_rect(
                centerx = board_actual_draw_x + i * config.SQUARE_SIZE + config.SQUARE_SIZE // 2,
                centery = board_actual_draw_y - config.COORDINATE_SPACE // 2
            )
            self.screen.blit(text_surface_top, text_rect_top)

        # Chiffres (1-8)
        for i in range(8): # i va de 0 (rangée 8) à 7 (rangée 1)
            rank_number_str = str(8 - i) 
            # Chiffres à gauche
            # La case A8 (col=0, row=0) est claire. Chiffre 8 -> couleur foncée
            text_color_left = config.COLOR_COORDINATES_DARK if (i % 2 == 0) else config.COLOR_COORDINATES_LIGHT
            text_surface_left = config.COORDINATE_FONT.render(rank_number_str, True, text_color_left)
            text_rect_left = text_surface_left.get_rect(
                centerx = board_actual_draw_x - config.COORDINATE_SPACE // 2,
                centery = board_actual_draw_y + i * config.SQUARE_SIZE + config.SQUARE_SIZE // 2
            )
            self.screen.blit(text_surface_left, text_rect_left)
            
            # Chiffres à droite
            # La case H8 (col=7, row=0) est foncée. Chiffre 8 -> couleur claire
            text_color_right = config.COLOR_COORDINATES_LIGHT if (i % 2 == 0) else config.COLOR_COORDINATES_DARK
            text_surface_right = config.COORDINATE_FONT.render(rank_number_str, True, text_color_right)
            text_rect_right = text_surface_right.get_rect(
                centerx = board_actual_draw_x + config.BOARD_SIZE_PX + config.COORDINATE_SPACE // 2,
                centery = board_actual_draw_y + i * config.SQUARE_SIZE + config.SQUARE_SIZE // 2
            )
            self.screen.blit(text_surface_right, text_rect_right)

    # --- MÉTHODE _draw_vertical_eval_bar À AJOUTER/REMPLACER ---
    def _draw_vertical_eval_bar(self):
        if not (self.stockfish_adapter and self.stockfish_adapter.engine and self.sidebar):
            bar_rect = pygame.Rect(self.eval_bar_x, self.eval_bar_y, config.EVAL_BAR_WIDTH, self.eval_bar_height)
            pygame.draw.rect(self.screen, (80, 80, 80), bar_rect, border_radius=3)
            return

        ratio_white = self.sidebar.get_white_bar_ratio() 
        white_height = int(self.eval_bar_height * ratio_white)
        black_height = self.eval_bar_height - white_height

        white_rect = pygame.Rect(self.eval_bar_x, self.eval_bar_y + black_height, config.EVAL_BAR_WIDTH, white_height)
        black_rect = pygame.Rect(self.eval_bar_x, self.eval_bar_y, config.EVAL_BAR_WIDTH, black_height)

        br_all = 3 # Rayon de base pour les coins arrondis

        # Dessiner la partie noire (en haut si les blancs ont l'avantage, ou toute la barre si noirs gagnent)
        if black_height == self.eval_bar_height: # Toute noire
            pygame.draw.rect(self.screen, (60, 60, 60), black_rect, border_radius=br_all)
        elif black_height > 0 :
            pygame.draw.rect(self.screen, (60, 60, 60), black_rect, 
                             border_top_left_radius=br_all, border_top_right_radius=br_all)
        
        # Dessiner la partie blanche (en bas si les blancs ont l'avantage, ou toute la barre si blancs gagnent)
        if white_height == self.eval_bar_height: # Toute blanche
            pygame.draw.rect(self.screen, (220, 220, 220), white_rect, border_radius=br_all)
        elif white_height > 0:
             pygame.draw.rect(self.screen, (220, 220, 220), white_rect,
                             border_bottom_left_radius=br_all, border_bottom_right_radius=br_all)
        
        # Si les deux existent, s'assurer que la jonction est droite
        if white_height > 0 and black_height > 0:
            # On a déjà dessiné les parties avec les bons coins externes.
            # La jonction interne sera naturellement droite.
            pass


    def draw(self): # L'appel à _draw_board_coordinates était déjà là, on s'assure que la méthode existe
        self.screen.fill(config.COLOR_BACKGROUND)
        self._draw_vertical_eval_bar() 
        self._draw_board_coordinates() # Appel à la méthode que nous venons de définir
        
        best_move_for_arrow = self.sidebar.best_move_object if self.sidebar else None
        self.board_display.draw(self.screen, best_move_for_arrow)
        
        self.sidebar.draw(self.screen)
        
        status_text_to_display = None
        if self.chess_logic.is_game_over() and not self.game_over_popup_active :
             status_text_to_display = self.chess_logic.get_game_status_message()
        elif self.chess_logic.is_in_check() and not self.chess_logic.is_game_over():
            status_text_to_display = "ÉCHEC !"
        
        if status_text_to_display and config.STATUS_FONT:
            text_color = (255,60,60) if "ÉCHEC !" in status_text_to_display else config.COLOR_TEXT
            text_surf = config.STATUS_FONT.render(status_text_to_display, True, text_color)
            # Centrer le message sous la zone du plateau (incluant les coordonnées)
            center_x_board_area = self.board_display_x_offset + config.BOARD_SIZE_PX // 2
            bottom_of_board_area = self.board_display_y_offset + config.BOARD_SIZE_PX + config.COORDINATE_SPACE
            text_rect = text_surf.get_rect(
                centerx=center_x_board_area, 
                top= bottom_of_board_area + config.MAIN_PADDING // 2 # Un peu d'espace sous les coordonnées
            )
            self.screen.blit(text_surf, text_rect)

        if self.game_over_popup_active:
            self._draw_game_over_popup()


    def _is_current_player_ai(self) -> bool:
        player_color = self.chess_logic.get_current_player_color()
        if player_color == chess.WHITE:
            return self.player_white_type == config.OPPONENT_AI_STOCKFISH
        else:
            return self.player_black_type == config.OPPONENT_AI_STOCKFISH

    def _ai_play_move(self):
        if not self.stockfish_adapter or not self.stockfish_adapter.engine:
            print("Tentative de coup IA sans moteur Stockfish actif.")
            return

        board_state = self.chess_logic.get_board_state()
        # Utiliser une limite de temps plus courte pour que l'IA joue rapidement
        # ou utiliser les paramètres de difficulté de Stockfish si configurés.
        best_move = self.stockfish_adapter.get_best_move_from_engine(board_state, time_limit_ms=500) # 0.5s pour jouer

        if best_move:
            is_capture = self.chess_logic.get_board_state().is_capture(best_move)
            is_castling = self.chess_logic.get_board_state().is_castling(best_move)
            is_promotion = best_move.promotion is not None # Vérifier si c'est une promotion

            if self.chess_logic.apply_move(best_move):
                print(f"IA ({self.current_active_player_object.name}) joue: {board_state.san(best_move)}")
                # Sons pour l'IA (on pourrait utiliser "move_opponent")
                if is_promotion: config.play_sound("promote")
                elif is_castling: config.play_sound("castle")
                elif is_capture: config.play_sound("capture")
                else: config.play_sound("move_opponent") # Son différent pour l'IA
                
                if self.chess_logic.is_in_check():
                    config.play_sound("check")
                
                # Mettre à jour le joueur actif et relancer l'analyse pour le joueur humain (ou l'autre IA)
                self.current_active_player_object = self.player_black if self.chess_logic.get_current_player_color() == chess.BLACK else self.player_white
                self.last_tick_time = pygame.time.get_ticks()
                if self.stockfish_adapter and self.stockfish_adapter.engine:
                    self.stockfish_adapter.start_analysis(self.chess_logic.get_board_state())
                self._check_game_end_condition() # Vérifier si la partie est finie après le coup de l'IA
            else:
                print(f"ERREUR: L'IA a tenté un coup illégal: {best_move}")
        else:
            print("ERREUR: L'IA (Stockfish) n'a pas retourné de coup.")
            # Potentiellement mat ou pat, ou erreur moteur

    def _check_game_end_condition(self):
        if self.chess_logic.is_game_over() and not self.game_over_popup_active:
            self.game_over_message_text = self.chess_logic.get_game_status_message()
            if not self.game_over_message_text: # Au cas où get_game_status_message ne couvre pas tous les cas
                outcome = self.chess_logic.board.outcome()
                if outcome:
                    if outcome.winner == chess.WHITE: self.game_over_message_text = "Les Blancs gagnent !"
                    elif outcome.winner == chess.BLACK: self.game_over_message_text = "Les Noirs gagnent !"
                    else: self.game_over_message_text = "Partie Nulle !"
                else:
                    self.game_over_message_text = "Partie Terminée" # Fallback

            self.show_game_over_popup()


    def show_game_over_popup(self):
        self.game_over_popup_active = True
        self.popup_buttons = [] # Réinitialiser les boutons du popup
        
        # Bouton "Retour au Menu" pour le popup
        popup_center_x = config.TOTAL_SCREEN_WIDTH // 2
        popup_center_y = config.TOTAL_HEIGHT // 2
        btn_width, btn_height = 200, 50

        def action_back_to_menu():
            if self.main_app_ref: # S'assurer que la référence existe
                self.main_app_ref.change_state(config.APP_STATE_MAIN_MENU)
            self.game_over_popup_active = False # Cacher le popup

        self.popup_buttons.append(Button(
            popup_center_x - btn_width // 2,
            popup_center_y + 40, # Sous le texte du message
            btn_width, btn_height,
            "Menu Principal",
            action=action_back_to_menu
        ))

    def handle_event(self, event):
        if self.game_over_popup_active:
            for button in self.popup_buttons:
                if button.handle_event(event):
                    return # L'événement est pour le popup
            # Si clic en dehors des boutons du popup, ne rien faire ou fermer le popup
            if event.type == pygame.MOUSEBUTTONDOWN: return 
        
        # Si la partie est terminée (mais le popup n'est pas encore géré)
        if self.chess_logic.is_game_over():
            return # Ne plus traiter les événements de jeu

        # --- Gestion normale des événements ---
        mouse_pos_sidebar_check = pygame.mouse.get_pos()
        is_on_sidebar = mouse_pos_sidebar_check[0] >= self.sidebar.rect.left

        if is_on_sidebar:
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEWHEEL:
                # Simuler MOUSEBUTTONDOWN pour MOUSEWHEEL pour la sidebar
                event_to_pass = event
                if event.type == pygame.MOUSEWHEEL:
                    button_to_simulate = 4 if event.y > 0 else 5
                    event_to_pass = pygame.event.Event(pygame.MOUSEBUTTONDOWN, 
                                                        button=button_to_simulate, 
                                                        pos=mouse_pos_sidebar_check)
                if self.sidebar.handle_event(event_to_pass):
                    return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Clic gauche
                if not is_on_sidebar and not self._is_current_player_ai(): # Clic sur le plateau et c'est au tour de l'humain
                    if self.board_display.handle_click(event.pos): # Si un coup a été fait par l'humain
                        if self.chess_logic.last_move: 
                            self.current_active_player_object = self.player_black if self.chess_logic.get_current_player_color() == chess.BLACK else self.player_white
                            self.last_tick_time = pygame.time.get_ticks()
                            if self.stockfish_adapter and self.stockfish_adapter.engine:
                                self.stockfish_adapter.start_analysis(self.chess_logic.get_board_state())
                            self._check_game_end_condition() # Vérifier fin après coup humain
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_u: 
                if not self._is_current_player_ai(): # L'humain peut annuler son coup (et celui de l'IA)
                    # Annuler deux fois si l'IA a joué entre-temps ? Logique à affiner.
                    # Pour l'instant, annule juste le dernier coup.
                    if self.chess_logic.undo_move():
                        self.current_active_player_object = self.player_black if self.chess_logic.get_current_player_color() == chess.BLACK else self.player_white
                        self.last_tick_time = pygame.time.get_ticks() 
                        if self.stockfish_adapter and self.stockfish_adapter.engine:
                            self.stockfish_adapter.start_analysis(self.chess_logic.get_board_state())
                        print("Coup annulé.")
            elif event.key == pygame.K_r: 
                if self.main_app_ref: # Pour redémarrer proprement via le MainApp et le menu
                    self.main_app_ref.change_state(config.APP_STATE_MAIN_MENU) 
                # else: # Fallback si pas de réf (redémarre juste GameScreen)
                #     self.__init__(self.screen, self.game_config)
                #     config.play_sound("game_start")

    def update(self):
        if self.chess_logic.is_game_over() or self.game_over_popup_active:
            # Pas de mise à jour de l'horloge ou de l'IA si la partie est finie ou popup actif
            self.sidebar.update() # La sidebar peut continuer à mettre à jour l'affichage de l'eval
            return

        current_time = pygame.time.get_ticks()
        delta_time_ms = current_time - self.last_tick_time 
        
        if delta_time_ms > 0 and self.current_active_player_object.time_left_ms != float('inf'):
            self.current_active_player_object.decrease_time(delta_time_ms)
            if self.current_active_player_object.is_timed_out:
                print(f"TEMPS ÉCOULÉ pour {self.current_active_player_object.name}!")
                winner = chess.BLACK if self.current_active_player_object.color == chess.WHITE else chess.WHITE
                self.chess_logic.game_over_flag = True
                self.chess_logic.outcome = chess.Outcome(termination=chess.Termination.TIME_FORFEIT, winner=winner)
                if self.current_active_player_object.color == chess.WHITE: config.play_sound("game_lose") 
                else: config.play_sound("game_win")
                self._check_game_end_condition() # Déclencher le popup
        self.last_tick_time = current_time
        
        self.sidebar.update()
        
        # Tour de l'IA
        if not self.chess_logic.is_game_over() and self._is_current_player_ai():
            self._ai_play_move()

    def _draw_game_over_popup(self):
        popup_width, popup_height = 400, 200
        popup_rect = pygame.Rect(
            (config.TOTAL_WIDTH - popup_width) // 2,
            (config.TOTAL_HEIGHT - popup_height) // 2,
            popup_width, popup_height
        )
        pygame.draw.rect(self.screen, config.COLOR_SIDEBAR_BACKGROUND, popup_rect, border_radius=10)
        pygame.draw.rect(self.screen, config.COLOR_TEXT, popup_rect, width=2, border_radius=10)

        if config.STATUS_FONT:
            message_surf = config.STATUS_FONT.render(self.game_over_message_text, True, config.COLOR_TEXT)
            message_rect = message_surf.get_rect(center=(popup_rect.centerx, popup_rect.centery - 30))
            self.screen.blit(message_surf, message_rect)
        
        for button in self.popup_buttons:
            button.draw(self.screen)

    # ... (handle_resign_button, handle_draw_offer_button) ...
    def handle_resign_button(self): # Doit maintenant vérifier si la partie est finie avant d'agir
        if not self.chess_logic.is_game_over():
            current_player_resigning = self.chess_logic.get_current_player_color()
            winner = chess.BLACK if current_player_resigning == chess.WHITE else chess.WHITE
            self.chess_logic.game_over_flag = True
            self.chess_logic.outcome = chess.Outcome(termination=chess.Termination.RESIGNATION, winner=winner)
            if current_player_resigning == chess.WHITE: config.play_sound("game_lose")
            else: config.play_sound("game_win")
            self._check_game_end_condition()

    def handle_draw_offer_button(self): # Idem
        if not self.chess_logic.is_game_over():
            # Dans un vrai jeu, l'autre joueur doit accepter. Ici on force la nulle.
            print("Partie déclarée nulle par accord.")
            self.chess_logic.game_over_flag = True
            self.chess_logic.outcome = chess.Outcome(termination=chess.Termination.AGREEMENT, winner=None)
            config.play_sound("game_draw")
            self._check_game_end_condition()

    def on_exit(self):
        if self.stockfish_adapter:
            self.stockfish_adapter.close()