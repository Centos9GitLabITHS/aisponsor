#!/usr/bin/env python3
"""
sponsor_match/models/entities.py
--------------------------------
Domain entity classes for SponsorMatch AI using SQLAlchemy ORM.
"""

from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Association(Base):
    """
    Represents an association (club) in the database.
    """
    __tablename__ = 'associations'

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(120))
    member_count  = Column(Integer)
    address       = Column(String(255))
    lat           = Column(Float)
    lon           = Column(Float)
    size_bucket   = Column(Enum('small', 'medium', 'large'))
    founded_year  = Column(Integer)

class Company(Base):
    """
    Represents a company in the database.
    """
    __tablename__ = 'companies'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    orgnr       = Column(String(10))
    name        = Column(String(200))
    revenue_ksek= Column(Float)
    employees   = Column(Integer)
    year        = Column(Integer)
    size_bucket = Column(Enum('small', 'medium', 'large'))
    industry    = Column(String(120))
    lat         = Column(Float)
    lon         = Column(Float)

# Legacy dataclasses for backward compatibility
from dataclasses import dataclass
from typing import Optional

@dataclass
class Club:
    """
    Legacy dataclass for an association (club).
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
class CompanyData:
    """
    Legacy dataclass for a company.
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
