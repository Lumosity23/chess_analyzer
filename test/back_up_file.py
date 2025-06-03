# ui/main_menu_screen.py
import pygame
import config
from /ui/ui_elements import Button, Label, OptionSelector

class MainMenuScreen:
    def __init__(self, screen_surface, main_app_ref):
        self.screen = screen_surface
        self.main_app = main_app_ref
        self.buttons = []
        self.labels = []
        self.option_selectors = {} # Dictionnaire pour stocker les sélecteurs
        self.expert_mode_enabled = False # Default to False
        self.expert_mode_button = None # Will be initialized in _setup_ui
        
        self._setup_ui()

    def _toggle_expert_mode(self):
        self.expert_mode_enabled = not self.expert_mode_enabled
        button_text_key = "expert_mode_enabled" if self.expert_mode_enabled else "expert_mode_disabled"
        self.expert_mode_button.text = config.TEXT_LABELS[button_text_key]
        # The button's draw method will use its text attribute.
        self._enforce_player_type_rules()

    def _enforce_player_type_rules(self):
        # If expert mode is disabled, prevent AI vs AI
        if not self.expert_mode_enabled:
            white_is_ai = config.CURRENT_GAME_CONFIG["white_player_type"] == config.OPPONENT_AI_STOCKFISH
            black_is_ai = config.CURRENT_GAME_CONFIG["black_player_type"] == config.OPPONENT_AI_STOCKFISH

            if white_is_ai and black_is_ai:
                # Revert Black player to Human
                config.CURRENT_GAME_CONFIG["black_player_type"] = config.OPPONENT_HUMAN
                if "black_player" in self.option_selectors:
                    self.option_selectors["black_player"].set_selected_value(config.OPPONENT_HUMAN)
                print("INFO: AI vs AI disabled. Black player set to Human.")
        
        # If expert mode is enabled, no restrictions.
        # Update player selectors to reflect current config, this handles cases where expert mode is re-enabled
        # or if the initial state needed adjustment.
        if "white_player" in self.option_selectors:
             self.option_selectors["white_player"].set_selected_value(config.CURRENT_GAME_CONFIG["white_player_type"])
        if "black_player" in self.option_selectors:
             self.option_selectors["black_player"].set_selected_value(config.CURRENT_GAME_CONFIG["black_player_type"])

    def _update_game_config(self, key, value):
        """Met à jour la configuration globale du jeu."""
        config.CURRENT_GAME_CONFIG[key] = value
        print(f"Config updated: {key} = {value}")

    def _setup_ui(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        center_x = screen_width // 2
        current_y = screen_height // 4

        title_font = config.STATUS_FONT # Ou une police plus grande
        if not title_font: title_font = pygame.font.SysFont("arial", 60, bold=True)
        
        self.labels.append(Label(center_x, current_y, "Jeu d'Échecs", 
                                 font=title_font, anchor="center"))
        current_y += 80

        # --- Configuration du Temps ---
        self.labels.append(Label(center_x - 250, current_y + 2, "Temps (min)", anchor="topleft"))
        time_options = [("3", 3), ("5", 5), ("10", 10), ("15", 15), ("∞", 0)]
        time_selector = OptionSelector(
            center_x - 50, current_y, time_options,
            config.CURRENT_GAME_CONFIG["time_minutes"],
            on_select_action=lambda val: self._update_game_config("time_minutes", val),
            button_width=60, button_height=40, spacing=5
        )
        self.option_selectors["time"] = time_selector
        current_y += (40 + 30) # Element height (40) + gap (30)

        # --- Configuration Joueur Blanc ---
        self.labels.append(Label(center_x - 175, current_y + 2, "Blancs", anchor="topleft"))
        player_type_options = [("Humain", config.OPPONENT_HUMAN), ("IA (Stockfish)", config.OPPONENT_AI_STOCKFISH)]
        white_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options,
            config.CURRENT_GAME_CONFIG["white_player_type"],
            on_select_action=lambda val: (self._update_game_config("white_player_type", val), self._enforce_player_type_rules()),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["white_player"] = white_player_selector
        current_y += (40 + 30) # Element height (40) + gap (30)

        # --- Configuration Joueur Noir ---
        self.labels.append(Label(center_x - 160, current_y + 2, "Noirs", anchor="topleft"))
        black_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options,
            config.CURRENT_GAME_CONFIG["black_player_type"],
            on_select_action=lambda val: (self._update_game_config("black_player_type", val), self._enforce_player_type_rules()),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["black_player"] = black_player_selector
        current_y += (40 + 30) # Element height (40) + larger gap (40) before main actions

        # --- Expert Mode Toggle ---
        expert_mode_label_y = current_y + 2 # Adjust for centering with button
        self.labels.append(Label(center_x - 250, expert_mode_label_y, config.TEXT_LABELS["expert_mode_label_short"], anchor="topleft"))
        
        initial_expert_button_text_key = "expert_mode_enabled" if self.expert_mode_enabled else "expert_mode_disabled"
        self.expert_mode_button = Button(
            center_x - 50, current_y, 270, 40, # Width for longer text like "AI vs AI: Activé (Risqué!)"
            config.TEXT_LABELS[initial_expert_button_text_key],
            action=self._toggle_expert_mode
        )
        self.buttons.append(self.expert_mode_button) # Add to general buttons list for event handling & drawing
        current_y += (40 + 40) # Element height (40) + larger gap (40) before main actions

        # --- Boutons d'Action ---
        btn_width = 300
        btn_height = 60
        btn_spacing = 25

        # "Jouer" Button
        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y, 
                                   btn_width, btn_height, "Jouer", action=self._start_game))
        current_y += btn_height + btn_spacing # Add button height and spacing

        # "Analyser PGN (Bientôt!)" Button
        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y,
                                   btn_width, btn_height, "Analyser PGN (Bientôt!)", 
                                   action=self._analyze_pgn, enabled=False))
        current_y += btn_height + btn_spacing # Add button height and spacing
        
        # "Quitter" Button
        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y,
                                   btn_width, btn_height, "Quitter", action=self._quit_game))
        # current_y += btn_height # No increment needed after the last button unless more follows
        
        # Initial enforcement of player type rules
        self._enforce_player_type_rules()

    def _start_game(self):
        # Vérifier si au moins un joueur est humain si l'autre est IA, ou les deux humains.
        # Pour l'instant, on permet IA vs IA aussi pour le test.
        print(f"Menu: Démarrage d'une partie avec config: {config.CURRENT_GAME_CONFIG}")
        self.main_app.change_state(config.APP_STATE_IN_GAME)

    def _analyze_pgn(self):
        print("Menu: Analyse PGN (non implémenté).")
        # self.main_app.change_state(config.APP_STATE_PGN_ANALYSIS)
        # Ici, il faudrait ouvrir un sélecteur de fichier ou demander un chemin.

    def _quit_game(self):
        self.main_app.running = False

    def handle_event(self, event):
        for selector in self.option_selectors.values():
            if selector.handle_event(event):
                return
        for button in self.buttons:
            if button.handle_event(event):
                return 

    def update(self):
        pass # Pas d'update logique spécifique pour le menu pour l'instant

    def draw(self):
        self.screen.fill(config.COLOR_BACKGROUND)
        for label in self.labels:
            label.draw(self.screen)
        for selector in self.option_selectors.values():
            selector.draw(self.screen)
        for button in self.buttons:
            button.draw(self.screen)












# ui/main_menu_screen.py
import pygame
import config
from .ui_elements import Button, Label, OptionSelector
import tkinter as tk
from tkinter import filedialog
import chess.pgn # Added for PGN parsing

class MainMenuScreen:
    def __init__(self, screen_surface, main_app_ref):
        self.screen = screen_surface
        self.main_app = main_app_ref
        self.buttons = []
        self.labels = []
        self.option_selectors = {} # Dictionnaire pour stocker les sélecteurs
        self.expert_mode_enabled = False # Default to False
        self.expert_mode_button = None # Will be initialized in _setup_ui
        
        self._setup_ui()

    def _toggle_expert_mode(self):
        self.expert_mode_enabled = not self.expert_mode_enabled
        button_text_key = "expert_mode_enabled" if self.expert_mode_enabled else "expert_mode_disabled"
        self.expert_mode_button.text = config.TEXT_LABELS[button_text_key]
        # The button's draw method will use its text attribute.
        self._enforce_player_type_rules()

    def _enforce_player_type_rules(self):
        # If expert mode is disabled, prevent AI vs AI
        if not self.expert_mode_enabled:
            white_is_ai = config.CURRENT_GAME_CONFIG["white_player_type"] == config.OPPONENT_AI_STOCKFISH
            black_is_ai = config.CURRENT_GAME_CONFIG["black_player_type"] == config.OPPONENT_AI_STOCKFISH

            if white_is_ai and black_is_ai:
                # Revert Black player to Human
                config.CURRENT_GAME_CONFIG["black_player_type"] = config.OPPONENT_HUMAN
                if "black_player" in self.option_selectors:
                    self.option_selectors["black_player"].set_selected_value(config.OPPONENT_HUMAN)
                print("INFO: AI vs AI disabled. Black player set to Human.")
        
        # If expert mode is enabled, no restrictions.
        # Update player selectors to reflect current config, this handles cases where expert mode is re-enabled
        # or if the initial state needed adjustment.
        if "white_player" in self.option_selectors:
             self.option_selectors["white_player"].set_selected_value(config.CURRENT_GAME_CONFIG["white_player_type"])
        if "black_player" in self.option_selectors:
             self.option_selectors["black_player"].set_selected_value(config.CURRENT_GAME_CONFIG["black_player_type"])

    def _update_game_config(self, key, value):
        """Met à jour la configuration globale du jeu."""
        config.CURRENT_GAME_CONFIG[key] = value
        print(f"Config updated: {key} = {value}")

    def _setup_ui(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        center_x = screen_width // 2
        current_y = screen_height // 4

        title_font = config.STATUS_FONT # Ou une police plus grande
        if not title_font: title_font = pygame.font.SysFont("arial", 60, bold=True)
        
        self.labels.append(Label(center_x, current_y, "Jeu d'Échecs", 
                                 font=title_font, anchor="center"))
        current_y += 80

        # --- Configuration du Temps ---
        self.labels.append(Label(center_x - 250, current_y + 2, "Temps (min)", anchor="topleft"))
        time_options = [("3", 3), ("5", 5), ("10", 10), ("15", 15), ("∞", 0)]
        time_selector = OptionSelector(
            center_x - 50, current_y, time_options,
            config.CURRENT_GAME_CONFIG["time_minutes"],
            on_select_action=lambda val: self._update_game_config("time_minutes", val),
            button_width=60, button_height=40, spacing=5
        )
        self.option_selectors["time"] = time_selector
        current_y += (40 + 30) # Element height (40) + gap (30)

        # --- Configuration Joueur Blanc ---
        self.labels.append(Label(center_x - 175, current_y + 2, "Blancs", anchor="topleft"))
        player_type_options = [("Humain", config.OPPONENT_HUMAN), ("IA (Stockfish)", config.OPPONENT_AI_STOCKFISH)]
        white_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options,
            config.CURRENT_GAME_CONFIG["white_player_type"],
            on_select_action=lambda val: (self._update_game_config("white_player_type", val), self._enforce_player_type_rules()),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["white_player"] = white_player_selector
        current_y += (40 + 30) # Element height (40) + gap (30)

        # --- Configuration Joueur Noir ---
        self.labels.append(Label(center_x - 160, current_y + 2, "Noirs", anchor="topleft"))
        black_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options,
            config.CURRENT_GAME_CONFIG["black_player_type"],
            on_select_action=lambda val: (self._update_game_config("black_player_type", val), self._enforce_player_type_rules()),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["black_player"] = black_player_selector
        current_y += (40 + 30) # Element height (40) + larger gap (40) before main actions

        # --- Expert Mode Toggle ---
        expert_mode_label_y = current_y + 2 # Adjust for centering with button
        self.labels.append(Label(center_x - 250, expert_mode_label_y, config.TEXT_LABELS["expert_mode_label_short"], anchor="topleft"))
        
        initial_expert_button_text_key = "expert_mode_enabled" if self.expert_mode_enabled else "expert_mode_disabled"
        self.expert_mode_button = Button(
            center_x - 50, current_y, 270, 40, # Width for longer text like "AI vs AI: Activé (Risqué!)"
            config.TEXT_LABELS[initial_expert_button_text_key],
            action=self._toggle_expert_mode
        )
        self.buttons.append(self.expert_mode_button) # Add to general buttons list for event handling & drawing
        current_y += (40 + 40) # Element height (40) + larger gap (40) before main actions

        # --- Boutons d'Action ---
        btn_width = 300
        btn_height = 60
        btn_spacing = 25

        # "Jouer" Button
        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y, 
                                   btn_width, btn_height, "Jouer", action=self._start_game))
        current_y += btn_height + btn_spacing # Add button height and spacing

        # "Analyser PGN" Button - Enabled
        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y,
                                   btn_width, btn_height, "Analyser PGN", 
                                   action=self._analyze_pgn, enabled=True)) # <-- Changed enabled to True and text
        current_y += btn_height + btn_spacing # Add button height and spacing
        
        # "Quitter" Button
        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y,
                                   btn_width, btn_height, "Quitter", action=self._quit_game))
        # current_y += btn_height # No increment needed after the last button unless more follows
        
        # Initial enforcement of player type rules
        self._enforce_player_type_rules()

    def _start_game(self):
        # Vérifier si au moins un joueur est humain si l'autre est IA, ou les deux humains.
        # Pour l'instant, on permet IA vs IA aussi pour le test.
        print(f"Menu: Démarrage d'une partie avec config: {config.CURRENT_GAME_CONFIG}")
        self.main_app.change_state(config.APP_STATE_IN_GAME)

    def _analyze_pgn(self):
        print("Menu: Analyse PGN cliqué.")
        root = tk.Tk()
        root.withdraw()  # Hide the main tkinter window
        file_path = filedialog.askopenfilename(
            title="Select PGN file",
            filetypes=(("PGN files", "*.pgn"), ("All files", "*.*"))
        )
        root.destroy() # Destroy the tkinter root window after use

        if file_path:
            print(f"PGN file selected: {file_path}")
            try:
                with open(file_path) as pgn_file:
                    game = chess.pgn.read_game(pgn_file)
                    if game:
                        # Placeholder: Process the game object
                        # For example, print all moves
                        print("Game loaded successfully. Moves:")
                        board = game.board()
                        for move in game.mainline_moves():
                            print(board.san(move))
                            board.push(move)
                        
                        # Here you would typically pass the game or moves
                        # to your analysis screen or logic
                        # For now, let's just print a message
                        print("PGN processing complete (placeholder).")
                        # Example: self.main_app.start_pgn_analysis(game) 
                        #          self.main_app.change_state(config.APP_STATE_PGN_ANALYSIS)
                    else:
                        print("Could not parse PGN file or no game found.")
            except Exception as e:
                print(f"Error reading or parsing PGN file: {e}")
        else:
            print("No PGN file selected.")

    def _quit_game(self):
        self.main_app.running = False

    def handle_event(self, event):
        for selector in self.option_selectors.values():
            if selector.handle_event(event):
                return
        for button in self.buttons:
            if button.handle_event(event):
                return 

    def update(self):
        pass # Pas d'update logique spécifique pour le menu pour l'instant

    def draw(self):
        self.screen.fill(config.COLOR_BACKGROUND)
        for label in self.labels:
            label.draw(self.screen)
        for selector in self.option_selectors.values():
            selector.draw(self.screen)
        for button in self.buttons:
            button.draw(self.screen)