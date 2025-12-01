# KeyDetect - Détecteur de Layout Clavier

**KeyDetect** est un outil de vision par ordinateur capable d'identifier le layout d'un clavier (AZERTY, QWERTY, QWERTZ) à partir d'une simple photo.

Contrairement aux approches classiques basées sur des zones fixes, ce projet utilise le **Clustering Géométrique (K-Means)** pour comprendre la structure du clavier, ce qui le rend robuste aux photos prises de biais, aux rotations légères et aux différents facteurs de forme.

## Fonctionnalités

- **Approche "Shotgun" (Multi-Vues) :** L'image est traitée simultanément par **4 algorithmes de vision** distincts (CLAHE, Adaptive Threshold, LAB, Inversion) pour maximiser les chances de lecture, quelles que soient les conditions (reflets, ombres, touches noires ou blanches).
- **Intelligence Géométrique :** Utilise l'algorithme **K-Means** pour regrouper dynamiquement les touches par rangées physiques (Haut/Milieu/Bas), rendant le système invariant à la rotation.
- **OCR:** Basé sur `EasyOCR` (PyTorch) pour une lecture robuste des caractères, même flous ou stylisés.
- **Système de Scoring Expert :** Un algorithme de décision pondéré qui applique des bonus pour les lettres clés et des malus fatals pour les contradictions.
- **Mode Benchmark (GUI) :** Interface graphique incluse pour valider automatiquement un lot d'images et calculer le taux de précision (Accuracy).

## Structure du Projet

```
KeyDetect/
├── data/
│   └── inputs/          # Placez vos images de test ici (.png)
├── src/
│   ├── __init__.py
│   ├── engine.py        # Cerveau : Pipeline OCR, Clustering & Scoring
│   └── preprocessing.py # Traitement d'image (OpenCV)
├── main.py              # Script console (analyse fichier par fichier)
├── gui_benchmark.py     # Interface graphique (analyse de masse & stats)
└── requirements.txt     # Dépendances
```

## Installation

Ce projet nécessite **Python 3.11** (pour la stabilité de l'interface graphique).

### 1. Pré-requis Système

  * **Windows :** Avoir Python installé.
  * **Linux :** `sudo apt-get install python3-tk`
  * **macOS (Important) :** Python via Homebrew pose souvent problème avec l'interface graphique (`tkinter`).
      * *Recommandé :* Installez **Python 3.11** via l'installateur officiel sur [python.org](https://www.python.org/downloads/macos/).

### 2. Installation de l'environnement

Ouvrez votre terminal à la racine du projet :

#### Sur macOS / Linux

```bash
# Créer un nouvel environnement virtuel (en pointant vers Python 3.11)
# Si installé via l'installeur officiel :
/usr/local/bin/python3.11 -m venv venv
# Sinon :
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

#### Sur Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

### Préparation des données

Placez vos photos de claviers dans le dossier `data/inputs`.
*Pour le benchmark automatique, nommez vos fichiers ainsi :* `TYPE-OS-LAYOUT-X.png` (ex: `ISO-WIN-AZERTY-1.png`). Le script cherche "AZERTY", "QWERTY" ou "QWERTZ" dans le nom.

### Mode Console (Analyse simple)

Pour voir le détail du processus (rangées détectées, scores détaillés) :

```bash
python main.py
```

### Mode Interface Graphique (Benchmark)

Pour lancer une validation de masse et voir les statistiques de réussite :

```bash
python gui_benchmark.py
```

1.  Cliquez sur **"Charger l'OCR"** (patientez quelques secondes).
2.  Cliquez sur **"LANCER L'ANALYSE"**.

## Fonctionnement

Le pipeline de détection suit 4 étapes rigoureuses pour chaque image :

1. Prétraitement "Shotgun" (Preprocessing)

Au lieu de parier sur un seul réglage, nous générons 4 versions de l'image pour aider l'OCR :

- Adaptive Threshold : Calcule le seuil de binarisation localement. Idéal pour gérer les reflets sur les touches plastiques.

- LAB Channel (Luminance) : Isole la luminosité en ignorant la couleur. Efficace pour les claviers colorés ou rétroéclairés.

- Inversion : Inverse les couleurs (Négatif). Les moteurs OCR préfèrent souvent le texte noir sur fond blanc ; cette méthode sauve les claviers à touches noires.

- CLAHE (Contrast Limited Adaptive Histogram Equalization) : Égalise l'histogramme localement pour rehausser le contraste dans les zones sombres. Redoutable pour les photos avec des ombres portées.

2. Extraction OCR & Fusion

EasyOCR scanne les 4 versions de l'image.

Les résultats sont fusionnés : une lettre n'est validée que si elle est détectée avec une confiance suffisante. Un filtre nettoie les erreurs fréquentes (ex: | devient I, 0 devient O).

3. Clustering Géométrique (K-Means 1D)

On récupère la coordonnée Y (hauteur) de chaque lettre validée. L'algorithme K-Means analyse ce nuage de points et cherche mathématiquement 3 clusters (groupes). Cela permet d'identifier les rangées physiques (Haut / Milieu / Bas) sans connaître l'angle de la photo. Si le clavier est penché, les clusters s'adaptent.

4. Scoring Pondéré

Le moteur analyse le contenu de chaque cluster identifié :

- Bonus (+15 pts) : Si une lettre discriminante est à sa place (ex: A en haut pour AZERTY, Z en bas pour QWERTY).

- Malus Fatal (-50 pts) : Si une lettre contredit formellement un layout (ex: trouver un Q dans la rangée du haut rend le layout AZERTY impossible).

- Le layout avec le score positif le plus élevé l'emporte.

## Auteur

Nicolas HOEDENAEKEN
Théo MERTENS
Baris OZCELIK
Khassan AKTAMIROV

Projet réalisé dans le cadre du cours de Signaux III a l'EPHEC.
