from scipy.ndimage import median_filter, binary_opening, binary_closing
from skimage import color, filters, exposure


def pretraiter_image(img, taille_filtre=3, seuil=None):
    # Étape 1 : Conversion en niveaux de gris
    gris = color.rgb2gray(img)

    # Étape 2 : Réduction du bruit avec un filtre médian
    filtree = median_filter(gris, size=taille_filtre)

    # Étape 2b : Egalisation de l'histogramme pour améliorer le contraste
    filtree = exposure.equalize_hist(filtree)

    # Étape 3 : Binarisation avec Otsu ou seuil manuel
    if seuil is None:
        seuil = filters.threshold_otsu(filtree)
    binaire = filtree > seuil

    # Étape 4 : Nettoyage morphologique
    nettoyee = binary_closing(binary_opening(binaire, iterations=2), iterations=3)

    return nettoyee
