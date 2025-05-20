#!/usr/bin/env python3
"""
sponsor_match/models/features.py
--------------------------------
Feature engineering for SponsorMatch ML models.

This module provides comprehensive feature engineering capabilities for analyzing
and scoring potential sponsor-club matches based on multiple dimensions including
geographic proximity, size compatibility, and industry relevance.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict

from geopy.distance import geodesic


class FeatureEngineer:
    """
    Compute pairwise features between clubs and companies for recommendation ranking.

    This class contains methods for calculating various features used in matching
    sponsors with clubs, including geographic distance, size compatibility, industry
    affinity, and economic indicators.
    """

    @staticmethod
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

        Raises
        ------
        TypeError
            If any coordinates are None.
        ValueError
            If any coordinates are zero or negative, or otherwise invalid.
        """
        # 1) None check
        if any(x is None for x in (lat1, lon1, lat2, lon2)):
            raise TypeError("Coordinates cannot be None")

        # 2) Domain check: all lats/lons must be positive in our context
        if any(v <= 0 for v in (lat1, lon1, lat2, lon2)):
            raise ValueError(f"Invalid coordinates for distance calculation: {(lat1, lon1, lat2, lon2)}")

        try:
            return geodesic((lat1, lon1), (lat2, lon2)).km
        except (ValueError, TypeError) as e:
            # Re-raise with more descriptive message
            raise type(e)(f"Invalid coordinates for distance calculation: {e}")

    @staticmethod
    def add_distance(
        df: pd.DataFrame,
        lat: float,
        lon: float,
        lat_col: str = "lat",
        lon_col: str = "lon",
        new_col: str = "distance_km",
    ) -> pd.DataFrame:
        """
        Return a copy of `df` with a new column `new_col` representing the distance
        from the fixed point (`lat`, `lon`) to each row's (lat_col, lon_col).
        """
        df_copy = df.copy()
        df_copy[new_col] = df_copy.apply(
            lambda row: FeatureEngineer.calculate_distance_km(
                lat, lon, row[lat_col], row[lon_col]
            ),
            axis=1,
        )
        return df_copy

    @staticmethod
    def bucket_assoc_size(members: int) -> str:
        """
        Bucket a club's member count into 'small', 'medium', or 'large'.
        """
        if members < 200:
            return "small"
        if members < 1000:
            return "medium"
        return "large"

    @staticmethod
    def calculate_distance(
        club_coords: pd.DataFrame,
        comp_coords: pd.DataFrame
    ) -> pd.Series:
        """
        Compute geodesic distance (km) between each club–company pair (row-wise).
        """
        if len(club_coords) != len(comp_coords):
            raise ValueError("Input DataFrames must have the same length")

        distances = [
            FeatureEngineer.calculate_distance_km(
                club_coords.iloc[i]["lat"],
                club_coords.iloc[i]["lon"],
                comp_coords.iloc[i]["lat"],
                comp_coords.iloc[i]["lon"],
            )
            for i in range(len(club_coords))
        ]
        return pd.Series(distances, name="distance_km")

    @staticmethod
    def calculate_size_match(
        club_sizes: pd.Series,
        comp_sizes: pd.Series
    ) -> pd.Series:
        """
        Score size compatibility: exact match → 1.0; adjacent → 0.5; else → 0.0.
        """
        size_map = {"small": 0, "medium": 1, "large": 2}

        def _score(cs, ps):
            a = size_map.get(cs, 0)
            b = size_map.get(ps, 0)
            if a == b:
                return 1.0
            if abs(a - b) == 1:
                return 0.5
            return 0.0

        scores = [_score(c, p) for c, p in zip(club_sizes, comp_sizes)]
        return pd.Series(scores, name="size_match")

    @staticmethod
    def calculate_industry_affinity(
        sport_types: pd.Series,
        industries: pd.Series
    ) -> pd.Series:
        """
        Calculate industry-sport affinity score (0.0 or 1.0).
        """
        def _affinity(sports, industry):
            if not isinstance(sports, list) or not isinstance(industry, str):
                return 0.0
            return 1.0 if any(sp.lower() in industry.lower() for sp in sports) else 0.0

        affinities = [_affinity(s, i) for s, i in zip(sport_types, industries)]
        return pd.Series(affinities, name="industry_sport_affinity")

    @staticmethod
    def calculate_growth_rate(
        companies_df: pd.DataFrame
    ) -> pd.Series:
        """
        Placeholder for company growth rate; returns zeros until time-series data is available.
        """
        return pd.Series(0.0, index=companies_df.index, name="growth_rate")

    @staticmethod
    def urban_rural_compatibility(
        club_loc: pd.Series,
        comp_loc: pd.Series
    ) -> pd.Series:
        """
        Binary match if club and company share the same location_type.
        """
        compat = [1.0 if cl == cp else 0.0 for cl, cp in zip(club_loc, comp_loc)]
        return pd.Series(compat, name="urban_rural_match")

    @classmethod
    def make_pair_features(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a feature DataFrame for club–company pairs for the matching model.

        Returns features:
          - distance_km: exact geodesic distance
          - size_match: size compatibility score
          - revenue_ksek: raw revenue value (in tkr)
          - employees: raw employee count
          - distance_score: exp(-distance_km/50) decay
        """
        features: Dict[str, pd.Series] = {}

        # Distance
        if all(col in df.columns for col in ["club_lat", "club_lon", "company_lat", "company_lon"]):
            features["distance_km"] = df.apply(
                lambda r: cls.calculate_distance_km(
                    r["club_lat"], r["club_lon"],
                    r["company_lat"], r["company_lon"]
                ),
                axis=1
            )

        # Size compatibility
        if "club_size" in df.columns and "company_size" in df.columns:
            features["size_match"] = cls.calculate_size_match(
                df["club_size"], df["company_size"]
            )

        # Raw financial and headcount features
        if "revenue_ksek" in df.columns:
            features["revenue_ksek"] = df["revenue_ksek"].rename("revenue_ksek")
        if "employees" in df.columns:
            features["employees"] = df["employees"].rename("employees")

        # Exponential distance decay
        if "distance_km" in features:
            features["distance_score"] = np.exp(-features["distance_km"] / 50)

        return pd.DataFrame(features)

    def create_features(
        self,
        clubs_df: pd.DataFrame,
        companies_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Build a comprehensive feature set for each club–company pair.

        Returns features including:
          - distance_km, distance_score
          - size_match
          - industry_sport_affinity
          - revenue_ksek, employees
          - company_age
          - growth_rate
          - urban_rural_match
        """
        feats: Dict[str, pd.Series] = {}

        # 1) Distance & decay
        if {"lat", "lon"}.issubset(clubs_df.columns) and {"lat", "lon"}.issubset(companies_df.columns):
            club_coords = clubs_df[["lat", "lon"]]
            comp_coords = companies_df[["lat", "lon"]]
            feats["distance_km"] = self.calculate_distance(club_coords, comp_coords)
            feats["distance_score"] = np.exp(-feats["distance_km"] / 50)

        # 2) Size match
        if "size_bucket" in clubs_df.columns and "size_bucket" in companies_df.columns:
            feats["size_match"] = self.calculate_size_match(
                clubs_df["size_bucket"], companies_df["size_bucket"]
            )

        # 3) Industry affinity
        if "sport_types" in clubs_df.columns and "industry" in companies_df.columns:
            feats["industry_sport_affinity"] = self.calculate_industry_affinity(
                clubs_df["sport_types"], companies_df["industry"]
            )

        # 4) Raw financial & headcount
        if "revenue_ksek" in companies_df.columns:
            feats["revenue_ksek"] = companies_df["revenue_ksek"].rename("revenue_ksek")
        if "employees" in companies_df.columns:
            feats["employees"] = companies_df["employees"].rename("employees")

        # 5) Company age
        if "founded_year" in companies_df.columns:
            feats["company_age"] = (
                datetime.now().year - companies_df["founded_year"]
            ).rename("company_age")

        # 6) Growth rate
        if "employees" in companies_df.columns:
            feats["growth_rate"] = self.calculate_growth_rate(companies_df)

        # 7) Urban/rural match
        if "location_type" in clubs_df.columns and "location_type" in companies_df.columns:
            feats["urban_rural_match"] = self.urban_rural_compatibility(
                clubs_df["location_type"], companies_df["location_type"]
            )

        return pd.DataFrame(feats)
