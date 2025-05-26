#!/usr/bin/env python3
"""
optimize_database.py - Add indexes and optimize database for performance
"""

from sqlalchemy import text
from golden_goal.core.db import get_engine


def optimize_database():
    """Add indexes for better query performance."""
    engine = get_engine()

    with engine.connect() as conn:
        # Add indexes for associations
        print("Adding indexes for associations table...")
        try:
            conn.execute(text("CREATE INDEX idx_assoc_name ON associations(name)"))
            conn.execute(text("CREATE INDEX idx_assoc_coords ON associations(lat, lon)"))
            conn.execute(text("CREATE INDEX idx_assoc_size ON associations(size_bucket)"))
            conn.commit()
            print("✅ Association indexes created")
        except Exception as e:
            if "Duplicate" not in str(e):
                print(f"⚠️ Error creating association indexes: {e}")

        # Add indexes for companies
        print("\nAdding indexes for companies table...")
        try:
            conn.execute(text("CREATE INDEX idx_comp_name ON companies(name)"))
            conn.execute(text("CREATE INDEX idx_comp_coords ON companies(lat, lon)"))
            conn.execute(text("CREATE INDEX idx_comp_size ON companies(size_bucket)"))
            conn.execute(text("CREATE INDEX idx_comp_industry ON companies(industry)"))

            # Spatial index for distance queries
            conn.execute(text("""
                              CREATE INDEX idx_comp_spatial ON companies (lat, lon) WHERE lat IS NOT NULL AND lon IS NOT NULL
                              """))
            conn.commit()
            print("✅ Company indexes created")
        except Exception as e:
            if "Duplicate" not in str(e):
                print(f"⚠️ Error creating company indexes: {e}")

        # Add full-text search indexes (MySQL specific)
        print("\nAdding full-text search indexes...")
        try:
            conn.execute(text("CREATE FULLTEXT INDEX ft_assoc_name ON associations(name)"))
            conn.execute(text("CREATE FULLTEXT INDEX ft_comp_name ON companies(name)"))
            conn.commit()
            print("✅ Full-text indexes created")
        except Exception as e:
            if "Duplicate" not in str(e) and "doesn't support" not in str(e):
                print(f"⚠️ Error creating full-text indexes: {e}")

        # Analyze tables for optimization
        print("\nOptimizing tables...")
        try:
            conn.execute(text("ANALYZE TABLE associations"))
            conn.execute(text("ANALYZE TABLE companies"))
            conn.commit()
            print("✅ Tables optimized")
        except Exception as e:
            print(f"⚠️ Error optimizing tables: {e}")

        # Show current indexes
        print("\nCurrent indexes:")
        for table in ['associations', 'companies']:
            indexes = conn.execute(text(f"SHOW INDEXES FROM {table}")).fetchall()
            print(f"\n{table}:")
            for idx in indexes:
                print(f"  - {idx[2]} on {idx[4]}")


if __name__ == "__main__":
    optimize_database()
