""" cartes (heatmap, bulles, geojson) """
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from src.config import MERGED_FILE_REGION

def plot_france_communes_risk_count(
    merged_gdf: gpd.GeoDataFrame,
    year: int,
    hazard: str,
    date_col: str = "date_debut",
    hazard_col: str = "type_risque",
    commune_code_col: str = "code_commune",
    figsize: tuple = (10, 10),
    cmap: str = "OrRd",
    metro_only: bool = True
):
    """
    Affiche une carte du nombre d'occurrences d'un aléa par commune
    pour une année donnée.

    Paramètres
    ----------
    merged_gdf : gpd.GeoDataFrame
        Base fusionnée contenant au minimum :
        - la date
        - le type de risque
        - le code commune
        - la géométrie
    year : int
        Année sélectionnée.
    hazard : str
        Aléa sélectionné.
    date_col : str, default="date_debut"
        Nom de la colonne de date.
    hazard_col : str, default="type_risque"
        Nom de la colonne du risque.
    commune_code_col : str, default="code_commune"
        Nom de la colonne du code commune.
    figsize : tuple, default=(10, 10)
        Taille de la figure.
    cmap : str, default="OrRd"
        Palette de couleurs matplotlib.
    metro_only : bool, default=True
        Si True, filtre sur la France métropolitaine.

    Retour
    ------
    fig : matplotlib.figure.Figure
    ax : matplotlib.axes.Axes
    france_map_4326 : gpd.GeoDataFrame
        GeoDataFrame final utilisé pour la carte.
    """

    gdf = merged_gdf.copy()

    required_cols = [date_col, hazard_col, commune_code_col, "geometry"]
    missing_cols = [col for col in required_cols if col not in gdf.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans merged_gdf : {missing_cols}")

    gdf[commune_code_col] = (
        gdf[commune_code_col]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    gdf[date_col] = pd.to_datetime(gdf[date_col], errors="coerce")
    gdf["year_tmp"] = gdf[date_col].dt.year

    france_communes = (
        gdf[[commune_code_col, "geometry"]]
        .dropna(subset=[commune_code_col, "geometry"])
        .drop_duplicates(subset=[commune_code_col])
        .copy()
    )

    filtered = gdf[
        (gdf["year_tmp"] == year) &
        (gdf[hazard_col] == hazard)
    ].copy()

    counts = (
        filtered.groupby(commune_code_col)
        .size()
        .reset_index(name="nb_occurrences")
    )

    france_map = france_communes.merge(
        counts,
        on=commune_code_col,
        how="left"
    )

    france_map["nb_occurrences"] = france_map["nb_occurrences"].fillna(0)
    france_map = gpd.GeoDataFrame(france_map, geometry="geometry", crs=gdf.crs)

    if france_map.crs is None:
        raise ValueError("Le CRS de merged_gdf est manquant.")

    france_map_4326 = france_map.to_crs(epsg=4326)

    if metro_only:
        france_map_4326 = france_map_4326.cx[-6:10, 41:52]

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    france_map_4326.plot(
        column="nb_occurrences",
        cmap=cmap,
        linewidth=0,
        legend=True,
        ax=ax
    )

    zone_label = "en France métropolitaine" if metro_only else "en France"
    ax.set_title(
        f"Nombre d'occurrences de l'aléa '{hazard}' par commune en {year}\n{zone_label}",
        fontsize=13
    )
    ax.axis("off")

    return fig, ax, france_map_4326


import json
import geopandas as gpd
import plotly.express as px

from src.config import FEATURES_FILE


def plot_france_regions_risk_count(
    year: int,
    hazard: str,
    region_file=MERGED_FILE_REGION,
    year_col: str = "annee",
    hazard_col: str = "type_risque",
    region_code_col: str = "code_region",
    region_name_col: str = "nom_region",
    count_col: str = "nb_catastrophes",
    color_scale: str = "OrRd",
    metro_only: bool = True
):
    gdf = gpd.read_file(region_file)

    required_cols = [year_col, hazard_col, region_code_col, region_name_col, count_col, "geometry"]
    missing_cols = [col for col in required_cols if col not in gdf.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans MERGED_REGION_FILE : {missing_cols}")

    filtered = gdf[
        (gdf[year_col] == year) &
        (gdf[hazard_col] == hazard)
    ].copy()

    if metro_only:
        dom_codes = {"01", "02", "03", "04", "06"}
        filtered = filtered[~filtered[region_code_col].isin(dom_codes)]

    filtered = filtered.to_crs(epsg=4326)

    geojson_data = json.loads(filtered.to_json())

    fig = px.choropleth(
        filtered,
        geojson=geojson_data,
        locations=region_code_col,
        featureidkey=f"properties.{region_code_col}",
        color=count_col,
        hover_name=region_name_col,
        hover_data={
            region_code_col: True,
            year_col: True,
            hazard_col: True,
            count_col: True
        },
        color_continuous_scale=color_scale,
        projection="mercator"
    )

    fig.update_geos(fitbounds="locations", visible=False)

    zone_label = "France métropolitaine" if metro_only else "France"
    fig.update_layout(
        title=f"Nombre de catastrophes de type '{hazard}' par région en {year} - {zone_label}",
        margin={"r": 0, "t": 60, "l": 0, "b": 0}
    )

    return fig, filtered