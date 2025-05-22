#!/usr/bin/env python3
"""
cli/train_matcher.py
---------------------
Train a GradientBoostingClassifier on labeled sponsor–club pairs
and save the model artifact under the project's `models/` directory.

Usage:
    python cli/train_matcher.py \
      --input data/positive_pairs.parquet \
      --test-size 0.2 \
      --random-state 1
"""

import logging
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier

from sponsor_match.models.features import FeatureEngineer

# configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Determine project root and models directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # cli/ -> project root
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models"

def main(
    input_path: Path,
    model_dir: Path,
    test_size: float,
    random_state: int
) -> None:
    """
    Load training data, engineer features, split into train/validation,
    train a GradientBoostingClassifier, evaluate, and save the model.

    Parameters
    ----------
    input_path : Path
        Parquet file of labeled club–company pairs with a 'label' column.
    model_dir : Path
        Directory in which to save the trained model artifact.
    test_size : float
        Fraction of data reserved for validation.
    random_state : int
        Seed for reproducible splits.
    """
    logger.info("Loading data from %s", input_path)
    df = pd.read_parquet(input_path)
    logger.info("Loaded %d rows", len(df))

    logger.info("Generating pairwise features")
    X = FeatureEngineer.make_pair_features(df)
    y = df["label"]

    logger.info(
        "Splitting into train/validation (test_size=%.2f, random_state=%d)",
        test_size, random_state
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    logger.info("Training GradientBoostingClassifier")
    clf = GradientBoostingClassifier(random_state=random_state)
    clf.fit(X_train, y_train)

    val_acc = clf.score(X_val, y_val)
    logger.info("Validation accuracy: %.4f", val_acc)

    # Ensure the models directory exists
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "match_gb.joblib"

    logger.info("Saving trained model to %s", model_path)
    joblib.dump(clf, model_path)
    logger.info("Done.")

if __name__ == "__main__":
    parser = ArgumentParser(description="Train the sponsor–club matching classifier")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/positive_pairs.parquet"),
        help="Parquet file of labeled pairs"
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=DEFAULT_MODEL_DIR,
        help="Directory for saving model artifacts"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data for validation"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=1,
        help="Seed for train/validation split"
    )

    args = parser.parse_args()
    main(
        input_path=args.input,
        model_dir=args.model_dir,
        test_size=args.test_size,
        random_state=args.random_state
    )
