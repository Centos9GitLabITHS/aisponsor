#!/usr/bin/env python3
"""Diagnose the data flow issue."""

from sponsor_match.core.db import get_engine
from sponsor_match.ml.pipeline import score_and_rank
import json


def diagnose():
    # First check what associations exist
    engine = get_engine()
    with engine.connect() as conn:
        assocs = list(conn.execute("SELECT id, name, size_bucket FROM associations LIMIT 5"))
        print("Available associations:")
        for id, name, bucket in assocs:
            print(f"  ID {id}: {name} ({bucket})")

    # Use first association
    if assocs:
        assoc_id, assoc_name, assoc_bucket = assocs[0]
        print(f"\nTesting score_and_rank with {assoc_name} (ID {assoc_id}):")
        print("-" * 50)

        results = score_and_rank(
            association_id=assoc_id,
            bucket=assoc_bucket,
            max_distance=50,  # Increased distance
            top_n=5
        )
    else:
        print("No associations found!")
        results = []

    print(f"\nGot {len(results)} results")

    if results:
        print("\nFirst result structure:")
        print(json.dumps(results[0], indent=2))

        print("\nAll results:")
        for i, r in enumerate(results, 1):
            print(f"{i}. ID: {r.get('id')}, Name: {r.get('name', 'MISSING!')}, Distance: {r.get('distance')}")

    # Check database directly
    print("\n\nChecking database companies:")
    print("-" * 50)

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute("SELECT id, name FROM companies LIMIT 5")
        for row in result:
            print(f"ID: {row[0]}, Name: {row[1]}")


if __name__ == "__main__":
    diagnose()
