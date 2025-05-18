import json
import os
import time
from datetime import datetime

import numpy as np


class Logger:
    """
    Gestionnaire de journalisation pour les simulations WB
    """

    def __init__(self, log_dir="outputs/logs", save_interval=10):
        """
        Initialise le logger

        Args:
            log_dir (str): Répertoire pour les fichiers de log
            save_interval (int): Intervalle entre les sauvegardes automatiques
        """
        self.log_dir = log_dir
        self.save_interval = save_interval
        self.stats = []
        self.start_time = time.time()

        # Création du dossier de logs si nécessaire
        os.makedirs(log_dir, exist_ok=True)

        # Nom de fichier basé sur la date/heure
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"simulation_{self.timestamp}.log")
        self.stats_file = os.path.join(log_dir, f"stats_{self.timestamp}.json")

        # Message initial
        self.log("Simulation démarrée")

    def log(self, message, level="INFO"):
        """
        Ajoute un message au fichier de log

        Args:
            message (str): Message à journaliser
            level (str): Niveau de log (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        # Affichage console
        print(log_entry)

        # Écriture dans le fichier
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def record_stats(self, step, model, step_stats=None):
        """
        Enregistre les statistiques de l'étape de simulation

        Args:
            step (int): Numéro de l'étape
            model (WBModel): Instance du modèle WB
            step_stats (dict, optional): Statistiques supplémentaires
        """
        # Statistiques de base
        stats = {"step": step, "timestamp": time.time() - self.start_time}

        # Ajout des statistiques du réseau
        if hasattr(model, "network"):
            stats.update(
                {
                    "node_count": model.network.number_of_nodes(),
                    "edge_count": model.network.number_of_edges(),
                }
            )

        # Statistiques sur les champs
        # Récupération des valeurs de rho
        if hasattr(model, "rho") and model.rho:
            # Si le modèle a un attribut rho explicite
            rho_values = list(model.rho.values())
        else:
            # Sinon, essayer de calculer rho à partir de get_effective_rho
            try:
                if hasattr(model, "network"):
                    rho_values = [
                        model.get_effective_rho(node) for node in model.network.nodes()
                    ]
                else:
                    rho_values = []
            except (AttributeError, TypeError):
                # Si get_effective_rho n'est pas disponible, utiliser sigma
                if hasattr(model, "sigma") and hasattr(model, "network"):
                    rho_values = [
                        1.0 if model.sigma.get(n, -1) == 1 else 0.1
                        for n in model.network.nodes()
                    ]
                else:
                    rho_values = []

        # Récupération des valeurs de sigma
        sigma_values = list(model.sigma.values()) if hasattr(model, "sigma") else []

        # Calcul des statistiques
        active_count = sum(1 for s in sigma_values if s == 1)

        stats.update(
            {
                "rho_mean": np.mean(rho_values) if rho_values else 0.0,
                "rho_std": np.std(rho_values) if rho_values else 0.0,
                "sigma_sum": sum(sigma_values) if sigma_values else 0,
                "sigma_mean": np.mean(sigma_values) if sigma_values else 0.0,
                "active_count": active_count,
                "N_pot": float(model.N_pot) if hasattr(model, "N_pot") else 0.0,
            }
        )

        # Ajout des statistiques supplémentaires
        if step_stats:
            stats.update(step_stats)

        # Ajout aux statistiques globales
        self.stats.append(stats)

        # Log des statistiques principales
        self.log(
            f"Étape {step}: N_pot={stats['N_pot']:.2f}, "
            f"Actifs={stats['active_count']}, "
            f"ρ_moy={stats['rho_mean']:.3f}"
        )

        # Sauvegarde périodique
        if step % self.save_interval == 0:
            self.save_stats()

    def save_stats(self):
        """
        Sauvegarde les statistiques dans un fichier JSON
        """
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

        self.log(f"Statistiques sauvegardées dans {self.stats_file}")

    def finalize(self):
        """
        Finalise la journalisation et sauvegarde les statistiques finales
        """
        elapsed_time = time.time() - self.start_time
        self.log(f"Simulation terminée. Durée totale: {elapsed_time:.2f} secondes")
        self.save_stats()

        # Résumé final
        if self.stats:
            last_stats = self.stats[-1]
            self.log(
                f"Résumé final - Étapes: {last_stats['step']}, Actifs: {last_stats.get('active_count', 0)}, N_pot: {last_stats['N_pot']:.2f}"
            )

        return self.stats_file
