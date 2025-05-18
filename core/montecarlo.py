import math
import random

from core.wb_model import WBModel

RHO_SOLITON_THRESHOLD = 0.6  # ρ au-dessus = on considère soliton
SOLITON_REFUND_FACTOR = 0.2  # fraction de ρ remboursée à la dissolution


def metropolis_step(model: WBModel, T: float = 1.0):
    nodes = list(model.graph.graph.nodes)
    random.shuffle(nodes)
    for n in nodes:
        # Enlever la condition d'arrêt quand N_pot est nul pour permettre les transitions A→P
        # qui vont recharger le réservoir

        dE = model.delta_energy_flip(n)
        # Λ_vac influence P→A : plus Λ bas, moins de flips

        Λ_vac = model.Lambda_vac

        # Différencier les coûts selon le type de transition
        if model.sigma[n] == -1:  # P→A (actualisation)
            base_cost = 1.0 * Λ_vac  # Coût positif
        else:  # A→P (désactualisation)
            # Option plus fine : rendre proportionnel à ρ
            rho_n = model.rho[n]
            if rho_n >= RHO_SOLITON_THRESHOLD:
                # remboursement proportionnel à la densité du soliton
                base_cost = -SOLITON_REFUND_FACTOR * rho_n
            else:
                base_cost = 0.0
        # Calcul de la probabilité d'acceptation
        prob = 1.0 if dE < 0 else math.exp(-dE / T)

        # Condition d'acceptation modifiée pour permettre les transitions A→P même si N_pot est bas
        if random.random() < prob:
            # Pour P→A, vérifier qu'on a assez de potentiel
            if model.sigma[n] == -1 and model.N_pot < base_cost:
                continue  # Pas assez de potentiel pour cette actualisation

            model.apply_flip(n)
            model.consume_N_pot(base_cost)
