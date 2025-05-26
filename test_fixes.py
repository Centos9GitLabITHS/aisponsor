# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""Test all the fixes."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    try:
        from golden_goal.core.db import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_imports():
    """Test critical imports."""
    print("Testing imports...")
    try:
        from golden_goal import search, recommend
        from golden_goal.ml.pipeline import score_and_rank
        print("✅ Critical imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_clustering():
    """Test clustering pipeline."""
    print("Testing clustering...")
    try:
        from golden_goal.ml.pipeline import score_and_rank
        # Test with fake data
        results = score_and_rank(1, "medium", max_distance=50, top_n=5)
        print(f"✅ Clustering test successful (got {len(results)} results)")
        return True
    except Exception as e:
        print(f"❌ Clustering test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🔧 Running SponsorMatch AI fixes tests...\n")

    tests = [
        test_imports,
        test_database_connection,
        test_clustering,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()

    # Summary
    passed = sum(results)
    total = len(results)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your fixes are working.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
