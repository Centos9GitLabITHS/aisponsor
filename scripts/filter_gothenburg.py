#!/usr/bin/env python3
"""
scripts/filter_gothenburg.py
-----------------------------
Extract all Göteborg-municipality companies from a raw SCB bulk file
(and build a full street address for each) by filtering on the
canonical 20 district names.

Usage:
    python scripts/filter_gothenburg.py \
      --input /home/bakri/Desktop/scb_bulkfil/scb_bulkfil_JE_20250512T094258_21.txt
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Logical field names we need
DESIRED = ["PeOrgNr", "Gatuadress", "PostNr", "PostOrt"]

# The 20 official Göteborg municipality districts
DISTRICTS = [
    "Agnesberg", "Angered", "Askim", "Asperö", "Billdal",
    "Brännö", "Donsö", "Gunnilse", "Göteborg", "Hisings Backa",
    "Hisings Kärra", "Hovås", "Kungälv", "Köpstadsö", "Olofstorp",
    "Styrsö", "Säve", "Torslanda", "Vrångö", "Västra Frölunda",
]
# Lower-case set for filtering, and map back for canonical casing
LOWER_DISTRICTS = {d.lower() for d in DISTRICTS}
DISTRICT_MAP = {d.lower(): d for d in DISTRICTS}


def infer_columns(header_cols: list[str]) -> dict[str, str]:
    """
    From the raw header_cols, find which actual column corresponds
    to each name in DESIRED. Returns mapping actual_name -> desired_name.
    Exits if any desired field is missing.
    """
    # map stripped, lower-cased to the real header
    lookup = {col.strip().lower(): col for col in header_cols}
    mapping: dict[str, str] = {}
    for want in DESIRED:
        key = want.lower()
        if key not in lookup:
            print(f"🛑 Missing required column '{want}' in SCB header.", file=sys.stderr)
            print("Available columns:", file=sys.stderr)
            for col in header_cols:
                print("   ", repr(col), file=sys.stderr)
            sys.exit(1)
        actual = lookup[key]
        mapping[actual] = want
    return mapping


def main(scb_path: Path):
    print(f"Reading SCB header from {scb_path} …")
    # 1) Sniff header to get actual column names (tab-separated, Latin-1)
    header_df = pd.read_csv(
        scb_path,
        sep="\t",
        nrows=0,
        encoding="latin1",
        low_memory=False
    )
    actual_cols = list(header_df.columns)

    # 2) Infer which actual names match our DESIRED fields
    col_map = infer_columns(actual_cols)

    # 3) Load only those columns
    print("Loading columns:", list(col_map.keys()))
    df = pd.read_csv(
        scb_path,
        sep="\t",
        usecols=list(col_map.keys()),
        dtype=str,
        encoding="latin1",
        low_memory=False
    )

    # 4) Rename to our standard logical names
    df = df.rename(columns=col_map)

    # 5) Filter to entries whose PostOrt is one of the 20 districts
    df["PostOrt_norm"] = df["PostOrt"].str.strip().str.lower()
    df = df[df["PostOrt_norm"].isin(LOWER_DISTRICTS)].copy()
    print(f"→ {len(df)} firms in Göteborg municipality")

    # 6) Normalize the district back to canonical casing
    df["district"] = df["PostOrt_norm"].map(DISTRICT_MAP)

    # 7) Build a full street address
    df["registered_address"] = (
        df["Gatuadress"].str.strip()
        + ", "
        + df["PostNr"].str.strip()
        + " "
        + df["district"]
    )

    # 8) Output the key fields
    out = df[["PeOrgNr", "district", "registered_address"]]

    dest = Path("data") / "goteborg_companies_addresses.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False, encoding="utf-8")
    print(f"Wrote {len(out)} rows to {dest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter SCB dump to Göteborg municipality and build full addresses"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to your raw SCB dump file (tab-separated, Latin-1 .txt)"
    )
    args = parser.parse_args()
    main(args.input)
