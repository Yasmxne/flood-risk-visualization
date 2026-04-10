"""jointure des datasets"""
import geopandas as gpd

from src.data.clean_data import clean_catnat
from src.data.load_data import load_communes, load_regions
from src.config import MERGED_FILE_REGION, MERGED_FILE_COMMUNES


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



def merge_catnat_regions():
    df_clean = clean_catnat()
    gdf_communes = load_communes()
    gdf_regions = load_regions()

    gdf_communes = gdf_communes.rename(columns={"code": "code_commune"})
    gdf_regions = gdf_regions.rename(columns={"code": "code_region", "nom": "nom_region"})

    df_clean["code_commune"] = df_clean["code_commune"].astype(str).str.zfill(5)
    gdf_communes["code_commune"] = gdf_communes["code_commune"].astype(str).str.zfill(5)
    gdf_communes["region"] = gdf_communes["region"].astype(str).str.zfill(2)
    gdf_regions["code_region"] = gdf_regions["code_region"].astype(str).str.zfill(2)

    df_clean = df_clean.merge(
        gdf_communes[["code_commune", "region"]],
        on="code_commune",
        how="inner"
    )

    df_region = (
        df_clean.groupby(["region", "annee", "type_risque"])
        .size()
        .reset_index(name="nb_catastrophes")
    )

    gdf_merged = df_region.merge(
        gdf_regions[["code_region", "nom_region", "geometry"]],
        left_on="region",
        right_on="code_region",
        how="inner"
    )

    gdf_merged = gpd.GeoDataFrame(gdf_merged, geometry="geometry")

    return gdf_merged

def save_merged_data():
    gdf_regions = merge_catnat_regions()
    gdf_regions.to_file(MERGED_FILE_REGION, driver="GeoJSON")

    gdf_communes = merge_catnat_communes()
    gdf_communes.to_file(MERGED_FILE_COMMUNES, driver="GeoJSON")

    print("Merged data saved")


if __name__ == "__main__":
    save_merged_data()