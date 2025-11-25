# --- Configuration Globale des Chemins ---
# Chemin vers l'image à analyser par défaut (pour main.py et explore_shape.py)
IMAGE_PATH_DEFAULT = 'data/inputs/INT-QWERTY-1.jpg' 

# --- Paramètres de Détection de Touche (Tuneable Parameters) ---
# Ces valeurs sont utilisées dans src/analysis.py pour filtrer les régions détectées.

# 1. Filtres sur l'Aire (en pixels)
# Ajuster pour inclure les touches de fonction (min) et la barre espace (max)
AIRE_MIN = 2000      
AIRE_MAX = 400000    

# 2. Filtres sur le Ratio Largeur/Hauteur
# Ajuster pour inclure les touches carrées (min) et la barre espace (max)
RATIO_MIN = 0.5      
RATIO_MAX = 8.0      

# 3. Filtrage Spatial (Anti-Trackpad et centrage clavier)
# Distance max verticale autorisée par rapport au centre Y moyen du clavier.
SEUIL_Y_PROXIMITE = 1000