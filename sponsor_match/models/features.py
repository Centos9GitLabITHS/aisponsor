#!/usr/bin/env python3
"""
sponsor_match/models/features.py
--------------------------------
Feature engineering for SponsorMatch ML models.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict

from geopy.distance import geodesic


class FeatureEngineer:
    """
    Compute pairwise features between a club and company DataFrame
    suitable for training/ranking sponsor recommendations.
    """

    @staticmethod
    def calculate_distance(
            club_coords: pd.DataFrame,
        comp_coords: pd.DataFrame
    ) -> pd.Series:
        """
        Compute geodesic distance (km) between each club–company pair.
        Expects both DataFrames to have the same length and columns ['lat','lon'].
        """
        def _dist(c, p):
            return geodesic((c[0], c[1]), (p[0], p[1])).km

        distances = [
            _dist(club_coords.iloc[i], comp_coords.iloc[i])
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
            a, b = size_map.get(cs, 0), size_map.get(ps, 0)
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
        Crude affinity: 1.0 if any sport in `sport_types` appears in industry string.
        """
        def _affinity(sports, industry):
            if not isinstance(sports, list):
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
        Placeholder for growth-rate feature.
        Currently returns zeros; implement as needed.
        """
        return pd.Series(0.0, index=companies_df.index, name="growth_rate")

    @staticmethod
    def urban_rural_compatibility(
            club_loc: pd.Series,
        comp_loc: pd.Series
    ) -> pd.Series:
        """
        1.0 if club and company share the same location_type, else 0.0.
        """
        compat = [
            1.0 if cl == cp else 0.0
            for cl, cp in zip(club_loc, comp_loc)
        ]
        return pd.Series(compat, name="urban_rural_match")

    def create_features(
        self,
        clubs_df: pd.DataFrame,
        companies_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Build a DataFrame of features for each club–company pair.

        Expects:
         - clubs_df & companies_df of equal length
         - Columns:
           ['lat','lon'], 'size_bucket', 'sport_types',
           'industry', 'revenue_ksek', 'employees',
           'founded_year', 'location_type'
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
