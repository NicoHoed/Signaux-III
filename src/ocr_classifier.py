import pytesseract
from PIL import Image
import numpy as np
from skimage import filters, exposure
import config
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Définition des layouts de référence
KEYBOARD_LAYOUTS = {
    # ----- QWERTY -----
    'QWERTY_US': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        'special_markers': {'pos_6': 'Y', 'pos_2': 'W'},
        'region': 'US',
        'iso_type': 'ANSI'
    },
    'QWERTY_UK': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        'special_markers': {'pos_6': 'Y', 'pos_2': 'W', 'shift_shape': 'ISO'},
        'region': 'UK',
        'iso_type': 'ISO'
    },
    'QWERTY_INTL': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        'special_markers': {'dead_keys': True},
        'region': 'International',
        'iso_type': 'ANSI'
    },
    'QWERTY_CA': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        'special_markers': {'accent': 'É'},
        'region': 'Canada',
        'iso_type': 'ANSI'
    },
    'QWERTY_AU': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        'special_markers': {},
        'region': 'Australia',
        'iso_type': 'ANSI'
    },
    'QWERTY_NORDIC': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'Å'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ø', 'Æ'],
        'special_markers': {'nordic': True},
        'region': 'DK/NO',
        'iso_type': 'ISO'
    },

    # ----- QWERTZ -----
    'QWERTZ_DE': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Z', 'U', 'I', 'O', 'P'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        'special_markers': {'pos_6': 'Z', 'pos_2': 'W'},
        'region': 'DE/CH/AT',
        'iso_type': 'ISO'
    },
    'QWERTZ_CH': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Z', 'U', 'I', 'O', 'P', 'È'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'É'],
        'special_markers': {'accents': ['È', 'É']},
        'region': 'CH',
        'iso_type': 'ISO'
    },
    'QWERTZ_CZ': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Z', 'U', 'I', 'O', 'P', 'Ú'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ž'],
        'special_markers': {'czech_letters': ['Á', 'É', 'Ě', 'Ř']},
        'region': 'CZ',
        'iso_type': 'ISO'
    },
    'QWERTZ_SK': {
        'row1': ['Q', 'W', 'E', 'R', 'T', 'Z', 'U', 'I', 'O', 'P', 'Ň'],
        'row2': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ľ', 'Š'],
        'special_markers': {'slavic_letters': True},
        'region': 'SK',
        'iso_type': 'ISO'
    },

    # ----- AZERTY -----
    'AZERTY_FR': {
        'row1': ['A', 'Z', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['Q', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M'],
        'special_markers': {'pos_1': 'A', 'pos_2': 'Z', 'pos_6': 'Y'},
        'region': 'FR',
        'iso_type': 'ISO'
    },
    'AZERTY_BE': {
        'row1': ['A', 'Z', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['Q', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M'],
        'special_markers': {'pos_1': 'A', 'pos_2': 'Z', 'pos_6': 'Y'},
        'region': 'BE',
        'iso_type': 'ISO'
    },
    'AZERTY_FR_MODERN': {
        'row1': ['A', 'Z', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'È'],
        'row2': ['Q', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'Ê'],
        'special_markers': {'extra_accents': True},
        'region': 'FR (AFNOR 2019)',
        'iso_type': 'ISO'
    },
    'AZERTY_MAC_FR': {
        'row1': ['A', 'Z', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        'row2': ['Q', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M'],
        'special_markers': {'apple_layout': True},
        'region': 'FR (Apple)',
        'iso_type': 'ISO'
    },
    'AZERTY_CH': {
        'row1': ['A', 'Z', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'È'],
        'row2': ['Q', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'É'],
        'special_markers': {'accents': ['È', 'É']},
        'region': 'CH (Romandie)',
        'iso_type': 'ISO'
    }
}


def extraire_texte_touche(region, img_gris, mode='letter'):
    """
    Extrait le caractère d'une touche via OCR avec prétraitement optimisé.
    
    Args:
        region: Région de la touche
        img_gris: Image en niveaux de gris
        mode: 'letter' pour lettres seules, 'all' pour tous caractères
    
    Returns:
        str or None: Caractère détecté en majuscule
    """
    minr, minc, maxr, maxc = region.bbox
    vignette = img_gris[minr:maxr, minc:maxc]

    if vignette.size == 0 or vignette.shape[0] < 5 or vignette.shape[1] < 5:
        return None

    # 1. Redimensionnement intelligent (ratio préservé)
    from skimage.transform import resize
    target_height = max(80, vignette.shape[0] * 3)
    target_width = int(vignette.shape[1] * (target_height / vignette.shape[0]))
    vignette = resize(vignette, (target_height, target_width),
                      order=1, mode="reflect", anti_aliasing=True)

    # 2. Sharpen adaptatif
    laplace = filters.laplace(vignette)
    vignette = np.clip(vignette + 0.5 * laplace, 0, 1)

    # 3. Amélioration du contraste
    vignette = exposure.equalize_adapthist(vignette, clip_limit=0.04)

    # 4. Conversion 8 bits
    vignette = (vignette * 255).astype(np.uint8)

    # 5. Binarisation avec marge de sécurité
    try:
        thresh = filters.threshold_otsu(vignette)
        vignette_bin = (vignette > thresh * 0.9).astype(np.uint8) * 255
    except Exception:
        vignette_bin = vignette

    # 6. Conversion PIL
    pil_img = Image.fromarray(vignette_bin)

    try:
        if mode == 'letter':
            whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        else:
            whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        config_ocr = f'--psm 10 -c tessedit_char_whitelist={whitelist}'
        texte = pytesseract.image_to_string(pil_img, config=config_ocr).strip().upper()
        
        texte = ''.join(c for c in texte if c.isalnum())
        return texte[0] if texte else None
    except Exception as e:
        if config.DEBUG_MODE:
            print(f"   Erreur OCR: {e}")
        return None


def trouver_touches_rangee(touches, y_ref, tolerance=30):
    """
    Trouve toutes les touches d'une rangée à partir d'une position Y de référence.
    """
    touches_rangee = []
    for r in touches:
        cy = r.centroid[0]
        if abs(cy - y_ref) < tolerance:
            touches_rangee.append(r)
    
    return sorted(touches_rangee, key=lambda r: r.centroid[1])


def extraire_sequence_touches(touches_rangee, img_gris, max_touches=10):
    """
    Extrait la séquence de caractères d'une rangée de touches.
    """
    sequence = []
    for i, touche in enumerate(touches_rangee[:max_touches]):
        h = touche.bbox[2] - touche.bbox[0]
        w = touche.bbox[3] - touche.bbox[1]
        ratio = w / h if h > 0 else 0
        
        if ratio > 1.8:
            continue
            
        char = extraire_texte_touche(touche, img_gris)
        if char:
            sequence.append(char)
    
    return sequence


def calculer_score_layout(sequence_detectee, layout_reference):
    """
    Compare une séquence détectée avec un layout de référence.
    """
    if not sequence_detectee or not layout_reference:
        return 0.0
    
    matches = 0
    min_length = min(len(sequence_detectee), len(layout_reference))
    
    for i in range(min_length):
        if sequence_detectee[i] == layout_reference[i]:
            matches += 1
    
    base_score = matches / min_length if min_length > 0 else 0
    
    if min_length >= 3:
        early_matches = sum(1 for i in range(3) if sequence_detectee[i] == layout_reference[i])
        bonus = early_matches * 0.1
        return min(1.0, base_score + bonus)
    
    return base_score


def classifier_layout_ocr(rois, touches, img_gris, iso_ansi_info=None):
    """
    Classification complète du layout avec détection du pays/région.
    
    Returns:
        tuple: (layout_complet, confiance, details)
    """
    if not rois.get("TL_LETTER"):
        return None, 0.0, {}
    
    if config.DEBUG_MODE:
        print("\n=== Classification Layout Améliorée ===")
    
    # 1. Extraire les séquences de la première rangée
    y_ref = rois["TL_LETTER"].centroid[0]
    rangee1 = trouver_touches_rangee(touches, y_ref, tolerance=25)
    
    if config.DEBUG_MODE:
        print(f"   Touches trouvées rangée 1: {len(rangee1)}")
    
    sequence_row1 = extraire_sequence_touches(rangee1, img_gris, max_touches=10)
    
    if config.DEBUG_MODE:
        print(f"   Séquence détectée: {sequence_row1}")
    
    # 2. Extraire la deuxième rangée
    h_ref = rois.get("h_ref", 50)
    y_ref_row2 = y_ref + (h_ref * 1.0)
    rangee2 = trouver_touches_rangee(touches, y_ref_row2, tolerance=25)
    sequence_row2 = extraire_sequence_touches(rangee2, img_gris, max_touches=9)
    
    if config.DEBUG_MODE:
        print(f"   Séquence rangée 2: {sequence_row2}")
    
    # 3. Calcul des scores pour chaque layout
    scores = {}
    for layout_name, layout_data in KEYBOARD_LAYOUTS.items():
        score_row1 = calculer_score_layout(sequence_row1, layout_data['row1'])
        score_row2 = calculer_score_layout(sequence_row2, layout_data['row2'])
        
        score_total = (score_row1 * 0.7) + (score_row2 * 0.3)
        
        if iso_ansi_info and layout_data['iso_type'] in iso_ansi_info:
            score_total += 0.1
        
        scores[layout_name] = min(1.0, score_total)
        
        if config.DEBUG_MODE:
            print(f"   {layout_name}: score={score_total:.2f} (r1={score_row1:.2f}, r2={score_row2:.2f})")
    
    # 4. Sélection du meilleur layout
    if not scores:
        return None, 0.0, {}
    
    best_layout = max(scores, key=scores.get)
    best_score = scores[best_layout]
    
    if best_score < 0.3:
        if config.DEBUG_MODE:
            print(f"   Score trop faible ({best_score:.2f}), fallback géométrique")
        return None, best_score, {'scores': scores, 'sequences': {'row1': sequence_row1, 'row2': sequence_row2}}
    
    layout_info = KEYBOARD_LAYOUTS[best_layout]
    details = {
        'layout_name': best_layout,
        'base_layout': best_layout.split('_')[0],
        'region': layout_info['region'],
        'iso_type': layout_info['iso_type'],
        'scores': scores,
        'sequences': {'row1': sequence_row1, 'row2': sequence_row2},
        'confidence': best_score
    }
    
    if config.DEBUG_MODE:
        print(f"\n   ✓ Layout détecté: {best_layout}")
        print(f"   ✓ Région: {layout_info['region']}")
        print(f"   ✓ Confiance: {best_score:.0%}")
    
    return best_layout, best_score, details