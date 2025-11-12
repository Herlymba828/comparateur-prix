import numpy as np
import pandas as pd
from ml_models.modele_prediction_prix import ModelePredictionPrix


def main():
    df = pd.read_csv("data/examples/prix_exemple.csv")
    # Exemple minimal: on ne garde que le volume comme feature numérique
    X = np.c_[df["volume"].values]
    y = df["prix_cible"].values

    model = ModelePredictionPrix()
    cv = model.cross_valider(X, y, cv_splits=3)
    ok = model.entrainer(X, y)
    ev = model.evaluer(X, y)

    print("KFold MAE_mean=", cv["mae_mean"], "±", cv["mae_std"])
    print("KFold R2_mean=", cv["r2_mean"], "±", cv["r2_std"])
    print("Train MAE=", ev.mae if ev else None, "R2=", ev.r2 if ev else None)


if __name__ == "__main__":
    main()
