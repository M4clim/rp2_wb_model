import numpy as np


def metropolis_step(model, node, current_energy=None, proposed_sigma=None):
    """
    Implémente l'algorithme de Metropolis pour décider si un flip de spin
    doit être effectué

    Args:
        model (WBModel): Instance du modèle WB
        node: Identifiant du nœud à mettre à jour
        current_energy (float, optional): Énergie actuelle du nœud
                                          (calculée si None)
        proposed_sigma (int, optional): Valeur proposée pour σ
                                        (inverse de l'actuelle si None)

    Returns:
        tuple: (did_flip, energy_delta, N_pot_after) - Si un flip a été
               effectué, le changement d'énergie et N_pot après
    """
    # Récupération de l'état actuel
    current_sigma = model.sigma.get(node, 0)

    # Si proposed_sigma n'est pas spécifié, on propose l'inverse de l'état actuel
    if proposed_sigma is None:
        proposed_sigma = -current_sigma

    # Si current_energy n'est pas spécifié, on le calcule
    if current_energy is None:
        current_energy = model.calculate_node_energy(node)

    # Sauvegarde de l'état actuel
    original_sigma = current_sigma

    # Flip temporaire du spin pour calculer la nouvelle énergie
    model.sigma[node] = proposed_sigma
    proposed_energy = model.calculate_node_energy(node)

    # Restauration de l'état original
    model.sigma[node] = original_sigma

    # Calcul de la différence d'énergie de base (sans barrière)
    delta_energy_base = proposed_energy - current_energy

    # Calcul du coût de barrière pour cette transition
    barrier_cost, potential_consumption = model.calculate_barrier_cost(
        node, proposed_sigma
    )

    # Différence d'énergie totale incluant la barrière
    delta_energy_total = delta_energy_base + barrier_cost

    # Vérification si la transition est possible compte tenu de N_pot
    can_afford, cost_for_N_pot = model.can_afford_transition(node, proposed_sigma)

    # Initialisation du résultat
    did_flip = False
    N_pot_after = model.N_pot

    # Application de l'algorithme de Metropolis seulement si N_pot est suffisant
    if can_afford:
        # Règle de Metropolis pour l'acceptation du flip
        if delta_energy_total <= 0:
            # Si l'énergie diminue, accepter le changement
            did_flip = True
        else:
            # Sinon, accepter avec une probabilité qui dépend de la température
            T_eff = model.config["T_eff"]
            if T_eff > 1e-9:  # Éviter division par zéro
                acceptance_probability = np.exp(-delta_energy_total / T_eff)
                if np.random.random() < acceptance_probability:
                    did_flip = True

    # Si le flip est accepté, mettre à jour l'état et N_pot
    if did_flip:
        model.sigma[node] = proposed_sigma

        # Mise à jour de N_pot si nécessaire (transition P→A)
        if original_sigma == -1 and proposed_sigma == 1:
            N_pot_after = model.update_N_pot(cost_for_N_pot)

    return (did_flip, delta_energy_total, N_pot_after)


def monte_carlo_sweep(model, num_sweeps=1):
    """
    Effectue un ou plusieurs balayages Monte Carlo sur tous les nœuds du graphe

    Args:
        model (WBModel): Instance du modèle WB
        num_sweeps (int): Nombre de balayages à effectuer

    Returns:
        dict: Statistiques des balayages
    """
    network = model.network
    num_nodes = network.number_of_nodes()
    total_flips = 0
    total_energy_delta = 0.0

    for _ in range(num_sweeps):
        # Parcours des nœuds dans un ordre aléatoire
        node_indices = np.random.permutation(num_nodes)

        for node_idx in node_indices:
            # Tentative de flip avec l'algorithme de Metropolis
            did_flip, energy_delta, _ = metropolis_step(model, node_idx)

            # Mise à jour des statistiques
            if did_flip:
                total_flips += 1
                total_energy_delta += energy_delta

    # Calcul des statistiques
    acceptance_ratio = (
        total_flips / (num_sweeps * num_nodes) if num_sweeps * num_nodes > 0 else 0
    )

    return {
        "flips": total_flips,
        "energy_delta": total_energy_delta,
        "acceptance_ratio": acceptance_ratio,
    }


def relax_phases(model, num_steps=1):
    """
    Relaxe les phases φ selon un modèle XY

    Args:
        model (WBModel): Instance du modèle WB
        num_steps (int): Nombre d'étapes de relaxation

    Returns:
        float: Cohérence moyenne des phases après relaxation
    """
    network = model.network
    num_nodes = network.number_of_nodes()
    delta_phi = model.config["delta_phi_relaxation_step"]

    for _ in range(num_steps):
        # Calcul des forces sur les phases
        phi_forces = np.zeros(num_nodes)

        for i in range(num_nodes):
            # Seuls les nœuds en état A (σ=+1) participent à la relaxation
            if model.sigma.get(i, -1) == 1:
                phi_force = 0.0

                # Parcours des voisins
                for j in model.graph.get_neighbors(i):
                    # Seules les interactions A-A contribuent
                    if model.sigma.get(j, -1) == 1:
                        # Vérification si le lien est TS
                        is_ts = model.graph.is_ts(i, j)

                        # Paramètres d'interaction
                        J_eff = (
                            model.config["J_prime_Wb_ts"]
                            if is_ts
                            else model.config["J_Wb_normal"]
                        )
                        A_top = np.pi if is_ts else 0.0

                        # Force sur la phase
                        phi_force += -J_eff * np.sin(
                            model.phi.get(i, 0) - model.phi.get(j, 0) - A_top
                        )

                phi_forces[i] = phi_force

        # Mise à jour des phases
        for i in range(num_nodes):
            if model.sigma.get(i, -1) == 1:
                # Mise à jour de la phase selon la force
                model.phi[i] = model.phi.get(i, 0) + delta_phi * phi_forces[i]

                # Normalisation dans [0, 2π]
                model.phi[i] = model.phi[i] % (2 * np.pi)
                if model.phi[i] < 0:
                    model.phi[i] += 2 * np.pi

    # Calcul de la cohérence finale
    return model.get_coherence()
