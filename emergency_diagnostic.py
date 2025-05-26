# Rapid troubleshooting script for common issues
# Detailed comments have been inserted in British English.

#!/usr/bin/env python3
"""
emergency_diagnostic.py - Rapid troubleshooting for SponsorMatch AI
Run this to diagnose and fix common issues
"""

# Standard library or third-party import
import subprocess
# Standard library or third-party import
import sys
# Standard library or third-party import
from pathlib import Path

# Color codes for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


# Definition of function 'print_status': explains purpose and parameters
def print_status(message, status='info'):
    """Print colored status messages"""
    if status == 'error':
        print(f"{RED}❌ {message}{RESET}")
    elif status == 'success':
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == 'warning':
        print(f"{YELLOW}⚠️  {message}{RESET}")
    else:
        print(f"{BLUE}ℹ️  {message}{RESET}")


# Definition of function 'check_python_version': explains purpose and parameters
def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} ✓", 'success')
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} - Need 3.8+", 'error')
        return False


# Definition of function 'check_required_packages': explains purpose and parameters
def check_required_packages():
    """Check and install required packages"""
    required = [
        'streamlit', 'pandas', 'numpy', 'folium', 'streamlit-folium',
        'sqlalchemy', 'pymysql', 'scikit-learn==1.5.0', 'geopy',
        'python-dotenv', 'plotly', 'joblib'
    ]

    missing = []
    for package in required:
        try:
            if package == 'streamlit-folium':
                __import__('streamlit_folium')
            else:
                __import__(package.split('==')[0])
        except ImportError:
            missing.append(package)

    if missing:
        print_status(f"Missing packages: {', '.join(missing)}", 'warning')
        print_status("Installing missing packages...", 'info')
        for pkg in missing:
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg],
                           capture_output=True)
        print_status("Packages installed", 'success')
    else:
        print_status("All required packages installed", 'success')

    return len(missing) == 0


# Definition of function 'check_data_files': explains purpose and parameters
def check_data_files():
    """Check if required data files exist"""
    data_files = {
        'associations_prepared.csv': 'Association data',
        'companies_prepared.csv': 'Company data',
        'associations_geocoded.csv': 'Geocoded associations',
        'companies_geocoded.csv': 'Geocoded companies'
    }

    data_dir = Path('data')
    missing_critical = []

    for file, desc in data_files.items():
        path = data_dir / file
        if path.exists():
            print_status(f"{desc}: {path} ✓", 'success')
        else:
            if 'prepared' in file:
                missing_critical.append(file)
            print_status(f"{desc}: {path} missing", 'warning')

    if missing_critical:
        print_status("Running data preparation script...", 'info')
        try:
            subprocess.run([sys.executable, 'prepare_all_data.py'], check=True)
            print_status("Data prepared successfully", 'success')
        except:
            print_status("Failed to prepare data", 'error')
            return False

    return True


# Definition of function 'check_database_connection': explains purpose and parameters
def check_database_connection():
    """Test database connection"""
    try:
# Standard library or third-party import
        from sponsor_match.core.db import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print_status("Database connection successful", 'success')

            # Check tables
# Standard library or third-party import
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if tables:
                print_status(f"Found tables: {', '.join(tables)}", 'info')
            else:
                print_status("No tables found - run setup_database.py", 'warning')
            return True
    except Exception as e:
        print_status(f"Database connection failed: {str(e)}", 'error')
        return False


# Definition of function 'fix_import_paths': explains purpose and parameters
def fix_import_paths():
    """Ensure project is in Python path"""
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print_status("Added project root to Python path", 'success')
    return True


# Definition of function 'check_models': explains purpose and parameters
def check_models():
    """Check if ML models exist"""
    models_dir = Path('models')
    required_models = ['kmeans.joblib', 'kmeans_large.joblib']

    if not models_dir.exists():
        models_dir.mkdir(exist_ok=True)
        print_status("Created models directory", 'info')

    missing_models = []
    for model in required_models:
        if not (models_dir / model).exists():
            missing_models.append(model)

    if missing_models:
        print_status(f"Missing models: {', '.join(missing_models)}", 'warning')
        print_status("Run: python retrain_clustering.py", 'info')
        return False
    else:
        print_status("All models present", 'success')
        return True


# Definition of function 'quick_app_test': explains purpose and parameters
def quick_app_test():
    """Test if the app can start"""
    print_status("Testing app startup...", 'info')

    # Check which app file exists
    app_files = [
        Path('sponsor_match/ui/simple_app.py'),
        Path('sponsor_match/ui/app.py'),
        Path('streamlit_app.py')
    ]

    for app_file in app_files:
        if app_file.exists():
            print_status(f"Found app file: {app_file}", 'success')
            return True

    print_status("No app file found!", 'error')
    return False


# Definition of function 'run_diagnostics': explains purpose and parameters
def run_diagnostics():
    """Run all diagnostic checks"""
    print(f"\n{BLUE}{'=' * 50}")
    print("🔧 SPONSORMATCH AI EMERGENCY DIAGNOSTIC")
    print(f"{'=' * 50}{RESET}\n")

    checks = [
        ("Python Version", check_python_version),
        ("Import Paths", fix_import_paths),
        ("Required Packages", check_required_packages),
        ("Data Files", check_data_files),
        ("Database Connection", check_database_connection),
        ("ML Models", check_models),
        ("App Files", quick_app_test)
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{BLUE}Checking {name}...{RESET}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_status(f"Check failed: {str(e)}", 'error')
            results.append((name, False))

    # Summary
    print(f"\n{BLUE}{'=' * 50}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'=' * 50}{RESET}\n")

    failed_checks = [name for name, result in results if not result]

    if not failed_checks:
        print_status("All checks passed! 🎉", 'success')
        print(f"\n{GREEN}Ready to run the app with:{RESET}")
        print(f"  {BLUE}python run_app.py{RESET}")
        print(f"  or")
        print(f"  {BLUE}streamlit run sponsor_match/ui/simple_app.py{RESET}")
    else:
        print_status(f"Failed checks: {', '.join(failed_checks)}", 'error')
        print(f"\n{YELLOW}Quick fixes:{RESET}")

        if "Database Connection" in failed_checks:
            print(f"  1. Check MySQL is running: {BLUE}sudo service mysql start{RESET}")
            print(f"  2. Verify credentials in .env file")
            print(f"  3. Run: {BLUE}python utils/setup_database.py{RESET}")

        if "ML Models" in failed_checks:
            print(f"  - Run: {BLUE}python retrain_clustering.py{RESET}")

        if "Data Files" in failed_checks:
            print(f"  - Run: {BLUE}python prepare_all_data.py{RESET}")

    # Emergency fallback
    print(f"\n{YELLOW}{'=' * 50}")
    print("EMERGENCY FALLBACK")
    print(f"{'=' * 50}{RESET}\n")
    print("If all else fails, run the demo:")
    print(f"  {BLUE}python emergency-demo-script.py{RESET}")
    print("\nThis will show what the system does without needing database/data")


# Entry point check: script execution starts here when run directly
if __name__ == "__main__":
    run_diagnostics()