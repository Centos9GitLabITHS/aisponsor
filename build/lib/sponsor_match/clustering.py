import joblib, pandas as pd, numpy as np, pathlib
from sklearn.cluster import MiniBatchKMeans
from sponsor_match.db import get_engine

MODEL_DIR = pathlib.Path("models"); MODEL_DIR.mkdir(exist_ok=True)

def train_kmeans(df, size_bucket: str):
    coords = df[["lat","lon"]].to_numpy()
    km = MiniBatchKMeans(n_clusters=8, random_state=42, batch_size=256).fit(coords)
    joblib.dump(km, MODEL_DIR / f"kmeans_{size_bucket}.joblib")

def main():
    eng = get_engine()
    clubs = pd.read_sql("select * from clubs", eng)
    firms = pd.read_sql("select * from companies", eng)

    for bucket in ["small","medium","large"]:
        sub = firms[firms.size_bucket==bucket]
        if len(sub) >= 100:
            train_kmeans(sub, bucket)

if __name__ == "__main__":
    main()
