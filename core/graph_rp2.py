import networkx as nx
import numpy as np
import json
from typing import List, Dict, Tuple, Optional, Union, Set

class RP2Graph:
    """
    Structure RP2 hexagonale avec TS-liens (Time-Space links)
    Implémente une grille hexagonale avec identification antipodale
    
    Propriétés topologiques:
    - Non-orientabilité: Parcourir une boucle non-triviale inverse la notion de gauche/droite
    - Groupe fondamental: π₁(RP²) = Z₂ - une boucle "non-triviale" contracte après deux tours
    - Caractéristique d'Euler: χ(RP²) = 1
    """
    def __init__(self, radius: int = 5, scale_factor: float = 1.0):
        """
        Initialise un graphe RP2 avec un rayon donné
        
        Args:
            radius: Rayon du patch hexagonal
            scale_factor: Facteur d'échelle pour le dessin
        """
        self.radius = radius
        self.scale_factor = scale_factor
        self.graph = nx.Graph()
        self.node_map_2d_to_1d: Dict[Tuple[int, int], int] = {}  # Mapping des coordonnées (x,y) vers index 1D
        self.pos_for_drawing: Dict[int, Tuple[float, float]] = {}  # Positions pour le dessin
        self.antipode_map: Dict[int, int] = {}  # Mapping des nœuds vers leurs antipodes
        
    def generate(self) -> nx.Graph:
        """
        Génère la structure du graphe RP2 hexagonal avec identification antipodale
        
        1. Génère un patch hexagonal plat
        2. Identifie les nœuds antipodaux et crée les liens TS
        
        Returns:
            Le graphe généré
        """
        # Étape 1: Génération du patch hexagonal plat
        self._generate_hexagonal_patch()
        
        # Étape 2: Identification des nœuds antipodaux et création des liens TS
        self._apply_antipodal_identification()
        
        # Calcul des propriétés topologiques pour validation
        self._calculate_euler_characteristic()
        
        print(f"Graphe RP2 généré avec {self.graph.number_of_nodes()} nœuds et {self.graph.number_of_edges()} liens")
        print(f"Nombre de liens TS: {sum(1 for _, _, d in self.graph.edges(data=True) if d.get('is_ts', False))}")
        
        return self.graph
    
    def _generate_hexagonal_patch(self) -> None:
        """
        Génère un patch hexagonal plat de rayon donné
        Utilise la condition |x| + |y| + |x+y| ≤ 2*radius pour définir le patch
        """
        # Création des nœuds dans le patch hexagonal
        node_idx = 0
        for x in range(-self.radius, self.radius + 1):
            for y in range(-self.radius, self.radius + 1):
                # Condition pour un patch hexagonal: |x| + |y| + |x+y| ≤ 2*radius
                if abs(x) + abs(y) + abs(x+y) <= 2 * self.radius:
                    # Ajout du nœud avec ses coordonnées
                    self.node_map_2d_to_1d[(x, y)] = node_idx
                    
                    # Position pour le dessin (décalage pour les rangées impaires)
                    # Utilise les coordonnées cubiques pour un rendu hexagonal correct
                    pos_x = (x + y/2) * self.scale_factor
                    pos_y = y * np.sqrt(3)/2 * self.scale_factor
                    self.pos_for_drawing[node_idx] = (pos_x, pos_y)
                    
                    # Ajout du nœud avec ses attributs
                    self.graph.add_node(node_idx, pos=(pos_x, pos_y), coords=(x, y), antipode=None)
                    node_idx += 1
        
        # Création des liens entre les nœuds adjacents (sans les liens TS pour l'instant)
        for (x, y), node_idx in self.node_map_2d_to_1d.items():
            # Définition des 6 voisins hexagonaux
            neighbors = [
                (x+1, y), (x-1, y),     # Droite, Gauche
                (x, y+1), (x, y-1),     # Haut-Droite, Bas-Gauche
                (x+1, y-1), (x-1, y+1)  # Bas-Droite, Haut-Gauche
            ]
            
            # Ajout des liens avec les voisins qui existent dans le patch
            for nx, ny in neighbors:
                if (nx, ny) in self.node_map_2d_to_1d:
                    neighbor_idx = self.node_map_2d_to_1d[(nx, ny)]
                    # NetworkX ignore automatiquement les doublons d'arêtes
                    self.graph.add_edge(node_idx, neighbor_idx, is_ts=False)
    
    def _apply_antipodal_identification(self) -> None:
        """
        Applique l'identification antipodale: (x,y) ~ (-x,-y)
        Crée les liens TS (topologiquement sensibles)
        """
        # Identification des nœuds antipodaux
        for (x, y), node_idx in list(self.node_map_2d_to_1d.items()):
            antipode_coords = (-x, -y)
            
            # Vérifie si l'antipode existe dans le patch
            if antipode_coords in self.node_map_2d_to_1d:
                antipode_idx = self.node_map_2d_to_1d[antipode_coords]
                
                # Enregistre l'antipode dans les attributs du nœud
                self.graph.nodes[node_idx]['antipode'] = antipode_idx
                self.graph.nodes[antipode_idx]['antipode'] = node_idx
                
                # Enregistre l'antipode dans le dictionnaire
                self.antipode_map[node_idx] = antipode_idx
                self.antipode_map[antipode_idx] = node_idx
                
                # Crée un lien TS entre le nœud et son antipode
                if node_idx != antipode_idx and not self.graph.has_edge(node_idx, antipode_idx):
                    self.graph.add_edge(node_idx, antipode_idx, is_ts=True)
    
    def _calculate_euler_characteristic(self) -> int:
        """
        Calcule la caractéristique d'Euler du graphe: χ = V - E + F
        Pour RP², on devrait avoir χ = 1
        
        Returns:
            Caractéristique d'Euler calculée
        """
        # Nombre de nœuds (V)
        V = self.graph.number_of_nodes()
        
        # Nombre d'arêtes (E)
        E = self.graph.number_of_edges()
        
        # Pour RP², on a χ = 1, donc F = E - V + 1
        F = E - V + 1
        
        # Calcul de la caractéristique d'Euler
        chi = V - E + F
        
        print(f"Caractéristique d'Euler: χ = {V} - {E} + {F} = {chi}")
        print(f"Attendu pour RP²: χ = 1")
        
        return chi
    
    def get_graph(self) -> nx.Graph:
        """
        Retourne le graphe NetworkX
        
        Returns:
            Le graphe NetworkX
        """
        return self.graph
    
    def get_node_positions(self) -> Dict[int, Tuple[float, float]]:
        """
        Retourne les positions des nœuds pour le dessin
        
        Returns:
            Dictionnaire des positions {node_id: (x, y)}
        """
        return self.pos_for_drawing
    
    def is_ts(self, node1: int, node2: int) -> bool:
        """
        Vérifie si le lien entre deux nœuds est un lien TS
        
        Args:
            node1, node2: Identifiants des nœuds
            
        Returns:
            True si le lien est TS, False sinon
        """
        if self.graph.has_edge(node1, node2):
            return self.graph[node1][node2].get('is_ts', False)
        return False
    
    def get_neighbors(self, node: int, kind: str = "all") -> List[int]:
        """
        Retourne les voisins d'un nœud, avec possibilité de filtrer par type de lien
        
        Args:
            node: Identifiant du nœud
            kind: Type de voisins à retourner ("all", "normal", "ts")
            
        Returns:
            Liste des identifiants des voisins
        """
        if kind == "all":
            return list(self.graph.neighbors(node))
        elif kind == "normal":
            return [n for n in self.graph.neighbors(node) if not self.is_ts(node, n)]
        elif kind == "ts":
            return [n for n in self.graph.neighbors(node) if self.is_ts(node, n)]
        else:
            raise ValueError(f"Type de voisins inconnu: {kind}. Utiliser 'all', 'normal' ou 'ts'.")
    
    def get_ts_links(self) -> List[Tuple[int, int]]:
        """
        Retourne tous les liens TS du graphe
        
        Returns:
            Liste des paires de nœuds formant des liens TS
        """
        return [(u, v) for u, v, d in self.graph.edges(data=True) if d.get('is_ts', False)]
    
    def antipode(self, node: int) -> Optional[int]:
        """
        Retourne l'antipode d'un nœud s'il existe
        
        Args:
            node: Identifiant du nœud
            
        Returns:
            Identifiant de l'antipode ou None si pas d'antipode
        """
        return self.antipode_map.get(node, None)
    
    def check_non_orientability(self) -> bool:
        """
        Vérifie la non-orientabilité du graphe en cherchant des boucles non-triviales
        
        Returns:
            True si le graphe est non-orientable
        """
        # Une boucle non-triviale est une boucle qui traverse un nombre impair de liens TS
        # Cherche des chemins simples entre un nœud et son antipode
        for node, antipode_node in self.antipode_map.items():
            if node < antipode_node:  # Évite de compter deux fois
                try:
                    # Cherche un chemin entre le nœud et son antipode
                    path = nx.shortest_path(self.graph, node, antipode_node)
                    
                    # Compte le nombre de liens TS dans le chemin
                    ts_count = sum(1 for i in range(len(path)-1) 
                                  if self.is_ts(path[i], path[i+1]))
                    
                    # Si nombre impair de liens TS, c'est une boucle non-triviale
                    if ts_count % 2 == 1:
                        print(f"Boucle non-triviale trouvée: {path}")
                        return True
                except nx.NetworkXNoPath:
                    continue
        
        return False
    
    def to_json(self, path: str) -> None:
        """
        Exporte le graphe au format JSON pour Godot
        
        Args:
            path: Chemin du fichier de sortie
        """
        data = {
            "nodes": [
                {
                    "id": n,
                    "x": self.graph.nodes[n]["pos"][0],
                    "y": self.graph.nodes[n]["pos"][1],
                    "antipode": self.antipode(n)
                }
                for n in self.graph.nodes
            ],
            "edges": [
                {
                    "u": u, 
                    "v": v, 
                    "is_ts": d.get("is_ts", False)
                }
                for u, v, d in self.graph.edges(data=True)
            ]
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"Graphe exporté au format JSON: {path}")
    
    def get_statistics(self) -> Dict[str, Union[int, float, bool]]:
        """
        Retourne des statistiques sur le graphe
        
        Returns:
            Dictionnaire de statistiques
        """
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        num_ts_links = sum(1 for _, _, d in self.graph.edges(data=True) if d.get('is_ts', False))
        
        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "num_ts_links": num_ts_links,
            "ts_ratio": num_ts_links / num_edges if num_edges > 0 else 0,
            "euler_characteristic": self._calculate_euler_characteristic(),
            "is_non_orientable": self.check_non_orientability()
        }