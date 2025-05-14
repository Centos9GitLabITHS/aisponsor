#!/usr/bin/env python3
"""
sponsor_match/ui/train_matcher.py
-------------------------------
Train a GradientBoostingClassifier on labeled sponsor–club pairs and save the model.

Usage:
    python -m sponsor_match.train_matcher \
        --input data/positive_pairs.parquet \
        --model-dir models \
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

from sponsor_match.features import make_pair_features

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

def main(
    input_path: Path,
    model_dir: Path,
    test_size: float,
    random_state: int
) -> None:
    """
    Load training data, engineer features, split into train/validation,
    train a GradientBoostingClassifier, evaluate on validation,
    and persist the model.

    Parameters
    ----------
    input_path : Path
        Parquet file containing positive and negative club–company pairs with a 'label' column.
    model_dir : Path
        Directory in which to save the trained model artifact.
    test_size : float
        Proportion of the dataset to reserve for validation.
    random_state : int
        Seed for reproducibility of the train/validation split.
    """
    logger.info("Loading data from %s", input_path)
    df = pd.read_parquet(input_path)
    logger.info("Data contains %d rows", len(df))

    logger.info("Creating pairwise features")
    X = make_pair_features(df)
    y = df["label"]

    logger.info(
        "Splitting data (test_size=%.2f, random_state=%d)",
        test_size, random_state
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    logger.info("Training GradientBoostingClassifier")
    clf = GradientBoostingClassifier()
    clf.fit(X_train, y_train)

    val_score = clf.score(X_val, y_val)
    logger.info("Validation accuracy: %.4f", val_score)

    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "match_gb.joblib"
    joblib.dump(clf, model_path)
    logger.info("Model saved to %s", model_path)

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Train the sponsor–club matching classifier"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/positive_pairs.parquet"),
        help="Path to Parquet file with labeled pairs"
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models"),
        help="Directory to write the trained model"
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
        help="Random seed for splitting"
    )
    args = parser.parse_args()
    main(
        input_path=args.input,
        model_dir=args.model_dir,
        test_size=args.test_size,
        random_state=args.random_state
    )
