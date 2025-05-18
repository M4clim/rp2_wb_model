import os
import json
import time
import numpy as np
from datetime import datetime

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
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def record_stats(self, step, model, step_stats=None):
        """
        Enregistre les statistiques de l'étape de simulation
        
        Args:
            step (int): Numéro de l'étape
            model (WBModel): Instance du modèle WB
            step_stats (dict): Statistiques supplémentaires de l'étape
        """
        # Statistiques de base
        stats = {
            "step": step,
            "timestamp": time.time() - self.start_time,
            "node_count": len(model.network.nodes()),
            "edge_count": len(model.network.edges())
        }
        
        # Statistiques sur les champs
        # Calcul de rho pour chaque nœud en utilisant get_effective_rho
        rho_values = [model.get_effective_rho(node) for node in model.network.nodes()]
        sigma_values = list(model.sigma.values())
        
        stats.update({
            "rho_mean": np.mean(rho_values),
            "rho_std": np.std(rho_values),
            "sigma_sum": sum(sigma_values),
            "sigma_mean": np.mean(sigma_values)
        })
        
        # Ajout des statistiques supplémentaires
        if step_stats:
            stats.update(step_stats)
        
        # Ajout aux statistiques globales
        self.stats.append(stats)
        
        # Log des statistiques principales
        self.log(f"Étape {step}: ρ_moy={stats['rho_mean']:.3f}, σ_moy={stats['sigma_mean']:.3f}")
        
        # Sauvegarde périodique
        if step % self.save_interval == 0:
            self.save_stats()
    
    def save_stats(self):
        """
        Sauvegarde les statistiques dans un fichier JSON
        """
        with open(self.stats_file, 'w', encoding='utf-8') as f:
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
            self.log(f"Résumé final - Étapes: {last_stats['step']}, ρ_moy final: {last_stats['rho_mean']:.3f}")
        
        return self.stats_file