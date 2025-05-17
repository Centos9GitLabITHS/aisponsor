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
    sponsors with clubs, including geographic distance, size compatibility,
    industry affinity, and economic indicators.
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
            If any coordinates are None or not convertible to float.
        ValueError
            If coordinates are invalid for distance calculation.
        """
        # Add explicit None check to match test expectations
        if any(x is None for x in [lat1, lon1, lat2, lon2]):
            raise TypeError("Coordinates cannot be None")

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

    @staticmethod
    def calculate_distance(
            club_coords: pd.DataFrame,
            comp_coords: pd.DataFrame
    ) -> pd.Series:
        """
        Compute geodesic distance (km) between each club–company pair.

        This batch method is more efficient than applying calculate_distance_km
        individually when processing many pairs.

        Parameters
        ----------
        club_coords : DataFrame
            DataFrame with lat/lon columns for clubs
        comp_coords : DataFrame
            DataFrame with lat/lon columns for companies

        Returns
        -------
        Series
            Distances in kilometers, named "distance_km"

        Notes
        -----
        Both DataFrames must have the same length and matching rows.
        """
        if len(club_coords) != len(comp_coords):
            raise ValueError("Input DataFrames must have the same length")

        # Use vectorized calculation when possible, falling back to row-wise
        distances = [
            FeatureEngineer.calculate_distance_km(
                club_coords.iloc[i]["lat"],
                club_coords.iloc[i]["lon"],
                comp_coords.iloc[i]["lat"],
                comp_coords.iloc[i]["lon"]
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

        Parameters
        ----------
        club_sizes : Series
            Size categories for clubs (small/medium/large)
        comp_sizes : Series
            Size categories for companies (small/medium/large)

        Returns
        -------
        Series
            Compatibility scores between 0 and 1
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

        scores = [
            _score(c, p) for c, p in zip(club_sizes, comp_sizes)
        ]
        return pd.Series(scores, name="size_match")

    @staticmethod
    def calculate_industry_affinity(
            sport_types: pd.Series,
            industries: pd.Series
    ) -> pd.Series:
        """
        Calculate industry-sport affinity score.

        Returns 1.0 if any sport in a club's sport_types list appears
        in the company's industry description.

        Parameters
        ----------
        sport_types : Series
            Lists of sport types for each club
        industries : Series
            Industry descriptions for companies

        Returns
        -------
        Series
            Binary affinity scores (0.0 or 1.0)
        """

        def _affinity(sports, industry):
            if not isinstance(sports, list):
                return 0.0
            if not isinstance(industry, str):
                return 0.0
            return 1.0 if any(sp.lower() in industry.lower() for sp in sports) else 0.0

        affinities = [
            _affinity(s, i) for s, i in zip(sport_types, industries)
        ]
        return pd.Series(affinities, name="industry_sport_affinity")

    @staticmethod
    def calculate_growth_rate(
            companies_df: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate company growth rate.

        Currently a placeholder returning zeros; implement with actual
        growth calculation when time-series data becomes available.

        Parameters
        ----------
        companies_df : DataFrame
            Company data including relevant growth metrics

        Returns
        -------
        Series
            Growth rate scores
        """
        return pd.Series(0.0, index=companies_df.index, name="growth_rate")

    @staticmethod
    def urban_rural_compatibility(
            club_loc: pd.Series,
            comp_loc: pd.Series
    ) -> pd.Series:
        """
        Calculate location type compatibility.

        Returns 1.0 if club and company share the same location_type
        (e.g., both urban or both rural), 0.0 otherwise.

        Parameters
        ----------
        club_loc : Series
            Location types for clubs
        comp_loc : Series
            Location types for companies

        Returns
        -------
        Series
            Binary compatibility scores (0.0 or 1.0)
        """
        compat = [
            1.0 if cl == cp else 0.0
            for cl, cp in zip(club_loc, comp_loc)
        ]
        return pd.Series(compat, name="urban_rural_match")

    @classmethod
    def make_pair_features(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a feature DataFrame for club–company pairs for the matching model.

        This method is primarily used by the training pipeline. For production
        recommendations, use create_features() instead.

        Parameters
        ----------
        df : DataFrame
            DataFrame with club and company attributes merged into single rows.
            Required columns include:
              - 'club_lat', 'club_lon', 'company_lat', 'company_lon'
              - 'club_size', 'company_size'
              - 'revenue_ksek', 'employees'

        Returns
        -------
        DataFrame
            Features for each club-company pair:
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
                lambda r: cls.calculate_distance_km(
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

    def create_features(
            self,
            clubs_df: pd.DataFrame,
            companies_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Build a comprehensive feature DataFrame for each club–company pair.

        This is the primary method for generating features in the recommendation
        system, supporting a wider range of features than make_pair_features().

        Parameters
        ----------
        clubs_df : DataFrame
            Club data with equal rows to companies_df
        companies_df : DataFrame
            Company data with equal rows to clubs_df

        Expected columns include:
            ['lat','lon'], 'size_bucket', 'sport_types',
            'industry', 'revenue_ksek', 'employees',
            'founded_year', 'location_type'

        Returns
        -------
        DataFrame
            Complete feature set for ranking and recommendations
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

        # 4) Revenue per employee
        if "revenue_ksek" in companies_df.columns and "employees" in companies_df.columns:
            rev_per_emp = (
                    companies_df["revenue_ksek"] * 1000
                    / companies_df["employees"].clip(lower=1)
            )
            feats["rev_per_emp"] = rev_per_emp.rename("rev_per_emp")
            if rev_per_emp.std() > 0:
                norm = (rev_per_emp - rev_per_emp.min()) / (rev_per_emp.max() - rev_per_emp.min())
                feats["rev_per_emp_normalized"] = norm.rename("rev_per_emp_normalized")

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