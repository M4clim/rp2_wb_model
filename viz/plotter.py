import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
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
        
    def plot_graph(self, model, ax=None, show=True, save_path=None):
        """
        Visualise le graphe avec les champs ρ, φ, σ
        
        Args:
            model (WBModel): Instance du modèle WB
            ax (matplotlib.axes.Axes, optional): Axes matplotlib existants
            show (bool): Afficher la figure
            save_path (str, optional): Chemin pour sauvegarder l'image
            
        Returns:
            matplotlib.figure.Figure: Figure matplotlib
        """
        # Création de la figure si nécessaire
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        else:
            fig = ax.figure
            
        # Récupération du graphe
        G = model.network
        
        # Positions des nœuds
        pos = nx.get_node_attributes(G, 'pos')
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
            G, pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.8,
            ax=ax
        )
        
        # Dessin des liens
        nx.draw_networkx_edges(
            G, pos,
            width=0.5,
            alpha=0.5,
            ax=ax
        )
        
        # Paramètres de la figure
        ax.set_title(f"Graphe RP2 - {len(G.nodes())} nœuds")
        ax.set_axis_off()
        
        # Légende
        ax.text(0.02, 0.02, "Couleur: φ (phase)\nTaille: ρ (densité)\nLuminosité: σ (spin)",
                transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.7))
        
        # Sauvegarde si demandée
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure sauvegardée dans {save_path}")
        
        # Affichage
        if show:
            plt.tight_layout()
            plt.show()
            
        return fig
    
    def plot_stats(self, stats, ax=None, show=True, save_path=None):
        """
        Visualise l'évolution des statistiques de simulation
        
        Args:
            stats (list): Liste des statistiques par étape
            ax (matplotlib.axes.Axes, optional): Axes matplotlib existants
            show (bool): Afficher la figure
            save_path (str, optional): Chemin pour sauvegarder l'image
            
        Returns:
            matplotlib.figure.Figure: Figure matplotlib
        """
        if not stats:
            print("Aucune statistique à afficher")
            return None
            
        # Création de la figure si nécessaire
        if ax is None:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, sharex=True)
        else:
            fig = ax.figure
            ax1, ax2 = ax[0], ax[1]
            
        # Extraction des données
        steps = [s['step'] for s in stats]
        rho_means = [s['rho_mean'] for s in stats]
        sigma_means = [s['sigma_mean'] for s in stats]
        
        # Graphique de ρ moyen
        ax1.plot(steps, rho_means, 'b-', label='ρ moyen')
        ax1.set_ylabel('Densité moyenne (ρ)')
        ax1.set_title('Évolution des champs au cours de la simulation')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Graphique de σ moyen
        ax2.plot(steps, sigma_means, 'r-', label='σ moyen')
        ax2.set_xlabel('Étape de simulation')
        ax2.set_ylabel('Spin moyen (σ)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Sauvegarde si demandée
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure sauvegardée dans {save_path}")
        
        # Affichage
        if show:
            plt.tight_layout()
            plt.show()
            
        return fig