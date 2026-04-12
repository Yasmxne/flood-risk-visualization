"""logique des pages + filtres (année, catastrophe)"""

from flask import Blueprint, render_template, request
from src.app.utils import (
    get_available_regions,
    get_available_years,
    get_available_risks,
    generate_plot
)

main = Blueprint("main", __name__)


def fig_to_html(fig):
    if isinstance(fig, tuple):
        fig = fig[0]

    if hasattr(fig, "to_html"):
        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    return "<p>Erreur : figure non affichable.</p>"


@main.route("/")
def index():
    regions = get_available_regions()
    years = get_available_years()
    risks = get_available_risks()

    return render_template(
        "index.html",
        regions=regions,
        years=years,
        risks=risks
    )


@main.route("/plot/france-map", methods=["POST"])
def plot_france_map():
    year = request.form.get("year", type=int)
    hazard = request.form.get("hazard", type=str)

    fig = generate_plot(
        plot_name="france_regions_risk_count",
        year=year,
        hazard=hazard
    )
    return fig_to_html(fig)


@main.route("/plot/region-time-series", methods=["POST"])
def plot_region_time_series():
    region = request.form.get("region", type=str)
    hazard = request.form.get("hazard", type=str)

    fig = generate_plot(
        plot_name="region_hazard_time_series",
        region=region,
        hazard=hazard
    )
    return fig_to_html(fig)


@main.route("/plot/monthly-comparison", methods=["POST"])
def plot_monthly():
    region = request.form.get("region", type=str)
    hazards = request.form.getlist("risks")
    years_raw = request.form.getlist("years")
    years = [int(y) for y in years_raw if y]

    fig = generate_plot(
        plot_name="monthly_comparison",
        region=region,
        years=years,
        risks=hazards
    )
    return fig_to_html(fig)


@main.route("/plot/seasonality-boxplot", methods=["POST"])
def plot_seasonality():
    region = request.form.get("region", type=str)
    hazards = request.form.getlist("risks")

    fig = generate_plot(
        plot_name="seasonality_boxplot",
        region=region,
        risks=hazards
    )
    return fig_to_html(fig)


@main.route("/plot/waterways-flood", methods=["POST"])
def plot_waterways():
    region = request.form.get("region", type=str)

    fig = generate_plot(
        plot_name="region_waterways_flood_timeseries",
        region=region
    )
    return fig_to_html(fig)