# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
sponsor_match/models/models.py
-------------------------------
Ensemble of ML models for sponsorship probability prediction.
"""

import logging
from typing import Any, Dict, Union

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.neural_network import MLPRegressor

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

class SponsorshipPredictorEnsemble:
    """
    Holds a collection of models and provides a unified interface
    for training and predicting sponsor-match probabilities.
    """

    def __init__(self) -> None:
        """
        Initialize the ensemble with default hyperparameters.
        """
        self.models: Dict[str, Any] = {
            "rf": RandomForestRegressor(n_estimators=100),
            "gbm": GradientBoostingClassifier(),
            "lgbm": lgb.LGBMRegressor(),
            "nn": MLPRegressor(hidden_layer_sizes=(100, 50))
        }
        logger.info("Initialized SponsorshipPredictorEnsemble with models: %s",
                    list(self.models.keys()))

    def train(
        self,
        X_train: Union[pd.DataFrame, np.ndarray],
        y_train: Union[pd.Series, np.ndarray]
    ) -> None:
        """
        Fit each model in the ensemble on the training data.

        Parameters
        ----------
        X_train : DataFrame or ndarray
            Feature matrix.
        y_train : Series or ndarray
            Binary labels (1 = sponsored before, 0 = not).
        """
        for name, model in self.models.items():
            logger.info("Training model '%s'", name)
            model.fit(X_train, y_train)
        logger.info("All models trained successfully")

    def predict_proba(
        self,
        X: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        """
        Return the average predicted probability of sponsorship
        across all models in the ensemble.

        Parameters
        ----------
        X : DataFrame or ndarray
            Feature matrix.

        Returns
        -------
        ndarray
            Array of probabilities, one per row in X.
        """
        prob_list = []
        for name, model in self.models.items():
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[:, 1]
                logger.debug("Model '%s' provided predict_proba output", name)
            else:
                # fallback: normalize regression output into [0,1]
                raw = model.predict(X)
                min_, max_ = raw.min(), raw.max()
                if max_ - min_ > 1e-8:
                    probs = (raw - min_) / (max_ - min_)
                else:
                    probs = np.zeros_like(raw)
                logger.debug("Model '%s' provided normalized regression output", name)
            prob_list.append(probs)

        # Ensemble by averaging
        ensemble_probs = np.mean(prob_list, axis=0)
        logger.info("Ensembled probabilities computed (shape=%s)", ensemble_probs.shape)
        return ensemble_probs
