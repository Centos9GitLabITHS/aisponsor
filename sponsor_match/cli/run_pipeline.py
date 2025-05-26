# run_pipeline.py
"""
Batch-run sponsor recommendations for a single association using the ML pipeline.
Outputs a JSON file of scored and ranked companies.
"""
import argparse  # CLI parsing
import json  # JSON serialization

from sponsor_match.ml.pipeline import score_and_rank  # ML function


def main():
    """Parse arguments, call the ML pipeline, and write recommendations to file."""
    parser = argparse.ArgumentParser(
        description="Batch-run sponsor recommendations for one association"
    )
    parser.add_argument("--assoc-id", type=int, required=True, help="Association ID")
    parser.add_argument("--bucket", choices=["small","medium","large"], required=True)
    parser.add_argument("--max-distance", type=float, default=50.0)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    args = parser.parse_args()

    # Call the ML pipeline: scores and ranks companies
    recs = score_and_rank(
        association_id=args.assoc_id,
        bucket=args.bucket,
        max_distance=args.max_distance,
        top_n=args.top_n
    )

    # Write out the list of recommendation dicts
    with open(args.output, "w") as f:
        json.dump(recs, f, indent=2)
    print(f"Wrote {len(recs)} recommendations to {args.output}")


if __name__ == "__main__":
    main()
