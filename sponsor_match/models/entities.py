#!/usr/bin/env python3
"""
models/entities.py
------------------
Domain entity classes for SponsorMatch AI.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Club:
    """
    Represents a sports club as loaded from the `clubs` table.
    """
    id: int
    name: str
    member_count: int
    address: str
    lat: Optional[float]
    lon: Optional[float]
    size_bucket: str
    founded_year: int


@dataclass
class Company:
    """
    Represents a company as loaded from the `companies` table.
    """
    id: int
    orgnr: str
    name: str
    revenue_ksek: float
    employees: int
    year: int
    size_bucket: str
    lat: Optional[float]
    lon: Optional[float]
    industry: str
