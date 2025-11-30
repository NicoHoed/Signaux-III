# --- Configuration Globale des Chemins ---
#IMAGE_PATH_DEFAULT = 'data/inputs/ISO-WIN-QWERTZ-2.png'
IMAGE_PATH_DEFAULT = 'data/inputs/ISO-WIN-AZERTY-5.png'

# --- Paramètres de Détection de Touche ---
AIRE_MIN = 2000      
AIRE_MAX = 400000
AIRE_MIN_RATIO = 0.0005  # 0.05% de l'aire totale
AIRE_MAX_RATIO = 0.15    # 15% de l'aire totale

RATIO_MIN = 0.5      
RATIO_MAX = 8.0

SOLIDITY_MIN = 0.50
EXTENT_MIN = 0.35
TOUCHE_QUALITE_MIN = 1e-4

# Filtrage Spatial
SEUIL_Y_PROXIMITE = 1000
SEUIL_Y_RATIO = 0.50

MIN_TOUCHES_DETECTEES = 35

# --- Paramètres de Classification ---

# 1. ISO vs ANSI
THRESHOLD_SHIFT_RATIO_ISO = 2.2

# 2. Enter
THRESHOLD_ENTER_RATIO_H_L_ISO = 1.3
THRESHOLD_ENTER_RATIO_H_L_ANSI = 0.95

# 3. Mac vs Windows
THRESHOLD_EULER_MAC = -2
THRESHOLD_EULER_WIN = 2

# 4. AZERTY vs QWERTY (géométrique - fallback uniquement)
THRESHOLD_TL_CENTER_Y_AZERTY = 0.48
THRESHOLD_TL_EXTENT_AZERTY = 0.82

# --- Paramètres OCR Améliorés ---

# Confiance minimale pour accepter résultat OCR
OCR_MIN_CONFIDENCE = 0.35  # 35% de confiance minimum

# Nombre de touches à lire par rangée
OCR_MAX_KEYS_PER_ROW = 10

# Prétraitement OCR
OCR_SCALE_FACTOR = 3  # Facteur d'agrandissement
OCR_SHARPEN_STRENGTH = 0.5  # Force du sharpening (0-1)
OCR_CONTRAST_CLIP = 0.04  # CLAHE clip limit

# Tolérance pour regrouper touches d'une même rangée
OCR_ROW_TOLERANCE_PX = 25  # pixels

# Filtrage des touches anormales (Tab, etc.)
OCR_MAX_RATIO_NORMAL_KEY = 1.8  # Ratio L/H maximum pour touche "normale"

# --- Paramètres de Zoning ---
ZONING_HR_MULTIPLIERS = {
    "OS_DY_TOLERANCE": 0.8,
    "SHIFT_Y_MIN_HR": 0.5,
    "SHIFT_Y_MAX_HR": 2.0,
    "TL_LETTER_Y_MIN_HR": 2.5,
    "TL_LETTER_Y_MAX_HR": 3.8,
    "ENTER_Y_TARGET_HR": 2.5,
    "ENTER_Y_TOLERANCE_HR": 1.5,
}

# Validation des ratios
SPACE_RATIO_MIN = 2.0
SHIFT_RATIO_MIN = 1.5
SHIFT_RATIO_MAX = 3.0
OS_KEY_RATIO_MIN = 0.8
OS_KEY_RATIO_MAX = 1.5
TL_LETTER_RATIO_MIN = 0.7
TL_LETTER_RATIO_MAX = 1.5
THRESHOLD_TAB_RATIO = 1.2

# --- Paramètres de Prétraitement ---
PREPROCESS_MODE = "adaptive"
GAMMA_DARK = 0.7
GAMMA_BRIGHT = 1.3
LUMINOSITY_THRESHOLD_DARK = 0.3
LUMINOSITY_THRESHOLD_BRIGHT = 0.7

# --- Mode Debug ---
DEBUG_MODE = True
SAVE_DEBUG_IMAGES = False

# --- Configuration des Layouts Détectables ---
SUPPORTED_LAYOUTS = {
    'QWERTY': ['US', 'UK', 'INT'],
    'QWERTZ': ['DE', 'CH', 'AT'],
    'AZERTY': ['FR', 'BE']
}

# Poids pour scoring multi-critères
LAYOUT_SCORING_WEIGHTS = {
    'row1_match': 0.7,      # Importance de la première rangée
    'row2_match': 0.3,      # Importance de la deuxième rangée
    'early_keys_bonus': 0.1,  # Bonus si les 3 premières touches matchent
    'iso_ansi_bonus': 0.1   # Bonus si ISO/ANSI correspond
}
