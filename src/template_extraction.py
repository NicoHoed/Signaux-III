import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color
import os
import re

# ============================================================
# MAPPING : Caractères spéciaux → Noms de fichiers sûrs
# ============================================================
CHAR_MAPPING = {
    '/': 'slash',
    '\\': 'backslash',
    '|': 'pipe',
    ':': 'colon',
    ';': 'semicolon',
    ',': 'comma',
    '.': 'period',
    '<': 'less_than',
    '>': 'greater_than',
    '?': 'question',
    '*': 'asterisk',
    '"': 'quote_double',
    "'": 'quote_single',
    '`': 'backtick',
    '~': 'tilde',
    '!': 'exclamation',
    '@': 'at',
    '#': 'hash',
    '$': 'dollar',
    '%': 'percent',
    '^': 'caret',
    '&': 'ampersand',
    '(': 'paren_left',
    ')': 'paren_right',
    '[': 'bracket_left',
    ']': 'bracket_right',
    '{': 'brace_left',
    '}': 'brace_right',
    '=': 'equal',
    '+': 'plus',
    '-': 'minus',
    '_': 'underscore',
    ' ': 'space',
}


def label_vers_nom_fichier(label):
    """
    Convertit un label (potentiellement avec caractères spéciaux)
    en un nom de fichier sûr

    Exemples :
      '/' -> 'slash'
      ';' -> 'semicolon'
      'Q' -> 'Q'
      'shift' -> 'shift'

    Paramètres :
    - label : caractère ou texte à convertir

    Retourne : nom de fichier sûr (sans extension)
    """
    # Si c'est un caractère spécial, utiliser le mapping
    if label in CHAR_MAPPING:
        return CHAR_MAPPING[label]

    # Sinon, garder tel quel (lettres, chiffres, underscores OK)
    # Mais remplacer les espaces par underscore
    safe_label = label.replace(' ', '_')

    # Vérifier que c'est un nom valide
    if re.match(r'^[a-zA-Z0-9_\-]+$', safe_label):
        return safe_label
    else:
        # Si toujours invalide, nettoyer
        safe_label = re.sub(r'[^a-zA-Z0-9_\-]', '_', safe_label)
        return safe_label


def extraire_templates_interactif(img, grille, dossier_templates='templates', 
                                  start_ligne=0, start_col=0):
    """
    Extraction interactive des templates avec gestion des caractères spéciaux

    Paramètres :
    - img : image en niveaux de gris
    - grille : structure de grille (liste de listes de dictionnaires)
    - dossier_templates : dossier où sauvegarder les templates
    - start_ligne : ligne de départ (pour reprendre après une erreur)
    - start_col : colonne de départ (pour reprendre après une erreur)

    Retourne : liste des templates créés
    """
    from src.character_recognition import extraire_roi, normaliser_roi
    
    # Créer le dossier templates
    os.makedirs(dossier_templates, exist_ok=True)

    print("🎯 Extraction interactive des templates")
    print("Pour chaque touche, tapez le caractère correspondant")
    print("Les caractères spéciaux seront automatiquement convertis")
    print("Commandes : 'skip' (ignorer), 'stop' (arrêter), 'list' (voir templates)")
    print("-" * 60)

    templates_crees = []

    for i, ligne in enumerate(grille):
        # Sauter les lignes avant start_ligne
        if i < start_ligne:
            continue

        for j, touche in enumerate(ligne):
            # Sauter les colonnes avant start_col (seulement pour start_ligne)
            if i == start_ligne and j < start_col:
                continue

            bbox = touche['bbox']
            roi = extraire_roi(img, bbox, padding=15)

            # Afficher la touche
            plt.figure(figsize=(4, 4))
            plt.imshow(roi, cmap='gray')
            plt.title(f"Ligne {i}, Touche {j}")
            plt.axis('off')
            plt.show()

            # Boucle pour redemander si erreur
            while True:
                label = input(f"Label pour Ligne {i}, Touche {j} (ou skip/stop/list): ").strip()

                # Commandes spéciales
                if label.lower() == 'stop':
                    print(f"\n⏸️  Extraction arrêtée ({len(templates_crees)} templates créés)")
                    plt.close()
                    return templates_crees

                if label.lower() == 'list':
                    print(f"\n📂 Templates créés jusqu'à présent ({len(templates_crees)}) :")
                    for t in templates_crees[-10:]:  # Afficher les 10 derniers
                        print(f"  - {t}")
                    continue

                if label.lower() == 'skip' or label == '':
                    print(f"  ⊘ Ignoré\n")
                    plt.close()
                    break

                # Convertir le label en nom de fichier sûr
                nom_fichier = label_vers_nom_fichier(label)
                template_path = os.path.join(dossier_templates, f'{nom_fichier}.png')

                try:
                    # Vérifier si existe déjà
                    if os.path.exists(template_path):
                        print(f"  ⚠️  '{nom_fichier}.png' existe déjà")
                        overwrite = input(f"     Écraser ? (o/n): ").strip().lower()
                        if overwrite != 'o':
                            print(f"  ⊘ Non sauvegardé\n")
                            plt.close()
                            break

                    # Sauvegarder
                    roi_norm = normaliser_roi(roi, taille_cible=(50, 50))
                    io.imsave(template_path, (roi_norm * 255).astype('uint8'))

                    # Afficher avec mapping si caractère spécial
                    if label != nom_fichier:
                        print(f"  ✓ '{label}' sauvegardé comme '{nom_fichier}.png'\n")
                    else:
                        print(f"  ✓ Sauvegardé : {template_path}\n")

                    templates_crees.append(f"{label} → {nom_fichier}.png")
                    plt.close()
                    break

                except Exception as e:
                    print(f"  ❌ Erreur lors de la sauvegarde : {e}")
                    print(f"     Réessayez avec un autre label ou tapez 'skip'")

    print(f"\n✓✓✓ Extraction terminée ! {len(templates_crees)} templates créés")
    return templates_crees


def extraire_templates_auto(img, grille, labels_dict, dossier_templates='templates'):
    """
    Extraction automatique avec labels prédéfinis

    Paramètres :
    - img : image en niveaux de gris
    - grille : structure de grille
    - labels_dict : dictionnaire {num_ligne: [liste de labels]}
    - dossier_templates : dossier où sauvegarder

    Exemple labels_dict :
    {
        0: ['esc', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'minus', 'equal', 'delete'],
        1: ['tab', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\'],
        ...
    }

    Retourne : nombre de templates créés
    """
    from src.character_recognition import extraire_roi, normaliser_roi
    
    os.makedirs(dossier_templates, exist_ok=True)

    print("🚀 Extraction automatique des templates...")
    templates_crees = 0

    for i, ligne in enumerate(grille):
        if i not in labels_dict:
            print(f"⚠️  Pas de labels pour la ligne {i}, ignorée")
            continue

        labels = labels_dict[i]

        for j, touche in enumerate(ligne):
            if j >= len(labels):
                print(f"⚠️  Pas de label pour ligne {i}, col {j}, ignorée")
                continue

            label = labels[j]
            bbox = touche['bbox']

            # Extraire la ROI
            roi = extraire_roi(img, bbox, padding=15)
            roi_norm = normaliser_roi(roi, taille_cible=(50, 50))

            # Convertir en nom de fichier sûr
            nom_fichier = label_vers_nom_fichier(label)
            template_path = os.path.join(dossier_templates, f'{nom_fichier}.png')

            # Sauvegarder le template
            io.imsave(template_path, (roi_norm * 255).astype('uint8'))

            if label != nom_fichier:
                print(f"✓ '{label}' → {nom_fichier}.png (Ligne {i}, Col {j})")
            else:
                print(f"✓ {label}.png (Ligne {i}, Col {j})")

            templates_crees += 1

    print(f"\n✓ {templates_crees} templates extraits automatiquement!")
    return templates_crees