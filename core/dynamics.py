import cmath
import math
from typing import Any, Dict

from core.cluster_utils import find_soliton_clusters
from core.metric_effective import compute_g_eff
from core.montecarlo import metropolis_step
from core.phase_dynamics import next_twist_step, update_phase_and_rho
from core.wb_model import WBModel


def step_simulation(model: WBModel, step_id: int, params) -> dict:
    """
    0) Mise à jour dynamique de model.Lambda_vac (UNE FOIS)
    1) Flips MC (P↔A) avec coût dépendant de model.Lambda_vac
    2) Calcul de la métrique effective
    3) Mise à jour de phi & rho (vectorielle + Ω)
    4) Relaxation simple (1 passe)
    5) Retourne les stats pour tracé
    """

    # 0) Mise à jour de Lambda_vac UNE SEULE FOIS
    Phi_Wb = sum(1 for s in model.sigma.values() if s == 1)
    Lmin = params.get("L_min", 0.2)
    L0 = params.get("L0", 1.0)
    kφ = params.get("k_phi", 0.01)
    model.Lambda_vac = Lmin + (L0 - Lmin) * math.exp(-kφ * Phi_Wb)

    # 1) Flips Monte Carlo
    metropolis_step(model, T=params.get("T_eff", 1.0))

    # 2) Calcul de la métrique effective
    compute_g_eff(
        model,
        alpha=params.get("alpha", 1.0),
        n=params.get("n_power", 1.0),
        beta=params.get("beta", 1.0),
        eps0=params.get("eps0", 1.0),
        m=params.get("m_power", 1.0),
        p=params.get("p_power", 1.0),
    )
    for _ in range(params.get("twist_steps_per_iter", 5)):
        for twist in model.graph.graph.nodes:
            twist = next_twist_step(model, twist)

    # 3) Dynamique de phase & rho
    update_phase_and_rho(model, c2=params.get("c2", 1.0), c3=params.get("c3", 1.5))

    # 3bis) Cluster detection & refund
    # Seuil et facteur à régler dans params
    threshold = params.get("rho_soliton_threshold", 0.6)
    refund_factor = params.get("sol_refund_factor", 0.2)
    clusters = find_soliton_clusters(model.graph, model.rho, threshold)
    for cluster in clusters:
        # Si cluster actif avant et entièrement inactif maintenant → dissolution
        was_active = any(model.prev_sigma.get(n, 0) == 1 for n in cluster)
        now_inactive = all(model.sigma.get(n, 0) != 1 for n in cluster)
        if was_active and now_inactive:
            # Calcul de l'énergie effective
            E_sol = sum(model.rho.get(n, 0) for n in cluster)
            refund = refund_factor * E_sol
            # remboursement
            model.consume_N_pot(-refund)

    # 4) Relaxation simple (1 passe)
    new_phis = {}
    for n in model.graph.graph.nodes:
        if model.sigma.get(n, 0) != 1:
            continue
        neighs = [j for j in model.graph.get_neighbors(n) if model.sigma.get(j, 0) == 1]
        if len(neighs) == 0:
            continue
        # moyenne vectorielle
        vec = sum(cmath.exp(1j * model.phi[j]) for j in neighs)
        avg_angle = cmath.phase(vec)
        new_phis[n] = avg_angle
    for n, angle in new_phis.items():
        model.phi[n] = angle % (2 * math.pi)

    # 5) Retour des statistiques
    stats = {
        "step": step_id,
        "N_pot": model.N_pot,
        "active": Phi_Wb,
        "Lambda_vac": model.Lambda_vac,
        "mean_rho": sum(model.rho.values()) / len(model.rho),
    }
    return stats


def run_simulation(
    model, num_steps=100, num_mc_sweeps=1, callback=None, params: Dict[str, Any] = {}
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
            stats = step_simulation(model, t, params)
            history.append(stats)

            # Appeler la fonction de callback si elle est fournie
            if callback:
                callback(model, t, stats)

    return history


def calculate_order_parameters(model):
    active = sum(1 for s in model.sigma.values() if s == 1)
    mean_rho = sum(model.rho.values()) / len(model.rho)
    return {"active": active, "mean_rho": mean_rho}
