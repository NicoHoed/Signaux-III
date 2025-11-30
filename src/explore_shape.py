import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
from skimage import io, measure
from src.preprocessing import pretraiter_image
import config

# Script d'exploration pour diagnostiquer les problèmes de détection

CONFIG = {
    'IMAGE_PATH': config.IMAGE_PATH_DEFAULT,
    'AIRE_MIN': config.AIRE_MIN,
    'AIRE_MAX': config.AIRE_MAX,
    'RATIO_MIN': config.RATIO_MIN,
    'RATIO_MAX': config.RATIO_MAX,
    'SEUIL_Y_PROXIMITE': config.SEUIL_Y_PROXIMITE
}


def detecter_regions_exploration(img_binaire, config_dict):
    """
    Détection pour exploration avec statistiques détaillées.
    """
    inversee = np.invert(img_binaire.astype(bool))
    
    label_image = measure.label(inversee)
    all_regions = measure.regionprops(label_image)
    
    print(f"\n📊 Statistiques initiales:")
    print(f"   Régions détectées (brutes): {len(all_regions)}")
    
    candidats_initiaux = []
    rejetes_aire = 0
    rejetes_ratio = 0
    rejetes_qualite = 0
    
    # 1. Filtrage par dimensions
    for r in all_regions:
        minr, minc, maxr, maxc = r.bbox
        hauteur = maxr - minr
        largeur = maxc - minc
        
        if hauteur == 0:
            continue
        
        aire = r.area
        ratio = largeur / hauteur
        solidite = r.solidity
        extent = r.extent
        
        # Statistiques de rejet
        if not (config_dict['AIRE_MIN'] <= aire <= config_dict['AIRE_MAX']):
            rejetes_aire += 1
            continue
        
        if not (config_dict['RATIO_MIN'] <= ratio <= config_dict['RATIO_MAX']):
            rejetes_ratio += 1
            continue
        
        if solidite < config.SOLIDITY_MIN or extent < config.EXTENT_MIN:
            rejetes_qualite += 1
            continue
        
        candidats_initiaux.append(r)

    print(f"\n🔍 Filtrage dimensionnel:")
    print(f"   Rejetés (aire)    : {rejetes_aire}")
    print(f"   Rejetés (ratio)   : {rejetes_ratio}")
    print(f"   Rejetés (qualité) : {rejetes_qualite}")
    print(f"   Candidats retenus : {len(candidats_initiaux)}")

    if not candidats_initiaux:
        return [], 0, 0, 0

    # 2. Filtrage Spatial
    centres_y = [r.centroid[0] for r in candidats_initiaux]
    moyenne_y = np.mean(centres_y)
    mediane_y = np.median(centres_y)
    ecart_type_y = np.std(centres_y)
    
    print(f"\n📍 Distribution spatiale (Y):")
    print(f"   Moyenne    : {moyenne_y:.1f} px")
    print(f"   Médiane    : {mediane_y:.1f} px")
    print(f"   Écart-type : {ecart_type_y:.1f} px")
    
    y_min_valid = moyenne_y - config_dict['SEUIL_Y_PROXIMITE']
    y_max_valid = moyenne_y + config_dict['SEUIL_Y_PROXIMITE']
    
    bonnes_regions = []
    rejetes_spatial = 0
    
    for r in candidats_initiaux:
        cy, _ = r.centroid
        if y_min_valid < cy < y_max_valid:
            bonnes_regions.append(r)
        else:
            rejetes_spatial += 1

    print(f"\n🎯 Filtrage spatial:")
    print(f"   Zone valide Y  : [{y_min_valid:.1f}, {y_max_valid:.1f}]")
    print(f"   Rejetés (hors zone) : {rejetes_spatial}")
    print(f"   Touches finales     : {len(bonnes_regions)}")

    return bonnes_regions, moyenne_y, y_min_valid, y_max_valid


def analyser_features(region):
    """Extraction complète des métriques."""
    minr, minc, maxr, maxc = region.bbox
    hauteur = maxr - minr
    largeur = maxc - minc
    cy, cx = region.centroid
    
    centroid_y_norm = (cy - minr) / hauteur if hauteur > 0 else 0
    ratio_l_h = largeur / hauteur if hauteur > 0 else 0
    ratio_h_l = hauteur / largeur if largeur > 0 else 0
    
    return {
        "x": int(cx),
        "y": int(cy),
        "width": largeur,
        "height": hauteur,
        "minc": int(minc),
        "minr": int(minr),
        "area": region.area,
        "ratio_l_h": ratio_l_h,
        "ratio_h_l": ratio_h_l,
        "extent": region.extent,
        "solidity": region.solidity,
        "euler": region.euler_number,
        "centroid_norm": centroid_y_norm
    }


def diagnostiquer_touche(stats):
    """Diagnostic intelligent basé sur les métriques."""
    diagnostics = []
    
    # Identification par aire
    if stats['area'] > 50000:
        diagnostics.append("🔵 BARRE ESPACE probable (grande aire)")
    
    # Identification par ratio
    if stats['ratio_l_h'] > 4.0:
        diagnostics.append("🔵 BARRE ESPACE (ratio L/H très élevé)")
    elif config.SHIFT_RATIO_MIN < stats['ratio_l_h'] < config.SHIFT_RATIO_MAX:
        if stats['ratio_l_h'] < config.THRESHOLD_SHIFT_RATIO_ISO:
            diagnostics.append("🟠 SHIFT ISO probable (petit ratio)")
        else:
            diagnostics.append("🟠 SHIFT ANSI probable (grand ratio)")
    elif 0.7 < stats['ratio_l_h'] < 1.3:
        diagnostics.append("🟢 TOUCHE STANDARD (quasi-carrée)")
    
    # Identification par Enter
    if stats['ratio_h_l'] > config.THRESHOLD_ENTER_RATIO_H_L_ISO:
        diagnostics.append("🔷 ENTER ISO probable (H/L élevé)")
    elif stats['ratio_h_l'] < config.THRESHOLD_ENTER_RATIO_H_L_ANSI:
        diagnostics.append("🔷 ENTER ANSI probable (H/L faible)")
    
    # Identification OS par Euler
    if stats['euler'] <= config.THRESHOLD_EULER_MAC:
        diagnostics.append("🍎 Touche COMMAND (Mac) probable")
    elif stats['euler'] >= config.THRESHOLD_EULER_WIN:
        diagnostics.append("🪟 Touche WINDOWS probable")
    
    # Identification AZERTY/QWERTY
    if stats['centroid_norm'] > config.THRESHOLD_TL_CENTER_Y_AZERTY:
        if stats['extent'] < config.THRESHOLD_TL_EXTENT_AZERTY:
            diagnostics.append("🇫🇷 Lettre AZERTY probable (A)")
        else:
            diagnostics.append("🇬🇧 Lettre QWERTY probable (Q)")
    
    return diagnostics if diagnostics else ["❔ Type indéterminé"]


def on_click(event, ax, regions, fig):
    """Gestion des clics avec diagnostic avancé."""
    if event.inaxes != ax:
        return
    
    x_click, y_click = event.xdata, event.ydata
    
    print("\n" + "="*70)
    print(f"🖱️  CLIC EN ({int(x_click)}, {int(y_click)})")
    print("="*70)
    
    touche_trouvee = False
    
    for r in regions:
        minr, minc, maxr, maxc = r.bbox
        if minc <= x_click <= maxc and minr <= y_click <= maxr:
            touche_trouvee = True
            stats = analyser_features(r)
            diagnostics = diagnostiquer_touche(stats)
            
            print("\n📌 TOUCHE SÉLECTIONNÉE")
            print("-"*70)
            print(f"   Position (X, Y)       : ({stats['x']}, {stats['y']}) px")
            print(f"   BBox (minC, minR)     : ({stats['minc']}, {stats['minr']})")
            print(f"   Dimensions (L × H)    : {stats['width']} × {stats['height']} px")
            print(f"   Aire                  : {stats['area']:,} px²")
            print("\n📏 RATIOS")
            print("-"*70)
            print(f"   Ratio L/H             : {stats['ratio_l_h']:.3f} (seuil ISO Shift: {config.THRESHOLD_SHIFT_RATIO_ISO})")
            print(f"   Ratio H/L             : {stats['ratio_h_l']:.3f} (seuil ISO Enter: {config.THRESHOLD_ENTER_RATIO_H_L_ISO})")
            print("\n🔬 MÉTRIQUES DE FORME")
            print("-"*70)
            print(f"   Extent                : {stats['extent']:.3f} (min: {config.EXTENT_MIN})")
            print(f"   Solidité              : {stats['solidity']:.3f} (min: {config.SOLIDITY_MIN})")
            print(f"   Euler                 : {stats['euler']:>3} (Mac: ≤{config.THRESHOLD_EULER_MAC}, Win: ≥{config.THRESHOLD_EULER_WIN})")
            print(f"   Centre Y relatif      : {stats['centroid_norm']:.3f} (seuil AZERTY: {config.THRESHOLD_TL_CENTER_Y_AZERTY})")
            print("\n🎯 DIAGNOSTIC AUTOMATIQUE")
            print("-"*70)
            for diag in diagnostics:
                print(f"   {diag}")
            print("="*70)
            
            # Mise en surbrillance visuelle
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                      fill=False, edgecolor='yellow', linewidth=4)
            ax.add_patch(rect)
            
            # Label
            ax.text(minc, minr - 15, f"Aire:{stats['area']}", 
                   color='yellow', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
            
            fig.canvas.draw()
            break
    
    if not touche_trouvee:
        print("   Aucune touche à cet emplacement")


def main():
    image_path = CONFIG['IMAGE_PATH']
    
    print("="*70)
    print("🔬 MODE EXPLORATION - DIAGNOSTIC DE DÉTECTION")
    print("="*70)
    print(f"Image: {image_path}\n")
    
    try: 
        img = io.imread(image_path)
        print(f"✓ Image chargée: {img.shape}")
    except Exception as e: 
        print(f"❌ Erreur: {e}")
        return

    print("\n🔄 Prétraitement en cours...")
    img_bin, img_gris = pretraiter_image(img)
    print("✓ Prétraitement terminé")

    print("\n🔍 Détection des touches avec paramètres actuels...")
    regions, mean_y, y_min, y_max = detecter_regions_exploration(img_bin, CONFIG)
    
    if len(regions) == 0:
        print("\n❌ ÉCHEC: Aucune touche détectée!")
        print("\n💡 Suggestions:")
        print("   1. Vérifiez l'image binaire (panneau de droite)")
        print("   2. Ajustez AIRE_MIN et AIRE_MAX dans config.py")
        print("   3. Modifiez SEUIL_Y_PROXIMITE si touches hors zone")
        print("   4. Diminuez SOLIDITY_MIN ou EXTENT_MIN si trop strict")
        
        # Affichage quand même pour diagnostic
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        ax1.imshow(img, cmap='gray')
        ax1.set_title("Image originale (AUCUNE touche détectée)", color='red', fontweight='bold')
        ax2.imshow(np.invert(img_bin), cmap='gray')
        ax2.set_title("Masque binaire")
        plt.show()
        return

    # Affichage des résultats
    print("\n" + "="*70)
    print(f"✅ DÉTECTION RÉUSSIE: {len(regions)} touches")
    print("="*70)
    print("\n💡 INSTRUCTIONS:")
    print("   • Cliquez sur les touches pour voir leurs statistiques")
    print("   • Vérifiez que toutes les touches du clavier sont détectées")
    print("   • Notez les valeurs des touches clés (Espace, Shift, Enter, etc.)")
    print("   • Ajustez config.py si nécessaire\n")

    # Visualisation
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 7))
    
    # Panneau 1: Résultats
    ax1.imshow(img, cmap='gray')
    ax1.set_title(f"Touches détectées: {len(regions)}", fontsize=14, fontweight='bold')
    
    ax1.axhline(y=mean_y, color='blue', linestyle='--', linewidth=2, alpha=0.6, label='Centre moyen')
    ax1.axhline(y=y_min, color='red', linestyle='-', linewidth=2, alpha=0.6, label='Limites zone')
    ax1.axhline(y=y_max, color='red', linestyle='-', linewidth=2, alpha=0.6)
    ax1.legend(loc='upper right')

    for r in regions:
        minr, minc, maxr, maxc = r.bbox
        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                  fill=False, edgecolor='lime', linewidth=1.5)
        ax1.add_patch(rect)

    # Panneau 2: Masque binaire
    ax2.imshow(np.invert(img_bin), cmap='gray')
    ax2.set_title("Masque binaire inversé", fontsize=14, fontweight='bold')

    # Panneau 3: Histogramme des aires
    aires = [r.area for r in regions]
    ax3.hist(aires, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
    ax3.axvline(CONFIG['AIRE_MIN'], color='red', linestyle='--', linewidth=2, label=f"Min: {CONFIG['AIRE_MIN']}")
    ax3.axvline(CONFIG['AIRE_MAX'], color='red', linestyle='--', linewidth=2, label=f"Max: {CONFIG['AIRE_MAX']}")
    ax3.set_title("Distribution des aires", fontsize=14, fontweight='bold')
    ax3.set_xlabel("Aire (pixels²)")
    ax3.set_ylabel("Nombre de touches")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    fig.canvas.mpl_connect('button_press_event', lambda event: on_click(event, ax1, regions, fig))
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
