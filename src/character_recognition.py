"""
character_recognition.py
Reconnaissance de caractères par template matching et corrélation croisée
Utilise les techniques de traitement de signal vues en cours
"""

import numpy as np
from skimage import transform, io, color
from scipy.signal import correlate2d
import os


def extraire_roi(img, bbox, padding=10):
    """
    Extrait la région d'intérêt d'une touche avec padding
    
    Paramètres :
    - img : image source (niveaux de gris ou binaire)
    - bbox : tuple (minr, minc, maxr, maxc)
    - padding : marge à retirer pour éviter les bords de touche
    
    Retourne : sous-image de la touche
    """
    minr, minc, maxr, maxc = bbox
    
    # Ajouter padding pour éviter les bords noirs de la touche
    minr_p = max(0, minr + padding)
    minc_p = max(0, minc + padding)
    maxr_p = min(img.shape[0], maxr - padding)
    maxc_p = min(img.shape[1], maxc - padding)
    
    roi = img[minr_p:maxr_p, minc_p:maxc_p]
    
    return roi


def normaliser_roi(roi, taille_cible=(50, 50)):
    """
    Normalise une ROI à une taille fixe pour la comparaison
    
    Paramètres :
    - roi : image de la touche
    - taille_cible : tuple (hauteur, largeur) de sortie
    
    Retourne : ROI redimensionnée et normalisée
    """
    if roi.size == 0:
        return np.zeros(taille_cible)
    
    # Redimensionner
    roi_resized = transform.resize(roi, taille_cible, anti_aliasing=True, preserve_range=True)
    
    # Normaliser entre 0 et 1
    if roi_resized.max() > roi_resized.min():
        roi_resized = (roi_resized - roi_resized.min()) / (roi_resized.max() - roi_resized.min())
    
    return roi_resized


def calculer_correlation_normalisee(roi, template):
    """
    Calcule le coefficient de corrélation normalisée (NCC) entre une ROI et un template
    Technique classique de template matching par corrélation
    
    Paramètres :
    - roi : image de la touche normalisée
    - template : image du template de référence
    
    Retourne : score de corrélation (entre -1 et 1, idéalement proche de 1)
    """
    # Centrer les images (retirer la moyenne)
    roi_centered = roi - np.mean(roi)
    template_centered = template - np.mean(template)
    
    # Corrélation normalisée (Normalized Cross-Correlation)
    numerateur = np.sum(roi_centered * template_centered)
    denominateur = np.sqrt(np.sum(roi_centered**2) * np.sum(template_centered**2))
    
    if denominateur == 0:
        return 0.0
    
    correlation = numerateur / denominateur
    
    # Retourner un score entre 0 et 1
    return max(0.0, correlation)


def charger_templates(chemin_templates='templates/', taille=(50, 50)):
    """
    Charge les templates de caractères depuis un dossier
    
    Structure attendue du dossier templates/ :
    - A.png, B.png, ..., Z.png (lettres majuscules)
    - 0.png, 1.png, ..., 9.png (chiffres)
    - shift.png, enter.png, space.png (touches spéciales)
    
    Paramètres :
    - chemin_templates : chemin vers le dossier contenant les templates
    - taille : taille de normalisation des templates
    
    Retourne : dictionnaire {caractère: template_normalisé}
    """
    templates = {}
    
    if not os.path.exists(chemin_templates):
        print(f"⚠️  Dossier {chemin_templates} introuvable. Créez-le et ajoutez vos templates.")
        return templates
    
    # Parcourir tous les fichiers du dossier templates
    for filename in sorted(os.listdir(chemin_templates)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            # Le nom du fichier (sans extension) = le caractère
            char = os.path.splitext(filename)[0]
            
            try:
                # Charger le template
                template_path = os.path.join(chemin_templates, filename)
                template_img = io.imread(template_path)
                
                # Convertir en niveaux de gris si nécessaire
                if len(template_img.shape) == 3:
                    template_img = color.rgb2gray(template_img)
                
                # Normaliser à la taille cible
                template_norm = normaliser_roi(template_img, taille)
                
                templates[char] = template_norm
                print(f"✓ Template chargé: '{char}'")
                
            except Exception as e:
                print(f"✗ Erreur lors du chargement de {filename}: {e}")
    
    return templates


def reconnaitre_caractere(img, bbox, templates, seuil_confiance=0.3):
    """
    Reconnaît le caractère dans une touche par template matching
    
    Paramètres :
    - img : image source complète (niveaux de gris)
    - bbox : bounding box de la touche (minr, minc, maxr, maxc)
    - templates : dictionnaire des templates {caractère: image}
    - seuil_confiance : score minimum pour valider une reconnaissance
    
    Retourne : tuple (caractère, score_confiance)
    """
    if not templates:
        return (None, 0.0)
    
    # Extraire la ROI
    roi = extraire_roi(img, bbox, padding=15)
    
    if roi.size == 0:
        return (None, 0.0)
    
    # Normaliser la ROI à la même taille que les templates
    taille_template = next(iter(templates.values())).shape
    roi_norm = normaliser_roi(roi, taille_template)
    
    # Calculer la corrélation avec chaque template
    meilleur_score = -1
    meilleur_char = None
    scores = {}
    
    for char, template in templates.items():
        score = calculer_correlation_normalisee(roi_norm, template)
        scores[char] = score
        
        if score > meilleur_score:
            meilleur_score = score
            meilleur_char = char
    
    # Vérifier le seuil de confiance
    if meilleur_score < seuil_confiance:
        return (None, meilleur_score)
    
    return (meilleur_char, meilleur_score)


def remplir_grille_avec_caracteres(img, grille, templates, seuil_confiance=0.3, verbose=True):
    """
    Remplit la grille avec les caractères reconnus
    
    Paramètres :
    - img : image source (niveaux de gris, NON binaire)
    - grille : structure de grille (liste de listes de dictionnaires)
    - templates : dictionnaire des templates
    - seuil_confiance : seuil minimum de confiance
    - verbose : afficher les résultats ligne par ligne
    
    Retourne : grille mise à jour avec les caractères et scores
    """
    if not templates:
        print("⚠️  Aucun template chargé. Impossible de reconnaître les caractères.")
        return grille
    
    for i, ligne in enumerate(grille):
        if verbose:
            print(f"\n📍 Ligne {i} ({len(ligne)} touches):")
        
        for j, touche in enumerate(ligne):
            bbox = touche['bbox']
            
            # Reconnaissance du caractère
            char, confiance = reconnaitre_caractere(img, bbox, templates, seuil_confiance)
            
            # Mise à jour de la grille
            grille[i][j]['char'] = char
            grille[i][j]['confiance'] = confiance
            
            if verbose:
                status = "✓" if char else "✗"
                char_display = char if char else "?"
                print(f"  {status} [{j:2d}] '{char_display}' (confiance: {confiance:.3f})")
    
    return grille


def exporter_layout_clavier(grille, fichier_sortie='keyboard_layout.txt'):
    """
    Exporte le layout du clavier détecté dans un fichier texte
    
    Paramètres :
    - grille : grille avec caractères reconnus
    - fichier_sortie : nom du fichier de sortie
    """
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LAYOUT CLAVIER DÉTECTÉ\n")
        f.write("=" * 80 + "\n\n")
        
        for i, ligne in enumerate(grille):
            f.write(f"Ligne {i}: ")
            chars = [touche['char'] if touche['char'] else '?' for touche in ligne]
            f.write(" | ".join(chars))
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("DÉTAILS:\n")
        f.write("=" * 80 + "\n\n")
        
        for i, ligne in enumerate(grille):
            f.write(f"\nLigne {i}:\n")
            for j, touche in enumerate(ligne):
                char = touche['char'] if touche['char'] else '?'
                conf = touche.get('confiance', 0.0)
                bbox = touche['bbox']
                f.write(f"  [{j:2d}] '{char}' (confiance: {conf:.3f}) bbox={bbox}\n")
    
    print(f"\n✓ Layout exporté dans '{fichier_sortie}'")
