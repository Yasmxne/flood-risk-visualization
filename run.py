"""lancer l'app facilement"""

from pathlib import Path
import sys

from src.config import (
    CATNAT_FILE,
    COMMUNES_FILE,
    REGIONS_FILE,
    WATERWAYS_FILE,
    CLEAN_CATNAT_FILE,
    MERGED_FILE_REGION,
    REGION_STATS_FILE,
    REGIONS_ONLY_FILE,
)

from src.data.clean_data import clean_catnat
from src.data.merge_data import merge_catnat_regions
from src.data.prepare_web_data import prepare_web_data
from src.app.app import app


def check_inputs():
    print("\n[1/5] Vérification des fichiers d'entrée...")

    required = {
        "CATNAT_FILE": CATNAT_FILE,
        "COMMUNES_FILE": COMMUNES_FILE,
        "REGIONS_FILE": REGIONS_FILE,
        "WATERWAYS_FILE": WATERWAYS_FILE,
    }

    missing = []

    for name, path in required.items():
        if Path(path).exists():
            print(f"  OK  - {name}: {path}")
        else:
            print(f"  KO  - {name}: {path}")
            missing.append(name)

    if missing:
        print("\nFichiers manquants. Pipeline arrêté.")
        sys.exit(1)


def run_clean_data():
    print("\n[2/5] Nettoyage de CATNAT...")
    df_clean = clean_catnat()

    CLEAN_CATNAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(CLEAN_CATNAT_FILE, index=False)

    print(f"  OK  - catnat_clean.csv créé")
    print(f"  -> {len(df_clean)} lignes")


def run_merge_data():
    print("\n[3/5] Merge régional...")
    gdf_regions = merge_catnat_regions()

    MERGED_FILE_REGION.parent.mkdir(parents=True, exist_ok=True)
    gdf_regions.to_file(MERGED_FILE_REGION, driver="GeoJSON")

    print(f"  OK  - gdf_merged_region.geojson créé")
    print(f"  -> {len(gdf_regions)} lignes")


def run_prepare_web_data():
    print("\n[4/5] Préparation des fichiers web légers...")
    prepare_web_data()
    print("  OK  - region_stats.csv créé")
    print("  OK  - regions_only.geojson créé")


def check_outputs():
    print("\n[5/5] Vérification des fichiers nécessaires à l'application...")

    required = {
        "CLEAN_CATNAT_FILE": CLEAN_CATNAT_FILE,
        "MERGED_FILE_REGION": MERGED_FILE_REGION,
        "REGION_STATS_FILE": REGION_STATS_FILE,
        "REGIONS_ONLY_FILE": REGIONS_ONLY_FILE,
    }

    missing = []

    for name, path in required.items():
        if Path(path).exists():
            print(f"  OK  - {name}: {path}")
        else:
            print(f"  KO  - {name}: {path}")
            missing.append(name)

    if missing:
        print("\nFichiers processed manquants. App non lancée.")
        sys.exit(1)


def main():
    print("=" * 60)
    print("Flood Risk Visualization - Pipeline")
    print("=" * 60)

    check_inputs()
    run_clean_data()
    run_merge_data()
    run_prepare_web_data()
    check_outputs()

    print("\nPipeline terminé.")
    print("Lancement de Flask...")
    print("http://127.0.0.1:5000\n")

    app.run(debug=False, use_reloader=False)


if __name__ == "__main__":
    main()