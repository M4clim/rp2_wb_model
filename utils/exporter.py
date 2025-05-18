import json
import os


def export_to_json(model, filename: str):
    """
    Exporte l'état du modèle WB au format JSON

    Args:
        model: Instance du modèle WB
        filename: Chemin du fichier de sortie
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Vérifier si le modèle utilise graph.G ou graph.graph
    graph_attr = getattr(model.graph, "G", None)
    if graph_attr is None:
        graph_attr = getattr(model.graph, "graph", None)

    if graph_attr is None:
        raise AttributeError(
            "Le graphe du modèle n'a ni attribut 'G' ni attribut 'graph'"
        )

    # Vérifier si le modèle a un attribut rho direct
    has_rho = hasattr(model, "rho") and model.rho

    data = {
        "N_pot": float(model.N_pot),
        "nodes": [
            {
                "id": int(n),
                "sigma": int(model.sigma.get(n, 0)),
                "phi": float(model.phi.get(n, 0)),
                "rho": (
                    float(model.rho.get(n, 0))
                    if has_rho
                    else (1.0 if model.sigma.get(n, -1) == 1 else 0.1)
                ),
            }
            for n in graph_attr.nodes
        ],
        "edges": [],
    }

    # Ajouter les arêtes avec leurs attributs
    for u, v, d in graph_attr.edges(data=True):
        edge_data = {"u": int(u), "v": int(v)}

        # Ajouter l'attribut is_ts s'il existe
        if "is_ts" in d:
            edge_data["is_ts"] = bool(d["is_ts"])

        data["edges"].append(edge_data)

    # Écriture dans le fichier JSON
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"État du modèle exporté dans {filename}")
    return filename
