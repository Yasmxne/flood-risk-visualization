"""jointure des datasets"""
import geopandas as gpd

from src.data.clean_data import clean_catnat
from src.data.load_data import load_communes
from src.config import MERGED_FILE


def merge_catnat_communes():

    df_clean = clean_catnat()
    gdf_communes = load_communes()

    gdf_communes = gdf_communes.rename(columns={"code": "code_commune"})

    df_clean["code_commune"] = df_clean["code_commune"].astype(str).str.zfill(5)
    gdf_communes["code_commune"] = gdf_communes["code_commune"].astype(str).str.zfill(5)

    # merge 
    df_merge = df_clean.merge(
        gdf_communes[["code_commune", "geometry"]],
        on="code_commune",
        how="inner"
    )

    # transformer en GeoDataFrame
    gdf_merge = gpd.GeoDataFrame(df_merge, geometry="geometry")

    return gdf_merge


def save_merged_data():
    gdf = merge_catnat_communes()
    gdf.to_file(MERGED_FILE, driver="GeoJSON")
    print("Merged GeoJSON saved")


if __name__ == "__main__":
    save_merged_data()