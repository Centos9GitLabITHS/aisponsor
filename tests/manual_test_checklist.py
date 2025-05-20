# tests/manual_test_checklist.py
"""
Manual Testing Checklist for SponsorMatchAI

This script provides a structured approach to manually test each component
of the application. It's like a doctor's checklist - we check vital signs
one by one to diagnose where the problem lies.

Usage: python tests/manual_test_checklist.py
"""

import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Color codes for terminal output to make results easy to read
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_header(test_name, test_number):
    """Print a formatted header for each test"""
    print(f"\n{Colors.BLUE}{'=' * 60}")
    print(f"TEST {test_number}: {test_name}")
    print(f"{'=' * 60}{Colors.END}")


def print_instruction(instruction):
    """Print instructions for manual testing"""
    print(f"{Colors.YELLOW}➤ {instruction}{Colors.END}")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_failure(message):
    """Print failure message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def wait_for_user():
    """Wait for user to press Enter"""
    input("\nPress Enter to continue...")


# Test 1: Environment and Dependencies
def test_environment():
    """
    Check if the Python environment is properly set up.
    This is like checking if all your tools are in the toolbox.
    """
    print_header("Environment and Dependencies Check", 1)

    print_instruction("Checking Python version...")
    import platform
    python_version = platform.python_version()
    print(f"Python version: {python_version}")

    # Check if version is 3.8 or higher
    major, minor = map(int, python_version.split('.')[:2])
    if major >= 3 and minor >= 8:
        print_success("Python version is compatible")
    else:
        print_failure(f"Python {python_version} might be too old. Consider upgrading to 3.8+")

    print_instruction("Checking required packages...")
    required_packages = [
        'streamlit',
        'pandas',
        'mysql-connector-python',
        'python-dotenv',
        'numpy',
        'sklearn',
        'sqlalchemy',
        'folium',
        'streamlit-folium'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if package == 'mysql-connector-python':
                __import__('mysql.connector')
            elif package == 'sklearn':
                __import__('sklearn')
            else:
                __import__(package.replace('-', '_'))
            print_success(f"{package} is installed")
        except ImportError:
            print_failure(f"{package} is NOT installed")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n{Colors.YELLOW}To install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}{Colors.END}")

    wait_for_user()


# Test 2: Check Project Structure
def test_project_structure():
    """
    Verify that the expected project structure exists.
    This helps us understand what modules are actually available.
    """
    print_header("Project Structure Check", 2)

    expected_paths = [
        "sponsor_match/core/config.py",
        "sponsor_match/core/db.py",
        "sponsor_match/models/entities.py",
        "sponsor_match/services/service_v2.py",
        "sponsor_match/ui/app_v2.py",
        "sponsor_match/data/ingest_associations.py",
    ]

    # Note: __init__.py might not exist in every directory
    optional_paths = [
        "sponsor_match/__init__.py",
    ]

    all_found = True
    for path in expected_paths:
        full_path = project_root / path
        if full_path.exists():
            print_success(f"Found: {path}")
        else:
            print_failure(f"Missing: {path}")
            all_found = False

    for path in optional_paths:
        full_path = project_root / path
        if full_path.exists():
            print_success(f"Found (optional): {path}")
        else:
            print(f"{Colors.YELLOW}Optional file missing: {path}{Colors.END}")

    if all_found:
        print_success("\nAll required files are present!")
    else:
        print_failure("\nSome required files are missing. Check your project structure.")

    wait_for_user()


# Test 3: Database Configuration and Connection
def test_database_config():
    """
    Test the database configuration and connection.
    This ensures we can talk to our data storage.
    """
    print_header("Database Configuration Test", 3)

    try:
        print_instruction("Importing configuration...")
        from sponsor_match.core.config import Config
        print_success("Config imported successfully")

        print_instruction("Checking configuration attributes...")
        config_attrs = [attr for attr in dir(Config) if not attr.startswith('_')]
        print(f"Config attributes: {', '.join(config_attrs)}")

        # Look for database-related configuration
        db_attrs = [attr for attr in config_attrs if 'DB' in attr or 'DATABASE' in attr or 'MYSQL' in attr]
        if db_attrs:
            print_success(f"Found database config: {', '.join(db_attrs)}")
        else:
            print_failure("No database configuration attributes found")

        print_instruction("\nTesting database connection...")
        from sponsor_match.core.db import get_engine
        from sqlalchemy import text

        try:
            engine = get_engine()
            print_success("Database engine created successfully")

            # Test actual connection with proper SQLAlchemy 2.0 syntax
            with engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.fetchone()[0]
                print_success(f"Connected to MySQL version: {version}")

                # Check tables
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result]
                print(f"\nTables found: {len(tables)}")
                for table in tables:
                    print(f"  - {table}")

        except Exception as e:
            print_failure(f"Database connection failed: {e}")
            print("\nTroubleshooting steps:")
            print("1. Check if MySQL is running")
            print("2. Check your database credentials")
            print("3. Ensure the database exists")

    except ImportError as e:
        print_failure(f"Import error: {e}")
        print("Check if the module paths are correct")
    except Exception as e:
        print_failure(f"Configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    wait_for_user()


# Test 4: Entity Models (Dataclasses)
def test_entity_models():
    """
    Test that the entity models (Club and Company) are properly defined.
    These are the core data structures of your application.
    """
    print_header("Entity Models Test", 4)

    try:
        print_instruction("Importing entity models...")
        from sponsor_match.models.entities import Club, Company
        print_success("Entities imported successfully")

        print_instruction("\nChecking Club model structure...")
        # Check if it's a dataclass or regular class
        if hasattr(Club, '__dataclass_fields__'):
            print_success("Club is a dataclass")
            fields = Club.__dataclass_fields__.keys()
            print(f"Club fields: {', '.join(fields)}")
        else:
            # It's a regular class with required parameters
            print("Club is a regular class")
            # Try to inspect the __init__ method
            import inspect
            sig = inspect.signature(Club.__init__)
            params = [p for p in sig.parameters.keys() if p != 'self']
            print(f"Club parameters: {', '.join(params)}")

        print_instruction("\nChecking Company model structure...")
        if hasattr(Company, '__dataclass_fields__'):
            print_success("Company is a dataclass")
            fields = Company.__dataclass_fields__.keys()
            print(f"Company fields: {', '.join(fields)}")
        else:
            print("Company is a regular class")
            sig = inspect.signature(Company.__init__)
            params = [p for p in sig.parameters.keys() if p != 'self']
            print(f"Company parameters: {', '.join(params)}")

        # Since these aren't SQLAlchemy models, we can't query them directly
        print_instruction("\nTesting data loading through table queries...")
        from sponsor_match.core.db import get_engine
        import sqlalchemy

        engine = get_engine()
        with engine.connect() as conn:
            # Query clubs table directly
            result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM clubs"))
            club_count = result.scalar()
            print_success(f"Found {club_count} clubs in database")

            # Query companies table directly
            result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM companies"))
            company_count = result.scalar()
            print_success(f"Found {company_count} companies in database")

            # Get sample data
            if club_count > 0:
                result = conn.execute(sqlalchemy.text("SELECT name FROM clubs LIMIT 1"))
                sample_club = result.fetchone()
                print(f"Sample club: {sample_club[0]}")

            if company_count > 0:
                result = conn.execute(sqlalchemy.text("SELECT name FROM companies LIMIT 1"))
                sample_company = result.fetchone()
                print(f"Sample company: {sample_company[0]}")

    except Exception as e:
        print_failure(f"Entity models test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    wait_for_user()


# Test 5: Distance Calculation
def test_distance_calculation():
    """
    Test the distance calculation functionality.
    This is crucial for finding nearby sponsors.
    """
    print_header("Distance Calculation Test", 5)

    try:
        # The distance function exists in features module
        print_instruction("Importing distance calculation function...")
        from sponsor_match.models.features import FeatureEngineer
        print_success("Found calculate_distance_km in features module")

        print_instruction("\nTesting distance calculation with known points...")

        # Gothenburg city center
        lat1, lon1 = 57.7089, 11.9746
        # Nearby location (about 1.3 km away)
        lat2, lon2 = 57.7200, 11.9800

        distance = FeatureEngineer.calculate_distance_km(lat1, lon1, lat2, lon2)

        print(f"Point 1: ({lat1}, {lon1}) - City center")
        print(f"Point 2: ({lat2}, {lon2})")
        print(f"Calculated distance: {distance:.2f} km")

        # Verify the result is reasonable
        if 1.0 <= distance <= 1.5:
            print_success("Distance calculation seems correct!")
        else:
            print_failure(f"Distance {distance:.2f} km seems incorrect (expected ~1.3 km)")

    except Exception as e:
        print_failure(f"Distance calculation test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    wait_for_user()


# Test 6: Service Layer
def test_service_layer():
    """
    Test the service layer that handles the business logic.
    This is where the matching actually happens.
    """
    print_header("Service Layer Test", 6)

    try:
        print_instruction("Importing SponsorMatchService...")
        from sponsor_match.services.service_v2 import SponsorMatchService
        print_success("SponsorMatchService imported successfully")

        print_instruction("\nUnderstanding service requirements...")
        import inspect
        sig = inspect.signature(SponsorMatchService.__init__)
        params = [p for p in sig.parameters.keys() if p != 'self']
        print(f"SponsorMatchService requires: {', '.join(params)}")

        print_instruction("\nCreating service with required parameters...")
        from sponsor_match.core.db import get_engine

        # The service needs db_engine and cluster_models
        engine = get_engine()

        # Check if cluster models are available
        try:
            # This is likely where the trained models are stored
            import pickle
            import os

            models_dir = project_root / "models" / "clusters"
            if models_dir.exists():
                cluster_models = {}
                for model_file in models_dir.glob("*.pkl"):
                    with open(model_file, 'rb') as f:
                        size = model_file.stem  # e.g., 'small', 'medium', 'large'
                        cluster_models[size] = pickle.load(f)
                print_success(f"Loaded {len(cluster_models)} cluster models")
            else:
                print_failure("Cluster models directory not found")
                cluster_models = {}  # Empty dict for testing
        except Exception as e:
            print(f"Could not load cluster models: {e}")
            cluster_models = {}

        # Create service instance
        service = SponsorMatchService(db_engine=engine, cluster_models=cluster_models)
        print_success("Service instance created successfully")

        # Check available methods
        methods = [method for method in dir(service) if not method.startswith('_')]
        print(f"\nAvailable service methods: {', '.join(methods)}")

    except Exception as e:
        print_failure(f"Service layer test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    wait_for_user()


# Test 7: Streamlit Interface
def test_streamlit_interface():
    """
    Test the Streamlit web interface.
    This checks if the UI can be imported and initialized.
    """
    print_header("Streamlit Interface Test", 7)

    try:
        print_instruction("Importing Streamlit UI...")
        from sponsor_match.ui.app_v2 import SponsorMatchUI
        print_success("SponsorMatchUI imported successfully")

        print_instruction("\nCreating UI instance...")
        ui = SponsorMatchUI()
        print_success("UI instance created")

        print_instruction("\nChecking UI attributes and methods...")
        # The UI has these attributes based on the test output
        attrs = [attr for attr in dir(ui) if not attr.startswith('_')]
        print(f"UI attributes/methods: {', '.join(attrs)}")

        # Check specific attributes we saw in the test output
        expected_attrs = ['clubs_df', 'engine', 'render_main_page']
        for attr in expected_attrs:
            if hasattr(ui, attr):
                print_success(f"Found expected attribute: {attr}")
            else:
                print_failure(f"Missing expected attribute: {attr}")

        print("\nTo fully test the interface:")
        print("1. Open a new terminal")
        print("2. Run: streamlit run sponsor_match/ui/app_v2.py")
        print("3. Check for any error messages")
        print("4. Try using the filters and search functionality")

    except ImportError as e:
        print_failure(f"Could not import Streamlit UI: {str(e)}")
    except Exception as e:
        print_failure(f"Streamlit interface test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    wait_for_user()


# Main test runner
def main():
    """
    Run all tests in sequence.
    This gives you a complete health check of your application.
    """
    print(f"{Colors.GREEN}SponsorMatchAI Manual Test Suite")
    print(f"{'=' * 60}{Colors.END}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    tests = [
        test_environment,
        test_project_structure,
        test_database_config,
        test_entity_models,
        test_distance_calculation,
        test_service_layer,
        test_streamlit_interface,
    ]

    for i, test in enumerate(tests, 1):
        try:
            test()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Test suite interrupted by user{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}Test {i} crashed: {str(e)}{Colors.END}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{Colors.GREEN}Test suite completed!")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")


if __name__ == "__main__":
    main()
