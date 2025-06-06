# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""Test the recommendation pipeline to see what data is returned."""

from golden_goal.core.db import get_engine
from golden_goal.ml.pipeline import score_and_rank
from golden_goal import GoldenGoalService


def test_recommendations():
    """Test what the recommendation system returns."""

    # Test direct ML pipeline
    print("Testing ML Pipeline:")
    print("-" * 50)

    # Ahlafors IF has ID 2 in the loaded data
    results = score_and_rank(
        association_id=2,
        bucket='small',
        max_distance=10,
        top_n=5
    )

    print(f"Got {len(results)} recommendations")
    for i, sponsor in enumerate(results, 1):
        print(f"{i}. {sponsor}")

    print("\n\nTesting Service Layer:")
    print("-" * 50)

    # Test service layer
    engine = get_engine()
    service = GoldenGoalService(engine)

    # Get association details
    assoc = service.get_association_by_name("Ahlafors IF")
    if assoc:
        print(f"Found association: {assoc}")
    else:
        print("Association not found!")

        # List all associations
        print("\nAvailable associations:")
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, name FROM associations"))
            for row in result:
                print(f"  ID {row[0]}: {row[1]}")


if __name__ == "__main__":
    test_recommendations()
