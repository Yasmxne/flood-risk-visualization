
# Flood Risk Visualization

## Contexte

Projet réalisé dans le cadre du cours de **Data Storytelling**.

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/Yasmxne/flood-risk-visualization.git
cd flood-risk-visualization
```

### 2. Créer un environnement virtuel et l'activer
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

## Données externes

La base des cours d’eau étant trop volumineuse, elle n’a pas été ajoutée au dépôt.

Elle doit être téléchargée ici :
[Télécharger les données des cours d’eau](https://drive.google.com/drive/folders/1IkljDCdZGyMSMst5Sbc1OCRlLCymSdBd?usp=sharing)

Puis placer le dossier tel quel dans :

```bash
data/external
```
## Structure attendue du projet 
```
data/
├── raw/
│   └── catnat_gaspar.csv
│
├── external/
│   ├── communes-100m.geojson
│   ├── regions-100m.geojson
│   └── CoursEau_FXX-shp-20260227T123048Z-1-001/
│       └── CoursEau_FXX-shp/
│           ├── CoursEau_FXX.shp
│           ├── CoursEau_FXX.dbf
│           ├── CoursEau_FXX.shx
│           └── ...
```

## Lancement

à la racine du projet faire :

```bash
python run.py
```