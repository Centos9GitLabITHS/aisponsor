# tests/test_automated_suite.py
"""
Automated Test Suite for SponsorMatchAI

This test suite uses pytest to automatically verify all components of the application.
Since your entities are dataclasses (not SQLAlchemy models), we need to test
database queries differently.

To run: pytest tests/test_automated_suite.py -v
"""

import pytest
import sys
from pathlib import Path
from sponsor_match.models.features import FeatureEngineer
from unittest.mock import Mock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDatabaseConnection:
    """Test database connectivity and basic operations"""

    def test_database_engine_creation(self):
        """Test that we can create a database engine"""
        from sponsor_match.core.db import get_engine

        engine = get_engine()
        assert engine is not None
        assert 'mysql' in str(engine.url)

    def test_database_connection(self):
        """Test actual database connection"""
        from sponsor_match.core.db import get_engine
        from sqlalchemy import text

        engine = get_engine()
        with engine.connect() as conn:
            # Use text() for raw SQL in SQLAlchemy 2.0
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_table_queries(self):
        """Test querying tables directly since entities aren't ORM models"""
        from sponsor_match.core.db import get_engine
        from sqlalchemy import text

        engine = get_engine()
        with engine.connect() as conn:
            # Test clubs table
            result = conn.execute(text("SELECT COUNT(*) FROM clubs"))
            club_count = result.scalar()
            assert club_count >= 0

            # Test companies table
            result = conn.execute(text("SELECT COUNT(*) FROM companies"))
            company_count = result.scalar()
            assert company_count >= 0


class TestDistanceCalculation:
    """Test the geographic distance calculation functionality"""

    def test_distance_calculation_features(self):
        """Test distance calculation from features module"""
        # No need to import FeatureEngineer here, it's already at the top level

        # Test same location
        distance = FeatureEngineer.calculate_distance_km(57.7089, 11.9746, 57.7089, 11.9746)
        assert distance == 0

        # Test known distance
        distance = FeatureEngineer.calculate_distance_km(57.7089, 11.9746, 57.7200, 11.9800)
        assert 1.2 <= distance <= 1.4

    def test_distance_with_invalid_inputs(self):
        """Test distance calculation with edge cases"""
        # Test with zero values instead of None
        with pytest.raises(Exception):
            FeatureEngineer.calculate_distance_km(-1.0, 11.9746, 57.7200, 11.9800)


class TestServiceLayer:
    """Test the service layer functionality"""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine"""
        return Mock()

    @pytest.fixture
    def mock_cluster_models(self):
        """Create mock cluster models"""
        return {
            'small': Mock(),
            'medium': Mock(),
            'large': Mock()
        }

    def test_service_creation(self, mock_engine, mock_cluster_models):
        """Test that service can be instantiated with required parameters"""
        from sponsor_match.services.service_v2 import SponsorMatchService

        service = SponsorMatchService(
            db_engine=mock_engine,
            cluster_models=mock_cluster_models
        )
        assert service is not None
        assert service.db == mock_engine  # Changed from db_engine to db
        assert service.cluster_models == mock_cluster_models

    def test_service_methods(self, mock_engine, mock_cluster_models):
        """Test service methods exist"""
        from sponsor_match.services.service_v2 import SponsorMatchService

        service = SponsorMatchService(
            db_engine=mock_engine,
            cluster_models=mock_cluster_models
        )

        # Check for expected methods (note the leading underscore in _get_club_by_id)
        assert hasattr(service, '_get_club_by_id')  # Changed from get_club_by_id
        assert hasattr(service, 'recommend')


class TestModels:
    """Test the model classes (dataclasses)"""

    def test_club_entity_structure(self):
        """Test Club entity structure"""
        from sponsor_match.models.entities import Club

        # Test creating a club with all required parameters
        club = Club(
            id=1,
            name="Test FC",
            member_count=100,
            address="Test Street 1",
            lat=57.7089,
            lon=11.9746,
            size_bucket="medium",
            founded_year=2000
        )

        assert club.id == 1
        assert club.name == "Test FC"
        assert club.lat == 57.7089

    def test_company_entity_structure(self):
        """Test Company entity structure"""
        from sponsor_match.models.entities import Company

        # Test creating a company with all required parameters
        company = Company(
            id=1,
            orgnr="123456-7890",
            name="Test Company",
            revenue_ksek=1000,
            employees=50,
            year=2023,
            size_bucket="medium",
            lat=57.7089,
            lon=11.9746,
            industry="Technology"
        )

        assert company.id == 1
        assert company.name == "Test Company"
        assert company.size_bucket == "medium"

    def test_feature_engineer(self):
        """Test FeatureEngineer if available"""
        try:
            from sponsor_match.models.features import FeatureEngineer

            engineer = FeatureEngineer()
            # Just check it can be instantiated
            assert engineer is not None
        except ImportError:
            pytest.skip("FeatureEngineer not available")


class TestUI:
    """Test the UI components"""

    def test_ui_import(self):
        """Test that UI can be imported"""
        from sponsor_match.ui.app_v2 import SponsorMatchUI

        ui = SponsorMatchUI()
        assert ui is not None

    def test_ui_attributes(self):
        """Test UI has expected attributes"""
        from sponsor_match.ui.app_v2 import SponsorMatchUI

        ui = SponsorMatchUI()

        # Check for attributes we saw in the test output
        assert hasattr(ui, 'clubs_df')
        assert hasattr(ui, 'engine')
        assert hasattr(ui, 'render_main_page')


class TestDataIngestion:
    """Test data ingestion functionality"""

    def test_ingest_associations_import(self):
        """Test that ingest_associations can be imported"""
        from sponsor_match.data.ingest_associations import main
        assert main is not None

    def test_ingest_csv_import(self):
        """Test that ingest_csv can be imported"""
        from sponsor_match.data.ingest_csv import main
        assert main is not None


class TestIntegration:
    """Integration tests that test multiple components working together"""

    def test_database_to_dataclass_flow(self):
        """Test loading data from database into dataclass entities"""
        from sponsor_match.core.db import get_engine
        from sponsor_match.models.entities import Club
        from sqlalchemy import text

        engine = get_engine()
        with engine.connect() as conn:
            # Get a club from database
            result = conn.execute(text("""
                SELECT id, name, member_count, address, lat, lon, size_bucket, founded_year
                FROM clubs LIMIT 1
            """))
            row = result.fetchone()

            if row:
                # Create Club dataclass from database row
                club = Club(
                    id=row[0],
                    name=row[1],
                    member_count=row[2],
                    address=row[3],
                    lat=row[4],
                    lon=row[5],
                    size_bucket=row[6],
                    founded_year=row[7]
                )
                assert club.name == row[1]


class TestConfiguration:
    """Test configuration loading"""

    def test_config_import(self):
        """Test that config can be imported"""
        from sponsor_match.core.config import Config
        assert Config is not None

    def test_config_db_attributes(self):
        """Test that config has database-related attributes"""
        from sponsor_match.core.config import Config

        # Check for any database-related configuration
        config_attrs = dir(Config)
        db_attrs = [attr for attr in config_attrs if 'DB' in attr or 'DATABASE' in attr]
        assert len(db_attrs) > 0


class TestPerformance:
    """Test performance characteristics of the application"""

    def test_database_query_performance(self):
        """Test that database queries perform reasonably"""
        import time
        from sponsor_match.core.db import get_engine
        from sqlalchemy import text

        engine = get_engine()
        with engine.connect() as conn:
            start_time = time.time()
            result = conn.execute(text("SELECT * FROM companies LIMIT 100"))
            companies = result.fetchall()
            end_time = time.time()

            # Query should complete in less than 1 second
            assert end_time - start_time < 1.0
            assert len(companies) <= 100


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

