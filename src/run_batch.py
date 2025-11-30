import os
import csv
import glob
from skimage import io
import config
from datetime import datetime

from src.preprocessing import pretraiter_image
from src.analysis import detecter_touches, identifier_zones_cles, classifier_clavier
from src.debug_utils import generer_rapport_html

# --- CONFIGURATION ---
INPUT_DIR = 'data/inputs'
OUTPUT_DIR = 'data/outputs'
OUTPUT_CSV = os.path.join(OUTPUT_DIR, 'rapport_analyse.csv')
OUTPUT_HTML = os.path.join(OUTPUT_DIR, 'rapport_analyse.html')
EXTENSIONS = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.bmp']

def analyser_image(image_path, verbose=True):
    """
    Exécute le pipeline complet sur une image.
    Retourne un dictionnaire de résultats détaillés.
    """
    nom_fichier = os.path.basename(image_path)
    
    resultat = {
        "Fichier": nom_fichier,
        "Statut": "OK",
        "Format": "N/A",
        "OS": "N/A",
        "Langue": "N/A",
        "NB_Touches": 0,
        "Shift_Ratio": 0.0,
        "Enter_Ratio_H_L": 0.0,
        "OS_Euler": 0,
        "TL_CenterY": 0.0,
        "TL_Extent": 0.0,
        "h_ref": 0.0
    }

    try:
        # 1. Chargement
        img = io.imread(image_path)
        
        # 2. Prétraitement
        img_bin, img_gris = pretraiter_image(img)
        
        # 3. Détection
        touches, _, _, _ = detecter_touches(img_bin)
        resultat["NB_Touches"] = len(touches)
        
        if len(touches) < config.MIN_TOUCHES_DETECTEES:
            resultat["Statut"] = f"ÉCHEC (Seulement {len(touches)} touches, min: {config.MIN_TOUCHES_DETECTEES})"
            return resultat

        # 4. Zoning
        rois = identifier_zones_cles(touches)
        
        if rois is None:
            resultat["Statut"] = "ÉCHEC (Identification des zones clés impossible)"
            return resultat
        
        # Vérification des zones critiques
        zones_manquantes = []
        for zone in ["SPACE", "SHIFT", "OS_KEY"]:
            if not rois.get(zone):
                zones_manquantes.append(zone)
        
        if zones_manquantes:
            resultat["Statut"] = f"ÉCHEC (Zones manquantes: {', '.join(zones_manquantes)})"
            return resultat

        # 5. Classification
        verdict, debug = classifier_clavier(rois, img_gris, touches)
        
        # Remplissage des résultats
        resultat["Format"] = verdict.get("ISO_ANSI", "?")
        resultat["OS"] = verdict.get("MAC_WIN", "?")
        resultat["Langue"] = verdict.get("LAYOUT", "?")
        
        # Métriques techniques
        resultat["Shift_Ratio"] = round(debug.get("Shift_Ratio", 0), 2)
        resultat["Enter_Ratio_H_L"] = round(debug.get("Enter_Ratio_H_L", 0), 2)
        resultat["OS_Euler"] = debug.get("OS_Euler", 0)
        resultat["TL_CenterY"] = round(debug.get("TL_CenterY", 0), 3)
        resultat["TL_Extent"] = round(debug.get("TL_Extent", 0), 3)
        resultat["h_ref"] = round(rois.get("h_ref", 0), 1)
        
        # Ajout de la confiance OCR si disponible
        if "Layout_Confiance" in debug:
            resultat["OCR_Confiance"] = round(debug["Layout_Confiance"], 2)

    except Exception as e:
        resultat["Statut"] = f"ERREUR ({str(e)[:50]})"
        if verbose:
            print(f"      Exception détaillée: {str(e)}")
    
    return resultat


def main():
    print("="*70)
    print("🔄 TRAITEMENT PAR LOT - ANALYSE DE CLAVIERS")
    print("="*70)
    print(f"Répertoire d'entrée: {INPUT_DIR}")
    print(f"Fichier de sortie CSV: {OUTPUT_CSV}")
    print(f"Fichier de sortie HTML: {OUTPUT_HTML}\n")
    
    # 1. Récupération des fichiers
    fichiers = []
    for ext in EXTENSIONS:
        fichiers.extend(glob.glob(os.path.join(INPUT_DIR, ext)))
    
    if not fichiers:
        print(f"❌ Aucun fichier trouvé dans {INPUT_DIR}")
        print(f"   Extensions recherchées: {', '.join(EXTENSIONS)}")
        return

    print(f"📁 {len(fichiers)} image(s) trouvée(s)\n")
    print("-"*70)
    
    resultats_globaux = []
    success_count = 0
    
    # 2. Boucle de traitement
    start_time = datetime.now()
    
    for i, fichier in enumerate(fichiers):
        nom_court = os.path.basename(fichier)
        print(f"\n[{i+1}/{len(fichiers)}] 🔍 Traitement: {nom_court}")
        
        donnees = analyser_image(fichier, verbose=config.DEBUG_MODE)
        resultats_globaux.append(donnees)
        
        # Feedback visuel
        if "OK" in donnees["Statut"]:
            success_count += 1
            icon = "✅"
            color_code = "\033[92m"  # Vert
        else:
            icon = "❌"
            color_code = "\033[91m"  # Rouge
        
        reset_code = "\033[0m"
        
        print(f"   {icon} {color_code}Statut: {donnees['Statut']}{reset_code}")
        
        if "OK" in donnees["Statut"]:
            print(f"      Format: {donnees['Format']}")
            print(f"      OS: {donnees['OS']}")
            print(f"      Layout: {donnees['Langue']}")
            print(f"      Touches: {donnees['NB_Touches']}")
    
    # Temps d'exécution
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DU TRAITEMENT")
    print("="*70)
    print(f"✅ Succès: {success_count}/{len(fichiers)} ({success_count/len(fichiers)*100:.1f}%)")
    print(f"❌ Échecs: {len(fichiers) - success_count}/{len(fichiers)}")
    print(f"⏱️  Temps total: {elapsed:.1f}s ({elapsed/len(fichiers):.2f}s/image)")
    print("="*70)

    # 3. Sauvegarde CSV
    print(f"\n💾 Sauvegarde des résultats...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    colonnes = [
        "Fichier", "Statut", "Format", "OS", "Langue", "NB_Touches",
        "Shift_Ratio", "Enter_Ratio_H_L", "OS_Euler", 
        "TL_CenterY", "TL_Extent", "h_ref"
    ]
    
    # Ajouter OCR_Confiance si présent
    if any("OCR_Confiance" in r for r in resultats_globaux):
        colonnes.append("OCR_Confiance")
    
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=colonnes, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(resultats_globaux)
        
        print(f"   ✓ CSV sauvegardé: {OUTPUT_CSV}")
        
    except IOError as e:
        print(f"   ❌ Erreur d'écriture CSV: {e}")
        return
    
    # 4. Génération du rapport HTML
    try:
        generer_rapport_html(resultats_globaux, OUTPUT_HTML)
        print(f"   ✓ HTML sauvegardé: {OUTPUT_HTML}")
    except Exception as e:
        print(f"   ⚠️  Erreur génération HTML: {e}")
    
    print("\n✅ Traitement par lot terminé avec succès!")
    print(f"📄 Consultez les rapports dans: {OUTPUT_DIR}\n")


if __name__ == "__main__":
    main()
