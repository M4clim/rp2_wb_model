# core/metric_effective.py

import numpy as np


def compute_g_eff(model, alpha, n, beta, eps0, m, p):
    """
    Calcule pour chaque nœud i :
      f_i = 1/(1 + alpha * rho_i**n)
      grad2_i = sum_j (rho_i - rho_j)**2
      h_i = beta*grad2_i + eps0**2 * rho_i**m * grad2_i**p
      T_i[j] = ((rho_i - rho_j)/sqrt(grad2_i + eps0**2))**2  (direction sur arête i->j)
    Stocke :
      model.g_eff_iso[i]   = f_i
      model.g_eff_aniso[i] = h_i
      model.g_eff_T[(i,j)] = T_i[j] pour chaque voisin j
    """
    rho = model.rho
    graph = model.graph
    g_iso = {}
    g_aniso = {}
    g_T = {}

    for i in graph.graph.nodes():
        rho_i = rho[i]
        # isotrope
        f_i = 1.0 / (1.0 + alpha * (rho_i**n))
        # gradient discret
        neigh = list(graph.get_neighbors(i))
        grad2 = sum((rho_i - rho[j]) ** 2 for j in neigh)
        # anisotrope
        h_i = beta * grad2 + (eps0**2) * (rho_i**m) * (grad2**p)

        g_iso[i] = f_i
        g_aniso[i] = h_i

        # tenseur directionnel par voisin
        denom = grad2 + eps0**2
        for j in neigh:
            delta = rho_i - rho[j]
            # contribution proportionnelle au carré de la différence
            T_ij = (delta * delta) / denom
            g_T[(i, j)] = T_ij

    # stocker dans le modèle
    model.g_eff_iso = g_iso
    model.g_eff_aniso = g_aniso
    model.g_eff_T = g_T
