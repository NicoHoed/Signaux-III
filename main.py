# main.py
import cv2
import easyocr
import os
import sys

# IMPORTANT : On importe depuis le dossier 'src'
from src.preprocessing import get_processed_images
from src.engine import run_ocr_pipeline, cluster_rows, score_layout

def analyze_image(image_path, reader):
    print(f"\n--- Analyse de : {os.path.basename(image_path)} ---")
    
    # 1. Chargement
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Erreur: Impossible de lire l'image à {image_path}")
        return

    # 2. Prétraitement (3 versions)
    # Note: si une erreur survient ici, vérifiez que preprocessing.py est bien dans src/
    processed = get_processed_images(img)
    print("✅ Prétraitement terminé (3 méthodes générées)")

    # 3. OCR (Extraction des lettres et positions Y)
    print("⏳ OCR en cours (patience)...")
    validated_chars = run_ocr_pipeline(reader, processed)
    
    detected_list = list(validated_chars.keys())
    print(f"✅ Lettres détectées ({len(detected_list)}) : {sorted(detected_list)}")

    if len(detected_list) < 5:
        print("⚠️ Pas assez de lettres pour déterminer le layout.")
        return

    # 4. Clustering (Détermination des rangées Haut/Milieu/Bas)
    char_rows = cluster_rows(validated_chars)
    if char_rows:
        # Petit affichage debug des rangées trouvées
        rows_debug = {0: [], 1: [], 2: []}
        for c, r in char_rows.items(): 
            if r in rows_debug: rows_debug[r].append(c)
        
        print(f"   📐 Rangée Haut   : {sorted(rows_debug[0])}")
        print(f"   📐 Rangée Milieu : {sorted(rows_debug[1])}")
        print(f"   📐 Rangée Bas    : {sorted(rows_debug[2])}")
    else:
        print("❌ Echec du clustering des rangées.")
        return

    # 5. Scoring & Résultat
    best_layout, confidence, details = score_layout(char_rows)
    
    print("\n" + "="*30)
    print(f"🏆 RÉSULTAT : {best_layout}")
    print(f"📊 Confiance : {confidence:.1f}%")
    print("="*30)

if __name__ == "__main__":
    # Initialisation unique du lecteur (lourd)
    print("Chargement du modèle EasyOCR...")
    reader = easyocr.Reader(['en'], gpu=False) 
    
    # ADAPTATION DU CHEMIN : data/inputs
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir, "data", "inputs")
    
    if not os.path.exists(data_folder):
        print(f"❌ Le dossier n'existe pas : {data_folder}")
        print("Veuillez créer 'data/inputs' et y mettre vos images.")
        sys.exit()

    # On ne prend que les images
    extensions_valides = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
    files = [f for f in os.listdir(data_folder) if f.lower().endswith(extensions_valides)]
    
    if not files:
        print(f"❌ Aucune image trouvée dans {data_folder}")
    
    for f in files:
        path = os.path.join(data_folder, f)
        analyze_image(path, reader)