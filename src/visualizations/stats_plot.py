"""histogrammes, comparaisons"""

"""histogrammes, comparaisons"""

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.config import REGION_STATS_FILE


def plot_seasonality_boxplot(
    risks,
    region=None,
    df_stats: pd.DataFrame | None = None,
    hazard_col: str = "type_risque",
    region_name_col: str = "nom_region",
    year_col: str = "annee",
    month_col: str = "mois",
    count_col: str = "nb_catastrophes"
):
    if df_stats is None:
        df_stats = pd.read_csv(REGION_STATS_FILE)

    df = df_stats.copy()

    required_cols = [hazard_col, region_name_col, year_col, month_col, count_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes : {missing_cols}")

    df[hazard_col] = df[hazard_col].astype(str).str.strip().str.lower()
    df[region_name_col] = df[region_name_col].astype(str).str.strip()

    df_f = df[df[hazard_col].isin(risks)].copy()

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

    colors = {
        "Inondation": "#2196F3",
        "Sécheresse": "#FF9800",
        "Mouv. terrain": "#795548",
        "Tempête": "#9C27B0",
        "Neige / Grêle": "#607D8B",
        "Submersion": "#00BCD4",
        "Séisme": "#F44336",
        "Autre": "#9E9E9E"
    }

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

    counts["risque_label"] = counts[hazard_col].map(labels)

    region_title = region if region else "France entière"
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
    fig.suptitle(
        f"Saisonnalité des catastrophes naturelles — {region_title}\nDistribution mensuelle sur toutes les années",
        fontsize=14,
        fontweight="bold"
    )

    if n == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for ax, risk_label in zip(axes, labels_filtered.values()):
        data = counts[counts["risque_label"] == risk_label]

        sns.boxplot(
            data=data,
            x=month_col,
            y="nb",
            color=colors[risk_label],
            ax=ax,
            fliersize=2,
            linewidth=0.8,
            showfliers=False
        )

        ax.set_title(risk_label, fontsize=12, fontweight="bold", color=colors[risk_label])
        ax.set_xticks(range(12))
        ax.set_xticklabels(mois_names, fontsize=7, rotation=45)
        ax.set_xlabel("")
        ax.set_ylabel("Nb événements / an")

    for i in range(n, len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    return fig