"""fonctions utiles (chargement rapide, formatage)"""

import geopandas as gpd

from src.config import MERGED_FILE_REGION
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
from src.data.load_data import load_merged_regions



def get_available_regions():
    gdf = load_merged_regions()
    return sorted(gdf["nom_region"].dropna().unique().tolist())


def get_available_years():
    gdf = load_merged_regions()
    return sorted(gdf["annee"].dropna().astype(int).unique().tolist())


def get_available_risks():
    gdf = load_merged_regions()
    return sorted(gdf["type_risque"].dropna().unique().tolist())


def generate_plot(plot_name, region=None, year=None, hazard=None, years=None, risks=None):
    if plot_name == "france_regions_risk_count":
        return plot_france_regions_risk_count_1(
            year=year,
            hazard=hazard
        )

    elif plot_name == "region_waterways_flood_timeseries":
        return plot_region_waterways_and_flood_timeseries(
            region_name=region,
            hazard="inondation"
    )

    elif plot_name == "monthly_comparison":
        return plot_monthly_comparison(
            years=years,
            risks=risks,
            region=region
        )

    elif plot_name == "region_hazard_time_series":
        return plot_region_hazard_time_series(
            region_name=region,
            hazard=hazard
        )

    elif plot_name == "seasonality_boxplot":
        return plot_seasonality_boxplot(
            risks=risks,
            region=region
        )

    else:
        raise ValueError(f"Unknown plot name: {plot_name}")