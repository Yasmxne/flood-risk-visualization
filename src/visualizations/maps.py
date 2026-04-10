""" cartes (heatmap, bulles, geojson) """
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


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
    Carte du nombre d'occurrences d'un aléa par commune pour une année donnée.

    Paramètres
    ----------
    merged_gdf : GeoDataFrame
    year : int
    hazard : str
    date_col : str
    hazard_col : str
    commune_code_col : str
    figsize : tuple
    cmap : str
    metro_only : bool
        Si True, garde seulement la France métropolitaine.
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

    # Reprojection pour travailler proprement sur les bounds
    if france_map.crs is None:
        raise ValueError("Le CRS de merged_gdf est manquant.")

    france_map_4326 = france_map.to_crs(epsg=4326)

    # Garde seulement la métropole
    if metro_only:
        france_map_4326 = france_map_4326.cx[-6:10, 41:52]

    fig, ax = plt.subplots(figsize=figsize)

    # Si toutes les valeurs sont nulles, éviter scheme="quantiles"
    if france_map_4326["nb_occurrences"].sum() == 0:
        france_map_4326.plot(
            column="nb_occurrences",
            cmap=cmap,
            linewidth=0,
            legend=True,
            ax=ax
        )
    else:
        france_map_4326.plot(
            column="nb_occurrences",
            cmap=cmap,
            linewidth=0,
            legend=True,
            scheme="quantiles",
            k=5,
            ax=ax,
            legend_kwds={"label": "Nombre d'occurrences"}
        )

    zone_label = "en France métropolitaine" if metro_only else "en France"
    ax.set_title(
        f"Nombre d'occurrences de l'aléa '{hazard}' par commune en {year}\n{zone_label}",
        fontsize=13
    )
    ax.axis("off")

    return fig, ax, france_map_4326