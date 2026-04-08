"""Charge les datasets"""
import pandas as pd
import geopandas as gpd

from src.config import CATNAT_FILE, COMMUNES_FILE, WATERWAYS_FILE, CLEAN_CATNAT_FILE, MERGED_FILE, FEATURES_FILE


def load_catnat():
    df = pd.read_csv(CATNAT_FILE, sep=";", encoding="utf-8", low_memory=False)
    return df


def load_communes():
    gdf = gpd.read_file(COMMUNES_FILE)
    return gdf


def load_waterways():
    gdf = gpd.read_file(WATERWAYS_FILE)
    return gdf

def load_clean_catnat():
    df = pd.read_csv(CLEAN_CATNAT_FILE)
    df["date_debut"] = pd.to_datetime(df["date_debut"], errors="coerce")   
    return df

def load_merged():
    gdf = gpd.read_file(MERGED_FILE)
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

    print("\nLoading waterways...")
    gdf_water = load_waterways()
    print(gdf_water.shape)

    print("\nLoading clean catnat...")
    df_clean_catnat = load_clean_catnat()
    print(df_clean_catnat.shape)

    print("\nLoading merged data...")
    df_merged = load_merged()
    print(df_merged.shape)

    print("\nLoading dataset with features...")
    df_features = load_features()
    print(df_features.shape)