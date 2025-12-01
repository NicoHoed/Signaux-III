import easyocr
import numpy as np
from collections import Counter
from sklearn.mixture import GaussianMixture # Pour le clustering
import warnings

# Mapping pour corriger les erreurs fréquentes d'OCR sur les touches
OCR_CORRECTIONS = {
    '0': 'O', '1': 'I', '5': 'S', '2': 'Z', '4': 'A', '8': 'B', 
    '|': 'I', '$': 'S', '€': 'E', '(': 'C'
}

# Définition stricte des rangées
LAYOUTS = {
    "AZERTY": {
        "rows": ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN"],
        "indicators": ["A", "Z", "M"] # Lettres discriminantes
    },
    "QWERTY": {
        "rows": ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
        "indicators": ["Q", "W", "A"]
    },
    "QWERTZ": {
        "rows": ["QWERTZUIOP", "ASDFGHJKL", "YXCVBNM"],
        "indicators": ["Z", "Y"]
    }
}

def clean_char(text):
    text = text.upper().strip()
    if len(text) > 1: return "" # On veut des lettres uniques
    return OCR_CORRECTIONS.get(text, text)

def run_ocr_pipeline(reader, processed_images):
    """
    Lance l'OCR sur toutes les versions de l'image et fusionne les résultats.
    Retourne: { 'A': {'count': 2, 'avg_y': 150.5}, ... }
    """
    char_data = {}

    for method_name, img in processed_images:
        # Allowlist pour forcer EasyOCR à ne chercher que ça
        results = reader.readtext(img, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        for (bbox, text, conf) in results:
            if conf < 0.4: continue # Filtre confiance faible
            
            char = clean_char(text)
            if not char or not char.isalpha(): continue

            # Calcul du centre Y de la lettre (pour le clustering)
            # bbox = [[tl, tr, br, bl]] -> y est à l'index 1
            y_center = (bbox[0][1] + bbox[2][1]) / 2

            if char not in char_data:
                char_data[char] = {'y_sum': 0, 'count': 0, 'confs': []}
            
            char_data[char]['y_sum'] += y_center
            char_data[char]['count'] += 1
            char_data[char]['confs'].append(conf)

    # Filtrage : on ne garde que les lettres vues sur au moins 1 méthode (ou 2 pour être strict)
    validated_chars = {}
    for char, data in char_data.items():
        # On calcule la position Y moyenne de la lettre
        avg_y = data['y_sum'] / data['count']
        validated_chars[char] = avg_y

    return validated_chars

def cluster_rows(validated_chars):
    """
    Utilise le Gaussian Mixture Model pour trouver les 3 rangées clavier
    basé sur la position Y des lettres.
    """
    if len(validated_chars) < 5:
        return None # Pas assez de données

    # Préparation des données pour sklearn (tableau 2D)
    y_coords = np.array(list(validated_chars.values())).reshape(-1, 1)
    
    # On cherche 3 clusters (Haut, Milieu, Bas)
    try:
        gmm = GaussianMixture(n_components=3, random_state=42)
        labels = gmm.fit_predict(y_coords)
        means = gmm.means_.flatten()
        
        # On trie les clusters par position Y (0 = Haut, 1 = Milieu, 2 = Bas)
        sorted_indices = np.argsort(means)
        map_cluster = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted_indices)}
        
        # On associe chaque lettre à sa rangée (0, 1 ou 2)
        char_rows = {}
        chars_list = list(validated_chars.keys())
        for i, char in enumerate(chars_list):
            original_cluster = labels[i]
            corrected_row = map_cluster[original_cluster]
            char_rows[char] = corrected_row
            
        return char_rows
    except Exception as e:
        print(f"Erreur clustering: {e}")
        return None

def score_layout(char_to_row_map):
    """
    Compare la position réelle des lettres (char_to_row_map)
    avec la position théorique des layouts.
    """
    scores = {k: 0 for k in LAYOUTS.keys()}
    
    if not char_to_row_map:
        return "UNKNOWN", 0, {}

    for layout_name, layout_data in LAYOUTS.items():
        ref_rows = layout_data["rows"]
        
        for char, detected_row_idx in char_to_row_map.items():
            # Dans quelle rangée cette lettre DEVRAIT être pour ce layout ?
            expected_row_idx = -1
            for idx, row_str in enumerate(ref_rows):
                if char in row_str:
                    expected_row_idx = idx
                    break
            
            if expected_row_idx != -1:
                if expected_row_idx == detected_row_idx:
                    # +2 points si la lettre est exactement dans la bonne rangée
                    scores[layout_name] += 2
                    
                    # +5 points bonus si c'est une lettre clé (A, Z, Q, W)
                    if char in layout_data["indicators"]:
                        scores[layout_name] += 5
                else:
                    # -2 points si la lettre est dans la mauvaise rangée (ex: Q en bas)
                    scores[layout_name] -= 2
            else:
                # Lettre neutre ou absente du layout
                pass

    best_layout = max(scores, key=scores.get)
    max_score = scores[best_layout]
    
    # Confiance basique (normalisation)
    confidence = min(100, max(0, max_score * 2)) 
    
    return best_layout, confidence, scores