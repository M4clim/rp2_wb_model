import numpy as np

class WBModel:
    """
    Modèle Wolfram-Bogoliubov (WB) avec champs ρ, φ, σ et mécanismes de flip
    
    Le modèle WB implémente:
    - σ (sigma): Champ de spin binaire (-1 pour état P, +1 pour état A)
    - φ (phi): Champ de phase (0 à 2π)
    - N_pot: Réservoir de ressources (lié à ρ)
    """
    def __init__(self, graph, config=None):
        """
        Initialise le modèle WB avec un graphe RP2
        
        Args:
            graph (RP2Graph): Instance de graphe RP2
            config (dict, optional): Configuration du modèle
        """
        self.graph = graph
        self.network = graph.get_graph()
        self.num_nodes = self.network.number_of_nodes()
        
        # Configuration par défaut
        self.config = {
            # Paramètres énergétiques
            "E0": 0.0,                  # Énergie de base
            "DeltaE": 0.1,              # Écart d'énergie P→A
            "J_Wb_normal": 1.0,         # Couplage normal
            "J_prime_Wb_ts": 1.0,       # Couplage TS
            "T_eff": 0.1,               # Température effective
            
            # Paramètres de barrière
            "V0_base": 0.5,             # Hauteur de barrière de base
            "N_pot_max_sites_factor": 10.0,  # Facteur pour N_pot_max
            "N_pot_initial_fraction": 0.9,   # Fraction initiale de N_pot
            "eta1": 1.0,                # Exposant pour G_Npot
            "eta2": 1.0,                # Exposant pour F_Npot
            "alpha_phase": 0.5,         # Facteur de dépendance de phase
            "beta_asym": 2.0,           # Asymétrie A→P vs P→A
            "delta_Npot_base_actualisation": 0.1,  # Coût de base pour P→A
            
            # Paramètres de relaxation
            "delta_phi_relaxation_step": 0.1,  # Pas de relaxation de phase
        }
        
        # Mise à jour avec la configuration fournie
        if config:
            self.config.update(config)
        
        # Initialisation des champs
        self.sigma = {}  # Champ σ (spin)
        self.phi = {}    # Champ φ (phase)
        
        # Initialisation du réservoir N_pot
        self.N_pot_max = self.num_nodes * self.config["N_pot_max_sites_factor"]
        self.N_pot = self.N_pot_max * self.config["N_pot_initial_fraction"]
        
    def initialize_fields(self, sigma_config="all_P", phi_config="random", random_seed=None):
        """
        Initialise les champs σ, φ pour tous les nœuds du graphe
        
        Args:
            sigma_config (str): Configuration initiale de σ ("all_P", "center_A", "random")
            phi_config (str): Configuration initiale de φ ("uniform_zero", "random")
            random_seed (int, optional): Graine pour la génération aléatoire
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Initialisation de σ (spin)
        if sigma_config == "all_P":
            # Tous les nœuds en état P (-1)
            for node in self.network.nodes():
                self.sigma[node] = -1
        elif sigma_config == "center_A":
            # Tous en P sauf le centre en A
            for node in self.network.nodes():
                self.sigma[node] = -1
            
            # Trouver le nœud central
            if self.num_nodes > 0:
                center_node = self.num_nodes // 2
                self.sigma[center_node] = 1
        else:  # random
            for node in self.network.nodes():
                self.sigma[node] = np.random.choice([-1, 1])
        
        # Initialisation de φ (phase)
        if phi_config == "uniform_zero":
            for node in self.network.nodes():
                self.phi[node] = 0.0
        else:  # random
            for node in self.network.nodes():
                self.phi[node] = np.random.uniform(0, 2 * np.pi)
        
        print(f"Champs initialisés pour {self.num_nodes} nœuds")
        print(f"État initial: N_pot={self.N_pot:.2f}, Num_A={self.count_active_nodes()}")
    
    def count_active_nodes(self):
        """
        Compte le nombre de nœuds en état A (σ = +1)
        
        Returns:
            int: Nombre de nœuds actifs
        """
        return sum(1 for s in self.sigma.values() if s == 1)
    
    def get_node_state(self, node):
        """
        Retourne l'état complet d'un nœud
        
        Args:
            node: Identifiant du nœud
            
        Returns:
            dict: État du nœud avec ses champs
        """
        return {
            'sigma': self.sigma.get(node, 0),
            'phi': self.phi.get(node, 0),
            'rho': self.get_effective_rho(node)  # ρ effectif calculé
        }
    
    def get_effective_rho(self, node):
        """
        Calcule la densité effective ρ pour un nœud
        Dans ce modèle, ρ est lié à l'état σ et au réservoir N_pot
        
        Args:
            node: Identifiant du nœud
            
        Returns:
            float: Densité effective ρ
        """
        if self.sigma.get(node, -1) == -1:
            # État P: faible densité
            return 0.1
        else:
            # État A: densité dépendant de N_pot
            n_pot_ratio = self.N_pot / self.N_pot_max if self.N_pot_max > 0 else 0
            return 0.3 + 0.7 * n_pot_ratio  # Varie entre 0.3 et 1.0
    
    def flip_spin(self, node):
        """
        Inverse le spin d'un nœud (sans vérifier les contraintes énergétiques)
        
        Args:
            node: Identifiant du nœud
            
        Returns:
            bool: True si le flip a été effectué
        """
        if node in self.sigma:
            self.sigma[node] *= -1
            return True
        return False
    
    def calculate_interaction_energy(self, node1, node2):
        """
        Calcule l'énergie d'interaction entre deux nœuds
        
        Args:
            node1, node2: Identifiants des nœuds
            
        Returns:
            float: Énergie d'interaction
        """
        # Récupération des états
        sigma_i = self.sigma.get(node1, 0)
        sigma_j = self.sigma.get(node2, 0)
        phi_i = self.phi.get(node1, 0)
        phi_j = self.phi.get(node2, 0)
        
        # Vérification si le lien est TS
        is_ts = self.graph.is_ts(node1, node2)
        
        # Calcul de l'énergie d'interaction
        energy = 0.0
        if sigma_i == 1 and sigma_j == 1:
            # Interaction entre états A
            J_eff = self.config["J_prime_Wb_ts"] if is_ts else self.config["J_Wb_normal"]
            A_top = np.pi if is_ts else 0.0
            energy = -J_eff * np.cos(phi_i - phi_j - A_top)
        
        return energy
    
    def calculate_node_energy(self, node):
        """
        Calcule l'énergie totale d'un nœud
        
        Args:
            node: Identifiant du nœud
            
        Returns:
            float: Énergie totale du nœud
        """
        sigma_i = self.sigma.get(node, 0)
        
        # Énergie de base et terme DeltaE
        N_pot_ratio = self.N_pot / self.N_pot_max if self.N_pot_max > 0 else 0
        DeltaE_current = self.config["DeltaE"] * (2.0 * N_pot_ratio - 1.0)
        energy = self.config["E0"] - sigma_i * DeltaE_current
        
        # Ajout des interactions avec les voisins
        for neighbor in self.graph.get_neighbors(node):
            energy += self.calculate_interaction_energy(node, neighbor)
        
        return energy
    
    def calculate_barrier_cost(self, node, proposed_sigma):
        """
        Calcule le coût de barrière pour une transition
        
        Args:
            node: Identifiant du nœud
            proposed_sigma: Valeur proposée pour σ
            
        Returns:
            float: Coût de barrière total
        """
        current_sigma = self.sigma.get(node, 0)
        total_barrier = 0.0
        potential_N_pot_consumption = 0.0
        
        # Parcours des voisins pour calculer les barrières
        for neighbor in self.graph.get_neighbors(node):
            is_ts = self.graph.is_ts(node, neighbor)
            if not is_ts:
                continue  # Barrières uniquement sur les liens TS
            
            neighbor_sigma = self.sigma.get(neighbor, 0)
            phi_i = self.phi.get(node, 0)
            phi_j = self.phi.get(neighbor, 0)
            
            barrier = 0.0
            A_top = np.pi  # Pour les liens TS
            phase_term = self.config["alpha_phase"] * (1.0 - np.cos(phi_i - phi_j - A_top))
            
            if current_sigma == -1 and proposed_sigma == 1:  # P→A
                # Facteur G_Npot qui AUGMENTE quand N_pot DIMINUE
                G_Npot_factor = 1.0 - self.N_pot / self.N_pot_max
                G_Npot_factor = max(0.0, G_Npot_factor)
                G_Npot = np.power(max(0.01, G_Npot_factor), self.config["eta1"])
                
                barrier = self.config["V0_base"] * (1.0 + phase_term) * G_Npot
                potential_N_pot_consumption += barrier
                
            elif current_sigma == 1 and proposed_sigma == -1:  # A→P
                if neighbor_sigma == 1:
                    # Facteur F_Npot qui DIMINUE avec N_pot
                    F_Npot_factor = self.N_pot / self.N_pot_max
                    F_Npot_factor = max(0.0, F_Npot_factor)
                    F_Npot = np.power(max(0.01, F_Npot_factor), self.config["eta2"])
                    
                    barrier = self.config["V0_base"] * (self.config["beta_asym"] + phase_term) * F_Npot
            
            total_barrier += barrier
        
        return total_barrier, potential_N_pot_consumption
    
    def can_afford_transition(self, node, proposed_sigma):
        """
        Vérifie si une transition est possible compte tenu de N_pot
        
        Args:
            node: Identifiant du nœud
            proposed_sigma: Valeur proposée pour σ
            
        Returns:
            tuple: (can_afford, cost)
        """
        current_sigma = self.sigma.get(node, 0)
        
        # Seules les transitions P→A consomment N_pot
        if current_sigma == -1 and proposed_sigma == 1:
            _, potential_consumption = self.calculate_barrier_cost(node, proposed_sigma)
            total_cost = self.config["delta_Npot_base_actualisation"] + potential_consumption
            
            return self.N_pot >= total_cost, total_cost
        
        return True, 0.0
    
    def update_N_pot(self, cost):
        """
        Met à jour le réservoir N_pot
        
        Args:
            cost: Coût à soustraire de N_pot
            
        Returns:
            float: Nouvelle valeur de N_pot
        """
        self.N_pot = max(0.0, self.N_pot - cost)
        return self.N_pot
    
    def get_coherence(self):
        """
        Calcule la cohérence moyenne des phases pour les nœuds actifs
        
        Returns:
            float: Cohérence moyenne (0-1)
        """
        active_phis = [self.phi[node] for node in self.network.nodes() 
                      if self.sigma.get(node, 0) == 1]
        
        if not active_phis:
            return 0.0
        
        # Calcul du paramètre d'ordre complexe
        complex_order = np.mean(np.exp(1j * np.array(active_phis)))
        return np.abs(complex_order)