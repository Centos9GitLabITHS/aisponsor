# debug/search_issue_debugger.py
"""
Search Issue Debugger for SponsorMatchAI

This script helps diagnose the specific search/filter issue you're experiencing.
It traces through the search process step by step, logging what happens at each stage.

Usage: python debug/search_issue_debugger.py

This debugger is specifically designed for your app's architecture where entities
are dataclasses, not SQLAlchemy ORM models.
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure detailed logging
log_file = Path(__file__).parent / f"search_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Disable other loggers to reduce noise
for logger_name in ['matplotlib', 'PIL', 'urllib3', 'sqlalchemy', 'mysql']:
    logging.getLogger(logger_name).setLevel(logging.WARNING)


class SearchDebugger:
    """
    A systematic debugger for the search functionality.
    We'll trace through each step and log everything that happens.
    """

    def __init__(self):
        self.steps_completed = []
        self.data_snapshots = {}
        self.errors = []

    def log_step(self, step_name, success=True, data=None, error=None):
        """Log the result of each debugging step"""
        step_info = {
            'name': step_name,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'error': str(error) if error else None
        }

        self.steps_completed.append(step_info)

        if data is not None:
            self.data_snapshots[step_name] = data

        if success:
            logger.info(f"✓ {step_name} completed successfully")
        else:
            logger.error(f"✗ {step_name} failed: {error}")
            self.errors.append((step_name, error))

    def debug_config_and_connection(self):
        """Step 1: Check configuration and database connection"""
        logger.info("=" * 60)
        logger.info("STEP 1: Testing Configuration and Database Connection")
        logger.info("=" * 60)

        try:
            from sponsor_match.core.config import Config
            logger.info(f"Config imported successfully")

            # Check what attributes Config actually has
            config_attrs = [attr for attr in dir(Config) if not attr.startswith('_')]
            logger.info(f"Config attributes: {config_attrs}")

            # Find database-related attributes
            db_attrs = [attr for attr in config_attrs if 'DB' in attr or 'DATABASE' in attr or 'MYSQL' in attr]
            logger.info(f"Database-related config: {db_attrs}")

            from sponsor_match.core.db import get_engine
            from sqlalchemy import text

            engine = get_engine()
            logger.info(f"Database engine created: {engine}")

            # Test connection with proper SQLAlchemy 2.0 syntax
            with engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                logger.info(f"Connected to MySQL version: {version}")

                # Get table list
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result]
                self.log_step("Database Connection", success=True,
                              data={'tables': tables, 'version': version})

        except Exception as e:
            self.log_step("Database Connection", success=False, error=e)
            traceback.print_exc()
            return False

        return True

    def debug_entity_loading(self):
        """Step 2: Test loading clubs and companies from database tables"""
        logger.info("=" * 60)
        logger.info("STEP 2: Testing Entity Loading")
        logger.info("=" * 60)

        try:
            from sponsor_match.core.db import get_engine
            from sponsor_match.models.entities import Club, Company
            from sqlalchemy import text

            engine = get_engine()

            with engine.connect() as conn:
                # Load clubs data using raw SQL
                logger.info("Loading clubs from database...")
                result = conn.execute(text("""
                    SELECT id, name, member_count, address, lat, lon, size_bucket, founded_year
                    FROM clubs
                """))

                clubs_data = result.fetchall()
                logger.info(f"Loaded {len(clubs_data)} clubs from database")

                # Create Club dataclasses
                clubs = []
                for row in clubs_data[:5]:  # Just first 5 for debugging
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
                    clubs.append(club)

                logger.info(f"Created {len(clubs)} Club dataclass instances")

                # Load companies data
                logger.info("Loading companies from database...")
                result = conn.execute(text("""
                    SELECT id, orgnr, name, revenue_ksek, employees, year, size_bucket, lat, lon, industry
                    FROM companies
                """))

                companies_data = result.fetchall()
                logger.info(f"Loaded {len(companies_data)} companies from database")

                # Check size distribution
                result = conn.execute(text("""
                    SELECT size_bucket, COUNT(*) as count
                    FROM companies
                    GROUP BY size_bucket
                """))
                size_dist = dict(result.fetchall())
                logger.info(f"Company size distribution: {size_dist}")

                self.log_step("Entity Loading", success=True,
                              data={'club_count': len(clubs_data),
                                    'company_count': len(companies_data),
                                    'size_distribution': size_dist})

        except Exception as e:
            self.log_step("Entity Loading", success=False, error=e)
            traceback.print_exc()
            return False

        return True

    def debug_service_layer(self):
        """Step 3: Test the service layer with proper initialization"""
        logger.info("=" * 60)
        logger.info("STEP 3: Testing Service Layer")
        logger.info("=" * 60)

        try:
            from sponsor_match.services.service_v2 import SponsorMatchService
            from sponsor_match.core.db import get_engine

            # Service requires db_engine and cluster_models
            engine = get_engine()

            # Try to load cluster models
            cluster_models = {}
            try:
                import pickle
                models_dir = project_root / "models" / "clusters"

                if models_dir.exists():
                    for model_file in models_dir.glob("*.pkl"):
                        with open(model_file, 'rb') as f:
                            size = model_file.stem
                            cluster_models[size] = pickle.load(f)
                    logger.info(f"Loaded {len(cluster_models)} cluster models")
                else:
                    logger.warning("Cluster models directory not found, using empty dict")
            except Exception as e:
                logger.warning(p
                "Could not load cluster models: {e}")

                # Initialize service
                service = SponsorMatchService(
                    db_engine=engine,
                    cluster_models=cluster_models
                )
                logger.info("Service instance created successfully")

                # List available methods
                methods = [method for method in dir(service) if not method.startswith('_')]
                logger.info(f"Available service methods: {methods}")

                self.log_step("Service Layer", success=True, data={'methods': methods})

            except Exception as e:
                self.log_step("Service Layer", success=False, error=e)
                traceback.print_exc()
                return False

            return True

        def debug_search_functionality(self):
            """Step 5: Debug the actual search/recommend functionality"""
            logger.info("=" * 60)
            logger.info("STEP 5: Testing Search/Recommendation Functionality")
            logger.info("=" * 60)

            try:
                from sponsor_match.services.service_v2 import SponsorMatchService
                from sponsor_match.core.db import get_engine
                from sponsor_match.models.entities import Club
                from sqlalchemy import text

                engine = get_engine()
                cluster_models = {}  # Empty for now

                # Get a test club
                with engine.connect() as conn:
                    result = conn.execute(text("""
                    SELECT id, name, member_count, address, lat, lon, size_bucket, founded_year
                    FROM clubs
                    LIMIT 1
                """))
                    club_data = result.fetchone()

                    if not club_data:
                        logger.error("No clubs found in database")
                        return False

                    # Create Club dataclass
                    club = Club(
                        id=club_data[0],
                        name=club_data[1],
                        member_count=club_data[2],
                        address=club_data[3],
                        lat=club_data[4],
                        lon=club_data[5],
                        size_bucket=club_data[6],
                        founded_year=club_data[7]
                    )

                    logger.info(f"Testing with club: {club.name} (ID: {club.id})")

                    # Create service
                    service = SponsorMatchService(
                        db_engine=engine,
                        cluster_models=cluster_models
                    )

                    # Try to call the recommend method
                    try:
                        logger.info("Calling service.recommend()...")
                        recommendations = service.recommend(club.id)
                        logger.info(
                            f"Got {len(recommendations) if hasattr(recommendations, '__len__') else '?'} recommendations")
                        self.log_step("Search Functionality", success=True,
                                      data={'method': 'recommend',
                                            'club_id': club.id})
                    except Exception as e:
                        logger.error(f"Error in recommend: {e}")
                        traceback.print_exc()
                        self.log_step("Search Functionality", success=False, error=e)

            except Exception as e:
                self.log_step("Search Functionality", success=False, error=e)
                traceback.print_exc()
                return False

            return True

        def debug_ui_search_flow(self):
            """Step 6: Debug how the UI search flow works"""
            logger.info("=" * 60)
            logger.info("STEP 6: Testing UI Search Flow")
            logger.info("=" * 60)

            try:
                from sponsor_match.ui.app_v2 import SponsorMatchUI

                # Create UI instance
                ui = SponsorMatchUI()
                logger.info("UI instance created")

                # The UI has these attributes based on test output
                logger.info(f"UI engine: {ui.engine}")
                logger.info(f"UI clubs_df type: {type(ui.clubs_df)}")

                # Try to understand how search works in the UI
                # Look for search-related methods
                ui_methods = [method for method in dir(ui) if not method.startswith('_')]
                search_methods = [m for m in ui_methods if any(keyword in m.lower()
                                                               for keyword in
                                                               ['search', 'filter', 'recommend', 'match'])]
                logger.info(f"Search-related UI methods: {search_methods}")

                # The main page rendering
                if hasattr(ui, 'render_main_page'):
                    logger.info("UI has render_main_page method")
                    # We can't actually call it without Streamlit context, but we know it exists

                self.log_step("UI Search Flow", success=True)

            except Exception as e:
                self.log_step("UI Search Flow", success=False, error=e)
                traceback.print_exc()
                return False

            return True

        def generate_report(self):
            """Generate a comprehensive debug report"""
            logger.info("=" * 60)
            logger.info("DEBUG REPORT SUMMARY")
            logger.info("=" * 60)

            # Summary of steps
            successful_steps = [step for step in self.steps_completed if step['success']]
            failed_steps = [step for step in self.steps_completed if not step['success']]

            logger.info(f"Successful steps: {len(successful_steps)}")
            logger.info(f"Failed steps: {len(failed_steps)}")

            if failed_steps:
                logger.error("\nFailed steps:")
                for step in failed_steps:
                    logger.error(f"  - {step['name']}: {step['error']}")

            # Save detailed report
            report = {
                'timestamp': datetime.now().isoformat(),
                'steps': self.steps_completed,
                'errors': [(name, str(error)) for name, error in self.errors],
                'data_snapshots': {k: v for k, v in self.data_snapshots.items()
                                   if isinstance(v, (dict, list, str, int, float))}
            }

            report_file = Path(__file__).parent / f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"\nDetailed report saved to: {report_file}")
            logger.info(f"Log file: {log_file}")

            # Specific diagnosis for the search issue
            logger.info("\nSpecific recommendations for the search/filter issue:")
            logger.info("1. Check the UI's render_main_page method for the search logic")
            logger.info("2. Verify how the UI calls the service.recommend() method")
            logger.info("3. Check if filters are properly passed from UI to service")
            logger.info("4. Look for any try/catch blocks that might be hiding errors")
            logger.info("5. Add logging to the exact point where search is triggered in the UI")

    def main():
        """Run the complete debugging process"""
        print("SponsorMatchAI Search Issue Debugger")
        print("=" * 40)
        print(f"Starting debug at: {datetime.now()}")
        print(f"Log file: {log_file}")
        print("=" * 40)

        debugger = SearchDebugger()

        # Run all debug steps
        steps = [
            ('Configuration and Database', debugger.debug_config_and_connection),
            ('Entity Loading', debugger.debug_entity_loading),
            ('Service Layer', debugger.debug_service_layer),
            ('Search Functionality', debugger.debug_search_functionality),
            ('UI Search Flow', debugger.debug_ui_search_flow)
        ]

        for step_name, step_function in steps:
            print(f"\nRunning: {step_name}...")
            success = step_function()

            if not success:
                print(f"Warning: {step_name} had issues")
                print("Continuing to gather more information...")

        # Generate final report
        debugger.generate_report()

        print("\n" + "=" * 40)
        print("Debug session complete!")
        print(f"Check the log file for details: {log_file}")
        print("=" * 40)

    if __name__ == "__main__":
        main()
