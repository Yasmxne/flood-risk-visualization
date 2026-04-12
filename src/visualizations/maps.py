""" cartes (heatmap, bulles, geojson) """
import pandas as pd
import geopandas as gpd
import json
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from shapely import wkt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.data.load_data import (
    load_communes,
    load_merged_communes,
    load_merged_communes_waterways,
)

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




def plot_france_regions_risk_count_1(
    year: int,
    hazard: str,
    region_file=MERGED_FILE_REGION,
    year_col: str = "annee",
    hazard_col: str = "type_risque",
    region_code_col: str = "code_region",
    region_name_col: str = "nom_region",
    count_col: str = "nb_catastrophes",
    metro_only: bool = True
):
    gdf = gpd.read_file(region_file)

    required_cols = [
        year_col,
        hazard_col,
        region_code_col,
        region_name_col,
        count_col,
        "geometry"
    ]
    missing_cols = [col for col in required_cols if col not in gdf.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes : {missing_cols}")

    # Harmonisation
    gdf[region_code_col] = gdf[region_code_col].astype(str).str.zfill(2)
    gdf[hazard_col] = gdf[hazard_col].astype(str).str.strip().str.lower()

    # Base géographique complète : une ligne par région
    france_regions = (
        gdf[[region_code_col, region_name_col, "geometry"]]
        .dropna(subset=[region_code_col, region_name_col, "geometry"])
        .drop_duplicates(subset=[region_code_col])
        .copy()
    )

    if metro_only:
        dom_codes = {"01", "02", "03", "04", "06"}
        france_regions = france_regions[~france_regions[region_code_col].isin(dom_codes)]

    # Données filtrées sur année + aléa
    filtered = gdf[
        (gdf[year_col] == year) &
        (gdf[hazard_col] == hazard.lower())
    ].copy()

    if metro_only:
        dom_codes = {"01", "02", "03", "04", "06"}
        filtered = filtered[~filtered[region_code_col].isin(dom_codes)]

    # Agrégation par région
    counts = (
        filtered.groupby(region_code_col, as_index=False)[count_col]
        .sum()
    )

    # Merge left pour garder toutes les régions
    france_map = france_regions.merge(
        counts,
        on=region_code_col,
        how="left"
    )

    # Remplir les absences par 0
    france_map[count_col] = france_map[count_col].fillna(0)

    # Si besoin, convertir en int
    france_map[count_col] = france_map[count_col].astype(int)

    france_map = gpd.GeoDataFrame(france_map, geometry="geometry", crs=gdf.crs)

    if france_map.crs is None:
        raise ValueError("Le CRS du GeoDataFrame est manquant.")

    france_map = france_map.to_crs(epsg=4326)

    # Palette selon aléa
    hazard_scales = {
        "inondation": ["#deebf7", "#9ecae1", "#3182bd", "#08519c"],
        "secheresse": ["#feedde", "#fdbe85", "#fd8d3c", "#d94701"],
        "mouvement_terrain": ["#f0f0f0", "#bdbdbd", "#636363", "#252525"],
        "tempete": ["#efedf5", "#bcbddc", "#756bb1", "#54278f"],
        "neige_grele": ["#edf8fb", "#b2e2e2", "#66c2a4", "#238b45"],
        "vagues_submersion": ["#eff3ff", "#bdd7e7", "#6baed6", "#2171b5"],
        "seisme": ["#fee5d9", "#fcae91", "#fb6a4a", "#cb181d"],
        "autre": ["#f7f7f7", "#cccccc", "#969696", "#525252"]
    }
    color_scale = hazard_scales.get(hazard.lower(), "OrRd")

    geojson_data = json.loads(france_map.to_json())

    fig = px.choropleth(
        france_map,
        geojson=geojson_data,
        locations=region_code_col,
        featureidkey=f"properties.{region_code_col}",
        color=count_col,
        hover_name=region_name_col,
        hover_data={
            region_code_col: True,
            count_col: True
        },
        color_continuous_scale=color_scale,
        projection="mercator"
    )

    # Supprimer l’échelle
    fig.update_layout(coloraxis_showscale=False)

    # Centroïdes pour afficher les labels
    centroids = france_map.copy()
    centroids_proj = centroids.to_crs(epsg=2154)
    centroids["geometry"] = centroids_proj.centroid.to_crs(epsg=4326)

    centroids["lon"] = centroids.geometry.x
    centroids["lat"] = centroids.geometry.y

    # Texte : nom + valeur
    fig.add_trace(
        go.Scattergeo(
            lon=centroids["lon"],
            lat=centroids["lat"],
            mode="text",
            text=centroids[region_name_col] + "<br>" + centroids[count_col].astype(str),
            textfont=dict(size=11, color="black"),
            showlegend=False,
            hoverinfo="skip"
        )
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False
    )

    zone_label = "France métropolitaine" if metro_only else "France"
    fig.update_layout(
        title=f"Nombre de catastrophes '{hazard}' par région en {year} - {zone_label}",
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
        height=800
    )

    return fig, france_map


def plot_commune_map_and_hazard_timeseries(
    commune_name: str,
    hazard: str = "inondation",
    commune_code_col: str = "code_commune",
    commune_name_col: str = "nom_commune",
    year_col: str = "annee",
    hazard_col: str = "type_risque",
    count_col: str = "nb_catastrophes",
):
    """
    Affiche :
    - une carte de la commune avec les cours d'eau qui la traversent
    - une courbe d'évolution annuelle du nombre de catastrophes de l'aléa choisi

    Paramètres
    ----------
    commune_name : str
        Nom de la commune.
    hazard : str, default="inondation"
        Aléa à afficher sur la série temporelle.

    Retour
    ------
    fig : plotly.graph_objects.Figure
    yearly_counts : pandas.DataFrame
    gdf_commune : geopandas.GeoDataFrame
    gdf_water : geopandas.GeoDataFrame
    """

    # -----------------------------
    # 1) Chargement des données
    # -----------------------------
    gdf_communes = load_communes().copy()
    df_waterways = load_merged_communes_waterways().copy()
    gdf_catnat = load_merged_communes().copy()

    # -----------------------------
    # 2) Harmonisation des colonnes
    # -----------------------------
    gdf_communes = gdf_communes.rename(columns={"code": "code_commune", "nom": "nom_commune"})
    gdf_communes["code_commune"] = (
        gdf_communes["code_commune"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )
    gdf_communes["nom_commune"] = gdf_communes["nom_commune"].astype(str).str.strip()

    df_waterways[commune_code_col] = (
        df_waterways[commune_code_col]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )
    df_waterways[commune_name_col] = df_waterways[commune_name_col].astype(str).str.strip()

    gdf_catnat[commune_code_col] = (
        gdf_catnat[commune_code_col]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )
    gdf_catnat[hazard_col] = gdf_catnat[hazard_col].astype(str).str.strip().str.lower()

    commune_name_clean = commune_name.strip().lower()
    hazard_clean = hazard.strip().lower()

    # -----------------------------
    # 3) Sélection de la commune
    # -----------------------------
    gdf_commune = gdf_communes[gdf_communes["nom_commune"].str.lower() == commune_name_clean].copy()

    if gdf_commune.empty:
        raise ValueError(f"Commune introuvable : '{commune_name}'")

    # En cas d'homonymie, on prend la première
    gdf_commune = gdf_commune.iloc[[0]].copy()

    commune_code = gdf_commune.iloc[0][commune_code_col]
    commune_label = gdf_commune.iloc[0][commune_name_col]

    if gdf_commune.crs is None:
        raise ValueError("Le CRS de la base communes est manquant.")

    gdf_commune = gdf_commune.to_crs(epsg=4326)

    # -----------------------------
    # 4) Récupération des cours d'eau
    # -----------------------------
    row_water = df_waterways[df_waterways[commune_code_col] == commune_code].copy()

    if row_water.empty:
        liste_cours_eau = []
        liste_geoms_wkt = []
        nb_cours_eau = 0
    else:
        row_water = row_water.iloc[0]
        liste_cours_eau = row_water.get("liste_cours_eau", [])
        liste_geoms_wkt = row_water.get("liste_geometries_cours_eau", [])
        nb_cours_eau = int(row_water.get("nb_cours_eau", 0))

    water_geoms = []
    for geom_txt in liste_geoms_wkt:
        try:
            water_geoms.append(wkt.loads(geom_txt))
        except Exception:
            pass

    gdf_water = gpd.GeoDataFrame(
        {"geometry": water_geoms},
        geometry="geometry",
        crs=gdf_commune.crs
    )

    # -----------------------------
    # 5) Série temporelle de l'aléa
    # -----------------------------
    all_years = pd.DataFrame({
        year_col: sorted(gdf_catnat[year_col].dropna().astype(int).unique())
    })

    filtered = gdf_catnat[
        (gdf_catnat[commune_code_col] == commune_code) &
        (gdf_catnat[hazard_col] == hazard_clean)
    ].copy()

    if count_col in filtered.columns:
        yearly_counts = (
            filtered.groupby(year_col, as_index=False)[count_col]
            .sum()
            .sort_values(year_col)
        )
        y_col = count_col
    else:
        yearly_counts = (
            filtered.groupby(year_col)
            .size()
            .reset_index(name="nb_occurrences")
            .sort_values(year_col)
        )
        y_col = "nb_occurrences"

    yearly_counts = all_years.merge(yearly_counts, on=year_col, how="left")
    yearly_counts[y_col] = yearly_counts[y_col].fillna(0).astype(int)

    # -----------------------------
    # 6) Création de la figure
    # -----------------------------
    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.58, 0.42],
        specs=[[{"type": "scattergeo"}, {"type": "xy"}]],
        subplot_titles=(
            f"Commune : {commune_label}",
            f"Évolution annuelle de '{hazard_clean}'"
        )
    )

    # -----------------------------
    # 7) Tracé de la commune
    # -----------------------------
    commune_geom = gdf_commune.geometry.iloc[0]

    if commune_geom.geom_type == "Polygon":
        polygons = [commune_geom]
    elif commune_geom.geom_type == "MultiPolygon":
        polygons = list(commune_geom.geoms)
    else:
        polygons = []

    for poly in polygons:
        x, y = poly.exterior.xy
        fig.add_trace(
            go.Scattergeo(
                lon=list(x),
                lat=list(y),
                mode="lines",
                fill="toself",
                fillcolor="rgba(180,180,180,0.35)",
                line=dict(color="black", width=1.5),
                showlegend=False,
                hoverinfo="skip"
            ),
            row=1,
            col=1
        )

    # -----------------------------
    # 8) Tracé des cours d'eau
    # -----------------------------
    for geom in gdf_water.geometry:
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = list(geom.geoms)
        else:
            lines = []

        for line in lines:
            x, y = line.xy
            fig.add_trace(
                go.Scattergeo(
                    lon=list(x),
                    lat=list(y),
                    mode="lines",
                    line=dict(color="royalblue", width=2),
                    showlegend=False,
                    hoverinfo="skip"
                ),
                row=1,
                col=1
            )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        row=1,
        col=1
    )

    # -----------------------------
    # 9) Courbe temporelle
    # -----------------------------
    color_map = {
        "inondation": "royalblue",
        "secheresse": "darkorange",
        "mouvement_terrain": "dimgray",
        "tempete": "mediumpurple",
        "neige_grele": "seagreen",
        "vagues_submersion": "steelblue",
        "seisme": "firebrick",
        "autre": "gray",
    }
    line_color = color_map.get(hazard_clean, "royalblue")

    fig.add_trace(
        go.Scatter(
            x=yearly_counts[year_col],
            y=yearly_counts[y_col],
            mode="lines+markers",
            line=dict(color=line_color, width=3),
            marker=dict(size=7),
            showlegend=False,
            hovertemplate="Année: %{x}<br>Nombre: %{y}<extra></extra>"
        ),
        row=1,
        col=2
    )

    fig.update_xaxes(title_text="Année", row=1, col=2)
    fig.update_yaxes(title_text="Nombre de catastrophes", row=1, col=2)

    # -----------------------------
    # 10) Titre global
    # -----------------------------
    if len(liste_cours_eau) == 0:
        rivers_text = "Aucun cours d'eau nommé"
    else:
        rivers_text = ", ".join(liste_cours_eau[:5])
        if len(liste_cours_eau) > 5:
            rivers_text += ", ..."

    fig.update_layout(
        title=(
            f"{commune_label} — {nb_cours_eau} cours d'eau"
            f"<br><sup>{rivers_text}</sup>"
        ),
        template="plotly_white",
        height=650,
        margin=dict(l=20, r=20, t=90, b=20)
    )

    return fig, yearly_counts, gdf_commune, gdf_water

import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.data.load_data import load_regions, load_waterways, load_merged_regions


def plot_region_waterways_and_flood_timeseries(
    region_name: str,
    hazard: str = "inondation",
    region_name_col_regions: str = "nom",
    region_code_col_regions: str = "code",
    water_name_col: str = "TopoOH",
    merged_region_name_col: str = "nom_region",
    merged_region_code_col: str = "code_region",
    year_col: str = "annee",
    hazard_col: str = "type_risque",
    count_col: str = "nb_catastrophes",
):
    """
    Affiche :
    - à gauche : carte de la région avec les cours d'eau
    - à droite : courbe d'évolution annuelle de l'aléa choisi

    Retour
    ------
    fig : plotly.graph_objects.Figure
    yearly_counts : pandas.DataFrame
    gdf_region_plot : geopandas.GeoDataFrame
    gdf_water_region : geopandas.GeoDataFrame
    """

    # -----------------------------
    # 1) Chargement des données
    # -----------------------------
    gdf_regions = load_regions().copy()
    gdf_waterways = load_waterways().copy()
    gdf_merged_regions = load_merged_regions().copy()

    # -----------------------------
    # 2) Harmonisation
    # -----------------------------
    gdf_regions[region_name_col_regions] = (
        gdf_regions[region_name_col_regions].astype(str).str.strip()
    )
    gdf_regions[region_code_col_regions] = (
        gdf_regions[region_code_col_regions].astype(str).str.strip().str.zfill(2)
    )

    gdf_merged_regions[merged_region_name_col] = (
        gdf_merged_regions[merged_region_name_col].astype(str).str.strip()
    )
    gdf_merged_regions[merged_region_code_col] = (
        gdf_merged_regions[merged_region_code_col].astype(str).str.strip().str.zfill(2)
    )
    gdf_merged_regions[hazard_col] = (
        gdf_merged_regions[hazard_col].astype(str).str.strip().str.lower()
    )

    region_name_clean = region_name.strip().lower()
    hazard_clean = hazard.strip().lower()

    if water_name_col not in gdf_waterways.columns:
        raise ValueError(f"Colonne introuvable dans la base cours d'eau : {water_name_col}")

    # -----------------------------
    # 3) Région sélectionnée
    # -----------------------------
    gdf_region = gdf_regions[
        gdf_regions[region_name_col_regions].str.lower() == region_name_clean
    ].copy()

    if gdf_region.empty:
        raise ValueError(f"Région introuvable : '{region_name}'")

    gdf_region = gdf_region.iloc[[0]].copy()
    region_label = gdf_region.iloc[0][region_name_col_regions]
    region_code = gdf_region.iloc[0][region_code_col_regions]

    if gdf_region.crs is None or gdf_waterways.crs is None:
        raise ValueError("Le CRS est manquant dans une des deux bases.")

    if gdf_region.crs != gdf_waterways.crs:
        gdf_waterways = gdf_waterways.to_crs(gdf_region.crs)

    # -----------------------------
    # 4) Cours d'eau intersectant la région
    # -----------------------------
    gdf_water_region = gpd.sjoin(
        gdf_waterways,
        gdf_region[[region_name_col_regions, "geometry"]],
        how="inner",
        predicate="intersects"
    ).copy()

    subset_cols = ["CdOH"] if "CdOH" in gdf_water_region.columns else [water_name_col, "geometry"]
    gdf_water_region = gdf_water_region.drop_duplicates(subset=subset_cols)

    # Reprojection pour Plotly
    gdf_region_plot = gdf_region.to_crs(epsg=4326)
    gdf_water_region = gdf_water_region.to_crs(epsg=4326)

    # -----------------------------
    # 5) Série temporelle
    # -----------------------------
    filtered = gdf_merged_regions[
        (gdf_merged_regions[merged_region_code_col] == region_code) &
        (gdf_merged_regions[hazard_col] == hazard_clean)
    ].copy()

    all_years = pd.DataFrame({
        year_col: sorted(gdf_merged_regions[year_col].dropna().astype(int).unique())
    })

    yearly_counts = (
        filtered.groupby(year_col, as_index=False)[count_col]
        .sum()
        .sort_values(year_col)
    )

    yearly_counts = all_years.merge(yearly_counts, on=year_col, how="left")
    yearly_counts[count_col] = yearly_counts[count_col].fillna(0).astype(int)

    total_cat = int(yearly_counts[count_col].sum())
    max_cat = int(yearly_counts[count_col].max())
    max_year = int(yearly_counts.loc[yearly_counts[count_col].idxmax(), year_col])

    # -----------------------------
    # 6) Figure
    # -----------------------------
    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.60, 0.40],
        specs=[[{"type": "scattergeo"}, {"type": "xy"}]],
        horizontal_spacing=0.08
    )

    # -----------------------------
    # 7) Carte de la région
    # -----------------------------
    region_geom = gdf_region_plot.geometry.iloc[0]

    if region_geom.geom_type == "Polygon":
        polygons = [region_geom]
    elif region_geom.geom_type == "MultiPolygon":
        polygons = list(region_geom.geoms)
    else:
        polygons = []

    for poly in polygons:
        x, y = poly.exterior.xy
        fig.add_trace(
            go.Scattergeo(
                lon=list(x),
                lat=list(y),
                mode="lines",
                fill="toself",
                fillcolor="rgba(200,200,200,0.30)",
                line=dict(color="#424147", width=1.3),
                showlegend=False,
                hoverinfo="skip"
            ),
            row=1,
            col=1
        )

    for _, row in gdf_water_region.iterrows():
        geom = row.geometry

        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = list(geom.geoms)
        else:
            lines = []

        river_name = row.get(water_name_col, None)
        if river_name is None or str(river_name).strip() == "" or str(river_name).lower() == "none":
            river_name = "Cours d'eau sans nom"

        for line in lines:
            x, y = line.xy
            fig.add_trace(
                go.Scattergeo(
                    lon=list(x),
                    lat=list(y),
                    mode="lines",
                    line=dict(color="#16035B", width=1.8),
                    showlegend=False,
                    hovertemplate=f"{river_name}<extra></extra>"
                ),
                row=1,
                col=1
            )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="white",
        row=1,
        col=1
    )

    # -----------------------------
    # 8) Courbe à droite
    # -----------------------------
    color_map = {
        "inondation": "#17057d",
        "secheresse": "#e67e22",
        "mouvement_terrain": "#6e6e6e",
        "tempete": "#7a5af8",
        "neige_grele": "#1f9d73",
        "vagues_submersion": "#2878b5",
        "seisme": "#c0392b",
        "autre": "#7f8c8d",
    }
    line_color = color_map.get(hazard_clean, "#051539")

    fill_color_map = {
        "inondation": "rgba(47,109,246,0.12)",
        "secheresse": "rgba(230,126,34,0.12)",
        "mouvement_terrain": "rgba(110,110,110,0.12)",
        "tempete": "rgba(122,90,248,0.12)",
        "neige_grele": "rgba(31,157,115,0.12)",
        "vagues_submersion": "rgba(40,120,181,0.12)",
        "seisme": "rgba(192,57,43,0.12)",
        "autre": "rgba(127,140,141,0.12)",
    }
    fill_color = fill_color_map.get(hazard_clean, "rgba(47,109,246,0.12)")

    fig.add_trace(
        go.Scatter(
            x=yearly_counts[year_col],
            y=yearly_counts[count_col],
            mode="lines+markers",
            line=dict(color=line_color, width=3),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor=fill_color,
            showlegend=False,
            hovertemplate="Année: %{x}<br>Nombre: %{y}<extra></extra>"
        ),
        row=1,
        col=2
    )

    fig.update_xaxes(
        title_text="Année",
        showgrid=False,
        zeroline=False,
        row=1,
        col=2
    )

    fig.update_yaxes(
        title_text="Nombre de catastrophes",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.10)",
        zeroline=False,
        row=1,
        col=2
    )

    # -----------------------------
    # 9) Layout général
    # -----------------------------
    fig.update_layout(
        title={
            "text": (
                f"<b>{region_label}</b> — Inondations et réseau hydrographique"
                f"<br><sup>Total : {total_cat} | Maximum annuel : {max_cat} ({max_year}) | "
                f"{len(gdf_water_region)} cours d'eau intersectent la région</sup>"
            ),
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 22, "color": "#17057d"}
        },
        template="plotly_white",
        height=650,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    return fig, yearly_counts, gdf_region_plot, gdf_water_region