import chess

class ChessBoardLogic:
    """
    Gère toute la logique du jeu d'échecs en utilisant la bibliothèque python-chess.
    Cette classe est agnostique à l'interface graphique (Pygame).
    """
    def __init__(self):
        self.board = chess.Board() # L'objet principal du plateau
        self.move_history_san = [] # Liste des coups joués en notation SAN (pour affichage)
        self.last_move = None      # Le dernier coup joué (objet chess.Move)
        self.game_over_flag = False # Indique si la partie est terminée
        self.outcome = None        # Résultat de la partie (si terminée)

    def apply_move(self, move: chess.Move) -> bool:
        """
        Applique un coup sur le plateau s'il est légal.
        Met à jour l'historique et l'état de fin de partie.
        Retourne True si le coup est appliqué, False sinon.
        """
        if self.game_over_flag:
            # print("Partie terminée, impossible de jouer un coup.") # Debug
            return False

        if move in self.board.legal_moves:
            # Enregistre le coup en SAN avant de le jouer
            san_move = self.board.san(move)
            self.board.push(move)
            self.move_history_san.append(san_move)
            self.last_move = move
            self._update_game_status()
            return True
        # else:
            # print(f"Coup illégal: {move}") # Debug
        return False

    def undo_move(self) -> bool:
        """
        Annule le dernier coup joué.
        Retourne True si un coup a été annulé, False sinon.
        """
        if self.board.move_stack:
            self.board.pop()
            if self.move_history_san: # S'assurer que l'historique SAN est synchronisé
                self.move_history_san.pop()
            self.last_move = self.board.peek() if self.board.move_stack else None
            self.game_over_flag = False # Si on annule, la partie n'est plus finie
            self.outcome = None
            return True
        return False

    def get_legal_moves_from_square(self, square: chess.Square) -> list[chess.Move]:
        """
        Retourne une liste de tous les coups légaux possibles depuis une case donnée.
        """
        return [move for move in self.board.legal_moves if move.from_square == square]

    def get_board_state(self) -> chess.Board:
        """Retourne l'objet chess.Board actuel."""
        return self.board

    def get_current_player_color(self) -> chess.Color:
        """Retourne la couleur du joueur dont c'est le tour."""
        return self.board.turn

    def get_game_status_message(self) -> str | None:
        """
        Retourne un message décrivant l'état de la partie (échec, mat, pat, etc.).
        """
        if self.board.is_checkmate():
            winner_color = "Noirs" if self.board.turn == chess.WHITE else "Blancs"
            return f"ÉCHEC ET MAT ! {winner_color} gagnent."
        if self.board.is_stalemate():
            return "PAT ! Partie nulle."
        if self.board.is_insufficient_material():
            return "MATÉRIEL INSUFFISANT. Partie nulle."
        if self.board.is_seventyfive_moves():
            return "RÈGLE DES 75 COUPS. Partie nulle."
        if self.board.is_fivefold_repetition():
            return "RÈGLE DES 5 RÉPÉTITIONS. Partie nulle."
        # Autres conditions de nulle peuvent être vérifiées ici si nécessaire (ex: can_claim_draw)
        return None

    def is_game_over(self) -> bool:
        """Vérifie si la partie est terminée."""
        return self.game_over_flag

    def is_in_check(self) -> bool:
        """Vérifie si le joueur actuel est en échec."""
        return self.board.is_check()
    
    def get_king_square(self, color: chess.Color) -> chess.Square | None:
        """Retourne la case du roi pour la couleur donnée, ou None si pas de roi (ne devrait pas arriver)."""
        return self.board.king(color)

    def get_last_move(self) -> chess.Move | None:
        """Retourne le dernier coup joué."""
        return self.last_move

    def get_move_history_san(self) -> list[str]:
        """Retourne l'historique des coups en notation SAN."""
        return self.move_history_san

    def get_fen(self) -> str:
        """Retourne la représentation FEN de la position actuelle."""
        return self.board.fen()

    def _update_game_status(self):
        """Met à jour les drapeaux internes de fin de partie."""
        self.game_over_flag = self.board.is_game_over()
        if self.game_over_flag:
            self.outcome = self.board.outcome() # Stocke l'objet Outcome de python-chess