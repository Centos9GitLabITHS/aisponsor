#!/usr/bin/env python3
"""
test_scoring_distribution.py - Test scoring with varied search parameters
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from golden_goal import GoldenGoalService
from golden_goal.core.db import get_engine
from sqlalchemy import text


def test_scoring_distribution():
    """Test scoring with different parameters to ensure good distribution."""
    print("COMPREHENSIVE SCORING TEST")
    print("=" * 60)

    engine = get_engine()
    service = GoldenGoalService(engine)

    # Get a few different associations to test
    with engine.connect() as conn:
        associations = conn.execute(text("""
                                         SELECT name, size_bucket
                                         FROM associations
                                         WHERE lat IS NOT NULL
                                           AND lon IS NOT NULL LIMIT 5
                                         """)).fetchall()

    test_configs = [
        {"distance": 10, "top_n": 20},  # Close range
        {"distance": 25, "top_n": 20},  # Medium range
        {"distance": 50, "top_n": 20},  # Far range
    ]

    for assoc_name, assoc_size in associations[:3]:
        print(f"\n{'=' * 60}")
        print(f"Testing: {assoc_name} (size: {assoc_size})")
        print(f"{'=' * 60}")

        for config in test_configs:
            print(f"\nConfig: max_distance={config['distance']}km, top_n={config['top_n']}")
            print("-" * 40)

            recommendations = service.recommend(
                association_name=assoc_name,
                top_n=config['top_n'],
                max_distance=config['distance']
            )

            if recommendations.empty:
                print("  ✗ No recommendations found")
                continue

            # Analyze score distribution
            scores = recommendations['score'].values
            distances = recommendations['distance_km'].values

            print(f"  Found: {len(recommendations)} companies")
            print(f"  Distances: {distances.min():.1f}km to {distances.max():.1f}km")
            print(f"  Scores: {scores.min():.3f} to {scores.max():.3f}")
            print(f"  Score range: {scores.max() - scores.min():.3f}")
            print(f"  Unique scores: {len(set(scores))}")

            # Group by distance ranges
            print("\n  Score by distance:")
            for dist_range in [(0, 1), (1, 5), (5, 10), (10, 20), (20, 50)]:
                mask = (distances >= dist_range[0]) & (distances < dist_range[1])
                if mask.any():
                    range_scores = scores[mask]
                    print(f"    {dist_range[0]}-{dist_range[1]}km: "
                          f"{range_scores.min():.3f} to {range_scores.max():.3f} "
                          f"(n={len(range_scores)})")

            # Show score distribution visually
            print("\n  Score distribution:")
            bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            for i in range(len(bins) - 1):
                count = ((scores >= bins[i]) & (scores < bins[i + 1])).sum()
                bar = "█" * (count * 50 // len(scores)) if len(scores) > 0 else ""
                print(f"    {bins[i]:.1f}-{bins[i + 1]:.1f}: {count:3d} {bar}")

            # Sample of results
            print("\n  Sample results:")
            sample_indices = [0, len(recommendations) // 4, len(recommendations) // 2, -1]
            for i in sample_indices:
                if 0 <= i < len(recommendations) or i == -1:
                    row = recommendations.iloc[i]
                    rank = row['rank'] if 'rank' in row else i + 1
                    print(f"    #{rank}: {row['name'][:30]:<30} "
                          f"Score: {row['score']:.3f} Dist: {row['distance_km']:.1f}km")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("\nExpected results:")
    print("- Scores should vary significantly (range > 0.1)")
    print("- Closer companies should generally score higher")
    print("- Different distance ranges should show different score ranges")
    print("- No single score value should dominate")


if __name__ == "__main__":
    test_scoring_distribution()
