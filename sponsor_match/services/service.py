import logging

import pandas as pd
from sqlalchemy import text

from sponsor_match.core.config import LOG_LEVEL

# Remove the problematic entity imports for now
# from sponsor_match.models.entities import Club, Company

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(message)s"
)


def search(engine, query: str) -> pd.DataFrame:
    """Search both associations and companies by name."""
    # Use raw SQL instead of ORM for now
    sql = text("""
        SELECT 'association' AS type, id, name, address, lat as latitude, lon as longitude
        FROM associations
        WHERE name LIKE :q
        UNION ALL
        SELECT 'company' AS type, id, name, NULL AS address, lat as latitude, lon as longitude
        FROM companies
        WHERE name LIKE :q
        LIMIT 100
    """)
    df = pd.read_sql(sql, engine, params={"q": f"%{query}%"})
    return df


def recommend(engine, association_name: str, top_n: int = 10) -> pd.DataFrame:
    """Recommend sponsors for a given association."""
    # Get association info using raw SQL
    association_sql = text("SELECT id, name, lat, lon, size_bucket FROM associations WHERE name = :name")
    association = pd.read_sql(association_sql, engine, params={"name": association_name})

    if association.empty:
        logging.warning(f"No association found matching '{association_name}'")
        return pd.DataFrame()

    lat, lon = association.iloc[0][["lat", "lon"]]

    # Get companies using raw SQL
    company_sql = text("""
        SELECT id, name, lat, lon, size_bucket, revenue_ksek, employees, industry
        FROM companies
        WHERE lat IS NOT NULL AND lon IS NOT NULL
    """)
    companies = pd.read_sql(company_sql, engine)

    if companies.empty:
        logging.info("No companies found.")
        return pd.DataFrame()

    # Simple distance calculation (Euclidean approximation)
    companies["distance"] = (
                                    (companies["lat"] - lat) ** 2 +
                                    (companies["lon"] - lon) ** 2
                            ) ** 0.5

    return companies.sort_values("distance").head(top_n).reset_index(drop=True)
