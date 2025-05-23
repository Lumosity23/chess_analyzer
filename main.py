# main.py
import pygame
import config 
from ui.main_menu_screen import MainMenuScreen
from ui.game_screen import GameScreen
# from ui.pgn_analysis_screen import PGNAnalysisScreen # Pour plus tard

class MainApplication:
    def __init__(self):
        pygame.init()
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.active_screen:
                    self.active_screen.handle_event(event)

            if self.active_screen:
                self.active_screen.update()
            
            # Pop-up de fin de partie (géré ici pour être au-dessus de tout)
            # Cette logique est un peu basique, un vrai système de pop-up serait mieux
            if self.current_state == config.APP_STATE_IN_GAME and self.active_screen.chess_logic.is_game_over() and not self.active_screen.game_over_message_shown:
                self.active_screen.show_game_over_popup() # Une méthode dans GameScreen

            if self.active_screen:
                self.active_screen.draw() # L'écran de jeu dessine son propre pop-up
            
            pygame.display.flip()
            self.clock.tick(config.FPS)
        
        # Nettoyage final si l'écran actif a une méthode on_exit
        if self.active_screen and hasattr(self.active_screen, 'on_exit') and callable(getattr(self.active_screen, 'on_exit')):
            print(f"INFO: Appel de on_exit final pour {type(self.active_screen).__name__}")
            self.active_screen.on_exit()
        
        pygame.quit()

if __name__ == '__main__':
    app = MainApplication()
    app.run()