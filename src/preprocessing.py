import numpy as np
from skimage import color, filters, exposure, morphology
from scipy.ndimage import median_filter, binary_opening, binary_closing

def pretraiter_image(img):
    """
    Applique la chaîne de traitement V1 :
    Gris -> Médian -> Égalisation -> Otsu -> Morphologie (Open/Close)
    
    Retourne:
        - nettoyee: image binaire nettoyée (True = Touche, False = Fond)
        - gris: image en niveaux de gris (pour analyse fine ultérieure)
    """
    # 1. Conversion en niveaux de gris
    if len(img.shape) == 3:
        gris = color.rgb2gray(img)
    else:
        gris = img

    # 2. Réduction du bruit (Filtre Médian)
    filtree = median_filter(gris, size=3)

    # 3. Amélioration du contraste (Histogramme)
    filtree = exposure.equalize_hist(filtree)

    # 4. Binarisation (Otsu)
    seuil = filters.threshold_otsu(filtree)
    # Note: On suppose touches sombres sur fond clair. 
    # Si inverse, changer le signe > en <.
    binaire = filtree > seuil 

    # 5. Nettoyage Morphologique (Signature V1)
    # Opening x2 pour détacher les touches, Closing x3 pour boucher les trous
    nettoyee = binary_opening(binaire, iterations=2)
    nettoyee = binary_closing(nettoyee, iterations=3)
    
    # Inversion finale : measure.label veut des objets "True" (Blancs).
    # Nos touches sont noires, donc on inverse ici pour que Touches = True.
    nettoyee = np.invert(nettoyee)

    return nettoyee, gris