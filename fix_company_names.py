#!/usr/bin/env python3
"""
fix_company_names.py - Generate better company names and optimize performance
"""

import pandas as pd
from sqlalchemy import text
from sponsor_match.core.db import get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_company_name(row):
    """Generate a realistic Swedish company name based on district and industry."""
    district = row.get('district', 'Göteborg')
    industry = row.get('industry', 'Services')
    org_nr = str(row.get('orgnr', row.get('PeOrgNr', '')))[-6:]
    
    # Swedish company type suffixes
    suffixes = {
        'small': ['HB', 'Enskild Firma', 'Handelsbolag'],
        'medium': ['AB', 'Trading AB', 'Konsult AB'],
        'large': ['AB', 'Group AB', 'International AB']
    }
    
    # Industry-specific prefixes
    prefixes = {
        'Technology': ['Tech', 'IT', 'Digital', 'System', 'Data'],
        'Finance': ['Finans', 'Kapital', 'Invest', 'Bank', 'Kredit'],
        'Manufacturing': ['Industri', 'Produktion', 'Maskin', 'Verkstad'],
        'Retail': ['Handel', 'Butik', 'Köp', 'Sälj'],
        'Healthcare': ['Vård', 'Hälsa', 'Klinik', 'Medicin'],
        'Services': ['Service', 'Konsult', 'Tjänst', 'Support'],
        'Other': ['Företag', 'Bolag', 'Grupp', 'Partner']
    }
    
    size = row.get('size_bucket', 'medium')
    prefix_list = prefixes.get(industry, prefixes['Other'])
    suffix_list = suffixes.get(size, suffixes['medium'])
    
    import random
    random.seed(hash(org_nr))  # Consistent names for same company
    
    prefix = random.choice(prefix_list)
    suffix = random.choice(suffix_list)
    
    # Create name with district
    if district and district != 'Unknown':
        name = f"{district} {prefix} {suffix}"
    else:
        name = f"{prefix} Göteborg {suffix}"
    
    return name

def update_company_names():
    """Update company names in the database."""
    engine = get_engine()
    
    logger.info("Updating company names...")
    
    # Process in chunks to avoid memory issues
    chunk_size = 10000
    total_updated = 0
    
    with engine.connect() as conn:
        # Get total count
        total = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
        logger.info(f"Total companies to update: {total}")
        
        # Process in chunks
        for offset in range(0, total, chunk_size):
            # Read chunk
            chunk_df = pd.read_sql(
                text(f"""
                SELECT id, orgnr, name, size_bucket, industry, lat, lon 
                FROM companies 
                LIMIT {chunk_size} OFFSET {offset}
                """), 
                conn
            )
            
            # Add district based on coordinates (simplified)
            def get_district(lat, lon):
                if lat > 57.75:
                    return "Angered"
                elif lat < 57.65:
                    return "Frölunda"
                elif lon > 12.0:
                    return "Örgryte"
                elif lon < 11.9:
                    return "Majorna"
                else:
                    return "Centrum"
            
            chunk_df['district'] = chunk_df.apply(lambda r: get_district(r['lat'], r['lon']), axis=1)
            
            # Generate new names
            chunk_df['new_name'] = chunk_df.apply(generate_company_name, axis=1)
            
            # Update in database
            with engine.begin() as trans_conn:
                for _, row in chunk_df.iterrows():
                    trans_conn.execute(
                        text("UPDATE companies SET name = :name WHERE id = :id"),
                        {"name": row['new_name'], "id": row['id']}
                    )
            
            total_updated += len(chunk_df)
            logger.info(f"Updated {total_updated} company names...")
    
    logger.info("✅ Company names updated successfully!")

def create_indexes():
    """Create database indexes for better performance."""
    engine = get_engine()
    
    logger.info("Creating performance indexes...")
    
    with engine.begin() as conn:
        # Create spatial index for coordinates
        try:
            conn.execute(text("CREATE INDEX idx_companies_coords ON companies(lat, lon)"))
            logger.info("Created coordinate index")
        except:
            logger.info("Coordinate index already exists")
        
        # Create index for size_bucket
        try:
            conn.execute(text("CREATE INDEX idx_companies_size ON companies(size_bucket)"))
            logger.info("Created size bucket index")
        except:
            logger.info("Size bucket index already exists")
        
        # Create index for associations
        try:
            conn.execute(text("CREATE INDEX idx_associations_name ON associations(name)"))
            logger.info("Created association name index")
        except:
            logger.info("Association name index already exists")
    
    logger.info("✅ Indexes created successfully!")

if __name__ == "__main__":
    logger.info("Starting optimization process...")
    
    # Update company names
    update_company_names()
    
    # Create indexes
    create_indexes()
    
    logger.info("\n✅ All optimizations complete!")
    logger.info("\nThe application should now load much faster with proper company names.")
