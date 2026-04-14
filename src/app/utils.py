"""fonctions utiles (chargement rapide, formatage)"""

"""fonctions utiles (chargement rapide, formatage, génération des figures)"""
import matplotlib.pyplot as plt
from functools import lru_cache
from io import BytesIO
import base64
import pandas as pd
import geopandas as gpd

from src.config import REGION_STATS_FILE, REGIONS_ONLY_FILE
from src.data.load_data import load_waterways

from src.visualizations.maps import (
    plot_france_regions_risk_count_1,
    plot_region_waterways_and_flood_timeseries
)
from src.visualizations.time_series import (
    plot_monthly_comparison,
    plot_region_hazard_time_series
)
from src.visualizations.stats_plot import (
    plot_seasonality_boxplot
)


@lru_cache(maxsize=1)
def load_region_stats():
    return pd.read_csv(REGION_STATS_FILE)


@lru_cache(maxsize=1)
def load_regions_only():
    return gpd.read_file(REGIONS_ONLY_FILE)


@lru_cache(maxsize=1)
def load_waterways_cached():
    return load_waterways()


def get_available_regions():
    df = load_region_stats()
    return sorted(df["nom_region"].dropna().unique().tolist())


def get_available_years():
    df = load_region_stats()
    return sorted(df["annee"].dropna().astype(int).unique().tolist())


def get_available_risks():
    df = load_region_stats()
    return sorted(df["type_risque"].dropna().unique().tolist())


def matplotlib_fig_to_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=120)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    buffer.close()
    plt.close(fig)
    return image_base64


def generate_plot(plot_name, region=None, year=None, hazard=None, years=None, risks=None):
    df_stats = load_region_stats()
    gdf_regions = load_regions_only()

    if plot_name == "france_regions_risk_count":
        fig, _ = plot_france_regions_risk_count_1(
            year=year,
            hazard=hazard,
            df_stats=df_stats,
            gdf_regions=gdf_regions
        )
        return {"type": "plotly", "figure": fig}

    elif plot_name == "region_waterways_flood_timeseries":
        gdf_waterways = load_waterways_cached()
        fig, _, _, _ = plot_region_waterways_and_flood_timeseries(
            region_name=region,
            hazard="inondation",
            df_stats=df_stats,
            gdf_regions=gdf_regions,
            gdf_waterways=gdf_waterways
        )
        return {"type": "plotly", "figure": fig}

    elif plot_name == "region_hazard_time_series":
        fig, _ = plot_region_hazard_time_series(
            region_name=region,
            hazard=hazard,
            df_stats=df_stats
        )
        return {"type": "plotly", "figure": fig}

    elif plot_name == "monthly_comparison":
        fig = plot_monthly_comparison(
            years=years,
            risks=risks,
            region=region,
            df_stats=df_stats
        )
        return {"type": "matplotlib", "figure": fig}

    elif plot_name == "seasonality_boxplot":
        fig = plot_seasonality_boxplot(
            risks=risks,
            region=region,
            df_stats=df_stats
        )
        return {"type": "matplotlib", "figure": fig}

    else:
        raise ValueError(f"Unknown plot name: {plot_name}")