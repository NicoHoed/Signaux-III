import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import median_filter, binary_opening, binary_closing
from skimage import io, color, filters, exposure, measure, morphology
import matplotlib.patches as mpatches

# --- 🔧 PARAMÈTRES AJUSTÉS SUR BASE DE TES DONNÉES ---
IMAGE_PATH = 'data/inputs/INT-QWERTY-1.jpg' 

# Paramètres de filtrage (V3.1)
AIRE_MIN = 2000      # Assez petit pour les touches de fonction (F1-F12) ou flèches
AIRE_MAX = 400000    # Augmenté (était 100k) -> Pour accepter la barre espace (~250k px)

RATIO_MIN = 0.5      # inchangé (touches hautes comme Entrée ISO)
RATIO_MAX = 8.0      # Augmenté (était 5.0) -> Pour accepter la barre espace (ratio ~6.5)

# C'est ici que se joue la détection de la ligne du bas
# Distance max verticale autorisée par rapport au centre du clavier
SEUIL_Y_PROXIMITE = 1000 # Augmenté (était 500) -> Pour aller chercher la ligne tout en bas

def pretraiter_image_v1(img):
    """Implémentation stricte du preprocessing.py de la V1"""
    if len(img.shape) == 3:
        gris = color.rgb2gray(img)
    else:
        gris = img

    filtree = median_filter(gris, size=3)
    filtree = exposure.equalize_hist(filtree)

    seuil = filters.threshold_otsu(filtree)
    binaire = filtree > seuil

    nettoyee = binary_opening(binaire, iterations=2)
    nettoyee = binary_closing(nettoyee, iterations=3)

    return nettoyee, gris

def detecter_regions_v1(img_binaire):
    """Logique V1 avec paramètres élargis"""
    # Inversion nécessaire car measure.label cherche les zones True (Blanches)
    inversee = np.invert(img_binaire.astype(bool))
    
    label_image = measure.label(inversee)
    all_regions = measure.regionprops(label_image)
    
    candidats_initiaux = []
    
    # 1. Filtrage par dimensions physiques
    for r in all_regions:
        minr, minc, maxr, maxc = r.bbox
        hauteur = maxr - minr
        largeur = maxc - minc
        
        if hauteur == 0: continue
        
        aire = r.area
        ratio = largeur / hauteur

        # On filtre large pour ne rien rater
        if AIRE_MIN <= aire <= AIRE_MAX and RATIO_MIN <= ratio <= RATIO_MAX:
            candidats_initiaux.append(r)

    if not candidats_initiaux:
        return [], 0, 0, 0

    # 2. Filtrage Spatial (Anti-Trackpad)
    # On calcule le centre Y moyen des touches trouvées
    centres_y = [r.centroid[0] for r in candidats_initiaux]
    moyenne_y = np.mean(centres_y)
    
    # On définit la zone valide
    y_min_valid = moyenne_y - SEUIL_Y_PROXIMITE
    y_max_valid = moyenne_y + SEUIL_Y_PROXIMITE
    
    bonnes_regions = []
    for r in candidats_initiaux:
        cy, _ = r.centroid
        if y_min_valid < cy < y_max_valid:
            bonnes_regions.append(r)

    return bonnes_regions, moyenne_y, y_min_valid, y_max_valid

def analyser_features(region):
    """Extraction des métriques pour l'analyse de layout"""
    minr, minc, maxr, maxc = region.bbox
    hauteur = maxr - minr
    cy, cx = region.centroid
    
    # Centre relatif (0.0 haut, 1.0 bas)
    centroid_y_norm = (cy - minr) / hauteur 
    
    return {
        "ratio": (maxc - minc) / hauteur,
        "extent": region.extent,
        "solidity": region.solidity,
        "euler": region.euler_number,
        "centroid_norm": centroid_y_norm
    }

def on_click(event, ax, regions):
    if event.inaxes != ax: return
    x, y = event.xdata, event.ydata
    
    print(f"\n🖱️ Clic en ({int(x)}, {int(y)})")
    
    for r in regions:
        minr, minc, maxr, maxc = r.bbox
        if minc <= x <= maxc and minr <= y <= maxr:
            stats = analyser_features(r)
            print("-" * 40)
            print(f"🎯 TOUCHE SÉLECTIONNÉE")
            print(f"   Aire         : {r.area} px")
            print(f"   Ratio (L/H)  : {stats['ratio']:.2f}")
            print(f"   Extent       : {stats['extent']:.2f}")
            print(f"   Euler        : {stats['euler']}")
            print(f"   Centre Y Rel : {stats['centroid_norm']:.2f}")
            
            # Détection basique pour info
            verdict = "Inconnu"
            if stats['ratio'] > 4.0: verdict = "Espace ?"
            elif stats['ratio'] > 1.8: verdict = "Shift/Enter/Cmd ?"
            elif stats['euler'] < 0: verdict = "Command (Mac) ?"
            
            print(f"   -> Hypothèse : {verdict}")
            print("-" * 40)
            
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                      fill=False, edgecolor='yellow', linewidth=3)
            ax.add_patch(rect)
            event.canvas.draw()
            return

def main():
    print(f"Chargement de {IMAGE_PATH}...")
    try: img = io.imread(IMAGE_PATH)
    except Exception as e: 
        print(f"Erreur: {e}")
        return

    print("Prétraitement...")
    img_bin, img_gris = pretraiter_image_v1(img)

    print("Détection des touches (Paramètres élargis)...")
    regions, mean_y, y_min, y_max = detecter_regions_v1(img_bin)
    
    if len(regions) == 0:
        print("❌ Aucune touche trouvée. Vérifiez le seuillage.")
        return

    print(f"✅ {len(regions)} touches détectées.")
    print(f"📍 Centre Y moyen : {mean_y:.0f} px")
    print(f"📐 Zone acceptée : Y={y_min:.0f} à Y={y_max:.0f}")

    # Affichage
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Vue Résultats
    ax1.imshow(img, cmap='gray')
    ax1.set_title(f"Touches détectées ({len(regions)})")
    
    # Dessin des lignes de la zone de filtrage spatial
    ax1.axhline(y=mean_y, color='blue', linestyle='--', alpha=0.5, label='Centre Moyen')
    ax1.axhline(y=y_min, color='red', linestyle='-', alpha=0.5, label='Limite Haute')
    ax1.axhline(y=y_max, color='red', linestyle='-', alpha=0.5, label='Limite Basse')
    ax1.legend()

    for r in regions:
        minr, minc, maxr, maxc = r.bbox
        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                  fill=False, edgecolor='#00FF00', linewidth=1)
        ax1.add_patch(rect)

    # Vue Masque
    ax2.imshow(np.invert(img_bin), cmap='gray') 
    ax2.set_title("Masque inversé (ce que voit l'algo)")

    print("\n💡 INFO: Les lignes rouges horizontales montrent la zone de recherche.")
    print("   Si des touches sont en dehors, augmentez SEUIL_Y_PROXIMITE.")
    print("   Cliquez sur les touches (Espace, Cmd, etc.) pour vérifier leurs stats.")
    
    fig.canvas.mpl_connect('button_press_event', lambda event: on_click(event, ax1, regions))
    plt.show()

if __name__ == "__main__":
    main()