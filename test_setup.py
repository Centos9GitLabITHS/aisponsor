# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
test_setup.py - Verify your SponsorMatch AI setup before presentation
"""

from datetime import datetime
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_imports():
    """Test all critical imports"""
    print(f"\n{BLUE}Testing imports...{RESET}")

    imports_to_test = [
        ('streamlit', 'Streamlit UI framework'),
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical operations'),
        ('folium', 'Map visualization'),
        ('streamlit_folium', 'Streamlit-Folium integration'),
        ('plotly', 'Analytics charts'),
        ('sklearn', 'Machine learning'),
        ('joblib', 'Model loading')
    ]

    all_good = True
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"  {GREEN}✓{RESET} {module} - {description}")
        except ImportError:
            print(f"  {RED}✗{RESET} {module} - {description}")
            all_good = False

    return all_good


def test_data_files():
    """Test data files exist and are valid"""
    print(f"\n{BLUE}Testing data files...{RESET}")

    data_dir = Path('data')
    files_to_check = {
        'associations_prepared.csv': 'Association data',
        'companies_prepared.csv': 'Company data',
        'associations_geocoded.csv': 'Geocoded associations',
        'companies_geocoded.csv': 'Geocoded companies'
    }

    all_good = True
    for filename, description in files_to_check.items():
        filepath = data_dir / filename
        if filepath.exists():
            # Check file size
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  {GREEN}✓{RESET} {filename} - {description} ({size_mb:.1f} MB)")

            # Quick data validation for prepared files
            if 'prepared' in filename:
                try:
                    import pandas as pd
                    df = pd.read_csv(filepath, nrows=5)
                    if 'size_bucket' in df.columns:
                        print(f"    → Has size_bucket column ✓")
                    else:
                        print(f"    {YELLOW}→ Missing size_bucket column{RESET}")
                        all_good = False
                except Exception as e:
                    print(f"    {RED}→ Error reading file: {e}{RESET}")
                    all_good = False
        else:
            print(f"  {RED}✗{RESET} {filename} - {description}")
            all_good = False

    return all_good


def test_models():
    """Test ML models exist"""
    print(f"\n{BLUE}Testing ML models...{RESET}")

    models_dir = Path('models')
    models_to_check = {
        'kmeans.joblib': 'Default clustering model',
        'kmeans_large.joblib': 'Large association model'
    }

    all_good = True
    for filename, description in models_to_check.items():
        filepath = models_dir / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            print(f"  {GREEN}✓{RESET} {filename} - {description} ({size_kb:.1f} KB)")

            # Try to load model
            try:
                import joblib
                model = joblib.load(filepath)
                model_type = type(model).__name__
                print(f"    → Model type: {model_type}")
            except Exception as e:
                print(f"    {YELLOW}→ Warning loading model: {e}{RESET}")
        else:
            print(f"  {YELLOW}✗{RESET} {filename} - {description} (will use distance-based scoring)")

    return all_good


def test_service():
    """Test the service layer"""
    print(f"\n{BLUE}Testing service layer...{RESET}")

    try:
        from archive.simple_service import SimpleSponsorService
        service = SimpleSponsorService()

        # Get stats
        stats = service.get_stats()
        print(f"  {GREEN}✓{RESET} Service initialized successfully")
        print(f"    → Total associations: {stats['total_associations']}")
        print(f"    → Total companies: {stats['total_companies']}")
        print(f"    → Model status: {stats['model_status']}")

        # Test search
        results = service.search_associations("IFK")
        print(f"  {GREEN}✓{RESET} Search working - found {len(results)} results for 'IFK'")

        # Test sponsor finding
        if not results.empty:
            test_id = results.iloc[0]['id']
            sponsors = service.find_sponsors(test_id, max_distance_km=10)
            print(f"  {GREEN}✓{RESET} Sponsor finding working - found {len(sponsors)} sponsors")

        return True

    except Exception as e:
        print(f"  {RED}✗{RESET} Service error: {e}")
        return False


def test_database():
    """Test database connection (optional)"""
    print(f"\n{BLUE}Testing database connection...{RESET}")

    try:
        from sponsor_match.core.db import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print(f"  {GREEN}✓{RESET} Database connection successful")
            return True
    except Exception as e:
        print(f"  {YELLOW}!{RESET} Database not connected: {e}")
        print(f"    → App will work with CSV files only")
        return True  # Not critical


def main():
    """Run all tests"""
    print(f"\n{'=' * 60}")
    print(f"{BLUE}SPONSORMATCH AI - PRESENTATION READINESS CHECK{RESET}")
    print(f"{'=' * 60}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Package imports", test_imports),
        ("Data files", test_data_files),
        ("ML models", test_models),
        ("Service layer", test_service),
        ("Database", test_database)
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"{BLUE}SUMMARY{RESET}")
    print(f"{'=' * 60}")

    all_passed = all(result for _, result in results)
    critical_passed = results[0][1] and results[1][1] and results[3][1]  # Imports, data, service

    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name}: {status}")

    print(f"\n{'=' * 60}")

    if all_passed:
        print(f"{GREEN}✅ ALL TESTS PASSED! Your app is ready for presentation.{RESET}")
        print(f"\nRun with: {BLUE}python run_app.py{RESET}")
        print(f"Or directly: {BLUE}streamlit run streamlit_app.py{RESET}")
    elif critical_passed:
        print(f"{YELLOW}⚠️  Some non-critical tests failed, but app should work.{RESET}")
        print(f"\nRun with: {BLUE}python run_app.py{RESET}")
    else:
        print(f"{RED}❌ Critical tests failed. Please fix issues before presentation.{RESET}")
        print(f"\nRun: {BLUE}python fix_common_issues.py{RESET}")

    print(f"\n{BLUE}Quick tips for presentation:{RESET}")
    print("1. Kill any stuck Streamlit processes: pkill -f streamlit")
    print("2. Use Chrome or Firefox for best compatibility")
    print("3. Have emergency-demo-script.py ready as backup")
    print("4. Test with 'IFK' or 'BK' for association search")


if __name__ == "__main__":
    main()
