import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from skimage import io
import numpy as np
import config

from src.preprocessing import pretraiter_image
from src.analysis import detecter_touches, identifier_zones_cles, classifier_clavier
from src.debug_utils import visualiser_detection_detaillee, sauvegarder_images_intermediaires

# --- CONFIGURATION ---
IMAGE_PATH = config.IMAGE_PATH_DEFAULT 

def main():
    print("="*60)
    print("🔍 ANALYSE DE CLAVIER - VERSION AMÉLIORÉE")
    print("="*60)
    print(f"Fichier: {IMAGE_PATH}")
    print(f"Mode debug: {'ACTIVÉ' if config.DEBUG_MODE else 'DÉSACTIVÉ'}\n")
    
    try:
        img = io.imread(IMAGE_PATH)
        print(f"✓ Image chargée: {img.shape}")
    except FileNotFoundError:
        print(f"❌ Erreur: Image non trouvée dans {IMAGE_PATH}")
        return
    except Exception as e:
        print(f"❌ Erreur de chargement: {e}")
        return

    # 1. Prétraitement
    print("\n" + "-"*60)
    print("ÉTAPE 1: Prétraitement de l'image")
    print("-"*60)
    
    img_bin, img_gris = pretraiter_image(img)
    print("✓ Prétraitement terminé")
    
    # Sauvegarde des images intermédiaires si mode debug
    if config.SAVE_DEBUG_IMAGES:
        sauvegarder_images_intermediaires(img, img_bin, img_gris, 
                                         prefix=IMAGE_PATH.split('/')[-1].split('.')[0])

    # 2. Détection
    print("\n" + "-"*60)
    print("ÉTAPE 2: Détection des touches")
    print("-"*60)
    
    touches, mean_y, y_min, y_max = detecter_touches(img_bin)
    
    if len(touches) < config.MIN_TOUCHES_DETECTEES:
        print(f"❌ Échec: Seulement {len(touches)} touches détectées (minimum: {config.MIN_TOUCHES_DETECTEES})")
        print("   Suggestions:")
        print("   - Vérifiez la qualité de l'image")
        print("   - Ajustez les paramètres dans config.py")
        print("   - Utilisez explore_shape.py pour analyser les seuils")
        return
    
    print(f"✓ {len(touches)} touches détectées")

    # 3. Identification des zones
    print("\n" + "-"*60)
    print("ÉTAPE 3: Identification des zones clés")
    print("-"*60)
    
    rois = identifier_zones_cles(touches)
    
    if rois is None:
        print("❌ Échec: Impossible d'identifier la structure du clavier")
        print("   Suggestions:")
        print("   - Vérifiez que le clavier est entièrement visible")
        print("   - Assurez-vous que l'éclairage est uniforme")
        print("   - Lancez explore_shape.py pour diagnostiquer")
        return
    
    zones_identifiees = [k for k, v in rois.items() if v and k != "h_ref"]
    print(f"✓ {len(zones_identifiees)} zones identifiées: {', '.join(zones_identifiees)}")

    # 4. Classification
    print("\n" + "-"*60)
    print("ÉTAPE 4: Classification du layout")
    print("-"*60)
    
    verdict, debug = classifier_clavier(rois, img_gris, touches)
    
    # --- AFFICHAGE RÉSULTATS TERMINAL ---
    print("\n" + "="*60)
    print("📋 RÉSULTATS DE L'ANALYSE")
    print("="*60)
    print(f"📐 Format   : {verdict.get('ISO_ANSI', '?')}")
    print(f"💻 Système  : {verdict.get('MAC_WIN', '?')}")
    print(f"🌍 Layout   : {verdict.get('LAYOUT', '?')}")
    print("\n" + "-"*60)
    print("📊 Métriques techniques:")
    print("-"*60)
    
    for k, v in sorted(debug.items()):
        if isinstance(v, (int, float)):
            print(f"   {k:<25} : {v:>8.2f}")
        else:
            print(f"   {k:<25} : {v}")
    
    print("="*60)

    # --- VISUALISATION GRAPHIQUE ---
    if config.DEBUG_MODE:
        # Mode debug: visualisation détaillée
        print("\n🖼️  Génération de la visualisation détaillée...")
        fig = visualiser_detection_detaillee(
            img, touches, rois, verdict, debug,
            save_path=f"data/debug/{IMAGE_PATH.split('/')[-1].split('.')[0]}_analyse.png"
        )
    else:
        # Mode normal: visualisation simple
        print("\n🖼️  Affichage de la visualisation...")
        fig, ax = plt.subplots(figsize=(14, 9))
        ax.imshow(img, cmap='gray')
        ax.set_title(f"{verdict['LAYOUT']} - {verdict['MAC_WIN']} - {verdict['ISO_ANSI']}", 
                    fontsize=16, fontweight='bold')

        # Zones de filtrage
        ax.axhline(y=y_min, color='red', linestyle='--', alpha=0.3, linewidth=2, label='Zone filtrage')
        ax.axhline(y=y_max, color='red', linestyle='--', alpha=0.3, linewidth=2)

        # Couleurs des ROI
        colors = {
            "SPACE": "blue",
            "SHIFT": "orange",
            "TL_LETTER": "green",
            "OS_KEY": "magenta",
            "ENTER_KEY": "cyan"
        }

        # Toutes les touches en vert pâle
        for r in touches:
            rect = mpatches.Rectangle((r.bbox[1], r.bbox[0]), 
                                      r.bbox[3] - r.bbox[1], 
                                      r.bbox[2] - r.bbox[0],
                                      fill=False, edgecolor='lime', linewidth=0.5, alpha=0.4)
            ax.add_patch(rect)

        # ROI en couleur
        for name, region in rois.items():
            if region and name != "h_ref":
                minr, minc, maxr, maxc = region.bbox
                color = colors.get(name, "yellow")
                rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                          fill=False, edgecolor=color, linewidth=3, label=name)
                ax.add_patch(rect)
                
                ax.text(minc, minr - 8, name, color=color, fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round', facecolor='black', alpha=0.6))

        # Légende
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=10)

    print("\n✓ Analyse terminée avec succès!")
    print("  Appuyez sur une touche pour fermer la fenêtre...\n")
    plt.show()

if __name__ == "__main__":
    main()
