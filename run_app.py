#!/usr/bin/env python3
"""
run_app.py
Clean launcher for the Streamlit app without recursive imports.
"""

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

def check_requirements():
    """Check if required packages are installed."""
    required_packages = ['streamlit', 'pandas', 'numpy', 'folium',
                         'streamlit_folium', 'plotly']
    package_names = {
        'streamlit_folium': 'streamlit-folium',
        'plotly': 'plotly'
    }
    missing_packages = []

    for package in required_packages:
        try:
            if package == 'streamlit_folium':
                __import__('streamlit_folium')
            else:
                __import__(package)
        except ImportError:
            install_name = package_names.get(package, package)
            missing_packages.append(install_name)

    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\nInstall them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    return True

def check_data_files():
    """Check if prepared data files exist."""
    data_dir = Path(__file__).parent / "data"
    required_files = ['associations_prepared.csv', 'companies_prepared.csv']
    missing_files = []

    for file in required_files:
        if not (data_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print("❌ Missing data files:")
        for file in missing_files:
            print(f"   - data/{file}")
        print("\nRun this command first:")
        print("   python prepare_all_data.py")
        return False

    # Verify size categories are present
    try:
        import pandas as pd
        assoc = pd.read_csv(data_dir / 'associations_prepared.csv')
        comp = pd.read_csv(data_dir / 'companies_prepared.csv')

        if 'size_bucket' not in assoc.columns or 'size_bucket' not in comp.columns:
            print("⚠️  Data files exist but don't have size categories.")
            print("   Please run: python prepare_all_data.py")
            return False

        print(f"✅ Data files ready with size categories")
        print(f"   - Associations: {len(assoc)} records")
        print(f"   - Companies: {len(comp)} records")

    except Exception as e:
        print(f"⚠️  Error checking data files: {e}")
        return False

    return True

def check_app_structure():
    """Check if the app structure exists."""
    app_path = Path(__file__).parent / "golden_goal" / "ui" / "simple_app.py"
    service_path = Path(__file__).parent / "golden_goal" / "services" / "simple_service.py"

    missing = []
    if not app_path.exists():
        missing.append(str(app_path))
    if not service_path.exists():
        missing.append(str(service_path))

    if missing:
        print("❌ Missing application files:")
        for file in missing:
            print(f"   - {file}")
        print("\nMake sure you've created the complete file structure")
        return False

    return True

def open_browser(url, delay=3):
    """Open browser after a delay."""
    time.sleep(delay)
    webbrowser.open(url)

def main():
    """Run the Streamlit app."""
    print("=== SponsorMatch AI Launcher ===\n")

    # Check requirements
    print("Checking requirements...")
    if not check_requirements():
        sys.exit(1)
    print("✅ All packages installed")

    # Check data files
    print("\nChecking data files...")
    if not check_data_files():
        sys.exit(1)
    print("✅ Data files ready")

    # Check app structure
    print("\nChecking app structure...")
    if not check_app_structure():
        sys.exit(1)
    print("✅ App structure complete")

    # Launch app
    app_path = Path(__file__).parent / "golden_goal" / "ui" / "simple_app.py"
    print(f"\n🚀 Starting SponsorMatch AI...")
    print(f"📂 Running: {app_path}")
    print(f"\n{'=' * 50}")
    print("The app will open in your browser automatically.")
    print("If it doesn't, go to: http://localhost:8501")
    print(f"{'=' * 50}\n")

    os.environ['PYTHONPATH'] = str(Path(__file__).parent)
    app_url = "http://localhost:8501"

    try:
        # Open browser after short delay
        browser_thread = threading.Thread(target=open_browser, args=(app_url,))
        browser_thread.daemon = True
        browser_thread.start()

        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ], check=True)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running Streamlit: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure port 8501 is not in use")
        print("2. Try running directly:")
        print(f"   streamlit run {app_path}")
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down SponsorMatch AI...")

if __name__ == "__main__":
    main()
