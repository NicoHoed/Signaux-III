# Détection de Layout de Clavier V2 : Approche par Analyse de Forme

## 1. La Théorie : Les 3 Filtres en Cascade

Au lieu de tenter de "lire" les lettres (OCR), nous allons déduire le layout en analysant les **propriétés géométriques et topologiques** (forme, trous, remplissage) de touches clés situées dans des zones spécifiques.

### Filtre 1 : La Géométrie Physique (ISO vs ANSI)
Ce filtre repose sur les dimensions des touches (bounding box), accessibles via `measure.regionprops`.

* **Zone à observer :** Le bord gauche (Touche MAJ) et le bord droit (Touche Entrée).
* **Le test (Analyse de l'aspect ratio) :**
    * **ISO (Europe - AZERTY/UK) :**
        * Touche MAJ Gauche : **Courte**. Ratio Largeur/Hauteur $\approx$ 1.2 à 1.5.
        * Touche Entrée : Forme complexe (souvent détectée comme haute et étroite si segmentée verticalement).
    * **ANSI (USA - QWERTY US) :**
        * Touche MAJ Gauche : **Longue**. Ratio Largeur/Hauteur $> 2.0$.
        * Touche Entrée : Rectangulaire horizontale.
    * **Conclusion :** Un `bbox` court pour le Shift gauche indique fortement un layout européen (ISO).

### Filtre 2 : La Signature Morphologique (AZERTY vs QWERTY)
On différencie les layouts par la forme globale de la première lettre en haut à gauche ("A" vs "Q").

| Propriété | **"A" (AZERTY)** | **"Q" (QWERTY)** |
| :--- | :--- | :--- |
| **Forme globale** | Triangulaire / Pyramidal | Circulaire / Carré |
| **Taux de remplissage (Extent)** | **Faible** (environ 0.5 - 0.6). La lettre ne remplit pas les coins supérieurs de sa boîte. | **Élevé** (environ 0.7 - 0.9). La lettre remplit presque toute sa boîte. |
| **Centre de masse (Centroid)** | Décalé vers le **bas** (base du triangle). | Proche du **centre** géométrique. |
| **Trous (Euler)** | 1 Trou (le triangle du haut). | 1 Trou (le cercle). *Critère peu discriminant ici.* |

* **Stratégie :** On extrait le "blob" en haut à gauche. Si son taux de remplissage (`area / bbox_area`) est faible et son centre de gravité bas, c'est probablement un **A**. Si c'est un bloc massif bien rempli, c'est un **Q**.

### Filtre 3 : L'OS (Mac vs Windows) via Topologie
On utilise la topologie (nombre de trous et de composantes connexes) pour identifier les touches spéciales du bas (Cmd vs Win).

* **Zone à observer :** La rangée du bas, à gauche ou droite de la barre espace.
* **Mac (Touche Command ⌘) :**
    * Forme unique avec **plusieurs boucles** (trous).
    * En utilisant `label` sur l'inverse de la touche ou via le nombre d'Euler, on détecte une complexité topologique élevée.
* **Windows (Logo Fenêtre) :**
    * Souvent composé de **4 petits carrés** distincts.
    * Une fois binarisé et labellisé *localement*, on trouve **4 composantes connexes** proches, ou une forme géométrique très stricte.

---

## 2. Le Pipeline de Traitement d'Image (Compatible Cours)

Ce pipeline n'utilise que des opérations matricielles, morphologiques et de mesure.

1.  **Prétraitement & Segmentation Globale :**
    * Conversion Gris -> Filtre Médian (Bruit) -> Égalisation (Contraste).
    * Binarisation (Otsu ou Adaptatif) pour obtenir les "Blobs".
    * Nettoyage (`opening`/`closing`) pour détacher les touches.
    * `measure.label` pour lister toutes les touches potentielles.

2.  **Filtrage Spatial (Zoning) :**
    * Identification des coins du clavier basés sur les coordonnées des régions (`min_row`, `min_col`).
    * Extraction des **ROI (Regions of Interest)** :
        * *ROI_1 :* La touche la plus en haut à gauche (Candidat A/Q).
        * *ROI_2 :* La touche la plus à gauche de la rangée avant-dernière (Candidat Shift).
        * *ROI_3 :* Touches adjacentes à la barre espace (Candidat OS).

3.  **Extraction de Caractéristiques (Feature Extraction) :**
    Pour chaque ROI, on calcule via `skimage.measure.regionprops` :
    * `bbox` (Hauteur/Largeur) $\rightarrow$ Pour le filtre ISO/ANSI.
    * `extent` (Aire / Aire BoundingBox) $\rightarrow$ Pour A vs Q.
    * `local_centroid` $\rightarrow$ Pour A vs Q (Centre de gravité).
    * `euler_number` ou analyse des trous (`binary_fill_holes` XOR image originale) $\rightarrow$ Pour Mac (Cmd).

4.  **Arbre de Décision (Classification) :**
    * `SI` Shift_Ratio < 1.5 `ALORS` ISO `SINON` ANSI.
    * `SI` HautGauche_Extent < 0.65 `ALORS` "A" (AZERTY) `SINON` "Q" (QWERTY).
    * `SI` Bas_Complexité > Seuil `ALORS` Mac `SINON` Win.

---

## 3. La "Subtilité Belge" (Bonus V2.5)
* **Théorie :** AZERTY Belge a souvent des symboles différents sur la ligne des chiffres par rapport à la France.
* **Approche Forme :** Très difficile sans OCR. On pourrait tenter de compter le nombre de petits "îlots" (composantes connexes) sur la touche `2` (pour voir si ça ressemble à un `@` complexe ou un `é` simple), mais c'est risqué. À garder pour la fin.

---

## Proposition de plan d'action (Mis à jour)

1.  **Script d'Analyse (Explorer) :** Créer un script simple qui prend une image, clique sur une touche, et affiche ses métriques (`Extent`, `Solidity`, `Euler`, `Ratio`). Cela nous servira à "calibrer" nos seuils (ex: est-ce qu'un A fait 0.5 ou 0.6 de remplissage ?).
2.  **Développement du Pipeline :** Implémenter la détection des zones (Haut-Gauche, Bas-Gauche) automatiquement.
3.  **Intégration :** Combiner les deux pour sortir le verdict final.

---

```
keyboard_detector_v2/
│
├── data/
│   ├── inputs/          # images ici (BE-azerty-1.jpg, etc.)
│   └── outputs/         # vide pour l'instant
│
├── src/
│   ├── __init__.py      # Fichier vide (pour que Python reconnaisse le dossier comme package)
│   ├── preprocessing.py # vide pour l'instant
│   └── analysis.py      # vide pour l'instant
│
├── explore_shape.py     # LE SCRIPT : Pour cliquer sur les touches et voir les stats
├── main.py              # Le script final
├── .gitignore
└── requirements.txt     # numpy, scikit-image, matplotlib...
```