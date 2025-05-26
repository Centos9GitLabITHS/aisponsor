#!/usr/bin/env python3
"""Complete fix script for SponsorMatch AI"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from golden_goal.core.db import get_engine
from golden_goal.utils.setup_database import setup_database
from golden_goal.utils.train_clustering_models import train_all_models
from sqlalchemy import text


def verify_environment():
    """Check that all required packages are installed"""
    required_packages = [
        'streamlit', 'folium', 'streamlit-folium', 'plotly',
        'pandas', 'numpy', 'scikit-learn', 'sqlalchemy',
        'pymysql', 'joblib', 'geopy'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Missing packages: {missing}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
    else:
        print("✅ All required packages are installed")


def fix_database():
    """Ensure database is properly set up"""
    print("\n📊 Setting up database...")
    try:
        setup_database()

        # Verify data
        engine = get_engine()
        with engine.connect() as conn:
            assoc_count = conn.execute(text("SELECT COUNT(*) FROM associations")).scalar()
            comp_count = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            print(f"✅ Database setup complete: {assoc_count} associations, {comp_count} companies")

            # Show sample associations
            sample_assocs = conn.execute(text("SELECT id, name, size_bucket FROM associations LIMIT 5")).fetchall()
            print("\nSample associations:")
            for assoc in sample_assocs:
                print(f"  - ID {assoc[0]}: {assoc[1]} ({assoc[2]})")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    return True


def fix_models():
    """Train clustering models"""
    print("\n🤖 Training clustering models...")
    try:
        models_dir = Path(__file__).parent / "golden_goal" / "models"
        models_dir.mkdir(exist_ok=True)
        train_all_models()

        # Verify models exist
        model_files = ['kmeans.joblib', 'kmeans_large.joblib']
        missing_models = []
        for model_file in model_files:
            if not (models_dir / model_file).exists():
                missing_models.append(model_file)

        if missing_models:
            print(f"❌ Missing model files: {missing_models}")
            return False
        else:
            print("✅ All models trained successfully")
    except Exception as e:
        print(f"❌ Model training failed: {e}")
        return False
    return True


def test_recommendations():
    """Test that recommendations work"""
    print("\n🧪 Testing recommendation system...")
    try:
        from golden_goal import GoldenGoalService
        engine = get_engine()
        service = GoldenGoalService(engine)

        # Get a test association
        with engine.connect() as conn:
            test_assoc = conn.execute(text("SELECT name FROM associations LIMIT 1")).fetchone()
            if test_assoc:
                assoc_name = test_assoc[0]
                print(f"Testing recommendations for: {assoc_name}")
                recommendations = service.recommend(assoc_name, top_n=5)
                if not recommendations.empty:
                    print(f"✅ Got {len(recommendations)} recommendations!")
                    print("\nTop 3 recommendations:")
                    for idx, row in recommendations.head(3).iterrows():
                        print(f"  - {row['name']}: {row['score'] * 100:.1f}% match")
                else:
                    print("⚠️ No recommendations found - check data and models")
    except Exception as e:
        print(f"❌ Recommendation test failed: {e}")
        return False
    return True


def create_test_script():
    """Create a test script for manual verification"""
    test_script = '''#!/usr/bin/env python3
"""Quick test script for SponsorMatch AI"""

from golden_goal.core.db import get_engine
from golden_goal.services.service import GoldenGoalService

# Test database connection
engine = get_engine()
print("✅ Database connected")

# Test service
service = GoldenGoalService(engine)

# Test search
results = service.search("IFK")
print(f"Search for 'IFK' found {len(results)} results")

# Test recommendations
if not results.empty:
    first_assoc = results.iloc[0]['name']
    print(f"\\nGetting recommendations for: {first_assoc}")
    recommendations = service.recommend(first_assoc, top_n=5)
    print(f"Found {len(recommendations)} recommendations")
    if not recommendations.empty:
        print("\\nTop recommendation:")
        top = recommendations.iloc[0]
        print(f"  {top['name']} - Score: {top['score']*100:.1f}%")
'''

    with open('test_golden_goal.py', 'w') as f:
        f.write(test_script)
    print("\n📄 Created test_golden_goal.py for manual testing")


def main():
    print("🔧 SponsorMatch AI Complete Fix Script")
    print("=" * 50)

    # Step 1: Verify environment
    verify_environment()

    # Step 2: Fix database
    if not fix_database():
        print("\n❌ Database setup failed. Please check your database configuration.")
        return

    # Step 3: Fix models
    if not fix_models():
        print("\n❌ Model training failed. Please check the error messages above.")
        return

    # Step 4: Test recommendations
    if not test_recommendations():
        print("\n⚠️ Recommendation test failed, but setup may still work.")

    # Step 5: Create test script
    create_test_script()

    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\nTo run the application:")
    print("  streamlit run golden_goal/ui/simple_app.py")
    print("\nTo test manually:")
    print("  python test_golden_goal.py")
    print("\nIf you encounter issues:")
    print("  1. Check that MySQL is running")
    print("  2. Verify your .env file has correct database credentials")
    print("  3. Check the logs above for specific errors")


if __name__ == "__main__":
    main()
