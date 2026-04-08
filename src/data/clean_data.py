"""Nettoyage dataset"""
import pandas as pd

from src.data.load_data import load_catnat
from src.config import CLEAN_CATNAT_FILE


def clean_catnat():
    df = load_catnat()

    df = df[["cod_commune","lib_commune", "num_risque_jo", "lib_risque_jo", "dat_deb"]]

    df = df.rename(columns={
        "cod_commune": "code_commune",
        "lib_risque_jo": "type_risque",
        "dat_deb": "date_debut",
        "num_risque_jo": "num_risque"

    })

    df["date_debut"] = pd.to_datetime(df["date_debut"], errors="coerce") 
    df = df.dropna(subset=["code_commune", "type_risque", "date_debut"])
    df["type_risque"] = df["type_risque"].str.lower().str.strip()

    mapping = {
        # Inondations
        "inondations et/ou coulées de boue": "inondation",
        "coulée de boue": "inondation",
        "inondations remontée nappe": "inondation",
        "inondations par choc mécanique des vagues": "inondation",
        "lave torrentielle": "inondation",

        # Sécheresse
        "sécheresse": "secheresse",
        "sécheressse": "secheresse",
        "mouvements de terrain différentiels consécutifs à la sécheresse et à la réhydratation des sols": "secheresse",

        # Mouvements de terrain
        "mouvement de terrain": "mouvement_terrain",
        "glissement de terrain": "mouvement_terrain",
        "glissement et effondrement de terrain": "mouvement_terrain",
        "effondrement et/ou affaisement": "mouvement_terrain",
        "eboulement et/ou chute de blocs": "mouvement_terrain",
        "glissement et eboulement rocheux": "mouvement_terrain",
        "mouvements de terrains (hors sécheresse géotechnique)": "mouvement_terrain",

        # Tempêtes
        "tempête": "tempete",
        "vents cycloniques": "tempete",

        # Neige / Grêle
        "poids de la neige": "neige_grele",
        "grêle": "neige_grele",

        # Vagues / submersion
        "chocs mécaniques liés à l'action des vagues": "vagues_submersion",
        "chocs m�caniques li�s � l'action des vagues": "vagues_submersion",
        "choc m�caniques li�s � l'action des vagues": "vagues_submersion",
        "raz de marée": "vagues_submersion",

        # Séismes
        "secousse sismique": "seisme",
        "séismes": "seisme",

        # Autres
        "avalanche": "autre",
        "divers": "autre",
        "eruption volcanique": "autre"
    }

    df["type_risque"] = df["type_risque"].replace(mapping)

    df = df.drop_duplicates(subset=["code_commune", "lib_commune", "num_risque", "type_risque", "date_debut"])

    # créer les colonnes annee et mois de l'occurence de l'aléa
    df["annee"] = df["date_debut"].dt.year
    df["mois"] = df["date_debut"].dt.month

    return df


def save_clean_data():
    df = clean_catnat()
    df.to_csv(CLEAN_CATNAT_FILE, index=False)
    print("Clean data saved")


if __name__ == "__main__":
    save_clean_data()