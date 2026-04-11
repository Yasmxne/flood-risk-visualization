""" séries temporelles """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json


REGION_NAMES = {
    '11': 'Île-de-France',
    '24': 'Centre-Val de Loire',
    '27': 'Bourgogne-Franche-Comté',
    '28': 'Normandie',
    '32': 'Hauts-de-France',
    '44': 'Grand Est',
    '52': 'Pays de la Loire',
    '53': 'Bretagne',
    '75': 'Nouvelle-Aquitaine',
    '76': 'Occitanie',
    '84': 'Auvergne-Rhône-Alpes',
    '93': "Provence-Alpes-Côte d'Azur",
    '94': 'Corse'
}


def add_region(df, communes_path):
    with open(communes_path) as f:
        data = json.load(f)

    commune_to_region = {}
    for feat in data['features']:
        code = feat['properties']['code']
        region_code = feat['properties']['region']
        commune_to_region[code] = REGION_NAMES.get(region_code, None)

    df = df.copy()
    df['code_commune'] = df['code_commune'].astype(str).str.strip().str.zfill(5)
    df['region'] = df['code_commune'].map(commune_to_region)
    return df


def get_available_regions():
    return list(REGION_NAMES.values())


def get_available_risks():
    return ['inondation', 'secheresse', 'mouvement_terrain', 'tempete',
            'neige_grele', 'vagues_submersion', 'seisme', 'autre']


def get_available_years(df):
    return sorted(df['annee'].dropna().unique().astype(int).tolist())


def plot_seasonality_boxplot(df, risks, region=None):

    df_f = df[df['type_risque'].isin(risks)]

    if region:
        df_f = df_f[df_f['region'] == region]

    counts = df_f.groupby(['type_risque', 'annee', 'mois']).size().reset_index(name='nb')

    labels = {
        'inondation': 'Inondation',
        'secheresse': 'Sécheresse',
        'mouvement_terrain': 'Mouv. terrain',
        'tempete': 'Tempête',
        'neige_grele': 'Neige / Grêle',
        'vagues_submersion': 'Submersion',
        'seisme': 'Séisme',
        'autre': 'Autre'
    }
    mois_names = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']
    colors = {
        'Inondation': '#2196F3',
        'Sécheresse': '#FF9800',
        'Mouv. terrain': '#795548',
        'Tempête': '#9C27B0',
        'Neige / Grêle': '#607D8B',
        'Submersion': '#00BCD4',
        'Séisme': '#F44336',
        'Autre': '#9E9E9E'
    }

    risks_with_data = [r for r in risks if r in counts['type_risque'].values]
    labels_filtered = {k: v for k, v in labels.items() if k in risks_with_data}

    if not risks_with_data:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "Aucune donnée pour cette sélection", ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig

    n = len(labels_filtered)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols

    counts['risque_label'] = counts['type_risque'].map(labels)

    region_title = region if region else "France entière"
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
    fig.suptitle(f"Saisonnalité des catastrophes naturelles — {region_title}\nDistribution mensuelle sur toutes les années",
                 fontsize=14, fontweight='bold')

    if n == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for ax, risk_label in zip(axes, labels_filtered.values()):
        data = counts[counts['risque_label'] == risk_label]
        sns.boxplot(data=data, x='mois', y='nb', color=colors[risk_label],
                    ax=ax, fliersize=2, linewidth=0.8, showfliers=False)
        ax.set_title(risk_label, fontsize=12, fontweight='bold', color=colors[risk_label])
        ax.set_xticklabels(mois_names, fontsize=7, rotation=45)
        ax.set_xlabel('')
        ax.set_ylabel('Nb événements / an')

    for i in range(n, len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    return fig


# --- Courbes de comparaison mensuelle ---

def plot_monthly_comparison(df, years, risks, region=None):

    df_f = df[(df['annee'].isin(years)) & (df['type_risque'].isin(risks))]

    if region:
        df_f = df_f[df_f['region'] == region]

    counts = df_f.groupby(['type_risque', 'annee', 'mois']).size().reset_index(name='nb')

    labels = {
        'inondation': 'Inondation',
        'secheresse': 'Sécheresse',
        'mouvement_terrain': 'Mouv. terrain',
        'tempete': 'Tempête',
        'neige_grele': 'Neige / Grêle',
        'vagues_submersion': 'Submersion',
        'seisme': 'Séisme',
        'autre': 'Autre'
    }
    mois_names = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']

    risks_with_data = [r for r in risks if r in counts['type_risque'].values]
    labels_filtered = {k: v for k, v in labels.items() if k in risks_with_data}

    if not risks_with_data:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "Aucune donnée pour cette sélection", ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig

    n = len(labels_filtered)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols

    region_title = region if region else "France entière"
    title_years = " vs ".join(str(y) for y in years)
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))
    fig.suptitle(f"Comparaison mensuelle des catastrophes — {title_years}\n{region_title}",
                 fontsize=14, fontweight='bold')

    if n == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for ax, risk in zip(axes, risks_with_data):
        for y in years:
            data = counts[(counts['type_risque'] == risk) & (counts['annee'] == y)]
            full = pd.DataFrame({'mois': range(1, 13)})
            data = full.merge(data, on='mois', how='left').fillna(0)
            ax.plot(data['mois'], data['nb'], marker='o', label=str(y), linewidth=2)
        ax.set_title(labels.get(risk, risk), fontsize=12, fontweight='bold')
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(mois_names, fontsize=7, rotation=45)
        ax.set_ylabel('Nb événements')
        ax.legend(title='Année')
        ax.grid(alpha=0.3)

    for i in range(n, len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    return fig