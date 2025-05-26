#!/usr/bin/env python3
"""
diagnose_ml_clean.py - Clean diagnostic script without IDE warnings
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sponsor_match.ml.pipeline import (
    load_models, score_and_rank_optimized,
    calculate_distance_score, calculate_size_match_score,
    calculate_industry_affinity
)
from sponsor_match.core.db import get_engine
from sqlalchemy import text


def check_ml_models():
    """Check if ML models are loading correctly."""
    print("=" * 60)
    print("ML MODEL DIAGNOSTIC")
    print("=" * 60)

    # Check model files
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "sponsor_match" / "models"

    print(f"\n1. Checking models directory: {models_dir}")
    if not models_dir.exists():
        print("   ✗ Models directory NOT FOUND!")
        print("   Run: python quick_train_models.py")
        return False

    print("   ✓ Models directory exists")
    model_files = list(models_dir.glob("*.joblib"))
    print(f"   Found {len(model_files)} model files:")
    for f in model_files:
        print(f"     - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    # Try loading models
    print("\n2. Testing model loading...")
    models = load_models()
    if not models:
        print("   ✗ No models loaded!")
        return False

    print(f"   ✓ Loaded {len(models)} models: {list(models.keys())}")
    for key, model in models.items():
        if isinstance(model, dict):
            print(f"     - {key}: dict with keys {list(model.keys())}")
        else:
            print(f"     - {key}: {type(model).__name__}")

    return True


def test_scoring():
    """Test the scoring function with a sample association."""
    print("\n3. Testing scoring function...")

    engine = get_engine()
    with engine.connect() as conn:
        # Get a sample association
        result = conn.execute(text("""
                                   SELECT id, name, lat, lon, size_bucket
                                   FROM associations
                                   WHERE lat IS NOT NULL
                                     AND lon IS NOT NULL LIMIT 1
                                   """)).fetchone()

        if not result:
            print("   ✗ No associations found in database!")
            return

        assoc_id, assoc_name, lat, lon, size_bucket = result
        print(f"   Testing with: {assoc_name} (ID: {assoc_id})")

        # Get recommendations
        recommendations = score_and_rank_optimized(
            association_id=assoc_id,
            bucket=size_bucket,
            max_distance=25,
            top_n=10
        )

        if not recommendations:
            print("   ✗ No recommendations returned!")
            return

        print(f"   ✓ Got {len(recommendations)} recommendations")

        # Check score distribution
        scores = [r['score'] for r in recommendations]
        unique_scores = len(set(scores))

        print(f"\n   Score Analysis:")
        print(f"   - Unique scores: {unique_scores}")
        print(f"   - Min score: {min(scores):.4f}")
        print(f"   - Max score: {max(scores):.4f}")
        print(f"   - Score range: {max(scores) - min(scores):.4f}")
        print(f"   - Avg score: {sum(scores) / len(scores):.4f}")

        if unique_scores == 1:
            print("   ✗ WARNING: All scores are identical!")
            print("     This indicates scoring is not working properly.")
        elif max(scores) - min(scores) < 0.01:
            print("   ⚠ WARNING: Score range too narrow!")
            print("     Scores need more differentiation.")
        else:
            print("   ✓ Scores are properly distributed")

        # Show top recommendations with component breakdown
        print("\n   Top 5 recommendations:")
        for i, rec in enumerate(recommendations[:5]):
            print(f"\n     {i + 1}. {rec['name']}")
            print(f"        Score: {rec['score']:.4f} ({rec['score'] * 100:.1f}%)")
            print(f"        Distance: {rec.get('distance', 'N/A')}km")
            if 'components' in rec:
                print(f"        Components:")
                for comp, val in rec['components'].items():
                    print(f"          - {comp}: {val:.3f}")


def check_scoring_components():
    """Test individual scoring components."""
    print("\n4. Testing individual scoring components...")

    # Test distance scoring
    print("\n   Distance scoring (max_distance=25km):")
    print("   Distance -> Score")
    for dist in [0, 2, 5, 10, 15, 20, 25, 30]:
        score = calculate_distance_score(dist, 25)
        bar = '█' * int(score * 20)
        print(f"   {dist:3d}km -> {score:.3f} {bar}")

    # Test size matching
    print("\n   Size match scoring:")
    print("   Assoc Size | Comp Size -> Score")
    sizes = ['small', 'medium', 'large']
    for s1 in sizes:
        for s2 in sizes:
            score = calculate_size_match_score(s1, s2)
            print(f"   {s1:6s} <-> {s2:6s} = {score:.1f}")

    # Test industry scoring
    print("\n   Industry affinity scores:")
    industries = ['Finance', 'Insurance', 'Retail', 'Technology',
                  'Manufacturing', 'Healthcare', 'Other']
    for ind in industries:
        score = calculate_industry_affinity(ind)
        bar = '█' * int(score * 20)
        print(f"   {ind:15s} -> {score:.2f} {bar}")


def check_database_status():
    """Check database connection and data availability."""
    print("\n5. Checking database status...")

    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Check associations
            assoc_count = conn.execute(
                text("SELECT COUNT(*) FROM associations")
            ).scalar()
            print(f"   ✓ Associations: {assoc_count}")

            # Check companies
            comp_count = conn.execute(
                text("SELECT COUNT(*) FROM companies")
            ).scalar()
            print(f"   ✓ Companies: {comp_count}")

            # Check companies with coordinates
            comp_with_coords = conn.execute(
                text("SELECT COUNT(*) FROM companies WHERE lat IS NOT NULL AND lon IS NOT NULL")
            ).scalar()
            print(f"   ✓ Companies with coordinates: {comp_with_coords}")

    except Exception as e:
        print(f"   ✗ Database error: {e}")


def main():
    """Run all diagnostics."""
    # Check models
    models_ok = check_ml_models()

    # Check database
    check_database_status()

    # Test scoring
    if models_ok:
        test_scoring()
        check_scoring_components()
    else:
        print("\n✗ Fix model loading issues before testing scoring!")

    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

    print("\nNext steps:")
    print("1. If scores are too similar, replace pipeline.py with enhanced version")
    print("2. If models are missing, run: python quick_train_models.py")
    print("3. Restart the Streamlit app to see improved scoring")


if __name__ == "__main__":
    main()