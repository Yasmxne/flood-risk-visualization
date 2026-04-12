"""jointure des datasets"""
import geopandas as gpd

from src.data.clean_data import clean_catnat
from src.data.load_data import load_communes, load_regions, load_waterways
from src.config import MERGED_FILE_REGION, MERGED_FILE_COMMUNES, MERGED_FILE_COMMUNES_WATERWAYS


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


"""jointure communes - cours d'eau"""
import pandas as pd
import geopandas as gpd

from src.data.load_data import load_communes, load_waterways
from src.config import PROCESSED_DIR


def merge_communes_cours_eau():
    """
    Construit une table par commune contenant :
    - la liste des noms des cours d'eau qui la traversent
    - leur nombre
    - la liste de leurs géométries (au format WKT)
    
    Retour
    ------
    df_out : pandas.DataFrame
        Table finale avec colonnes :
        - code_commune
        - nom_commune
        - liste_cours_eau
        - nb_cours_eau
        - liste_geometries_cours_eau
    """

    # Chargement des données
    gdf_communes = load_communes()
    gdf_cours_eau = load_waterways()
    

    # Harmonisation communes
    gdf_communes = gdf_communes.rename(columns={
        "code": "code_commune",
        "nom": "nom_commune"
    })
    gdf_communes["code_commune"] = (
        gdf_communes["code_commune"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    # Harmonisation cours d'eau
    gdf_cours_eau = gdf_cours_eau.rename(columns={
        "TopoOH": "nom_cours_eau"
    })

    # Vérification colonnes
    required_communes = ["code_commune", "nom_commune", "geometry"]
    missing_communes = [c for c in required_communes if c not in gdf_communes.columns]
    if missing_communes:
        raise ValueError(f"Colonnes manquantes dans la base communes : {missing_communes}")

    required_waterways = ["CdOH", "nom_cours_eau", "geometry"]
    missing_waterways = [c for c in required_waterways if c not in gdf_cours_eau.columns]
    if missing_waterways:
        raise ValueError(f"Colonnes manquantes dans la base cours d'eau : {missing_waterways}")

    # Colonnes utiles
    gdf_communes = gdf_communes[["code_commune", "nom_commune", "geometry"]].copy()
    gdf_cours_eau = gdf_cours_eau[["CdOH", "nom_cours_eau", "geometry"]].copy()

    # Vérification CRS
    if gdf_communes.crs is None or gdf_cours_eau.crs is None:
        raise ValueError("Le CRS est manquant dans une des deux bases.")

    if gdf_communes.crs != gdf_cours_eau.crs:
        gdf_cours_eau = gdf_cours_eau.to_crs(gdf_communes.crs)

    # Jointure spatiale :
    # une ligne = un cours d'eau qui intersecte une commune
    gdf_join = gpd.sjoin(
        gdf_cours_eau,
        gdf_communes,
        how="inner",
        predicate="intersects"
    ).drop_duplicates(subset=["CdOH", "code_commune"])

    # Géométrie du cours d'eau en WKT pour pouvoir l'agréger dans une liste
    gdf_join["geom_cours_eau_wkt"] = gdf_join.geometry.to_wkt()

    # Agrégation par commune
    df_agg = (
        gdf_join.groupby(["code_commune", "nom_commune"])
        .agg(
            liste_cours_eau=(
                "nom_cours_eau",
                lambda x: sorted(
                    set(v for v in x.dropna() if str(v).strip() != "")
                )
            ),
            liste_geometries_cours_eau=(
                "geom_cours_eau_wkt",
                lambda x: list(x.dropna())
            )
        )
        .reset_index()
    )

    # Nombre de cours d'eau nommés
    df_agg["nb_cours_eau"] = df_agg["liste_cours_eau"].apply(len)

    # Conserver toutes les communes, même sans cours d'eau
    df_out = (
        gdf_communes[["code_commune", "nom_commune"]]
        .drop_duplicates()
        .merge(
            df_agg,
            on=["code_commune", "nom_commune"],
            how="left"
        )
    )

    # Remplissage des communes sans cours d'eau
    df_out["liste_cours_eau"] = df_out["liste_cours_eau"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    df_out["liste_geometries_cours_eau"] = df_out["liste_geometries_cours_eau"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    df_out["nb_cours_eau"] = df_out["nb_cours_eau"].fillna(0).astype(int)

    
    # 🔥 conversion en string pour CSV (important)
    df_out["liste_cours_eau"] = df_out["liste_cours_eau"].astype(str)
    df_out["liste_geometries_cours_eau"] = df_out["liste_geometries_cours_eau"].astype(str)

    # Sauvegarde CSV uniquement
    df_out.to_csv(MERGED_FILE_COMMUNES_WATERWAYS, index=False, encoding="utf-8")


    return df_out

def save_merged_data():
    gdf_regions = merge_catnat_regions()
    gdf_regions.to_file(MERGED_FILE_REGION, driver="GeoJSON")

    gdf_communes = merge_catnat_communes()
    gdf_communes.to_file(MERGED_FILE_COMMUNES, driver="GeoJSON")

    merge_communes_cours_eau()

    print("Merged data saved")

if __name__ == "__main__":
    save_merged_data()