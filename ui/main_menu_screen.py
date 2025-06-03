# ui/main_menu_screen.py
import pygame
import config
from .ui_elements import Button, Label, OptionSelector
# import tkinter as tk # No longer needed
# from tkinter import filedialog # No longer needed
import chess.pgn
import pygame_gui # Added for pygame-gui

class MainMenuScreen:
    def __init__(self, screen_surface, main_app_ref):
        self.screen = screen_surface
        self.main_app = main_app_ref
        self.buttons = []
        self.labels = []
        self.option_selectors = {}
        self.expert_mode_enabled = False
        self.expert_mode_button = None
        
        # Pygame-GUI setup
        self.ui_manager = pygame_gui.UIManager((config.TOTAL_SCREEN_WIDTH, config.TOTAL_HEIGHT), 'theme.json' if config.USE_THEME else None)
        self.file_dialog = None # To store the file dialog instance

        self._setup_ui()

    def _toggle_expert_mode(self):
        self.expert_mode_enabled = not self.expert_mode_enabled
        button_text_key = "expert_mode_enabled" if self.expert_mode_enabled else "expert_mode_disabled"
        self.expert_mode_button.text = config.TEXT_LABELS[button_text_key]
        self._enforce_player_type_rules()

    def _enforce_player_type_rules(self):
        if not self.expert_mode_enabled:
            white_is_ai = config.CURRENT_GAME_CONFIG["white_player_type"] == config.OPPONENT_AI_STOCKFISH
            black_is_ai = config.CURRENT_GAME_CONFIG["black_player_type"] == config.OPPONENT_AI_STOCKFISH
            if white_is_ai and black_is_ai:
                config.CURRENT_GAME_CONFIG["black_player_type"] = config.OPPONENT_HUMAN
                if "black_player" in self.option_selectors:
                    self.option_selectors["black_player"].set_selected_value(config.OPPONENT_HUMAN)
                print("INFO: AI vs AI disabled. Black player set to Human.")
        if "white_player" in self.option_selectors:
             self.option_selectors["white_player"].set_selected_value(config.CURRENT_GAME_CONFIG["white_player_type"])
        if "black_player" in self.option_selectors:
             self.option_selectors["black_player"].set_selected_value(config.CURRENT_GAME_CONFIG["black_player_type"])

    def _update_game_config(self, key, value):
        config.CURRENT_GAME_CONFIG[key] = value
        print(f"Config updated: {key} = {value}")

    def _setup_ui(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        center_x = screen_width // 2
        current_y = screen_height // 4

        title_font = config.STATUS_FONT
        if not title_font: title_font = pygame.font.SysFont("arial", 60, bold=True)
        
        self.labels.append(Label(center_x, current_y, "Jeu d'Échecs", font=title_font, anchor="center"))
        current_y += 80

        self.labels.append(Label(center_x - 250, current_y + 2, "Temps (min)", anchor="topleft"))
        time_options = [("3", 3), ("5", 5), ("10", 10), ("15", 15), ("∞", 0)]
        time_selector = OptionSelector(
            center_x - 50, current_y, time_options, config.CURRENT_GAME_CONFIG["time_minutes"],
            on_select_action=lambda val: self._update_game_config("time_minutes", val),
            button_width=60, button_height=40, spacing=5
        )
        self.option_selectors["time"] = time_selector
        current_y += (40 + 30)

        self.labels.append(Label(center_x - 175, current_y + 2, "Blancs", anchor="topleft"))
        player_type_options = [("Humain", config.OPPONENT_HUMAN), ("IA (Stockfish)", config.OPPONENT_AI_STOCKFISH)]
        white_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options, config.CURRENT_GAME_CONFIG["white_player_type"],
            on_select_action=lambda val: (self._update_game_config("white_player_type", val), self._enforce_player_type_rules()),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["white_player"] = white_player_selector
        current_y += (40 + 30)

        self.labels.append(Label(center_x - 160, current_y + 2, "Noirs", anchor="topleft"))
        black_player_selector = OptionSelector(
            center_x - 50, current_y, player_type_options, config.CURRENT_GAME_CONFIG["black_player_type"],
            on_select_action=lambda val: (self._update_game_config("black_player_type", val), self._enforce_player_type_rules()),
            button_width=150, button_height=40, spacing=10
        )
        self.option_selectors["black_player"] = black_player_selector
        current_y += (40 + 30)

        expert_mode_label_y = current_y + 2
        self.labels.append(Label(center_x - 250, expert_mode_label_y, config.TEXT_LABELS["expert_mode_label_short"], anchor="topleft"))
        initial_expert_button_text_key = "expert_mode_enabled" if self.expert_mode_enabled else "expert_mode_disabled"
        self.expert_mode_button = Button(
            center_x - 50, current_y, 270, 40, config.TEXT_LABELS[initial_expert_button_text_key],
            action=self._toggle_expert_mode
        )
        self.buttons.append(self.expert_mode_button)
        current_y += (40 + 40)

        btn_width = 300
        btn_height = 60
        btn_spacing = 25

        self.buttons.append(Button((screen_width - btn_width) // 2, current_y, btn_width, btn_height, "Jouer", action=self._start_game))
        current_y += btn_height + btn_spacing

        # "Analyser PGN" Button - Still uses your custom Button class for now
        # The action _analyze_pgn will now trigger the pygame-gui file dialog
        self.buttons.append(Button((screen_width - btn_width) // 2, current_y, btn_width, btn_height, "Analyser PGN", 
                                   action=self._analyze_pgn, enabled=True))
        current_y += btn_height + btn_spacing
        
        self.buttons.append(Button((screen_width - btn_width) // 2, current_y, btn_width, btn_height, "Quitter", action=self._quit_game))
        
        self._enforce_player_type_rules()

    def _start_game(self):
        print(f"Menu: Démarrage d'une partie avec config: {config.CURRENT_GAME_CONFIG}")
        self.main_app.change_state(config.APP_STATE_IN_GAME)

    def _analyze_pgn(self):
        print("Menu: Analyse PGN cliqué. Affichage du sélecteur de fichier pygame-gui.")
        # Close existing dialog if any
        if self.file_dialog:
            self.file_dialog.kill()
            self.file_dialog = None

        # Make the dialog larger: 80% of screen width, 70% of screen height
        dialog_width = int(config.TOTAL_SCREEN_WIDTH * 0.8)
        dialog_height = int(config.TOTAL_HEIGHT * 0.7)

        self.file_dialog = pygame_gui.windows.UIFileDialog(
            rect=pygame.Rect((0, 0), (dialog_width, dialog_height)), # Adjusted size
            manager=self.ui_manager,
            window_title='Select PGN File',
            initial_file_path='.', 
            allow_picking_directories=False,
            allow_existing_files_only=True,
            allowed_suffixes={".pgn"}
        )
        # Center the dialog
        self.file_dialog.set_relative_position(((config.TOTAL_SCREEN_WIDTH - self.file_dialog.rect.width) // 2,
                                                (config.TOTAL_HEIGHT - self.file_dialog.rect.height) // 2))

    def _process_selected_pgn(self, file_path):
        if file_path:
            print(f"PGN file selected via pygame-gui: {file_path}")
            try:
                with open(file_path) as pgn_file:
                    game = chess.pgn.read_game(pgn_file)
                    if game:
                        print("Game loaded successfully. Moves:")
                        board = game.board()
                        for move in game.mainline_moves():
                            print(board.san(move))
                            board.push(move)
                        print("PGN processing complete (placeholder).")
                        # config.CURRENT_GAME_CONFIG["pgn_filepath"] = file_path # Store for analysis screen
                        # self.main_app.change_state(config.APP_STATE_PGN_ANALYSIS) # Uncomment when ready
                    else:
                        print("Could not parse PGN file or no game found.")
            except Exception as e:
                print(f"Error reading or parsing PGN file: {e}")
        else:
            print("No PGN file selected or dialog cancelled.")
        self.file_dialog = None # Clear the dialog instance

    def _quit_game(self):
        self.main_app.running = False

    def handle_event(self, event):
        # Pass events to pygame-gui UIManager first.
        # It returns True if the event is consumed by a pygame-gui element.
        event_consumed_by_manager = self.ui_manager.process_events(event)

        if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
            if event.ui_element == self.file_dialog:
                self._process_selected_pgn(event.text)
                return True  # Event handled by file dialog selection

        if event.type == pygame_gui.UI_WINDOW_CLOSE: # Handle dialog close button (e.g., 'X')
            if event.ui_element == self.file_dialog:
                print("File dialog closed by user via close button.")
                self.file_dialog = None # Clear dialog instance
                return True # Event handled by closing the dialog

        # If the event was consumed by the UIManager (e.g., clicking on the dialog window, its scrollbar, or its internal buttons),
        # then we typically don't need to process it further with our custom background buttons/selectors.
        if event_consumed_by_manager:
            return True

        # If the event was NOT consumed by the UIManager (e.g., a click outside the dialog, or if no dialog is active),
        # then process our custom UI elements.
        for selector in self.option_selectors.values():
            if selector.handle_event(event):
                return True  # Event handled by custom selector

        for button in self.buttons:
            if button.handle_event(event):
                return True  # Event handled by custom button

        return False # Event not handled by this screen's elements

    def update(self, time_delta): # pygame-gui needs time_delta
        self.ui_manager.update(time_delta)
        # Your existing update logic (if any)
        # pass

    def draw(self):
        self.screen.fill(config.COLOR_BACKGROUND)
        for label in self.labels:
            label.draw(self.screen)
        for selector in self.option_selectors.values():
            selector.draw(self.screen)
        for button in self.buttons:
            button.draw(self.screen)
        
        # Draw pygame-gui elements
        self.ui_manager.draw_ui(self.screen)

    def on_exit(self): # Clean up pygame-gui resources
        if self.file_dialog:
            self.file_dialog.kill()
            self.file_dialog = None
        # If you have other pygame-gui elements managed directly by this screen that need killing, do it here.
        # self.ui_manager.clear_and_reset() # This might be too aggressive if UIManager is shared or persists
        print("MainMenuScreen on_exit called.")

