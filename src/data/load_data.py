"""Charge les datasets"""
import pandas as pd
import geopandas as gpd

from src.config import CATNAT_FILE, COMMUNES_FILE, REGIONS_FILE, WATERWAYS_FILE, CLEAN_CATNAT_FILE, FEATURES_FILE, MERGED_FILE_REGION, MERGED_FILE_COMMUNES


def load_catnat():
    df = pd.read_csv(CATNAT_FILE, sep=";", encoding="utf-8", low_memory=False)
    return df


def load_communes():
    gdf = gpd.read_file(COMMUNES_FILE)
    return gdf

def load_regions():
    gdf = gpd.read_file(REGIONS_FILE)
    return gdf

def load_waterways():
    gdf = gpd.read_file(WATERWAYS_FILE)
    return gdf

def load_clean_catnat():
    df = pd.read_csv(CLEAN_CATNAT_FILE)
    df["date_debut"] = pd.to_datetime(df["date_debut"], errors="coerce")   
    return df

def load_merged_regions():
    gdf = gpd.read_file(MERGED_FILE_REGION)
    return gdf

def load_merged_communes():
    gdf = gpd.read_file(MERGED_FILE_COMMUNES)
    return gdf

def load_features():
    gdf = gpd.read_file(FEATURES_FILE)
    return gdf

if __name__ == "__main__":
    
    print("Loading catnat...")
    df_catnat = load_catnat()
    print(df_catnat.shape)

    print("\nLoading communes...")
    gdf_communes = load_communes()
    print(gdf_communes.shape)

    print("\nLoading regions...")
    gdf_regions = load_regions()
    print(gdf_regions.shape)

    print("\nLoading waterways...")
    gdf_water = load_waterways()
    print(gdf_water.shape)

    print("\nLoading clean catnat...")
    df_clean_catnat = load_clean_catnat()
    print(df_clean_catnat.shape)

    print("\nLoading merged data with region geometry...")
    df_merged_regions = load_merged_regions()
    print(df_merged_regions.shape)

    print("\nLoading merged data with communes geometry...")
    df_merged_communes = load_merged_communes()
    print(df_merged_communes.shape)

    print("\nLoading dataset with features...")
    df_features = load_features()
    print(df_features.shape)