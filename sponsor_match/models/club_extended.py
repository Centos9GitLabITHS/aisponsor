#!/usr/bin/env python3
"""
models/club_extended.py
------------------------
Extended data model for sports clubs, including enrichment fields
for membership, financials, and sponsorship details.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ExtendedClub:
    """
    Represents a sports club with both basic and enriched metadata.
    """

    # Basic info
    id: int
    name: str
    member_count: int
    address: str
    lat: Optional[float]
    lon: Optional[float]
    size_bucket: str

    # Extended basic info
    founded_year: int
    club_type: str
    registration_number: str
    website: str
    email: str
    phone: str
    social_media: Dict[str, str] = field(default_factory=dict)

    # Sports & activities
    sport_types: List[str] = field(default_factory=list)
    primary_sport: str = ""
    leagues: List[str] = field(default_factory=list)
    division_level: int = 0

    # Membership breakdown
    active_members: int = 0
    youth_members: int = 0
    gender_distribution: Dict[str, float] = field(default_factory=dict)
    membership_growth_rate: float = 0.0

    # Financials
    annual_revenue: float = 0.0
    sponsorship_revenue: float = 0.0
    financial_status: str = ""

    # Sponsorship history
    current_sponsors: List[str] = field(default_factory=list)
    sponsorship_packages: List[Dict[str, any]] = field(default_factory=list)
    sponsor_retention_rate: float = 0.0

    # Community engagement
    volunteer_count: int = 0
    fan_base_size: int = 0
    social_media_followers: Dict[str, int] = field(default_factory=dict)

    # Infrastructure
    owned_facilities: List[str] = field(default_factory=list)
    stadium_capacity: int = 0
    facility_conditions: Dict[str, str] = field(default_factory=dict)
