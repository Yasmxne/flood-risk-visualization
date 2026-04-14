import geopandas as gpd
import pandas as pd

from src.config import MERGED_FILE_REGION, PROCESSED_DIR


def prepare_web_data():
    gdf = gpd.read_file(MERGED_FILE_REGION)

    df_stats = gdf.drop(columns="geometry").copy()
    df_stats.to_csv(PROCESSED_DIR / "region_stats.csv", index=False)

    gdf_regions = gdf[["code_region", "nom_region", "geometry"]].drop_duplicates(subset=["code_region"]).copy()
    gdf_regions.to_file(PROCESSED_DIR / "regions_only.geojson", driver="GeoJSON")

    print("Web data prepared")


if __name__ == "__main__":
    prepare_web_data()