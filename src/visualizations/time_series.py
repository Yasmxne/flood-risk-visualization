""" séries temporelles """
import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from src.config import REGION_STATS_FILE


def plot_monthly_comparison(
    years,
    risks,
    region=None,
    df_stats: pd.DataFrame | None = None,
    year_col: str = "annee",
    month_col: str = "mois",
    hazard_col: str = "type_risque",
    region_name_col: str = "nom_region",
    count_col: str = "nb_catastrophes"
):
    if df_stats is None:
        df_stats = pd.read_csv(REGION_STATS_FILE)

    df = df_stats.copy()

    required_cols = [year_col, month_col, hazard_col, region_name_col, count_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes : {missing_cols}")

    df[hazard_col] = df[hazard_col].astype(str).str.strip().str.lower()
    df[region_name_col] = df[region_name_col].astype(str).str.strip()

    df_f = df[
        (df[year_col].isin(years)) &
        (df[hazard_col].isin(risks))
    ].copy()

    if region:
        df_f = df_f[df_f[region_name_col] == region]

    counts = df_f[[hazard_col, year_col, month_col, count_col]].copy()
    counts = counts.rename(columns={count_col: "nb"})

    labels = {
        "inondation": "Inondation",
        "secheresse": "Sécheresse",
        "mouvement_terrain": "Mouv. terrain",
        "tempete": "Tempête",
        "neige_grele": "Neige / Grêle",
        "vagues_submersion": "Submersion",
        "seisme": "Séisme",
        "autre": "Autre"
    }

    mois_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

    risks_with_data = [r for r in risks if r in counts[hazard_col].values]
    labels_filtered = {k: v for k, v in labels.items() if k in risks_with_data}

    if not risks_with_data:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "Aucune donnée pour cette sélection", ha="center", va="center", fontsize=14)
        ax.axis("off")
        return fig

    n = len(labels_filtered)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols

    region_title = region if region else "France entière"
    title_years = " vs ".join(str(y) for y in years)

    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
    fig.suptitle(
        f"Comparaison mensuelle des catastrophes — {title_years}\n{region_title}",
        fontsize=14,
        fontweight="bold"
    )

    if n == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for ax, risk in zip(axes, risks_with_data):
        for y in years:
            data = counts[
                (counts[hazard_col] == risk) &
                (counts[year_col] == y)
            ][[month_col, "nb"]].copy()

            full = pd.DataFrame({month_col: range(1, 13)})
            data = full.merge(data, on=month_col, how="left").fillna(0)

            ax.plot(data[month_col], data["nb"], marker="o", label=str(y), linewidth=2)

        ax.set_title(labels.get(risk, risk), fontsize=12, fontweight="bold")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(mois_names, fontsize=7, rotation=45)
        ax.set_ylabel("Nb événements")
        ax.legend(title="Année")
        ax.grid(alpha=0.3)

    for i in range(n, len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    return fig


def plot_region_hazard_time_series(
    region_name: str,
    hazard: str,
    df_stats: pd.DataFrame | None = None,
    year_col: str = "annee",
    hazard_col: str = "type_risque",
    region_code_col: str = "code_region",
    region_name_col: str = "nom_region",
    count_col: str = "nb_catastrophes"
):
    if df_stats is None:
        df_stats = pd.read_csv(REGION_STATS_FILE)

    df = df_stats.copy()

    required_cols = [year_col, hazard_col, region_code_col, region_name_col, count_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes : {missing_cols}")

    df[hazard_col] = df[hazard_col].astype(str).str.strip().str.lower()
    df[region_name_col] = df[region_name_col].astype(str).str.strip()

    region_name_clean = region_name.strip().lower()
    hazard_clean = hazard.strip().lower()

    region_exists = (df[region_name_col].str.lower() == region_name_clean).any()
    if not region_exists:
        raise ValueError(f"Région introuvable dans la base : '{region_name}'")

    region_data = df[df[region_name_col].str.lower() == region_name_clean].copy()

    all_years = pd.DataFrame({
        year_col: sorted(df[year_col].dropna().astype(int).unique())
    })

    filtered = region_data[region_data[hazard_col] == hazard_clean].copy()

    yearly_counts = (
        filtered.groupby(year_col, as_index=False)[count_col]
        .sum()
        .sort_values(year_col)
    )

    yearly_counts = all_years.merge(yearly_counts, on=year_col, how="left")
    yearly_counts[count_col] = yearly_counts[count_col].fillna(0).astype(int)

    hazard_colors = {
        "inondation": "#1b0572",
        "secheresse": "#d94701",
        "mouvement_terrain": "#525252",
        "tempete": "#756bb1",
        "neige_grele": "#238b45",
        "vagues_submersion": "#2171b5",
        "seisme": "#cb181d",
        "autre": "#969696"
    }
    line_color = hazard_colors.get(hazard_clean, "#1f77b4")

    fig = px.line(
        yearly_counts,
        x=year_col,
        y=count_col,
        markers=True,
        title=f"Évolution annuelle du nombre de catastrophes '{hazard}' en {region_name}"
    )

    fig.update_traces(
        line=dict(width=3, color=line_color),
        marker=dict(size=8, color=line_color)
    )

    fig.update_layout(
        xaxis_title="Année",
        yaxis_title="Nombre de catastrophes",
        template="plotly_white",
        hovermode="x unified"
    )

    return fig, yearly_counts