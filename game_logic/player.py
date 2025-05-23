import chess # Pour chess.WHITE, chess.BLACK

class Player:
    """
    Représente un joueur d'échecs, gérant son nom, sa couleur et son temps.
    """
    def __init__(self, color: chess.Color, name: str, initial_time_ms: int, is_human: bool = True):
        self.color = color
        self.name = name
        self.time_left_ms = initial_time_ms
        self.is_human = is_human
        self.is_timed_out = False # Drapeau pour indiquer si le temps est écoulé

    def decrease_time(self, delta_ms: int):
        """
        Décrémente le temps du joueur.
        """
        if not self.is_timed_out:
            self.time_left_ms -= delta_ms
            if self.time_left_ms <= 0:
                self.time_left_ms = 0
                self.is_timed_out = True
                # print(f"Temps écoulé pour {self.name}!") # Debug

    def get_time_left_formatted(self) -> str:
        """
        Retourne le temps restant formaté en 'MM:SS.d' (minutes:secondes.dixiemes).
        """
        if self.is_timed_out:
            return "00:00.0"

        total_seconds = self.time_left_ms / 1000.0
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        tenths = int((total_seconds * 10) % 10) # Un chiffre après la virgule

        return f"{minutes:02}:{seconds:02}.{tenths}"
    
    def get_time_left_ms(self) -> int:
        """Retourne le temps restant en millisecondes."""
        return self.time_left_ms

    def reset_time(self, new_initial_time_ms: int):
        """Réinitialise le temps du joueur."""
        self.time_time_ms = new_initial_time_ms
        self.is_timed_out = False

    def get_color_name(self) -> str:
        """Retourne 'Blanc' ou 'Noir' en fonction de la couleur du joueur."""
        return "Blanc" if self.color == chess.WHITE else "Noir"