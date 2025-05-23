# engine/stockfish_adapter.py

import chess
import chess.engine
import config # Pour STOCKFISH_PATH
import threading # Pour exécuter l'analyse en arrière-plan
import queue     # Pour communiquer les résultats de l'analyse
import os

class StockfishAdapter:
    def __init__(self):
        self.engine = None
        self.analysis_thread = None
        self.analysis_queue = queue.Queue() # Pour récupérer les résultats de l'analyse
        self.current_analysis_info = None   # Stocke la dernière info d'analyse complète

        try:
            if not os.path.exists(config.STOCKFISH_PATH):
                raise FileNotFoundError(f"Stockfish exécutable non trouvé à: {config.STOCKFISH_PATH}")
            
            # popen_uci lance Stockfish en tant que sous-processus
            self.engine = chess.engine.SimpleEngine.popen_uci(config.STOCKFISH_PATH)
            print(f"INFO: Stockfish démarré avec succès depuis {config.STOCKFISH_PATH}")
            
            # Configurer Stockfish (optionnel, mais peut être utile)
            # self.engine.configure({"Threads": 2}) # Exemple: utiliser 2 threads
            # self.engine.configure({"Hash": 128})   # Exemple: 128 MB de table de hachage

        except Exception as e:
            print(f"ERREUR CRITIQUE: Impossible de démarrer Stockfish: {e}")
            print("Vérifiez que Stockfish est correctement installé et que le chemin dans config.py est correct.")
            self.engine = None # Assurer que l'engine est None en cas d'échec

    def _analyze_in_background(self, board_fen):
        """Fonction exécutée dans un thread séparé pour l'analyse."""
        if not self.engine:
            self.analysis_queue.put(None) # Indiquer qu'il n'y a pas de résultat
            return

        try:
            # Créer une nouvelle instance de board pour le thread
            thread_board = chess.Board(fen=board_fen)
            
            # Utilisation de 'analyse' avec multipv pour obtenir plusieurs lignes si besoin
            # Pour une simple évaluation et meilleur coup, multipv=1 suffit.
            # Limit peut être par temps (time) ou profondeur (depth).
            with self.engine.analysis(thread_board, chess.engine.Limit(time=config.STOCKFISH_ANALYSIS_TIME_MS / 1000.0), multipv=1) as analysis:
                for info in analysis:
                    # On s'intéresse principalement à la dernière mise à jour de la ligne principale
                    # ou à la fin de l'analyse.
                    # Pour un flux continu, on pourrait mettre 'info' dans la queue ici.
                    # Pour cet exemple, on attend la fin de l'analyse pour la ligne principale.
                    pass # Laisser la boucle se terminer pour que 'info' contienne la dernière info
            
            # Mettre le résultat (la dernière info de la ligne principale) dans la queue
            # 'info' contient 'score', 'pv' (meilleure variante), 'depth', etc.
            self.analysis_queue.put(info)
            
        except chess.engine.EngineTerminatedError:
            print("ERREUR: Le moteur Stockfish s'est terminé de manière inattendue pendant l'analyse.")
            self.analysis_queue.put(None)
        except Exception as e:
            print(f"ERREUR: Exception dans le thread d'analyse Stockfish: {e}")
            self.analysis_queue.put(None)


    def start_analysis(self, board: chess.Board):
        """Lance une analyse de la position actuelle dans un thread séparé."""
        if not self.engine:
            print("ATTENTION: Stockfish non initialisé, analyse impossible.")
            return

        # Si une analyse est déjà en cours, on pourrait l'arrêter ou l'ignorer
        if self.analysis_thread and self.analysis_thread.is_alive():
            # print("DEBUG: Analyse précédente toujours en cours, nouvelle analyse ignorée ou en attente.")
            # Pour une version simple, on ne lance pas une nouvelle si une est en cours.
            # Pour une version plus avancée, on pourrait tuer l'ancien thread ou utiliser une gestion plus fine.
            return 

        # Vider la queue des résultats précédents
        while not self.analysis_queue.empty():
            try:
                self.analysis_queue.get_nowait()
            except queue.Empty:
                break
        
        self.current_analysis_info = None # Réinitialiser l'info actuelle
        board_fen = board.fen() # Obtenir le FEN pour le passer au thread
        self.analysis_thread = threading.Thread(target=self._analyze_in_background, args=(board_fen,))
        self.analysis_thread.daemon = True # Permet au programme principal de se fermer même si le thread est en cours
        self.analysis_thread.start()

    def get_latest_analysis_info(self):
        """
        Vérifie la queue pour de nouvelles informations d'analyse.
        Met à jour self.current_analysis_info si de nouvelles données sont disponibles.
        Retourne self.current_analysis_info.
        Non bloquant.
        """
        try:
            # Récupérer la dernière info de la queue sans bloquer
            new_info = self.analysis_queue.get_nowait()
            if new_info:
                self.current_analysis_info = new_info
        except queue.Empty:
            pass # Pas de nouvelle info, c'est normal

        return self.current_analysis_info

    def get_best_move_from_engine(self, board: chess.Board, time_limit_ms=500):
        """
        Demande au moteur de jouer un coup (synchrone).
        Utilisé si vous voulez que Stockfish joue un coup pour l'IA.
        """
        if not self.engine:
            return None
        try:
            result = self.engine.play(board, chess.engine.Limit(time=time_limit_ms / 1000.0))
            return result.move
        except Exception as e:
            print(f"ERREUR: lors de la demande du meilleur coup à Stockfish: {e}")
            return None

    def close(self):
        """Arrête proprement le moteur Stockfish."""
        if self.engine:
            print("INFO: Arrêt de Stockfish...")
            # Attendre que le thread d'analyse en cours se termine (optionnel, avec un timeout)
            if self.analysis_thread and self.analysis_thread.is_alive():
                try:
                    # On ne peut pas 'tuer' un thread de manière propre directement.
                    # L'engine.quit() devrait signaler au thread d'arrêter son travail.
                    # Ou alors, il faudrait une variable de drapeau pour que le thread se termine.
                    # Pour l'instant, on espère que engine.quit() suffit.
                    print("INFO: Thread d'analyse en cours, tentative d'arrêt...")
                    # self.analysis_thread.join(timeout=1.0) # Attendre un peu
                except Exception as e:
                    print(f"ERREUR: en attendant la fin du thread d'analyse: {e}")
            
            try:
                self.engine.quit()
                print("INFO: Stockfish arrêté.")
            except chess.engine.EngineTerminatedError:
                print("INFO: Stockfish était déjà arrêté.") # Cas où le moteur s'est crashé avant
            except Exception as e:
                print(f"ERREUR: lors de l'arrêt de Stockfish: {e}")
            self.engine = None