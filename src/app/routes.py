"""logique des pages + filtres (année, catastrophe)"""

from flask import Blueprint, render_template, request, jsonify
import json
import plotly

from src.app.utils import (
    get_available_regions,
    get_available_years,
    get_available_risks,
    generate_plot,
    matplotlib_fig_to_base64
)

main = Blueprint("main", __name__)


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


def build_response(plot_result):
    plot_type = plot_result["type"]
    fig = plot_result["figure"]

    if plot_type == "plotly":
        figure_json = json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
        return jsonify({
            "plot_type": "plotly",
            "figure": figure_json
        })

    elif plot_type == "matplotlib":
        image_base64 = matplotlib_fig_to_base64(fig)
        return jsonify({
            "plot_type": "matplotlib",
            "image_base64": image_base64
        })

    return jsonify({
        "plot_type": "error",
        "message": "Type de figure non reconnu."
    }), 500


@main.route("/plot/france-map", methods=["POST"])
def plot_france_map():
    year = request.form.get("year", type=int)
    hazard = request.form.get("hazard", type=str)

    plot_result = generate_plot(
        plot_name="france_regions_risk_count",
        year=year,
        hazard=hazard
    )
    return build_response(plot_result)


@main.route("/plot/region-time-series", methods=["POST"])
def plot_region_time_series():
    region = request.form.get("region", type=str)
    hazard = request.form.get("hazard", type=str)

    plot_result = generate_plot(
        plot_name="region_hazard_time_series",
        region=region,
        hazard=hazard
    )
    return build_response(plot_result)


@main.route("/plot/monthly-comparison", methods=["POST"])
def plot_monthly():
    region = request.form.get("region", type=str)
    hazards = request.form.getlist("risks")
    years_raw = request.form.getlist("years")
    years = [int(y) for y in years_raw if y]

    plot_result = generate_plot(
        plot_name="monthly_comparison",
        region=region,
        years=years,
        risks=hazards
    )
    return build_response(plot_result)


@main.route("/plot/seasonality-boxplot", methods=["POST"])
def plot_seasonality():
    region = request.form.get("region", type=str)
    hazards = request.form.getlist("risks")

    plot_result = generate_plot(
        plot_name="seasonality_boxplot",
        region=region,
        risks=hazards
    )
    return build_response(plot_result)


@main.route("/plot/waterways-flood", methods=["POST"])
def plot_waterways():
    region = request.form.get("region", type=str)

    plot_result = generate_plot(
        plot_name="region_waterways_flood_timeseries",
        region=region
    )
    return build_response(plot_result)