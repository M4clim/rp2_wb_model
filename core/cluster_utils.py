# core/cluster_utils.py
from collections import deque
from typing import List

from .graph_rp2 import RP2Graph


def find_soliton_clusters(
    graph: RP2Graph, rho: dict, threshold: float
) -> List[List[int]]:
    """
    Parcourt le graphe et retourne toutes les composantes connexes
    de nœuds dont rho[i] >= threshold.
    """
    visited = set()
    clusters = []
    for i, val in rho.items():
        if val < threshold or i in visited:
            continue
        queue = deque([i])
        visited.add(i)
        cluster = []
        while queue:
            u = queue.popleft()
            cluster.append(u)
            for v in graph.graph.neighbors(u):
                if v not in visited and rho.get(v, 0.0) >= threshold:
                    visited.add(v)
                    queue.append(v)
        clusters.append(cluster)
    return clusters
