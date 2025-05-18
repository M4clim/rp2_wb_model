# core/phase_dynamics.py
import random

import numpy as np


def next_twist_step(model, i):
    """
    Retourne un voisin j choisi selon la métrique effective.
    """
    neigh = list(model.graph.graph.neighbors(i))
    # Calculer/collecter les poids
    weights = []
    for j in neigh:
        w_iso = model.g_eff_iso[i]
        w_aniso = model.g_eff_aniso[i] * model.g_eff_T.get((i, j), 0.0)
        weights.append(w_iso + w_aniso)
    # Normaliser
    total = sum(weights)
    probs = [w / total for w in weights]
    # Tirage au sort pondéré
    return random.choices(neigh, probs)[0]


def update_phase_and_rho(model, c2, c3):
    """
    Met à jour les phases et les densités en fonction de la dynamique du modèle.

    Args:
        model: Le modèle WB
        c2: Coefficient pour le terme de gradient
        c3: Coefficient pour le terme de densité
    """
    # Créer des dictionnaires pour stocker les nouvelles valeurs
    new_phi = {}
    new_rho = {}

    # Mise à jour des phases
    for i in model.graph.graph.nodes:
        # Récupérer les voisins actifs
        j = next_twist_step(model, i)
        if j is None:
            # Si pas de voisins actifs, garder la même phase
            new_phi[i] = model.phi.get(i, 0.0)
        else:
            # Moyenne vectorielle des e^{i φ_j}
            vec_sum = np.exp(1j * model.phi.get(j, 0.0))
            avg_arg = np.angle(vec_sum)

            # Gradient discret sur le graphe
            grad2 = (model.rho.get(i, 0.0) - model.rho.get(j, 0.0)) ** 2
            Omega = c3 * model.rho.get(i, 0.0) + c2 * grad2

            # Mettre à jour la phase
            new_phi[i] = (avg_arg + Omega) % (2 * np.pi)

    # Mise à jour des densités
    for i in model.graph.graph.nodes:
        # Récupérer les voisins actifs
        j = next_twist_step(model, i)
        if j is None:
            # Si pas de voisins actifs, densité nulle
            new_rho[i] = 0.1 if model.sigma.get(i, -1) == -1 else 0.6
        else:
            # Calculer la cohérence de phase locale
            vec_sum = np.exp(1j * new_phi.get(j, 0.0))
            coherence = np.abs(vec_sum)

            # La densité est proportionnelle au carré de la cohérence
            base = 0.1 if model.sigma.get(i, -1) == -1 else 0.6
            new_rho[i] = base + 0.3 * coherence**2

    # Mettre à jour le modèle
    model.phi.update(new_phi)
    model.rho.update(new_rho)
