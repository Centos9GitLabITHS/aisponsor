#!/usr/bin/env python3
"""
verify_scoring_fix.py - Quick script to verify scoring is fixed
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sponsor_match.services.service import SponsorMatchService
from sponsor_match.core.db import get_engine


def verify_scoring():
    """Quick verification that scoring is working with good differentiation."""
    print("SCORING VERIFICATION TEST")
    print("=" * 50)

    # Initialize service
    engine = get_engine()
    service = SponsorMatchService(engine)

    # Test with a known association
    test_associations = [
        "IFK Göteborg",
        "GAIS",
        "BK Häcken"
    ]

    for assoc_name in test_associations:
        print(f"\nTesting: {assoc_name}")
        print("-" * 30)

        # Get recommendations
        recommendations = service.recommend(
            association_name=assoc_name,
            top_n=10,
            max_distance=20
        )

        if recommendations.empty:
            print("  ✗ No recommendations found")
            continue

        # Analyze scores
        scores = recommendations['score'].values
        score_range = scores.max() - scores.min()
        unique_scores = len(set(scores))

        print(f"  Results: {len(recommendations)} companies")
        print(f"  Score range: {scores.min():.3f} to {scores.max():.3f}")
        print(f"  Score spread: {score_range:.3f}")
        print(f"  Unique scores: {unique_scores}")

        # Check if scoring is good
        if score_range < 0.01:
            print("  ✗ PROBLEM: Scores too similar!")
        elif score_range < 0.05:
            print("  ⚠ WARNING: Low score differentiation")
        else:
            print("  ✓ GOOD: Scores well differentiated")

        # Show top 3
        print("\n  Top 3 matches:")
        for idx, row in recommendations.head(3).iterrows():
            print(f"    {row['name']}: {row['score']:.3f} ({row['score'] * 100:.1f}%) "
                  f"at {row.get('distance_km', row.get('distance', 0)):.1f}km")

    print("\n" + "=" * 50)
    print("VERIFICATION COMPLETE")
    print("\nIf scores are too similar, replace pipeline.py with the enhanced version.")


if __name__ == "__main__":
    verify_scoring()
