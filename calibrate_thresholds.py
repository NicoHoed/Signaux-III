"""
Script de calibration automatique des seuils géométriques.
Analysez quelques images de chaque type pour trouver les seuils optimaux.
"""
import glob
import numpy as np
from skimage import io
from src.preprocessing import pretraiter_image
from src.analysis import detecter_touches, identifier_zones_cles

def analyser_image_pour_calibration(image_path):
    """
    Extrait les métriques géométriques d'une image.
    """
    try:
        img = io.imread(image_path)
        img_bin, img_gris = pretraiter_image(img)
        touches, _, _, _ = detecter_touches(img_bin)
        rois = identifier_zones_cles(touches)
        
        if not rois or not rois.get("TL_LETTER"):
            return None
        
        r = rois["TL_LETTER"]
        minr, _, maxr, _ = r.bbox
        h = maxr - minr
        cy_norm = (r.centroid[0] - minr) / h if h > 0 else 0
        extent = r.extent
        
        return {
            'fichier': image_path.split('\\')[-1],
            'cy_norm': cy_norm,
            'extent': extent
        }
    except Exception as e:
        print(f"Erreur sur {image_path}: {e}")
        return None


def calibrer_seuils():
    """
    Calibration interactive des seuils.
    """
    print("="*70)
    print("🎯 CALIBRATION DES SEUILS GÉOMÉTRIQUES")
    print("="*70)
    print("\nCe script va analyser vos images pour trouver les seuils optimaux.\n")
    
    # Collecte des images
    print("📁 Recherche des images dans data/inputs/...")
    images = glob.glob('data/inputs/*.png') + glob.glob('data/inputs/*.jpg')
    
    if not images:
        print("❌ Aucune image trouvée dans data/inputs/")
        return
    
    print(f"✓ {len(images)} image(s) trouvée(s)\n")
    
    # Classification manuelle
    resultats = {'QWERTY': [], 'QWERTZ': [], 'AZERTY': []}
    
    print("Pour chaque image, indiquez le layout RÉEL:")
    print("  1 = QWERTY")
    print("  2 = QWERTZ")
    print("  3 = AZERTY")
    print("  s = skip (ignorer)")
    print("-"*70)
    
    for img_path in images:
        nom = img_path.split('\\')[-1]
        print(f"\n📷 {nom}")
        
        # Analyse automatique
        metriques = analyser_image_pour_calibration(img_path)
        
        if not metriques:
            print("   ⚠️ Échec analyse, ignoré")
            continue
        
        print(f"   Métriques: CenterY={metriques['cy_norm']:.3f}, Extent={metriques['extent']:.3f}")
        
        # Demande utilisateur
        while True:
            choix = input("   Layout réel (1=QWERTY, 2=QWERTZ, 3=AZERTY, s=skip): ").strip().lower()
            
            if choix == '1':
                resultats['QWERTY'].append(metriques)
                print("   ✓ Enregistré comme QWERTY")
                break
            elif choix == '2':
                resultats['QWERTZ'].append(metriques)
                print("   ✓ Enregistré comme QWERTZ")
                break
            elif choix == '3':
                resultats['AZERTY'].append(metriques)
                print("   ✓ Enregistré comme AZERTY")
                break
            elif choix == 's':
                print("   ⊘ Ignoré")
                break
            else:
                print("   ❌ Choix invalide, recommencez")
    
    # Calcul des seuils optimaux
    print("\n" + "="*70)
    print("📊 RÉSULTATS DE LA CALIBRATION")
    print("="*70)
    
    total = sum(len(v) for v in resultats.values())
    
    if total < 2:
        print("\n❌ Pas assez de données pour calibrer (minimum 2 images)")
        return
    
    print(f"\n✓ {total} image(s) analysée(s):")
    for layout, data in resultats.items():
        if data:
            print(f"   - {layout}: {len(data)} image(s)")
    
    # Calcul statistiques
    print("\n" + "-"*70)
    print("📈 STATISTIQUES PAR LAYOUT")
    print("-"*70)
    
    stats = {}
    for layout, data in resultats.items():
        if data:
            cy_values = [d['cy_norm'] for d in data]
            extent_values = [d['extent'] for d in data]
            
            stats[layout] = {
                'cy_mean': np.mean(cy_values),
                'cy_std': np.std(cy_values),
                'extent_mean': np.mean(extent_values),
                'extent_std': np.std(extent_values)
            }
            
            print(f"\n{layout}:")
            print(f"   CenterY : {stats[layout]['cy_mean']:.3f} ± {stats[layout]['cy_std']:.3f}")
            print(f"   Extent  : {stats[layout]['extent_mean']:.3f} ± {stats[layout]['extent_std']:.3f}")
    
    # Calcul des seuils optimaux
    if 'AZERTY' in stats and ('QWERTY' in stats or 'QWERTZ' in stats):
        print("\n" + "-"*70)
        print("🎯 SEUILS OPTIMAUX CALCULÉS")
        print("-"*70)
        
        # Seuil CenterY : point médian entre AZERTY et QWERTY/QWERTZ
        azerty_cy = stats['AZERTY']['cy_mean']
        qwerty_cy = stats.get('QWERTY', {}).get('cy_mean', 
                              stats.get('QWERTZ', {}).get('cy_mean', azerty_cy))
        
        optimal_cy = (azerty_cy + qwerty_cy) / 2
        
        # Seuil Extent : point médian
        azerty_ext = stats['AZERTY']['extent_mean']
        qwerty_ext = stats.get('QWERTY', {}).get('extent_mean',
                               stats.get('QWERTZ', {}).get('extent_mean', azerty_ext))
        
        optimal_extent = (azerty_ext + qwerty_ext) / 2
        
        print(f"\nTHRESHOLD_TL_CENTER_Y_AZERTY = {optimal_cy:.2f}")
        print(f"THRESHOLD_TL_EXTENT_AZERTY = {optimal_extent:.2f}")
        
        print("\n💡 Copiez ces valeurs dans config.py, section:")
        print("   # 4. AZERTY vs QWERTY (géométrique - fallback uniquement)")
        
        # Test de validation
        print("\n" + "-"*70)
        print("🧪 VALIDATION DES SEUILS")
        print("-"*70)
        
        correct = 0
        total_test = 0
        
        for layout, data in resultats.items():
            for metriques in data:
                total_test += 1
                cy = metriques['cy_norm']
                ext = metriques['extent']
                
                # Test du seuil
                is_azerty = (cy > optimal_cy and ext < optimal_extent)
                predicted = "AZERTY" if is_azerty else "QWERTY/QWERTZ"
                actual = layout
                
                match = (predicted == "AZERTY" and actual == "AZERTY") or \
                        (predicted == "QWERTY/QWERTZ" and actual in ["QWERTY", "QWERTZ"])
                
                if match:
                    correct += 1
                    symbol = "✓"
                else:
                    symbol = "✗"
                
                print(f"   {symbol} {metriques['fichier']}: {actual} → {predicted}")
        
        accuracy = (correct / total_test * 100) if total_test > 0 else 0
        print(f"\n🎯 Précision: {correct}/{total_test} ({accuracy:.1f}%)")
        
        if accuracy < 70:
            print("\n⚠️  ATTENTION: Précision faible (<70%).")
            print("   Recommandation: La méthode géométrique seule ne suffit pas.")
            print("   → Installez Tesseract pour utiliser l'OCR (méthode fiable)")
    else:
        print("\n⚠️  Impossible de calculer les seuils:")
        print("   Il faut au moins 1 image AZERTY ET 1 image QWERTY/QWERTZ")


if __name__ == "__main__":
    calibrer_seuils()