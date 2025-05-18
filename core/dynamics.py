import numpy as np
from .montecarlo import monte_carlo_sweep, relax_phases

def step_simulation(model, num_mc_sweeps=1, num_relax_steps=5):
    """
    Effectue une étape de simulation pour le modèle WB
    
    Args:
        model (WBModel): Instance du modèle WB
        num_mc_sweeps (int): Nombre de balayages Monte Carlo à effectuer
        num_relax_steps (int): Nombre d'étapes de relaxation de phase
        
    Returns:
        dict: Statistiques de l'étape de simulation
    """
    # 1. Étape Monte Carlo: tentatives de flip avec l'algorithme de Metropolis
    mc_stats = monte_carlo_sweep(model, num_sweeps=num_mc_sweeps)
    
    # 2. Relaxation des phases φ
    coherence = relax_phases(model, num_steps=num_relax_steps)
    
    # Statistiques de l'étape
    stats = {
        "flips": mc_stats["flips"],
        "energy_delta": mc_stats["energy_delta"],
        "acceptance_ratio": mc_stats["acceptance_ratio"],
        "coherence": coherence,
        "num_active": model.count_active_nodes(),
        "N_pot": model.N_pot
    }
    
    return stats

def run_simulation(model, num_steps, num_mc_sweeps=1, num_relax_steps=5, callback=None):
    """
    Exécute une simulation complète du modèle WB
    
    Args:
        model (WBModel): Instance du modèle WB
        num_steps (int): Nombre d'étapes de simulation
        num_mc_sweeps (int): Nombre de balayages Monte Carlo par étape
        num_relax_steps (int): Nombre d'étapes de relaxation par étape
        callback (function, optional): Fonction appelée après chaque étape
        
    Returns:
        list: Historique des statistiques de simulation
    """
    history = []
    
    print(f"Simulation démarrée avec {model.num_nodes} nœuds")
    print(f"Paramètres: T_eff={model.config['T_eff']}, DeltaE={model.config['DeltaE']}, J={model.config['J_Wb_normal']}, J'={model.config['J_prime_Wb_ts']}")
    print(f"État initial: N_pot={model.N_pot:.2f}, Num_A={model.count_active_nodes()}")
    
    for step in range(num_steps):
        # Exécution d'une étape de simulation
        stats = step_simulation(model, num_mc_sweeps, num_relax_steps)
        
        # Ajout des statistiques à l'historique
        stats["step"] = step
        history.append(stats)
        
        # Appel du callback si fourni
        if callback:
            callback(model, step, stats)
        
        # Affichage périodique
        if step % max(1, num_steps // 20) == 0 or step == num_steps - 1:
            print(f"Étape {step:5d}: N_pot={stats['N_pot']:8.2f}, Num_A={stats['num_active']:5d}, "
                  f"Cohérence={stats['coherence']:.3f}, Acc_Ratio={stats['acceptance_ratio']:.4f}")
            
            # Vérification si N_pot est épuisé
            if model.N_pot <= 1e-9 and model.config["delta_Npot_base_actualisation"] > 0:
                print("N_pot épuisé (ou très proche de zéro).")
    
    print("Simulation terminée.")
    return history

def calculate_order_parameters(model):
    """
    Calcule les paramètres d'ordre du système
    
    Args:
        model (WBModel): Instance du modèle WB
        
    Returns:
        dict: Paramètres d'ordre calculés
    """
    # Calcul de la cohérence des phases (paramètre d'ordre XY)
    coherence = model.get_coherence()
    
    # Calcul de la magnétisation (proportion d'états A)
    num_active = model.count_active_nodes()
    magnetization = (2 * num_active / model.num_nodes) - 1 if model.num_nodes > 0 else 0
    
    # Calcul de la densité moyenne effective
    rho_values = [model.get_effective_rho(node) for node in range(model.num_nodes)]
    rho_mean = np.mean(rho_values) if rho_values else 0
    
    return {
        "coherence": coherence,
        "magnetization": magnetization,
        "rho_mean": rho_mean,
        "num_active": num_active,
        "N_pot_ratio": model.N_pot / model.N_pot_max if model.N_pot_max > 0 else 0
    }

def analyze_phase_structure(model):
    """
    Analyse la structure des phases dans le système
    
    Args:
        model (WBModel): Instance du modèle WB
        
    Returns:
        dict: Résultats de l'analyse
    """
    # Récupération des nœuds actifs (état A)
    active_nodes = [node for node in range(model.num_nodes) if model.sigma.get(node, -1) == 1]
    num_active = len(active_nodes)
    
    if num_active == 0:
        return {"clusters": 0, "largest_cluster": 0, "cluster_sizes": []}
    
    # Construction du sous-graphe des nœuds actifs
    active_edges = []
    for node in active_nodes:
        neighbors = model.graph.get_neighbors(node)
        for neighbor in neighbors:
            if neighbor in active_nodes:
                active_edges.append((node, neighbor))
    
    # Analyse des clusters (composantes connexes)
    clusters = []
    visited = set()
    
    for node in active_nodes:
        if node not in visited:
            # Nouveau cluster
            cluster = []
            queue = [node]
            visited.add(node)
            
            while queue:
                current = queue.pop(0)
                cluster.append(current)
                
                # Ajout des voisins actifs non visités
                for neighbor in model.graph.get_neighbors(current):
                    if neighbor in active_nodes and neighbor not in visited:
                        queue.append(neighbor)
                        visited.add(neighbor)
            
            clusters.append(cluster)
    
    # Calcul des tailles des clusters
    cluster_sizes = [len(cluster) for cluster in clusters]
    
    return {
        "clusters": len(clusters),
        "largest_cluster": max(cluster_sizes) if cluster_sizes else 0,
        "cluster_sizes": cluster_sizes
    }