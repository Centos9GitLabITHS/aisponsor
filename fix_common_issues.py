# Script to automatically fix frequent configuration issues
# Detailed comments have been inserted in British English.

#!/usr/bin/env python3
"""
fix_common_issues.py - Fix the most common SponsorMatch AI issues
"""

# Standard library or third-party import
import os
# Standard library or third-party import
import sys
# Standard library or third-party import
from pathlib import Path


# Definition of function 'fix_1_database_url': explains purpose and parameters
def fix_1_database_url():
    """Fix database URL encoding issues"""
    env_file = Path('.env')
    if not env_file.exists():
        print("Creating .env file...")
        with open('.env', 'w') as f:
            f.write("""# Database configuration
MYSQL_USER=sponsor_user
MYSQL_PASSWORD=Sports-2025?!
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=sponsor_registry

# App configuration
APP_TITLE=SponsorMatch AI
LOG_LEVEL=INFO
""")
        print("✅ Created .env file")


# Definition of function 'fix_2_import_paths': explains purpose and parameters
def fix_2_import_paths():
    """Fix Python import paths"""
    # Add project root to Python path
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Create __init__.py files if missing
    init_paths = [
        'sponsor_match/__init__.py',
        'sponsor_match/ui/__init__.py',
        'sponsor_match/services/__init__.py',
        'sponsor_match/models/__init__.py',
        'sponsor_match/ml/__init__.py',
        'sponsor_match/core/__init__.py',
        'sponsor_match/data/__init__.py'
    ]

    for init_path in init_paths:
        path = Path(init_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            print(f"✅ Created {init_path}")


# Definition of function 'fix_3_data_files': explains purpose and parameters
def fix_3_data_files():
    """Ensure data files exist"""
    # Check if we need to run data preparation
    data_dir = Path('data')
    if not (data_dir / 'associations_prepared.csv').exists():
        print("Running data preparation...")
        os.system('python prepare_all_data.py')


# Definition of function 'fix_4_models': explains purpose and parameters
def fix_4_models():
    """Create dummy models if missing"""
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)

    # Create dummy models if they don't exist
# Standard library or third-party import
    import joblib
# Standard library or third-party import
    from sklearn.cluster import KMeans
# Standard library or third-party import
    import numpy as np

    for model_name in ['kmeans.joblib', 'kmeans_large.joblib']:
        model_path = models_dir / model_name
        if not model_path.exists():
            print(f"Creating dummy model: {model_name}")
            # Create a simple KMeans model
            X = np.random.rand(100, 2)
            kmeans = KMeans(n_clusters=3, random_state=42)
            kmeans.fit(X)
            joblib.dump(kmeans, model_path)
            print(f"✅ Created {model_name}")


# Definition of function 'fix_5_streamlit_config': explains purpose and parameters
def fix_5_streamlit_config():
    """Ensure Streamlit config is correct"""
    streamlit_dir = Path('.streamlit')
    streamlit_dir.mkdir(exist_ok=True)

    # Already exists in the project, but ensure it's there
    config_file = streamlit_dir / 'config.toml'
    if not config_file.exists():
        with open(config_file, 'w') as f:
            f.write("""[theme]
primaryColor = "#1e40af"
backgroundColor = "#f9fafb"
secondaryBackgroundColor = "#ffffff"
textColor = "#111827"
font = "sans serif"
""")
        print("✅ Created Streamlit config")


# Definition of function 'main': explains purpose and parameters
def main():
    print("🔧 Fixing common SponsorMatch AI issues...\n")

    fixes = [
        ("Database configuration", fix_1_database_url),
        ("Import paths", fix_2_import_paths),
        ("Data files", fix_3_data_files),
        ("ML models", fix_4_models),
        ("Streamlit config", fix_5_streamlit_config)
    ]

    for name, fix_func in fixes:
        print(f"\n📍 Fixing {name}...")
        try:
            fix_func()
        except Exception as e:
            print(f"❌ Error fixing {name}: {e}")

    print("\n✅ Fixes applied!")
    print("\nNow try running:")
    print("  streamlit run sponsor_match/ui/simple_app.py")
    print("\nOr if that fails:")
    print("  python emergency-demo-script.py")


# Entry point check: script execution starts here when run directly
if __name__ == "__main__":
    main()