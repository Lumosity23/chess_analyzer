import pygame
import chess
import os

# --- Constantes (inchangées) ---
SQUARE_SIZE = 150
BOARD_SIZE_PX = 8 * SQUARE_SIZE
TOTAL_WIDTH = BOARD_SIZE_PX
TOTAL_HEIGHT = BOARD_SIZE_PX + 80 # Espace pour les messages en bas

COLOR_LIGHT_SQUARE = pygame.Color(238, 238, 210)
COLOR_DARK_SQUARE = pygame.Color(118, 150, 86)
COLOR_SELECTED_SQUARE = pygame.Color(186, 202, 68, 180)
COLOR_LEGAL_MOVE_DOT = pygame.Color(0, 0, 0, 80)
COLOR_LEGAL_CAPTURE_RING = pygame.Color(150, 0, 0, 120)
COLOR_CHECK = pygame.Color(255, 0, 0, 100)
COLOR_BACKGROUND = pygame.Color(49, 46, 43)
COLOR_TEXT = pygame.Color(220, 220, 220)

# --- Variables globales pour les assets (seront remplies après init) ---
PIECE_IMAGES = {}
SOUNDS = {}
INFO_FONT = None
STATUS_FONT = None

# Dossiers d'assets
PIECES_DIR = "pieces"
SOUNDS_DIR = "sounds"

def load_assets(): # Regroupe le chargement de tous les assets
    global PIECE_IMAGES, SOUNDS, INFO_FONT, STATUS_FONT

    # Charger les images
    piece_symbols_map_chess_to_file = {'P': 'p', 'N': 'n', 'B': 'b', 'R': 'r', 'Q': 'q', 'K': 'k'}
    colors = ['w', 'b']
    for color_prefix in colors:
        for chess_symbol_upper, file_symbol_lower in piece_symbols_map_chess_to_file.items():
            filename = f"{color_prefix}{file_symbol_lower}.png"
            image_key = f"{color_prefix}{chess_symbol_upper}"
            try:
                image_path = os.path.join(PIECES_DIR, filename)
                image = pygame.image.load(image_path).convert_alpha() # convert_alpha est important
                PIECE_IMAGES[image_key] = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
            except pygame.error as e:
                print(f"Erreur chargement image {image_path}: {e}")
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
            print(f"Erreur chargement son {sound_path}: {e}")
            SOUNDS[sound_name] = None
            
    # Charger les polices
    font_name = None # Mettre un chemin vers un .ttf si vous en avez un, ex: "fonts/Arial.ttf"
    # Si font_name reste None, on utilise SysFont
    if font_name:
        try:
            INFO_FONT = pygame.font.Font(font_name, SQUARE_SIZE // 5)
            # Pour une version bold, vous auriez besoin d'un fichier de police bold, ex: "fonts/Arial-Bold.ttf"
            STATUS_FONT = pygame.font.Font(font_name, SQUARE_SIZE // 4) # Supposons que cette police est déjà "bold" ou "regular"
        except pygame.error as e:
            print(f"Erreur chargement police depuis fichier {font_name}: {e}. Utilisation de SysFont.")
            font_name = None # Forcer l'utilisation de SysFont
    
    if not font_name: # Si le chargement depuis fichier a échoué ou n'était pas spécifié
        INFO_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 5)
        STATUS_FONT = pygame.font.SysFont("arial", SQUARE_SIZE // 4, bold=True) # bold=True est OK pour SysFont

    print("Assets chargés.")


def play_sound(sound_name):
    if sound_name in SOUNDS and SOUNDS[sound_name]:
        SOUNDS[sound_name].play()

class GameState:
    def __init__(self):
        self.board = chess.Board()
        self.selected_square_pygame = None
        self.legal_moves_for_selected = []
        # Les polices sont maintenant globales et chargées dans load_assets()
        play_sound("game_start")

    # ... (toutes les autres méthodes de GameState restent les mêmes)
    def get_piece_at_pygame_coords(self, row, col):
        square_index = self.pygame_to_chess_square_index(row, col)
        return self.board.piece_at(square_index)

    def pygame_to_chess_square_index(self, row, col):
        return chess.square(file_index=col, rank_index=7 - row)

    def chess_square_index_to_pygame(self, square_index):
        file_index = chess.square_file(square_index)
        rank_index = chess.square_rank(square_index)
        return (7 - rank_index, file_index)

    def handle_click(self, row, col):
        clicked_chess_square = self.pygame_to_chess_square_index(row, col)
        played_sound_this_click = False

        if self.selected_square_pygame:
            selected_chess_square = self.pygame_to_chess_square_index(self.selected_square_pygame[0], self.selected_square_pygame[1])
            
            promotion_piece = None
            piece_type = self.board.piece_type_at(selected_chess_square)
            if piece_type == chess.PAWN:
                if (self.board.turn == chess.WHITE and chess.square_rank(clicked_chess_square) == 7) or \
                   (self.board.turn == chess.BLACK and chess.square_rank(clicked_chess_square) == 0):
                    promotion_piece = chess.QUEEN

            move = chess.Move(selected_chess_square, clicked_chess_square, promotion=promotion_piece)

            if move in self.board.legal_moves:
                is_capture = self.board.is_capture(move)
                is_castling = self.board.is_castling(move)
                
                self.board.push(move)

                if promotion_piece: play_sound("promote")
                elif is_castling: play_sound("castle")
                elif is_capture: play_sound("capture")
                else: play_sound("move_self")
                
                played_sound_this_click = True

                if self.board.is_check():
                    play_sound("check")
                
                self.selected_square_pygame = None
                self.legal_moves_for_selected = []
                self.check_game_over_sounds()

            elif clicked_chess_square == selected_chess_square:
                self.selected_square_pygame = None
                self.legal_moves_for_selected = []
            else:
                piece_at_click = self.board.piece_at(clicked_chess_square)
                if piece_at_click and piece_at_click.color == self.board.turn:
                    self.selected_square_pygame = (row, col)
                    self._update_legal_moves_for_selected()
                    played_sound_this_click = True
                elif not played_sound_this_click: 
                    play_sound("illegal_move")
                    self.selected_square_pygame = None 
                    self.legal_moves_for_selected = []

        else: 
            piece = self.board.piece_at(clicked_chess_square)
            if piece and piece.color == self.board.turn:
                self.selected_square_pygame = (row, col)
                self._update_legal_moves_for_selected()
                played_sound_this_click = True
            elif not played_sound_this_click:
                play_sound("illegal_move")

    def _update_legal_moves_for_selected(self):
        self.legal_moves_for_selected = []
        if self.selected_square_pygame:
            from_square_chess = self.pygame_to_chess_square_index(self.selected_square_pygame[0], self.selected_square_pygame[1])
            for move in self.board.legal_moves:
                if move.from_square == from_square_chess:
                    self.legal_moves_for_selected.append(move)

    def get_game_status_message(self):
        if self.board.is_checkmate():
            winner_color = "Noirs" if self.board.turn == chess.WHITE else "Blancs"
            return f"ÉCHEC ET MAT ! {winner_color} gagnent."
        if self.board.is_stalemate(): return "PAT ! Partie nulle."
        if self.board.is_insufficient_material(): return "MATÉRIEL INSUFFISANT. Partie nulle."
        if self.board.is_seventyfive_moves(): return "RÈGLE DES 75 COUPS. Partie nulle."
        if self.board.is_fivefold_repetition(): return "RÈGLE DES 5 RÉPÉTITIONS. Partie nulle."
        return None

    def check_game_over_sounds(self):
        outcome = self.board.outcome()
        if outcome:
            is_player_white = True 
            
            if outcome.winner is not None: 
                if (outcome.winner == chess.WHITE and is_player_white) or \
                   (outcome.winner == chess.BLACK and not is_player_white):
                    play_sound("game_win")
                else:
                    play_sound("game_lose")
            else: 
                play_sound("game_draw")

    def get_piece_image_key(self, piece):
        color_char = 'w' if piece.color == chess.WHITE else 'b'
        return f"{color_char}{piece.symbol().upper()}"


# --- Fonctions d'affichage Pygame ---
def draw_board_squares(screen):
    for r in range(8):
        for c in range(8):
            color = COLOR_LIGHT_SQUARE if (r + c) % 2 == 0 else COLOR_DARK_SQUARE
            pygame.draw.rect(screen, color, pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces_images(screen, game_state):
    for r in range(8):
        for c in range(8):
            square_index = game_state.pygame_to_chess_square_index(r, c)
            piece = game_state.board.piece_at(square_index)
            if piece:
                image_key = game_state.get_piece_image_key(piece)
                image_to_draw = PIECE_IMAGES.get(image_key)
                if image_to_draw:
                    screen.blit(image_to_draw, (c * SQUARE_SIZE, r * SQUARE_SIZE))

def draw_highlights(screen, game_state):
    if game_state.selected_square_pygame:
        r, c = game_state.selected_square_pygame
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(COLOR_SELECTED_SQUARE)
        screen.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))

    for move in game_state.legal_moves_for_selected:
        to_r, to_c = game_state.chess_square_index_to_pygame(move.to_square)
        center_x = to_c * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = to_r * SQUARE_SIZE + SQUARE_SIZE // 2
        
        if game_state.board.is_capture(move):
            pygame.draw.circle(screen, COLOR_LEGAL_CAPTURE_RING, (center_x, center_y), SQUARE_SIZE * 0.45, width=max(1, SQUARE_SIZE // 15))
        else:
            pygame.draw.circle(screen, COLOR_LEGAL_MOVE_DOT, (center_x, center_y), SQUARE_SIZE // 8)

    if game_state.board.is_check():
        king_square = game_state.board.king(game_state.board.turn)
        if king_square is not None:
            r, c = game_state.chess_square_index_to_pygame(king_square)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(COLOR_CHECK)
            screen.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))

def draw_status_text(screen, game_state):
    # Vérifier que les polices sont chargées
    if not INFO_FONT or not STATUS_FONT:
        print("Polices non chargées, impossible d'afficher le statut.")
        return

    current_y = BOARD_SIZE_PX + 10
    line_height_info = INFO_FONT.get_height() + 3
    line_height_status = STATUS_FONT.get_height() + 5

    game_over_msg = game_state.get_game_status_message()

    if game_over_msg:
        text_surface = STATUS_FONT.render(game_over_msg, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=(TOTAL_WIDTH // 2, current_y + line_height_status // 2))
        screen.blit(text_surface, text_rect)
        current_y += line_height_status
    else:
        turn_text = "Tour des Blancs" if game_state.board.turn == chess.WHITE else "Tour des Noirs"
        text_surface = INFO_FONT.render(turn_text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=(TOTAL_WIDTH // 2, current_y + line_height_info // 2))
        screen.blit(text_surface, text_rect)
        current_y += line_height_info

        if game_state.board.is_check() and not game_state.board.is_checkmate():
            check_text_surface = STATUS_FONT.render("ÉCHEC !", True, (255, 60, 60))
            check_text_rect = check_text_surface.get_rect(center=(TOTAL_WIDTH // 2, current_y + line_height_status // 2))
            screen.blit(check_text_surface, check_text_rect)
            # current_y += line_height_status # Pas besoin d'incrémenter ici si c'est la dernière chose affichée


def main():
    pygame.init() # Initialise TOUS les modules Pygame, y compris font et mixer
    
    # 1. Créer la fenêtre (définir le mode vidéo)
    screen = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
    pygame.display.set_caption("Jeu d'Échecs")
    
    # 2. Initialiser le mixer audio (peut se faire après pygame.init())
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except pygame.error as e:
        print(f"Erreur initialisation mixer: {e}. Les sons pourraient ne pas fonctionner.")

    # 3. Charger tous les assets (images, sons, polices) MAINTENANT que le mode vidéo est défini
    load_assets() 
    
    # 4. Créer l'état du jeu
    game_state = GameState() # Doit être après load_assets si GameState utilise les sons/polices à l'init

    clock = pygame.time.Clock()
    running = True

    while running:
        is_game_over = game_state.board.is_game_over()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not is_game_over:
                    pos = pygame.mouse.get_pos()
                    if 0 <= pos[0] < BOARD_SIZE_PX and 0 <= pos[1] < BOARD_SIZE_PX:
                        col = pos[0] // SQUARE_SIZE
                        row = pos[1] // SQUARE_SIZE
                        game_state.handle_click(row, col)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state = GameState() # Recrée l'état, rejoue le son de début
                if event.key == pygame.K_u:
                    if len(game_state.board.move_stack) > 0:
                        game_state.board.pop()
                        game_state.selected_square_pygame = None
                        game_state.legal_moves_for_selected = []

        screen.fill(COLOR_BACKGROUND)
        draw_board_squares(screen)
        draw_highlights(screen, game_state)
        draw_pieces_images(screen, game_state)
        draw_status_text(screen, game_state)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()