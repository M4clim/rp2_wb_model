import math
from typing import Any, Dict

from core.montecarlo import metropolis_step
from core.phase_dynamics import update_phase_and_rho
from core.wb_model import WBModel


def step_simulation(model: WBModel, step_id: int = 0) -> Dict[str, Any]:
    """
    Effectue une étape de simulation pour le modèle WB

    Args:
        model: Instance du modèle WB
        step_id: Identifiant de l'étape

    Returns:
        dict: Statistiques de l'étape de simulation
    """
    # Étape Monte Carlo
    metropolis_step(model, T=1.0)
    update_phase_and_rho(model, c2=1.0, c3=1.5)
    # Relaxation phase φ (simple moyenne)
    for n in model.graph.graph.nodes:
        if model.sigma[n] == 1:
            phis = [model.phi[j] for j in model.graph.get_neighbors(n)]
            if phis:
                model.phi[n] = sum(phis) / len(phis)

    # Statistiques
    Φ_Wb = sum(1 for s in model.sigma.values() if s == 1)
    Λ_min, Λ0, kΦ = 0.2, 1.0, 0.01
    Λ_vac = Λ_min + (Λ0 - Λ_min) * math.exp(-kΦ * Φ_Wb)

    return {"step": step_id, "N_pot": model.N_pot, "active": Φ_Wb, "Λ_vac": Λ_vac}


def run_simulation(
    model, num_steps=100, num_mc_sweeps=1, num_relax_steps=5, callback=None
):
    """
    Exécute une simulation complète du modèle WB

    Args:
        model: Instance du modèle WB
        num_steps: Nombre d'étapes de simulation
        num_mc_sweeps: Nombre de balayages Monte Carlo par étape
        num_relax_steps: Nombre d'étapes de relaxation par étape
        callback: Fonction de rappel appelée à chaque étape

    Returns:
        Liste des statistiques pour chaque étape
    """
    history = []
    for t in range(num_steps):
        # Effectuer plusieurs balayages Monte Carlo si nécessaire
        for _ in range(num_mc_sweeps):
            stats = step_simulation(model, t)
            history.append(stats)

            # Appeler la fonction de callback si elle est fournie
            if callback:
                callback(model, t, stats)

    return history


def calculate_order_parameters(model):
    active = sum(1 for s in model.sigma.values() if s == 1)
    mean_rho = sum(model.rho.values()) / len(model.rho)
    return {"active": active, "mean_rho": mean_rho}
