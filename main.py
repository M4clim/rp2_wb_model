# Structure du projet Python – v1
# Dossier principal : rp2_wb_model/

import json
import os

import matplotlib.pyplot as plt

from core.dynamics import calculate_order_parameters, run_simulation
from core.graph_rp2 import RP2Graph
from core.wb_model import WBModel
from utils.exporter import export_to_json
from utils.logger import Logger
from viz.plotter import Plotter


def load_config(config_file="configs/config.json"):
    """
    Charge la configuration depuis un fichier JSON
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"Configuration chargée depuis {config_file}")
        return config
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {e}")
        print("Utilisation de la configuration par défaut")
        return {}


def ensure_output_dirs():
    """
    Crée les répertoires de sortie s'ils n'existent pas
    """
    dirs = ["outputs", "outputs/logs", "outputs/snapshots"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("Répertoires de sortie créés")


def main():
    """
    Fonction principale d'exécution
    """
    print("=== Modèle RP2-WB ===")

    # Création des répertoires de sortie
    ensure_output_dirs()

    # Chargement de la configuration
    config = load_config()

    # Paramètres de la simulation
    # Utilisation du rayon pour le patch hexagonal au lieu de size_r et size_c
    radius = config.get("radius", 5)
    num_steps = config.get("num_steps", 100)

    # Création du graphe RP2
    print(f"\nCréation du graphe RP2 hexagonal (rayon: {radius})...")
    graph = RP2Graph(radius=radius, scale_factor=1.5)
    graph.generate()

    # Vérification de la non-orientabilité (propriété fondamentale de RP²)
    is_non_orientable = graph.check_non_orientability()
    print(f"Le graphe est non-orientable: {is_non_orientable}")

    # Export du graphe au format JSON pour Godot
    graph.to_json("outputs/rp2_graph.json")

    # Affichage des statistiques du graphe
    stats = graph.get_statistics()
    print("\nStatistiques du graphe RP2:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    # Création du modèle WB
    print("\nInitialisation du modèle WB...")
    model = WBModel(graph, config)
    model.initialize_fields(
        sigma_config=config.get("initial_sigma_config", "center_A"),
        phi_config=config.get("initial_phi_config", "random"),
    )

    # Initialisation du logger
    logger = Logger()

    # Fonction de callback pour enregistrer les statistiques
    def log_callback(model, step, stats):
        logger.record_stats(step, model, stats)

        # Export périodique vers JSON
        if step % config.get("export_interval", 10) == 0:
            export_to_json(model, filename=f"outputs/snapshots/step_{step:04d}.json")

    # Exécution de la simulation
    print(f"\nDémarrage de la simulation ({num_steps} étapes)...")
    history = run_simulation(
        model,
        num_steps=num_steps,
        num_mc_sweeps=config.get("num_mc_sweeps", 1),
        num_relax_steps=config.get("num_relax_steps", 5),
        callback=log_callback,
    )

    # Calcul des paramètres d'ordre finaux
    order_params = calculate_order_parameters(model)
    print("\nParamètres d'ordre finaux:")
    for param, value in order_params.items():
        print(f"  {param}: {value:.4f}")

    # Export de l'état final
    export_to_json(model, filename="outputs/final_state.json")

    # Visualisation
    plotter = Plotter()

    # Visualisation du graphe avec mise en évidence des liens TS
    fig1 = plotter.plot_graph(model, highlight_ts=True, show=False)
    fig1.savefig("outputs/final_graph.png", dpi=300)

    # Visualisation des statistiques
    fig2 = plotter.plot_stats(history, show=False)
    fig2.savefig("outputs/simulation_stats.png", dpi=300)

    # Affichage des figures
    plt.show()

    # Finalisation du logger
    logger.finalize()

    print("\nSimulation terminée. Résultats sauvegardés dans le dossier 'outputs'.")


if __name__ == "__main__":
    main()
