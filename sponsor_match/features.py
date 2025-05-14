#!/usr/bin/env python3
"""
sponsor_match/features.py
--------------------------
Feature engineering utilities for SponsorMatch.

Functions:
- calculate_distance_km
- add_distance
- bucket_assoc_size
- make_pair_features
"""

from typing import Dict

import numpy as np
import pandas as pd
from geopy.distance import geodesic
from pandas import DataFrame


def calculate_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the geodesic distance in kilometers between two latitude/longitude points.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of the first point.
    lat2, lon2 : float
        Latitude and longitude of the second point.

    Returns
    -------
    float
        Distance in kilometers.
    """
    return geodesic((lat1, lon1), (lat2, lon2)).km


def add_distance(
    df: DataFrame,
    lat: float,
    lon: float,
    lat_col: str = "lat",
    lon_col: str = "lon",
    new_col: str = "distance_km",
) -> DataFrame:
    """
    Return a copy of `df` with a new column `new_col` representing the distance
    from the fixed point (`lat`, `lon`) to each row's (lat_col, lon_col).

    Parameters
    ----------
    df : DataFrame
        Input data with latitude/longitude columns.
    lat, lon : float
        Reference point coordinates.
    lat_col, lon_col : str, default "lat","lon"
        Column names in `df` for latitude and longitude.
    new_col : str, default "distance_km"
        Name of the output distance column.

    Returns
    -------
    DataFrame
        Copy of `df` with the added distance column.
    """
    df_copy = df.copy()
    df_copy[new_col] = df_copy.apply(
        lambda row: calculate_distance_km(
            lat, lon, row[lat_col], row[lon_col]
        ),
        axis=1,
    )
    return df_copy


def bucket_assoc_size(members: int) -> str:
    """
    Bucket a club's member count into 'small', 'medium', or 'large'.

    Parameters
    ----------
    members : int
        Number of members in the association.

    Returns
    -------
    str
        One of "small" (<200), "medium" (<1000), or "large" (>=1000).
    """
    if members < 200:
        return "small"
    if members < 1000:
        return "medium"
    return "large"


def make_pair_features(df: DataFrame) -> DataFrame:
    """
    Create a feature DataFrame for club–company pairs for the matching model.

    Expects in `df`:
      - 'club_lat', 'club_lon', 'company_lat', 'company_lon'
      - 'club_size', 'company_size'
      - 'revenue_ksek', 'employees'

    Returns:
      - distance_km: exact geodesic distance
      - size_match: 1.0 if same bucket, 0.5 if adjacent, else 0.0
      - rev_per_emp: revenue per employee
      - rev_per_emp_normalized: scaled to [0,1] if std > 0
      - distance_score: exp(−distance_km/50) decay
    """
    features: Dict[str, pd.Series] = {}

    # Distance feature
    if all(
        col in df.columns
        for col in ["club_lat", "club_lon", "company_lat", "company_lon"]
    ):
        features["distance_km"] = df.apply(
            lambda r: calculate_distance_km(
                r["club_lat"],
                r["club_lon"],
                r["company_lat"],
                r["company_lon"],
            ),
            axis=1,
        )

    # Size compatibility
    if "club_size" in df.columns and "company_size" in df.columns:
        size_map = {"small": 0, "medium": 1, "large": 2}

        def _size_score(row: pd.Series) -> float:
            a = size_map.get(row["club_size"], 0)
            b = size_map.get(row["company_size"], 0)
            if a == b:
                return 1.0
            if abs(a - b) == 1:
                return 0.5
            return 0.0

        features["size_match"] = df.apply(_size_score, axis=1)

    # Revenue per employee
    if "revenue_ksek" in df.columns and "employees" in df.columns:
        rev_per_emp = df["revenue_ksek"] * 1000 / df["employees"].clip(lower=1)
        features["rev_per_emp"] = rev_per_emp
        if rev_per_emp.std() > 0:
            features["rev_per_emp_normalized"] = (
                rev_per_emp - rev_per_emp.min()
            ) / (rev_per_emp.max() - rev_per_emp.min())

    # Exponential distance score
    if "distance_km" in features:
        features["distance_score"] = np.exp(-features["distance_km"] / 50)

    return pd.DataFrame(features)
