import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

def visualiser_detection_detaillee(img, touches, rois, verdict, debug_info, save_path=None):
    """
    Génère une visualisation complète en 4 panneaux pour debug approfondi.
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    
    # === Panneau 1: Toutes les touches détectées ===
    axes[0, 0].imshow(img, cmap='gray')
    axes[0, 0].set_title(f"Touches détectées: {len(touches)}", fontsize=14, fontweight='bold')
    
    for r in touches:
        rect = mpatches.Rectangle((r.bbox[1], r.bbox[0]), 
                                  r.bbox[3] - r.bbox[1], 
                                  r.bbox[2] - r.bbox[0],
                                  fill=False, edgecolor='lime', linewidth=0.8, alpha=0.5)
        axes[0, 0].add_patch(rect)
    
    # === Panneau 2: Zones ROI identifiées ===
    axes[0, 1].imshow(img, cmap='gray')
    axes[0, 1].set_title("Zones clés (ROI)", fontsize=14, fontweight='bold')
    
    colors = {
        "SPACE": "blue",
        "SHIFT": "orange", 
        "TL_LETTER": "green",
        "OS_KEY": "magenta",
        "ENTER_KEY": "cyan"
    }
    
    for name, region in rois.items():
        if region and name != "h_ref":
            minr, minc, maxr, maxc = region.bbox
            color = colors.get(name, 'yellow')
            
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                      fill=False, edgecolor=color, linewidth=3)
            axes[0, 1].add_patch(rect)
            
            # Label
            axes[0, 1].text(minc, minr - 10, name, 
                           color=color, fontsize=11, fontweight='bold',
                           bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    
    # === Panneau 3: Distribution verticale ===
    centres_y = [r.centroid[0] for r in touches]
    axes[1, 0].hist(centres_y, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
    axes[1, 0].set_title("Distribution Y des touches", fontsize=14, fontweight='bold')
    axes[1, 0].set_xlabel("Position Y (pixels)", fontsize=11)
    axes[1, 0].set_ylabel("Nombre de touches", fontsize=11)
    axes[1, 0].grid(True, alpha=0.3)
    
    # Ligne de médiane
    if centres_y:
        mediane = np.median(centres_y)
        axes[1, 0].axvline(mediane, color='red', linestyle='--', linewidth=2, label=f'Médiane: {mediane:.0f}px')
        axes[1, 0].legend()
    
    # === Panneau 4: Statistiques et résultats ===
    axes[1, 1].axis('off')
    
    # Construction du texte de statistiques
    stats_lines = [
        "="*50,
        "RÉSULTATS DE LA CLASSIFICATION",
        "="*50,
        "",
        f"Format     : {verdict.get('ISO_ANSI', '?')}",
        f"Système    : {verdict.get('MAC_WIN', '?')}",
        f"Layout     : {verdict.get('LAYOUT', '?')}",
        "",
        "-"*50,
        "STATISTIQUES DE DÉTECTION",
        "-"*50,
        "",
        f"Touches détectées    : {len(touches)}",
        f"ROIs identifiées     : {sum(1 for k, v in rois.items() if v and k != 'h_ref')}/5",
        f"h_ref (hauteur std)  : {rois.get('h_ref', 0):.1f} px",
        "",
        "-"*50,
        "MÉTRIQUES TECHNIQUES",
        "-"*50,
        ""
    ]
    
    # Ajout des métriques de debug
    for key, value in debug_info.items():
        if isinstance(value, (int, float)):
            stats_lines.append(f"{key:<20} : {value:.2f}")
        else:
            stats_lines.append(f"{key:<20} : {value}")
    
    stats_text = "\n".join(stats_lines)
    
    axes[1, 1].text(0.05, 0.95, stats_text, 
                   fontsize=10, 
                   family='monospace',
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"   Visualisation sauvegardée: {save_path}")
    
    return fig


def sauvegarder_images_intermediaires(img_originale, img_bin, img_gris, prefix="debug"):
    """
    Sauvegarde les étapes intermédiaires du prétraitement.
    """
    output_dir = "data/debug"
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Image originale
    axes[0].imshow(img_originale, cmap='gray')
    axes[0].set_title("Image originale")
    axes[0].axis('off')
    
    # Image en niveaux de gris traitée
    axes[1].imshow(img_gris, cmap='gray')
    axes[1].set_title("Niveaux de gris traités")
    axes[1].axis('off')
    
    # Image binaire
    axes[2].imshow(np.invert(img_bin), cmap='gray')
    axes[2].set_title("Binarisation finale")
    axes[2].axis('off')
    
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, f"{prefix}_pretraitement.png")
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"   Images intermédiaires sauvegardées: {filepath}")


def generer_rapport_html(resultats_batch, output_path="data/outputs/rapport.html"):
    """
    Génère un rapport HTML interactif pour l'analyse batch.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Rapport d'Analyse Clavier</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
            .summary { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            th { background: #4CAF50; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
            tr:hover { background: #f1f1f1; }
            .ok { color: #4CAF50; font-weight: bold; }
            .error { color: #f44336; font-weight: bold; }
            .stat { display: inline-block; margin: 10px 20px; }
        </style>
    </head>
    <body>
        <h1>📊 Rapport d'Analyse de Claviers</h1>
        <div class="summary">
            <h2>Résumé Global</h2>
            <div class="stat">✅ Succès: <strong>{success_count}</strong></div>
            <div class="stat">❌ Échecs: <strong>{failure_count}</strong></div>
            <div class="stat">📈 Taux de réussite: <strong>{success_rate:.1f}%</strong></div>
        </div>
        <table>
            <tr>
                <th>Fichier</th>
                <th>Statut</th>
                <th>Format</th>
                <th>OS</th>
                <th>Layout</th>
                <th>Touches</th>
            </tr>
            {table_rows}
        </table>
    </body>
    </html>
    """
    
    # Calcul des statistiques
    success_count = sum(1 for r in resultats_batch if "OK" in r.get("Statut", ""))
    failure_count = len(resultats_batch) - success_count
    success_rate = (success_count / len(resultats_batch) * 100) if resultats_batch else 0
    
    # Génération des lignes du tableau
    table_rows = []
    for r in resultats_batch:
        status_class = "ok" if "OK" in r.get("Statut", "") else "error"
        row = f"""
        <tr>
            <td>{r.get('Fichier', 'N/A')}</td>
            <td class="{status_class}">{r.get('Statut', 'N/A')}</td>
            <td>{r.get('Format', 'N/A')}</td>
            <td>{r.get('OS', 'N/A')}</td>
            <td>{r.get('Langue', 'N/A')}</td>
            <td>{r.get('NB_Touches', 0)}</td>
        </tr>
        """
        table_rows.append(row)
    
    # Remplissage du template
    html_final = html_content.format(
        success_count=success_count,
        failure_count=failure_count,
        success_rate=success_rate,
        table_rows="".join(table_rows)
    )
    
    # Sauvegarde
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_final)
    
    print(f"\n📄 Rapport HTML généré: {output_path}")