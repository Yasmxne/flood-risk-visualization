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
    figsize: tuple = (14, 14),
    cmap: str = "OrRd"
):
    """
    Affiche une carte de la France communale où chaque commune prend comme valeur :
    le nombre d'occurrences de l'aléa sélectionné pour l'année sélectionnée.

    Paramètres
    ----------
    merged_gdf : GeoDataFrame
        Base fusionnée contenant :
        - une colonne de date
        - une colonne d'aléa
        - une colonne code commune
        - la géométrie des communes
    year : int
        Année choisie.
    hazard : str
        Aléa choisi.
    date_col : str
        Nom de la colonne de date.
    hazard_col : str
        Nom de la colonne de type d'aléa.
    commune_code_col : str
        Nom de la colonne code commune.
    figsize : tuple
        Taille de la figure.
    cmap : str
        Palette de couleurs.

    Retour
    ------
    fig, ax, france_map
    """

    gdf = merged_gdf.copy()

    # Vérifications
    required_cols = [date_col, hazard_col, commune_code_col, "geometry"]
    missing_cols = [col for col in required_cols if col not in gdf.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans merged_gdf : {missing_cols}")

    # Harmonisation du code commune
    gdf[commune_code_col] = (
        gdf[commune_code_col]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    # Conversion de la date
    gdf[date_col] = pd.to_datetime(gdf[date_col], errors="coerce")
    gdf["year_tmp"] = gdf[date_col].dt.year

    # Fond de carte France communale :
    # une seule géométrie par commune
    france_communes = (
        gdf[[commune_code_col, "geometry"]]
        .dropna(subset=[commune_code_col, "geometry"])
        .drop_duplicates(subset=[commune_code_col])
        .copy()
    )

    # Filtrer année + aléa
    filtered = gdf[
        (gdf["year_tmp"] == year) &
        (gdf[hazard_col] == hazard)
    ].copy()

    # Compter le nombre d'occurrences par commune
    counts = (
        filtered.groupby(commune_code_col)
        .size()
        .reset_index(name="nb_occurrences")
    )

    # Jointure avec toutes les communes de France
    france_map = france_communes.merge(
        counts,
        on=commune_code_col,
        how="left"
    )

    # Les communes sans occurrence prennent 0
    france_map["nb_occurrences"] = france_map["nb_occurrences"].fillna(0)

    # Refaire un GeoDataFrame propre
    france_map = gpd.GeoDataFrame(france_map, geometry="geometry", crs=gdf.crs)

    # Tracé
    fig, ax = plt.subplots(figsize=figsize)

    france_map.plot(
        column="nb_occurrences",
        cmap=cmap,
        linewidth=0.05,
        edgecolor="black",
        legend=True,
        ax=ax,
        legend_kwds={"label": "Nombre d'occurrences", "shrink": 0.6}
    )

    ax.set_title(
        f"Nombre d'occurrences de l'aléa '{hazard}' par commune en {year}",
        fontsize=14
    )
    ax.axis("off")

    return fig, ax, france_map