# sponsor_match/train_matcher.py
import joblib, pandas as pd, pathlib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sponsor_match.features import make_pair_features   # write small helper

MODEL_DIR = pathlib.Path("models"); MODEL_DIR.mkdir(exist_ok=True)

def main():
    df = pd.read_parquet("data/positive_pairs.parquet")  # 1=already sponsored
    X = make_pair_features(df)
    y = df["label"]
    X_train,X_val,y_train,y_val = train_test_split(X,y,test_size=.2,random_state=1)
    clf = GradientBoostingClassifier().fit(X_train, y_train)
    print("val AUC:", clf.score(X_val,y_val))
    joblib.dump(clf, MODEL_DIR/"match_gb.joblib")

if __name__ == "__main__":
    main()
