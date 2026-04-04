"""configurations chemins"""
from pathlib import Path

# Root du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Dossiers data
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
EXTERNAL_DIR = DATA_DIR / "external"
PROCESSED_DIR = DATA_DIR / "processed"

# Fichiers principaux
CATNAT_FILE = RAW_DIR / "catnat_gaspar.csv"
COMMUNES_FILE = EXTERNAL_DIR / "communes-100m.geojson"
WATERWAYS_FILE = EXTERNAL_DIR / "CoursEau_FXX-shp-20260227T123048Z-1-001" / "CoursEau_FXX-shp" / "CoursEau_FXX.shp"


# Outputs utiles
CLEAN_CATNAT_FILE = PROCESSED_DIR / "catnat_clean.csv"
MERGED_FILE = PROCESSED_DIR / "catnat_communes.geojson"
FEATURES_FILE = PROCESSED_DIR / "features.csv"
