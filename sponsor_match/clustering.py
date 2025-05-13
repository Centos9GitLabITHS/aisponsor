# sponsor_match/clustering.py
from pathlib import Path
import joblib, pandas as pd
from sklearn.cluster import KMeans
from sponsor_match.db import get_engine

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "kmeans.joblib"

FEATURES = ["lat", "lon", "rev_per_emp"]          # simple starter feature set
N_CLUSTERS = 8

def train_kmeans(df: pd.DataFrame, save_path: Path = MODEL_PATH):
    kmeans = KMeans(n_clusters=N_CLUSTERS, n_init="auto", random_state=42)
    kmeans.fit(df[FEATURES])
    joblib.dump(kmeans, save_path)
    return kmeans

def load_model():
    return joblib.load(MODEL_PATH)
