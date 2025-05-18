# core/phase_dynamics.py
import numpy as np


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
        neigh = [j for j in model.graph.get_neighbors(i) if model.sigma.get(j, -1) == 1]

        if not neigh:
            # Si pas de voisins actifs, garder la même phase
            new_phi[i] = model.phi.get(i, 0.0)
        else:
            # Moyenne vectorielle des e^{i φ_j}
            vec_sum = sum(np.exp(1j * model.phi.get(j, 0.0)) for j in neigh)
            avg_arg = np.angle(vec_sum)

            # Gradient discret sur le graphe
            grad2 = sum(
                (model.rho.get(i, 0.0) - model.rho.get(j, 0.0)) ** 2 for j in neigh
            )
            Omega = c3 * model.rho.get(i, 0.0) + c2 * grad2

            # Mettre à jour la phase
            new_phi[i] = (avg_arg + Omega) % (2 * np.pi)

    # Mise à jour des densités
    for i in model.graph.graph.nodes:
        # Récupérer les voisins actifs
        neigh = [j for j in model.graph.get_neighbors(i) if model.sigma.get(j, -1) == 1]

        if not neigh:
            # Si pas de voisins actifs, densité nulle
            new_rho[i] = 0.1 if model.sigma.get(i, -1) == -1 else 0.6
        else:
            # Calculer la cohérence de phase locale
            vec_sum = sum(np.exp(1j * new_phi.get(j, 0.0)) for j in neigh)
            coherence = np.abs(vec_sum / len(neigh))

            # La densité est proportionnelle au carré de la cohérence
            base = 0.1 if model.sigma.get(i, -1) == -1 else 0.6
            new_rho[i] = base + 0.3 * coherence**2

    # Mettre à jour le modèle
    model.phi.update(new_phi)
    model.rho.update(new_rho)
