#!/usr/bin/env python3
"""
models/entities.py
------------------
Domain entity classes for SponsorMatch AI with proper SQLAlchemy ORM mappings.
"""

from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Association(Base):
    """
    Represents a sports club/association as stored in the `associations` table.
    """
    __tablename__ = 'associations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120))
    member_count = Column(Integer)
    address = Column(String(255))
    lat = Column(Float)
    lon = Column(Float)
    size_bucket = Column(Enum('small', 'medium', 'large'))
    founded_year = Column(Integer)


class Company(Base):
    """
    Represents a company as stored in the `companies` table.
    """
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    orgnr = Column(String(10))
    name = Column(String(200))
    revenue_ksek = Column(Float)
    employees = Column(Integer)
    year = Column(Integer)
    size_bucket = Column(Enum('small', 'medium', 'large'))
    industry = Column(String(120))
    lat = Column(Float)
    lon = Column(Float)


# Legacy dataclasses for backward compatibility
from dataclasses import dataclass
from typing import Optional


@dataclass
class Club:
    """
    Legacy dataclass representation of a sports club.
    Use Association ORM model for database operations.
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
    Legacy dataclass representation of a company.
    Use Company ORM model for database operations.
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