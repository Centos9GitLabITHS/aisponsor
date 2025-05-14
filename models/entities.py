#!/usr/bin/env python3
"""
models/entities.py
------------------
Domain entity classes for SponsorMatch AI.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass(frozen=True)
class Club:
    """
    Basic representation of a sports club.
    """
    id: int
    name: str
    member_count: int
    address: str
    lat: Optional[float]
    lon: Optional[float]
    size_bucket: str
    founded_year: Optional[int]
    sport_types: List[str] = field(default_factory=list)
    youth_teams: int = 0


@dataclass(frozen=True)
class Company:
    """
    Basic representation of a company sponsor.
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
    previous_sponsorships: List[str] = field(default_factory=list)
