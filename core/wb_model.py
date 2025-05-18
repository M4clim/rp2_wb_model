from __future__ import annotations

import math
import random
from typing import Any, Dict

from numba import njit
from numpy.polynomial.tests.test_laguerre import L0


class WBModel:
    """Contient σ, φ, ρ et le réservoir N_pot."""

    def __init__(self, graph: "RP2Graph", config: Dict[str, Any] = None):
        self.graph = graph
        self.Lambda_vac = L0  # initial
        # Paramètres par défaut
        N_pot_max = 1000.0
        N_pot_initial_fraction = 0.8

        # Si config est fourni, utiliser les valeurs du dictionnaire
        if isinstance(config, dict):
            N_pot_max = config.get("N_pot_max_sites_factor", 10.0) * len(
                graph.graph.nodes
            )
            N_pot_initial_fraction = config.get("N_pot_initial_fraction", 0.8)

        self.N_pot_max = N_pot_max
        self.N_pot = N_pot_initial_fraction * N_pot_max
        self.sigma: Dict[int, int] = {}
        self.phi: Dict[int, float] = {}
        self.rho: Dict[int, float] = {}
        self.prev_sigma = dict(self.sigma)

    # ------------------ INIT ------------------
    def initialize_fields(self, mode: str = "random", phi_config: str = "random"):
        """
        Initialise les champs σ, φ, ρ pour tous les nœuds du graphe

        Args:
            mode: Configuration initiale de σ ("all_P", "center_A", "random")
            phi_config: Configuration initiale de φ ("uniform_zero", "random")
        """
        for n in self.graph.graph.nodes:
            if mode == "all_P":
                s = -1
            elif mode == "center_A":
                x, y = self.graph.graph.nodes[n]["pos"]
                s = 1 if x == 0 and y == 0 else -1
            else:  # 10 % activés aléatoirement
                s = 1 if random.random() < 0.1 else -1
            self.sigma[n] = s

            if phi_config == "uniform_zero":
                self.phi[n] = 0.0
            else:
                self.phi[n] = random.uniform(0, math.pi)

        self._update_rho_all()

    def consume_N_pot(self, delta: float) -> None:
        """
        Consomme (delta>0) ou rembourse (delta<0) du N_pot,
        sans jamais dépasser la valeur initiale ni passer en dessous de 0.
        """
        new_val = self.N_pot - delta
        # clamp entre 0 et N_pot_max
        self.N_pot = max(0.0, min(self.N_pot_max, new_val))

    # ------------------ ρ dynamics -------------
    def _rho_single(self, n):
        """ρ dépend de σ et du voisinage actif."""
        active = sum(1 for j in self.graph.get_neighbors(n) if self.sigma[j] == 1)
        frac = active / max(1, len(self.graph.get_neighbors(n)))
        base = 0.1 if self.sigma[n] == -1 else 0.6
        return base + 0.3 * frac

    def _update_rho_all(self):
        for n in self.graph.graph.nodes:
            self.rho[n] = self._rho_single(n)

    # ------------------ ΔE optimisé ------------
    @staticmethod
    @njit
    def _delta_energy_core(sigma_i, sigma_nbrs, phi_i, phi_nbrs, ts_flags):
        dE = 0.0
        for k in range(len(sigma_nbrs)):
            if sigma_nbrs[k] == 1:
                phase_term = math.cos(
                    phi_i - phi_nbrs[k] - (math.pi if ts_flags[k] else 0.0)
                )
                before = -1.0 * (1 if sigma_i == 1 else 0) * phase_term
                after = -1.0 * (1 if -sigma_i == 1 else 0) * phase_term
                dE += after - before
        return dE

    def delta_energy_flip(self, n: int):
        # Récupération des voisins et de leurs propriétés
        nbrs = self.graph.get_neighbors(n)
        sigma_nbrs = [self.sigma[j] for j in nbrs]
        phi_nbrs = [self.phi[j] for j in nbrs]
        ts_flags = [self.graph.is_ts(n, j) for j in nbrs]

        # Calcul de l'énergie d'interaction avec les voisins
        dE_interaction = self._delta_energy_core(
            self.sigma[n], sigma_nbrs, self.phi[n], phi_nbrs, ts_flags
        )

        # Calcul de l'énergie interne dépendant de N_pot
        # E_{int,i}(σ_i, N_pot) = E_0 - σ_i · ΔE_effective(N_pot)
        # ΔE_effective(N_pot) = ΔE_coeff · (2 · N_pot/N_potmax - 1)
        E0 = 0.0  # Valeur par défaut, à remplacer par la valeur du config
        DeltaE_coeff = 3.5  # Valeur par défaut, à remplacer par la valeur du config

        # Calcul de ΔE_effective
        N_pot_ratio = self.N_pot / max(
            0.001, self.N_pot_max
        )  # Éviter division par zéro
        DeltaE_effective = DeltaE_coeff * (2.0 * N_pot_ratio - 1.0)

        # Énergie interne avant et après le flip
        E_internal_before = E0 - self.sigma[n] * DeltaE_effective
        E_internal_after = E0 - (-self.sigma[n]) * DeltaE_effective

        # Variation d'énergie interne
        dE_internal = E_internal_after - E_internal_before

        # Énergie totale = énergie interne + énergie d'interaction
        return dE_internal + dE_interaction

    # ------------------ flips / N_pot ----------
    def apply_flip(self, n: int):
        self.prev_sigma[n] = self.sigma[n]
        self.sigma[n] = -self.sigma[n]
        self.rho[n] = self._rho_single(n)
