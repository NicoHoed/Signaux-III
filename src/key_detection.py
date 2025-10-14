import numpy as np
import matplotlib.pyplot as plt
from skimage import measure, draw
from src.preprocessing import pretraiter_image
from skimage import io


def detect_keys(img, taille_filtre=3, seuil=None, min_area=100, max_area=5000):
    """
    Détecte les touches d'un clavier à partir d'une image.
    """

    # Étape 1 : Prétraitement
    binary_image = pretraiter_image(img, taille_filtre=taille_filtre, seuil=seuil)

    # Étape 2 : Détection des composants connectés
    labels = measure.label(binary_image)
    regions = measure.regionprops(labels)

    key_boxes = []

    for region in regions:
        # Filtrage par aire
        if min_area <= region.area <= max_area:
            minr, minc, maxr, maxc = region.bbox
            key_boxes.append((minr, minc, maxr, maxc))

    return key_boxes, binary_image


def plot_keys(img, key_boxes):
    """
    Affiche l'image avec les rectangles des touches détectées.
    """
    fig, ax = plt.subplots()
    ax.imshow(img, cmap="gray")
    for bbox in key_boxes:
        minr, minc, maxr, maxc = bbox
        rect = plt.Rectangle(
            (minc, minr),
            maxc - minc,
            maxr - minr,
            edgecolor="red",
            facecolor="none",
            linewidth=1.5,
        )
        ax.add_patch(rect)
    ax.set_axis_off()
    plt.show()
