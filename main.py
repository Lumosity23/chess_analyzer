# main.py
import pygame
import config 
from ui.main_menu_screen import MainMenuScreen
from ui.game_screen import GameScreen
# from ui.pgn_analysis_screen import PGNAnalysisScreen # Pour plus tard

class MainApplication:
    def __init__(self):
        pygame.init()
        # FONT TEST - Add these lines
        print("--- FONT TEST ---")
        font_path_to_test = "theme.json" # This MUST match theme.json
        test_font_size = 30
        try:
            # Test loading by Pygame directly
            test_font = pygame.font.Font(font_path_to_test, test_font_size)
            print(f"SUCCESS: Pygame loaded font '{font_path_to_test}' at size {test_font_size}.")
        except pygame.error as e:
            print(f"PYGAME FONT LOAD ERROR: Could not load font '{font_path_to_test}'. Error: {e}")
        except FileNotFoundError:
            print(f"PYGAME FONT FILE NOT FOUND: Ensure '{font_path_to_test}' exists relative to main.py. Current working directory: {os.getcwd()}") # Added CWD
        print("--- END FONT TEST ---")

        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((config.TOTAL_SCREEN_WIDTH, config.TOTAL_HEIGHT))
        pygame.display.set_caption("Jeu d'Échecs Python")
        config.load_assets()
        if not config.INFO_FONT:
            print("ERREUR CRITIQUE: Polices non chargées.")
            pygame.quit()
            exit()

        self.clock = pygame.time.Clock()
        self.running = True
        self.current_state = config.APP_STATE_MAIN_MENU
        self.active_screen = None
        self._change_active_screen()

    def _change_active_screen(self):
        if self.active_screen and hasattr(self.active_screen, 'on_exit') and callable(getattr(self.active_screen, 'on_exit')):
            self.active_screen.on_exit() # Nettoyer l'ancien écran (ex: arrêter Stockfish)

        if self.current_state == config.APP_STATE_MAIN_MENU:
            self.active_screen = MainMenuScreen(self.screen, self)
        elif self.current_state == config.APP_STATE_IN_GAME:
            self.active_screen = GameScreen(self.screen, config.CURRENT_GAME_CONFIG)
            if hasattr(self.active_screen, 'set_main_app_ref'): # Si la méthode existe
                self.active_screen.set_main_app_ref(self) # Passer la référence à MainApplication
            config.play_sound("game_start")
        # elif self.current_state == config.APP_STATE_PGN_ANALYSIS:
            # self.active_screen = PGNAnalysisScreen(self.screen, self, config.CURRENT_GAME_CONFIG["pgn_filepath"])
        else:
            print(f"État inconnu: {self.current_state}. Retour au menu.")
            self.current_state = config.APP_STATE_MAIN_MENU
            self.active_screen = MainMenuScreen(self.screen, self)

    def change_state(self, new_state):
        if self.current_state != new_state:
            print(f"Changement d'état: {self.current_state} -> {new_state}")
            self.current_state = new_state
            self._change_active_screen()

    def run(self):
        while self.running:
            time_delta = self.clock.tick(config.FPS) / 1000.0 # Calculate time_delta

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.active_screen:
                    self.active_screen.handle_event(event) # Pass event to active screen

            if self.active_screen:
                self.active_screen.update(time_delta) # Pass time_delta to active screen's update
            
            # Pop-up de fin de partie (géré ici pour être au-dessus de tout)
            if self.current_state == config.APP_STATE_IN_GAME and \
               hasattr(self.active_screen, 'chess_logic') and \
               self.active_screen.chess_logic.is_game_over() and \
               not self.active_screen.game_over_message_shown:
                self.active_screen.show_game_over_popup()

            if self.active_screen:
                self.active_screen.draw() 
            
            pygame.display.flip()
        
        if self.active_screen and hasattr(self.active_screen, 'on_exit') and callable(getattr(self.active_screen, 'on_exit')):
            print(f"INFO: Appel de on_exit final pour {type(self.active_screen).__name__}")
            self.active_screen.on_exit()
        
        pygame.quit()


if __name__ == '__main__':
    app = MainApplication()
    app.run()