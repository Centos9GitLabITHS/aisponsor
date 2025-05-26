# train_matcher.py
"""
Train a GradientBoostingClassifier on labelled sponsor–club pairs
and save the model artifact under the project's `models/` directory.
"""
import logging  # Informative logging
from argparse import ArgumentParser  # CLI parsing
from pathlib import Path  # Filesystem paths

import joblib  # Model persistence
import pandas as pd  # Data loading
from sklearn.ensemble import GradientBoostingClassifier  # ML algorithm
from sklearn.model_selection import train_test_split  # Data splitting

from sponsor_match.models.features import FeatureEngineer  # Custom feature engineering

# Configure logging format and level
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Default model directory under project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models"


def main(input_path: Path, model_dir: Path, test_size: float, random_state: int) -> None:
    """
    Load training data, generate features, split into train/validation,
    train a GradientBoostingClassifier, evaluate performance, and save model.
    """
    logger.info("Loading data from %s", input_path)
    df = pd.read_parquet(input_path)
    logger.info("Loaded %d rows", len(df))

    # Generate pairwise features for ML model
    logger.info("Generating pairwise features")
    X = FeatureEngineer.make_pair_features(df)
    y = df["label"]

    # Split data ensuring reproducibility
    logger.info("Splitting data (test_size=%.2f, random_state=%d)", test_size, random_state)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Train the Gradient Boosting classifier
    logger.info("Training GradientBoostingClassifier")
    clf = GradientBoostingClassifier(random_state=random_state)
    clf.fit(X_train, y_train)

    # Evaluate and log validation accuracy
    val_acc = clf.score(X_val, y_val)
    logger.info("Validation accuracy: %.4f", val_acc)

    # Ensure output directory exists and save the model
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "match_gb.joblib"
    logger.info("Saving trained model to %s", model_path)
    joblib.dump(clf, model_path)
    logger.info("Model training complete.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Train the sponsor–club matching classifier")
    parser.add_argument("--input", type=Path, default=Path("data/positive_pairs.parquet"),
                        help="Parquet file of labelled pairs")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR,
                        help="Directory for saving model artifact")
    parser.add_argument("--test-size", type=float, default=0.2,
                        help="Fraction of data for validation")
    parser.add_argument("--random-state", type=int, default=1,
                        help="Seed for train/validation split")
    args = parser.parse_args()
    main(
        input_path=args.input,
        model_dir=args.model_dir,
        test_size=args.test_size,
        random_state=args.random_state
    )
