import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import hsv_to_rgb


class Plotter:
    """
    Visualisation du modèle WB avec matplotlib et NetworkX
    """

    def __init__(self, figsize=(10, 8)):
        """
        Initialise le plotter

        Args:
            figsize (tuple): Taille de la figure matplotlib
        """
        self.figsize = figsize

    def plot_graph(self, model, ax=None, show=True, save_path=None, highlight_ts=False):
        """
        Visualise le graphe avec les champs ρ, φ, σ

        Args:
            model (WBModel): Instance du modèle WB
            ax (matplotlib.axes.Axes, optional): Axes matplotlib existants
            show (bool): Afficher la figure
            save_path (str, optional): Chemin pour sauvegarder l'image
            highlight_ts (bool): Mettre en évidence les liens TS

        Returns:
            matplotlib.figure.Figure: Figure matplotlib
        """
        # Création de la figure si nécessaire
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure

        # Récupération du graphe
        G = model.graph.graph

        # Positions des nœuds
        pos = nx.get_node_attributes(G, "pos")
        if not pos:
            # Si les positions ne sont pas définies, utiliser un layout force-directed
            pos = nx.spring_layout(G)

        # Préparation des couleurs basées sur φ (phase) et tailles basées sur ρ (densité)
        node_colors = []
        node_sizes = []

        for node in G.nodes():
            # Couleur basée sur la phase (φ) pour la teinte
            phi = model.phi.get(node, 0)
            hue = phi / (2 * np.pi)  # Normalisation entre 0 et 1

            # Saturation basée sur ρ
            rho = model.rho.get(node, 0)
            saturation = min(1.0, max(0.2, rho))

            # Luminosité basée sur σ
            sigma = model.sigma.get(node, 0)
            value = 0.7 if sigma > 0 else 0.4

            # Conversion HSV vers RGB
            rgb_color = hsv_to_rgb((hue, saturation, value))
            node_colors.append(rgb_color)

            # Taille basée sur ρ
            node_sizes.append(100 + 200 * rho)

        # Dessin des nœuds
        nx.draw_networkx_nodes(
            G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8, ax=ax
        )

        # Dessin des liens
        if highlight_ts and hasattr(model.graph, "get_ts_links"):
            # Récupérer les liens TS
            ts_links = model.graph.get_ts_links()
            normal_links = [
                (u, v)
                for u, v in G.edges()
                if (u, v) not in ts_links and (v, u) not in ts_links
            ]

            # Dessiner les liens normaux
            nx.draw_networkx_edges(
                G, pos, edgelist=normal_links, width=0.5, alpha=0.5, ax=ax
            )

            # Dessiner les liens TS en rouge et plus épais
            nx.draw_networkx_edges(
                G, pos, edgelist=ts_links, width=1.5, alpha=0.7, edge_color="red", ax=ax
            )
        else:
            # Dessiner tous les liens sans distinction
            nx.draw_networkx_edges(G, pos, width=0.5, alpha=0.5, ax=ax)

        # Paramètres de la figure
        ax.set_title(f"Graphe RP2 - {len(G.nodes())} nœuds")
        ax.set_axis_off()

        # Légende
        legend_text = "Couleur: φ (phase)\nTaille: ρ (densité)\nLuminosité: σ (spin)"
        if highlight_ts:
            legend_text += "\nLiens rouges: liens TS"
        ax.text(
            0.02,
            0.02,
            legend_text,
            transform=ax.transAxes,
            bbox={"facecolor": "white", "alpha": 0.7},
        )

        # Sauvegarde si demandée
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Figure sauvegardée dans {save_path}")

        # Affichage
        if show:
            plt.tight_layout()
            plt.show()

        return fig

    def plot_statistics(self, history, ax=None, show=True, save_path=None):
        """
        Visualise l'évolution des statistiques du modèle WB

        Args:
            history: Liste des statistiques pour chaque étape
            ax: Axes matplotlib (optionnel)
            show: Afficher la figure
            save_path: Chemin pour sauvegarder la figure

        Returns:
            Figure matplotlib
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure

        # Extraction des données
        steps = [stat["step"] for stat in history]
        active = [stat["active"] for stat in history]
        n_pot = [stat["N_pot"] for stat in history]
        lambda_vac = [
            stat.get("Λ_vac", 1.0) for stat in history
        ]  # Nouveau paramètre Λ_vac

        # Création d'un axe secondaire pour N_pot
        ax2 = ax.twinx()

        # Tracé des courbes
        lines1 = ax.plot(steps, active, "b-", label="Actifs")
        lines2 = ax2.plot(steps, n_pot, "r-", label="N_pot")
        lines3 = ax.plot(steps, lambda_vac, "g--", label="Λ_vac")

        # Ajout des légendes et labels
        all_lines = lines1 + lines2 + lines3
        labels = [line.get_label() for line in all_lines]
        ax.legend(all_lines, labels, loc="upper right")

        ax.set_xlabel("Étape")
        ax.set_ylabel("Nombre de nœuds actifs / Λ_vac")
        ax2.set_ylabel("N_pot")

        ax.set_title("Évolution des statistiques du modèle WB")
        ax.grid(True, alpha=0.3)

        # Affichage ou sauvegarde
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    # Alias pour compatibilité avec le code existant
    plot_stats = plot_statistics
