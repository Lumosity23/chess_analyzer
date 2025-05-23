import pygame
import os
import chess # Import pour chess.WHITE/BLACK

# --- Constantes de la Fenêtre ---
SQUARE_SIZE = 150  # Taille des cases en pixels (selon vos images)
BOARD_SIZE_PX = 8 * SQUARE_SIZE # Taille du plateau en pixels (1200x1200)
MAIN_PADDING = 15 # Padding général entre les grands composants
COORDINATE_SPACE = 30 # Espace pour afficher les numéros et lettres des coordonnées

EVAL_BAR_WIDTH = 20 # Largeur de la barre de victoire verticale
BOARD_X_OFFSET = EVAL_BAR_WIDTH # Le plateau commence après la barre d'évaluation
SIDEBAR_WIDTH = 400 # Largeur de la barre latérale pour l'historique, Stockfish, etc.
TOTAL_SCREEN_WIDTH = 1800
TOTAL_HEIGHT = 1400 # Espace supplémentaire en bas pour des messages si pas de sidebar

FPS = 60 # Taux de rafraîchissement du jeu

# --- Options de Jeu par Défaut ---
DEFAULT_GAME_TIME_MINUTES = 5 # Temps par joueur en minutes
# Modes d'adversaire (chaînes de caractères pour identification)
OPPONENT_HUMAN = "HUMAN"
OPPONENT_AI_STOCKFISH = "AI_STOCKFISH"
DEFAULT_OPPONENT_MODE = OPPONENT_HUMAN

# Pour stocker la configuration de la partie actuelle
CURRENT_GAME_CONFIG = {
    "time_minutes": DEFAULT_GAME_TIME_MINUTES,
    "white_player_type": OPPONENT_HUMAN, # ou OPPONENT_AI_STOCKFISH
    "black_player_type": OPPONENT_HUMAN, # ou OPPONENT_AI_STOCKFISH
    "pgn_filepath": None # Pour le mode analyse PGN
}

# États de l'application
APP_STATE_MAIN_MENU = "MAIN_MENU"
APP_STATE_IN_GAME = "IN_GAME"
APP_STATE_PGN_ANALYSIS = "PGN_ANALYSIS" # Pour plus tard
APP_STATE_SETTINGS = "SETTINGS"       # Pour plus tard

# Couleurs pour les sélecteurs/options dans le menu
COLOR_OPTION_SELECTED = pygame.Color(100, 150, 255)
COLOR_OPTION_NORMAL = pygame.Color(70, 70, 70)

# --- Couleurs ---
COLOR_LIGHT_SQUARE = pygame.Color(238, 238, 210) # Blanc cassé
COLOR_DARK_SQUARE = pygame.Color(118, 150, 86)   # Vert foncé
COLOR_SELECTED_SQUARE = pygame.Color(186, 202, 68, 180) # Jaune semi-transparent
COLOR_LEGAL_MOVE_DOT = pygame.Color(0, 0, 0, 80)       # Point gris foncé semi-transparent
COLOR_LEGAL_CAPTURE_RING = pygame.Color(150, 0, 0, 120) # Anneau rouge semi-transparent pour captures
COLOR_CHECK = pygame.Color(255, 0, 0, 100)           # Rouge pour la case du roi en échec
COLOR_BACKGROUND = pygame.Color(49, 46, 43) # Fond général (style chess.com sombre)
COLOR_TEXT = pygame.Color(220, 220, 220) # Couleur pour le texte sur fond sombre
COLOR_INFO_BG = pygame.Color(35, 33, 31) # Fond pour la zone d'info si on en fait une séparée
COLOR_BUTTON_NORMAL = pygame.Color(70, 70, 70)
COLOR_BUTTON_HOVER = pygame.Color(100, 100, 100)
COLOR_BUTTON_TEXT = pygame.Color(220, 220, 220)
COLOR_SIDEBAR_BACKGROUND = pygame.Color(30, 28, 27) # Un peu plus clair que le fond général
COLOR_MOVE_HISTORY_BG = pygame.Color(40, 38, 37)
COLOR_MOVE_HISTORY_TEXT = pygame.Color(180, 180, 180)
COLOR_COORDINATES_LIGHT = pygame.Color(118, 150, 86) # Même que les cases foncées du plateau
COLOR_COORDINATES_DARK = pygame.Color(238, 238, 210)  # Même que les cases claires du plateau

# --- Chemins des Assets ---
# Assurez-vous que ces dossiers sont au même niveau que votre script main.py
PIECES_DIR = "pieces"
SOUNDS_DIR = "sounds"
FONTS_DIR = "fonts" # Si vous avez des polices personnalisées ici

# --- Variables Globales pour les Assets Chargés ---
# Ces dictionnaires et variables seront remplis par la fonction load_assets()
PIECE_IMAGES = {}
SOUNDS = {}
INFO_FONT = None
STATUS_FONT = None
BUTTON_FONT = None # Sera initialisé dans load_assets
MOVE_HISTORY_FONT = None # Sera initialisé dans load_assets
EVAL_BAR_WIDTH = 20 # Largeur de la barre de victoire verticale
COORDINATE_FONT = None # Sera initialisé dans load_assets


# --- Stockfish Configuration ---
# Adapter le nom de l'exécutable si nécessaire
STOCKFISH_EXECUTABLE_NAME = "stockfish.exe" if os.name == 'nt' else "stockfish" # Gère Windows vs autres
STOCKFISH_DIR = "stockfish"
STOCKFISH_PATH = os.path.join(STOCKFISH_DIR, STOCKFISH_EXECUTABLE_NAME)

# Paramètres pour l'analyse Stockfish (peuvent être ajustés)
STOCKFISH_ANALYSIS_TIME_MS = 1000  # Temps d'analyse par coup en millisecondes (1 seconde)
STOCKFISH_ANALYSIS_DEPTH = 15     # Profondeur d'analyse (alternative au temps)
# On utilisera plutôt la limite de temps pour une réactivité constante.

# --- Fonctions de Chargement des Assets ---
def load_assets():
    """Charge toutes les images, sons et polices nécessaires au jeu.
    Doit être appelée APRÈS pygame.init() et pygame.display.set_mode()."""
    global PIECE_IMAGES, SOUNDS, INFO_FONT, STATUS_FONT, COORDINATE_FONT, BUTTON_FONT, MOVE_HISTORY_FONT

    # Charger les images des pièces
    piece_symbols_map_chess_to_file = {'P': 'p', 'N': 'n', 'B': 'b', 'R': 'r', 'Q': 'q', 'K': 'k'}
    colors = ['w', 'b']
    for color_prefix in colors:
        for chess_symbol_upper, file_symbol_lower in piece_symbols_map_chess_to_file.items():
            filename = f"{color_prefix}{file_symbol_lower}.png"
            image_key = f"{color_prefix}{chess_symbol_upper}"
            try:
                image_path = os.path.join(PIECES_DIR, filename)
                image = pygame.image.load(image_path).convert_alpha()
                PIECE_IMAGES[image_key] = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
            except pygame.error as e:
                print(f"ATTENTION: Erreur chargement image {image_path}: {e}. La pièce ne sera pas affichée.")
                PIECE_IMAGES[image_key] = None
    
    # Charger les sons
    sound_files_to_load = {
        "move_self": "move-self.mp3", "move_opponent": "move-opponent.mp3",
        "capture": "capture.mp3", "check": "move-check.mp3",
        "castle": "castle.mp3", "promote": "promote.mp3",
        "game_start": "game-start.mp3", "game_win": "game-win.mp3",
        "game_lose": "game-lose.mp3", "game_draw": "game-draw.mp3",
        "illegal_move": "illegal.mp3",
    }
    for sound_name, filename in sound_files_to_load.items():
        try:
            sound_path = os.path.join(SOUNDS_DIR, filename)
            SOUNDS[sound_name] = pygame.mixer.Sound(sound_path)
        except pygame.error as e:
            print(f"ATTENTION: Erreur chargement son {sound_path}: {e}. Le son ne sera pas joué.")
            SOUNDS[sound_name] = None
            
    # Charger les polices
    # Exemple: font_path = os.path.join(FONTS_DIR, "OpenSans-Regular.ttf")
    # Pour l'instant, on utilise des polices système pour éviter les dépendances de fichiers .ttf
    font_path = None # Laissez None si vous n'avez pas de fichier .ttf spécifique

    if font_path and os.path.exists(font_path):
        try:
            INFO_FONT = pygame.font.Font(font_path, SQUARE_SIZE // 5)
            STATUS_FONT = pygame.font.Font(font_path, SQUARE_SIZE // 4) # Si votre .ttf n'est pas "bold", il ne le sera pas.
        except pygame.error as e:
            print(f"ATTENTION: Erreur chargement police depuis {font_path}: {e}. Utilisation de polices système.")
            INFO_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 5)
            STATUS_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 4, bold=True)
    else: # Si pas de chemin ou chemin invalide
        INFO_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 5)
        STATUS_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 4, bold=True)

    if not font_path:
        COORDINATE_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 6)
    else:
        try:
            COORDINATE_FONT = pygame.font.Font(font_path, SQUARE_SIZE // 6)
        except pygame.error:
            COORDINATE_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 6)

    print("Assets chargés avec succès (les avertissements ci-dessus sont normaux si des fichiers manquent).")

def play_sound(sound_name):
    """Joue un son si celui-ci a été chargé."""
    if sound_name in SOUNDS and SOUNDS[sound_name]:
        SOUNDS[sound_name].play()
    # else:
    #     print(f"Debug: Son '{sound_name}' non disponible.") # Décommenter pour déboguer si un son ne joue pas