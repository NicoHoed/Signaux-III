# Signaux III - Projet de Détection Automatisée de Layout de Clavier

## 1. Description du Projet

Ce projet, réalisé dans le cadre du cours de **Signaux III : Traitement Numérique** à l'EPHEC, a pour objectif de développer une application Python capable d'analyser une image de clavier d'ordinateur et d'en déterminer automatiquement les caractéristiques de layout et de format. L'implémentation repose entièrement sur l'application de techniques de **Traitement d'Images Numériques**, en s'appuyant sur les concepts de segmentation, de détection de contours et de classification morphologique.

Les trois caractéristiques principales identifiées sont :

1.  **Format Physique (ISO/ANSI) :** Déterminé par l'analyse du **ratio largeur/hauteur** de la touche `Shift` gauche.
2.  **Système d'Exploitation (Mac/Windows) :** Classifié en analysant la topologie du logo sur la touche `OS/Command` via le calcul du **Nombre d'Euler** (ou Caractéristique d'Euler).
3.  **Layout Linguistique (AZERTY/QWERTY) :** Inférencé par des heuristiques basées sur la géométrie et l'extension des touches dans le coin supérieur gauche du clavier (`TL_LETTER`).

### Pipeline de Traitement

Le pipeline de l'application suit une approche structurée de traitement d'image :

1.  **Prétraitement (`preprocessing.py`) :** Application d'un filtre médian pour la réduction du bruit, d'une égalisation d'histogramme pour l'amélioration du contraste, et d'une binarisation par seuillage d'Otsu. Des opérations de morphologie (ouverture et fermeture binaires) sont utilisées pour nettoyer le masque des touches.
2.  **Détection (`analysis.py`) :** Utilisation des propriétés de région (aire, ratio de forme) pour identifier les objets candidats (touches). Un filtrage spatial permet d'éliminer les éléments non pertinents (trackpad).
3.  **Zoning (`analysis.py`) :** Identification des régions d'intérêt (ROI) critiques (Espace, Shift Gauche, Touche OS, Touche Lettre Haut-Gauche) basées sur la topologie du clavier.
4.  **Classification (`analysis.py`) :** Application des algorithmes de classification et d'heuristiques pour déterminer le verdict final.

## 2. Installation et Configuration

### 2.1. Prérequis

Ce projet est développé en Python 3. Les librairies nécessaires sont listées dans `requirements.txt`.

### 2.2. Cloner le dépôt

```bash
git clone https://github.com/NicoHoed/Signaux-III
````

### 2.3. Installation des dépendances

Il est fortement recommandé de travailler dans un environnement virtuel.

```bash
# Création et activation de l'environnement
python -m venv venv
source venv/bin/activate 

# Installation des dépendances
pip install -r requirements.txt
```

Le projet repose sur les packages de calcul matriciel (`numpy`), de traitement d'images (`scikit-image`) et de visualisation (`matplotlib`).

### 2.4. Structure des données

Les images à analyser doivent être placées dans le répertoire `data/inputs/`.

## 3. Utilisation

Le projet propose deux modes d'exécution.

### 3.1. Analyse d'une image unique (`main.py`)

Ce mode permet d'analyser un fichier spécifique et d'afficher les résultats du diagnostic ainsi qu'une visualisation graphique détaillant la détection des zones clés.

1.  **Configuration :** Modifiez la variable `IMAGE_PATH` dans `main.py` pour spécifier l'image d'entrée.

    ```python
    IMAGE_PATH = 'data/inputs/INT-QWERTY-1.jpg' 
    ```

2.  **Exécution :**

    ```bash
    python main.py
    ```

### 3.2. Traitement par lots (`run_batch.py`)

Ce mode permet de traiter toutes les images présentes dans `data/inputs/` et de générer un rapport synthétique au format CSV.

1.  **Exécution :**

    ```bash
    python run_batch.py
    ```

2.  **Rapport :** Le fichier `data/outputs/rapport_analyse.csv` contiendra les résultats pour chaque image, incluant des indicateurs techniques (`Shift_Ratio`, `OS_Euler`, `TL_Extent`).

### 3.3. Outil d'exploration et de debug (`explore_shape.py`)

Ce script facultatif permet d'inspecter visuellement les touches détectées. En cliquant sur une région, on obtient ses métriques de forme (aire, ratio, Nombre d'Euler, etc.), ce qui est essentiel pour l'affinage des seuils de détection.

## 4. Auteurs

* **HOEDENAEKEN Nicolas**