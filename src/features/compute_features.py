""" compute_features.py
crée les variables utiles :

nb catastrophes par commune
distance aux cours d’eau
nb cours d’eau par commune
ratios / agrégations
"""

import geopandas as gpd

from src.data.load_data import load_merged
from src.config import FEATURES_FILE


def compute_features():
    gdf_merged = load_merged()

    df_features = (
        gdf_merged.groupby(["code_commune", "annee", "type_risque", "geometry"])
        .size()
        .reset_index(name="nb_catastrophes")
    )
    gdf_features = gpd.GeoDataFrame(df_features, geometry="geometry")
    return gdf_features


def save_features():
    gdf_features = compute_features()
    gdf_features.to_file(FEATURES_FILE, driver="GeoJSON")
    print("Features saved")


if __name__ == "__main__":
    save_features()