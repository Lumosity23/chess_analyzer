# ui/main_menu_screen.py
import pygame
import config
from .ui_elements import Button, Label, OptionSelector

class MainMenuScreen:
    def __init__(self, screen_surface, main_app_ref):
        self.screen = screen_surface
        self.main_app = main_app_ref
        self.buttons = []
        self.labels = []
        self.option_selectors = {} # Dictionnaire pour stocker les sélecteurs

        self._setup_ui()

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
        self.labels.append(Label(center_x - 150, current_y + 20, "Temps (min):", anchor="topleft"))
        time_options = [("3", 3), ("5", 5), ("10", 10), ("15", 15), ("0 (Infini)", 0)]
        time_selector = OptionSelector(
            center_x - 50, current_y, time_options,
            config.CURRENT_GAME_CONFIG["time_minutes"],
            on_select_action=lambda val: self._update_game_config("time_minutes", val),
            button_width=60, button_height=40, spacing=5
        )
        self.option_selectors["time"] = time_selector
        current_y += 60

        # --- Configuration Joueur Blanc ---
        self.labels.append(Label(center_x - 150, current_y + 20, "Blancs:", anchor="topleft"))
        player_type_options = [("Humain", config.OPPONENT_HUMAN), ("IA (Stockfish)", config.OPPONENT_AI_STOCKFISH)]
        white_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options,
            config.CURRENT_GAME_CONFIG["white_player_type"],
            on_select_action=lambda val: self._update_game_config("white_player_type", val),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["white_player"] = white_player_selector
        current_y += 60

        # --- Configuration Joueur Noir ---
        self.labels.append(Label(center_x - 150, current_y + 20, "Noirs:", anchor="topleft"))
        black_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options,
            config.CURRENT_GAME_CONFIG["black_player_type"],
            on_select_action=lambda val: self._update_game_config("black_player_type", val),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["black_player"] = black_player_selector
        current_y += 80

        # --- Boutons d'Action ---
        btn_width = 300
        btn_height = 60
        btn_spacing = 20

        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y, 
                                   btn_width, btn_height, "Jouer", action=self._start_game))
        current_y += btn_height + btn_spacing

        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y,
                                   btn_width, btn_height, "Analyser PGN (Bientôt!)", action=self._analyze_pgn))
        current_y += btn_height + btn_spacing
        
        self.buttons.append(Button( (screen_width - btn_width) // 2, current_y,
                                   btn_width, btn_height, "Quitter", action=self._quit_game))

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