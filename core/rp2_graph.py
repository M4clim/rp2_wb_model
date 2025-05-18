import math
from typing import Any, Dict, List, Set, Tuple

import networkx as nx
import numpy as np


class RP2Graph:
    """
    Classe qui encapsule un graphe NetworkX pour le modèle RP2-WB.
    Dans la version 3, le graphe est stocké dans l'attribut 'graph' (et non plus 'G').
    """

    def __init__(self, radius: int = 5, ts_links_fraction: float = 0.1):
        """
        Initialise un graphe RP2 avec un rayon donné.

        Args:
            radius: Rayon du patch hexagonal
            ts_links_fraction: Fraction des liens qui sont topologiquement sensibles (TS)
        """
        self.radius = radius
        self.ts_links_fraction = ts_links_fraction
        self.graph = nx.Graph()

        # Créer le graphe hexagonal
        self._create_hexagonal_lattice()

        # Ajouter les liens TS
        self._add_ts_links()

    def _create_hexagonal_lattice(self):
        """Crée un réseau hexagonal de rayon donné."""
        # Coordonnées des voisins dans un réseau hexagonal
        directions = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

        # Créer les nœuds
        node_id = 0
        for q in range(-self.radius, self.radius + 1):
            r_min = max(-self.radius, -q - self.radius)
            r_max = min(self.radius, -q + self.radius)
            for r in range(r_min, r_max + 1):
                # Convertir les coordonnées hexagonales en coordonnées cartésiennes
                x = q * 1.5
                y = r * math.sqrt(3) + q * math.sqrt(3) / 2

                # Ajouter le nœud avec ses coordonnées
                self.graph.add_node(node_id, pos=(x, y), q=q, r=r)
                node_id += 1

        # Créer les arêtes
        for node in self.graph.nodes:
            q, r = self.graph.nodes[node]["q"], self.graph.nodes[node]["r"]
            for dq, dr in directions:
                q2, r2 = q + dq, r + dr

                # Vérifier si le voisin est dans le graphe
                for neighbor in self.graph.nodes:
                    if (
                        self.graph.nodes[neighbor]["q"] == q2
                        and self.graph.nodes[neighbor]["r"] == r2
                    ):
                        self.graph.add_edge(node, neighbor, is_ts=False)
                        break

    def _add_ts_links(self):
        """Ajoute des liens topologiquement sensibles (TS) au graphe."""
        # Calculer le nombre de liens TS à ajouter
        total_edges = self.graph.number_of_edges()
        ts_count = int(total_edges * self.ts_links_fraction)

        # Sélectionner aléatoirement des liens à marquer comme TS
        edges = list(self.graph.edges())
        np.random.shuffle(edges)

        for i in range(min(ts_count, len(edges))):
            u, v = edges[i]
            self.graph[u][v]["is_ts"] = True

    def get_neighbors(self, node: int) -> List[int]:
        """
        Retourne la liste des voisins d'un nœud.

        Args:
            node: Identifiant du nœud

        Returns:
            Liste des identifiants des voisins
        """
        return list(self.graph.neighbors(node))

    def is_ts(self, u: int, v: int) -> bool:
        """
        Vérifie si le lien entre u et v est topologiquement sensible.

        Args:
            u: Premier nœud
            v: Second nœud

        Returns:
            True si le lien est TS, False sinon
        """
        if self.graph.has_edge(u, v):
            return self.graph[u][v].get("is_ts", False)
        return False

    def get_node_position(self, node: int) -> Tuple[float, float]:
        """
        Retourne la position d'un nœud.

        Args:
            node: Identifiant du nœud

        Returns:
            Tuple (x, y) des coordonnées du nœud
        """
        return self.graph.nodes[node]["pos"]

    def get_all_node_positions(self) -> Dict[int, Tuple[float, float]]:
        """
        Retourne un dictionnaire des positions de tous les nœuds.

        Returns:
            Dictionnaire {node_id: (x, y)}
        """
        return {n: self.graph.nodes[n]["pos"] for n in self.graph.nodes}

    def export_to_dict(self) -> Dict[str, Any]:
        """
        Exporte le graphe sous forme de dictionnaire pour la sérialisation JSON.

        Returns:
            Dictionnaire contenant les nœuds et les arêtes du graphe
        """
        nodes = []
        for n in self.graph.nodes:
            x, y = self.graph.nodes[n]["pos"]
            nodes.append({"id": n, "x": x, "y": y})

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({"u": u, "v": v, "is_ts": data.get("is_ts", False)})

        return {"nodes": nodes, "edges": edges}
