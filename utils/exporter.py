import json
import os
import numpy as np

def export_to_json(model, filename="outputs/model_state.json"):
    """
    Exporte l'état du modèle WB au format JSON pour Godot
    
    Args:
        model (WBModel): Instance du modèle WB
        filename (str): Chemin du fichier de sortie
        
    Returns:
        str: Chemin du fichier créé
    """
    # Création du dossier de sortie si nécessaire
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Préparation des données pour le JSON
    data = {
        "metadata": {
            "timestamp": np.datetime64('now').astype(str),
            "node_count": len(model.network.nodes()),
            "edge_count": len(model.network.edges())
        },
        "nodes": {},
        "edges": []
    }
    
    # Conversion des positions des nœuds et de leurs états
    for node in model.network.nodes():
        # Récupération de la position du nœud
        pos = model.network.nodes[node].get('pos', (0, 0))
        
        # Conversion des tuples en identifiants de chaîne pour le JSON
        node_id = f"{node[0]}_{node[1]}_{node[2]}" if isinstance(node, tuple) else str(node)
        
        # Ajout des données du nœud
        data["nodes"][node_id] = {
            "position": {"x": float(pos[0]), "y": float(pos[1]), "z": 0.0},
            "rho": float(model.rho.get(node, 0)),
            "phi": float(model.phi.get(node, 0)),
            "sigma": int(model.sigma.get(node, 0))
        }
    
    # Conversion des liens
    for edge in model.network.edges():
        source, target = edge
        source_id = f"{source[0]}_{source[1]}_{source[2]}" if isinstance(source, tuple) else str(source)
        target_id = f"{target[0]}_{target[1]}_{target[2]}" if isinstance(target, tuple) else str(target)
        
        data["edges"].append({
            "source": source_id,
            "target": target_id
        })
    
    # Écriture du fichier JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Modèle exporté vers {filename}")
    return filename

def export_simulation_stats(stats, filename="outputs/simulation_stats.json"):
    """
    Exporte les statistiques de simulation au format JSON
    
    Args:
        stats (list): Liste des statistiques par étape
        filename (str): Chemin du fichier de sortie
        
    Returns:
        str: Chemin du fichier créé
    """
    # Création du dossier de sortie si nécessaire
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Écriture du fichier JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Statistiques exportées vers {filename}")
    return filename