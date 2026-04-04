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

    return df


def save_clean_data():
    df = clean_catnat()
    df.to_csv(CLEAN_CATNAT_FILE, index=False)
    print("Clean data saved")


if __name__ == "__main__":
    save_clean_data()