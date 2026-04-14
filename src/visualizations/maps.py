"""cartes (heatmap, geojson)"""

import json
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import REGION_STATS_FILE, REGIONS_ONLY_FILE
from src.data.load_data import load_waterways


def plot_france_regions_risk_count_1(
    year: int,
    hazard: str,
    df_stats: pd.DataFrame | None = None,
    gdf_regions: gpd.GeoDataFrame | None = None,
    year_col: str = "annee",
    hazard_col: str = "type_risque",
    region_code_col: str = "code_region",
    region_name_col: str = "nom_region",
    count_col: str = "nb_catastrophes",
    metro_only: bool = True
):
    if df_stats is None:
        df_stats = pd.read_csv(REGION_STATS_FILE)

    if gdf_regions is None:
        gdf_regions = gpd.read_file(REGIONS_ONLY_FILE)

    df_stats = df_stats.copy()
    gdf_regions = gdf_regions.copy()

    required_stats = [year_col, hazard_col, region_code_col, region_name_col, count_col]
    missing_stats = [col for col in required_stats if col not in df_stats.columns]
    if missing_stats:
        raise ValueError(f"Colonnes manquantes dans df_stats : {missing_stats}")

    required_regions = [region_code_col, region_name_col, "geometry"]
    missing_regions = [col for col in required_regions if col not in gdf_regions.columns]
    if missing_regions:
        raise ValueError(f"Colonnes manquantes dans gdf_regions : {missing_regions}")

    df_stats[region_code_col] = df_stats[region_code_col].astype(str).str.zfill(2)
    df_stats[hazard_col] = df_stats[hazard_col].astype(str).str.strip().str.lower()

    gdf_regions[region_code_col] = gdf_regions[region_code_col].astype(str).str.zfill(2)
    gdf_regions[region_name_col] = gdf_regions[region_name_col].astype(str).str.strip()

    if metro_only:
        dom_codes = {"01", "02", "03", "04", "06"}
        gdf_regions = gdf_regions[~gdf_regions[region_code_col].isin(dom_codes)].copy()
        df_stats = df_stats[~df_stats[region_code_col].isin(dom_codes)].copy()

    filtered = df_stats[
        (df_stats[year_col] == year) &
        (df_stats[hazard_col] == hazard.lower())
    ].copy()

    counts = (
        filtered.groupby(region_code_col, as_index=False)[count_col]
        .sum()
    )

    france_map = gdf_regions.merge(
        counts,
        on=region_code_col,
        how="left"
    )

    france_map[count_col] = france_map[count_col].fillna(0).astype(int)

    if france_map.crs is None:
        raise ValueError("Le CRS de gdf_regions est manquant.")

    france_map = france_map.to_crs(epsg=4326)

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

    fig.update_layout(coloraxis_showscale=False)

    centroids_proj = france_map.to_crs(epsg=2154)
    centroids = france_map.copy()
    centroids["geometry"] = centroids_proj.centroid.to_crs(epsg=4326)
    centroids["lon"] = centroids.geometry.x
    centroids["lat"] = centroids.geometry.y

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


def plot_region_waterways_and_flood_timeseries(
    region_name: str,
    hazard: str = "inondation",
    df_stats: pd.DataFrame | None = None,
    gdf_regions: gpd.GeoDataFrame | None = None,
    gdf_waterways: gpd.GeoDataFrame | None = None,
    region_name_col: str = "nom_region",
    region_code_col: str = "code_region",
    water_name_col: str = "TopoOH",
    year_col: str = "annee",
    hazard_col: str = "type_risque",
    count_col: str = "nb_catastrophes",
):
    if df_stats is None:
        df_stats = pd.read_csv(REGION_STATS_FILE)

    if gdf_regions is None:
        gdf_regions = gpd.read_file(REGIONS_ONLY_FILE)

    if gdf_waterways is None:
        gdf_waterways = load_waterways()

    df_stats = df_stats.copy()
    gdf_regions = gdf_regions.copy()
    gdf_waterways = gdf_waterways.copy()

    gdf_regions[region_name_col] = gdf_regions[region_name_col].astype(str).str.strip()
    gdf_regions[region_code_col] = gdf_regions[region_code_col].astype(str).str.strip().str.zfill(2)

    df_stats[region_name_col] = df_stats[region_name_col].astype(str).str.strip()
    df_stats[region_code_col] = df_stats[region_code_col].astype(str).str.strip().str.zfill(2)
    df_stats[hazard_col] = df_stats[hazard_col].astype(str).str.strip().str.lower()

    region_name_clean = region_name.strip().lower()
    hazard_clean = hazard.strip().lower()

    if water_name_col not in gdf_waterways.columns:
        raise ValueError(f"Colonne introuvable dans la base cours d'eau : {water_name_col}")

    gdf_region = gdf_regions[
        gdf_regions[region_name_col].str.lower() == region_name_clean
    ].copy()

    if gdf_region.empty:
        raise ValueError(f"Région introuvable : '{region_name}'")

    gdf_region = gdf_region.iloc[[0]].copy()
    region_label = gdf_region.iloc[0][region_name_col]
    region_code = gdf_region.iloc[0][region_code_col]

    if gdf_region.crs is None or gdf_waterways.crs is None:
        raise ValueError("Le CRS est manquant dans une des deux bases.")

    if gdf_region.crs != gdf_waterways.crs:
        gdf_waterways = gdf_waterways.to_crs(gdf_region.crs)

    gdf_water_region = gpd.sjoin(
        gdf_waterways,
        gdf_region[[region_name_col, "geometry"]],
        how="inner",
        predicate="intersects"
    ).copy()

    subset_cols = ["CdOH"] if "CdOH" in gdf_water_region.columns else [water_name_col, "geometry"]
    gdf_water_region = gdf_water_region.drop_duplicates(subset=subset_cols)

    gdf_region_plot = gdf_region.to_crs(epsg=4326)
    gdf_water_region = gdf_water_region.to_crs(epsg=4326)

    filtered = df_stats[
        (df_stats[region_code_col] == region_code) &
        (df_stats[hazard_col] == hazard_clean)
    ].copy()

    all_years = pd.DataFrame({
        year_col: sorted(df_stats[year_col].dropna().astype(int).unique())
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

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.60, 0.40],
        specs=[[{"type": "scattergeo"}, {"type": "xy"}]],
        horizontal_spacing=0.08
    )

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