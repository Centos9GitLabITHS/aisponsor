# filter_gothenburg.py
"""
Extract Göteborg-municipality companies from a raw SCB bulk file,
filter by district names, and build full street addresses.
"""
import argparse  # CLI argument parsing
import sys  # For exiting on error
from pathlib import Path  # Filesystem paths

import pandas as pd  # DataFrame handling

# Fields we care about extracting
DESIRED = ["PeOrgNr", "Gatuadress", "PostNr", "PostOrt"]

# Official Göteborg districts for filtering
DISTRICTS = [
    "Agnesberg", "Angered", "Askim", "Asperö", "Billdal", "Brännö", "Donsö",
    "Gunnilse", "Göteborg", "Hisings Backa", "Hisings Kärra", "Hovås",
    "Kungälv", "Köpstadsö", "Olofstorp", "Styrsö", "Säve", "Torslanda",
    "Vrångö", "Västra Frölunda"
]
LOWER_DISTRICTS = {d.lower() for d in DISTRICTS}
DISTRICT_MAP = {d.lower(): d for d in DISTRICTS}


def infer_columns(header_cols: list[str]) -> dict[str, str]:
    """
    Map actual SCB column names to our desired logical names,
    accounting for case and whitespace.
    Exits with error message if any required column is missing.
    """
    lookup = {col.strip().lower(): col for col in header_cols}
    mapping = {}
    for want in DESIRED:
        key = want.lower()
        if key not in lookup:
            print(f"🛑 Missing required column '{want}'.", file=sys.stderr)
            sys.exit(1)
        mapping[lookup[key]] = want
    return mapping


def main(scb_path: Path):
    """Read SCB header, infer columns, load data, filter, and write output."""
    print(f"Reading SCB header from {scb_path} …")
    # Read only header row to get actual column names
    header_df = pd.read_csv(scb_path, sep="\t", nrows=0, encoding="latin1", low_memory=False)
    actual_cols = list(header_df.columns)

    # Determine which columns match our DESIRED fields
    col_map = infer_columns(actual_cols)

    # Load only those relevant columns
    print("Loading columns:", list(col_map.keys()))
    df = pd.read_csv(scb_path, sep="\t", usecols=list(col_map.keys()),
                     dtype=str, encoding="latin1", low_memory=False)

    # Rename to logical field names
    df = df.rename(columns=col_map)

    # Normalize district field and filter
    df["PostOrt_norm"] = df["PostOrt"].str.strip().str.lower()
    df = df[df["PostOrt_norm"].isin(LOWER_DISTRICTS)].copy()
    print(f"→ {len(df)} firms in Göteborg municipality")

    # Map back to canonical district names
    df["district"] = df["PostOrt_norm"].map(DISTRICT_MAP)

    # Build full registered address
    df["registered_address"] = (
        df["Gatuadress"].str.strip() + ", " +
        df["PostNr"].str.strip() + " " +
        df["district"]
    )

    # Output the key fields to CSV
    dest = Path("data") / "gothenburg_companies_addresses.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    df[["PeOrgNr", "district", "registered_address"]].to_csv(dest, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} rows to {dest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter SCB dump to Göteborg and build addresses")
    parser.add_argument("--input", "-i", type=Path, required=True, help="Path to SCB dump file")
    args = parser.parse_args()
    main(args.input)
