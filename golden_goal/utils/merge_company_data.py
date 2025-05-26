#!/usr/bin/env python3
"""
merge_company_data.py - Improved version with better encoding handling
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_company_data(data_dir: Path):
    """Merge all company data files with improved encoding and matching."""

    # 1. Load the SCB bulk file with correct encoding
    logger.info("Loading SCB bulk file...")
    scb_file = data_dir / "scb_bulkfil_JE_20250512T094258_21.txt"

    # Try different encodings for Swedish data
    encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
    scb_df = None

    for encoding in encodings_to_try:
        try:
            scb_df = pd.read_csv(
                scb_file,
                sep='\t',
                encoding=encoding,
                low_memory=False
            )
            # Check if Swedish characters look correct
            sample_text = str(scb_df['Foretagsnamn'].iloc[0] if 'Foretagsnamn' in scb_df.columns else '')
            if 'Ã' not in sample_text and '�' not in sample_text:
                logger.info(f"Successfully loaded with {encoding} encoding")
                break
        except Exception as e:
            logger.debug(f"Failed with {encoding}: {e}")
            continue

    if scb_df is None:
        logger.error("Could not load SCB file with any encoding")
        return None

    # Select relevant columns from SCB file
    scb_columns = ['PeOrgNr', 'Foretagsnamn', 'Gatuadress', 'PostNr', 'PostOrt', 'COAdress']
    available_columns = [col for col in scb_columns if col in scb_df.columns]
    scb_df = scb_df[available_columns].copy()

    # Clean and prepare SCB data
    scb_df['PeOrgNr'] = scb_df['PeOrgNr'].astype(str).str.strip()

    # Remove rows where company name is empty or just whitespace
    scb_df = scb_df[scb_df['Foretagsnamn'].notna()]
    scb_df = scb_df[scb_df['Foretagsnamn'].str.strip() != '']

    logger.info(f"Loaded {len(scb_df)} companies from SCB file (with non-empty names)")
    logger.info(f"Sample company names: {scb_df['Foretagsnamn'].head(3).tolist()}")

    # 2. Load companies_prepared.csv
    logger.info("Loading companies_prepared.csv...")
    prepared_df = pd.read_csv(data_dir / "companies_prepared.csv")
    prepared_df['PeOrgNr'] = prepared_df['PeOrgNr'].astype(str).str.strip()

    logger.info(f"Loaded {len(prepared_df)} companies with coordinates")

    # 3. Debug: Check why matching might fail
    logger.info("\nDebugging match issues:")

    # Check sample PeOrgNr from both datasets
    scb_sample = scb_df['PeOrgNr'].head(5).tolist()
    prepared_sample = prepared_df['PeOrgNr'].head(5).tolist()
    logger.info(f"SCB PeOrgNr samples: {scb_sample}")
    logger.info(f"Prepared PeOrgNr samples: {prepared_sample}")

    # Check for common PeOrgNr between datasets
    common_orgnr = set(prepared_df['PeOrgNr']).intersection(set(scb_df['PeOrgNr']))
    logger.info(f"Common PeOrgNr found: {len(common_orgnr)}")

    if len(common_orgnr) < 1000:
        # Try to understand the mismatch
        logger.warning("Very few matches found. Analyzing the issue...")

        # Check PeOrgNr lengths
        scb_lengths = scb_df['PeOrgNr'].str.len().value_counts().head()
        prepared_lengths = prepared_df['PeOrgNr'].str.len().value_counts().head()
        logger.info(f"SCB PeOrgNr lengths: \n{scb_lengths}")
        logger.info(f"Prepared PeOrgNr lengths: \n{prepared_lengths}")

    # 4. Rename columns to English
    scb_df.rename(columns={
        'Foretagsnamn': 'company_name',
        'Gatuadress': 'street_address',
        'PostNr': 'postal_code',
        'PostOrt': 'city',
        'COAdress': 'co_address'
    }, inplace=True)

    # Drop the placeholder 'name' column from prepared data
    if 'name' in prepared_df.columns:
        prepared_df = prepared_df.drop('name', axis=1)

    # 5. Merge datasets
    logger.info("\nMerging datasets...")
    merged_df = prepared_df.merge(
        scb_df,
        on='PeOrgNr',
        how='left'
    )

    # 6. Load additional address data if available
    address_file = data_dir / "gothenburg_companies_addresses.csv"
    if address_file.exists():
        logger.info("Loading additional address data...")
        address_df = pd.read_csv(address_file)
        if 'PeOrgNr' in address_df.columns:
            address_df['PeOrgNr'] = address_df['PeOrgNr'].astype(str).str.strip()

            # Merge additional address data
            merged_df = merged_df.merge(
                address_df[['PeOrgNr', 'registered_address']],
                on='PeOrgNr',
                how='left',
                suffixes=('', '_additional')
            )

    # 7. Clean up and organize columns
    if 'latitude' in merged_df.columns:
        merged_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True)

    # Create a clean address field
    def create_full_address(row):
        parts = []
        if pd.notna(row.get('street_address')) and str(row['street_address']).strip():
            parts.append(str(row['street_address']).strip())
        if pd.notna(row.get('postal_code')) and str(row['postal_code']).strip():
            postal = str(row['postal_code']).strip()
            if pd.notna(row.get('city')) and str(row['city']).strip():
                parts.append(f"{postal} {row['city'].strip()}")
            else:
                parts.append(postal)
        elif pd.notna(row.get('city')) and str(row['city']).strip():
            parts.append(str(row['city']).strip())

        return ', '.join(parts) if parts else None

    merged_df['full_address'] = merged_df.apply(create_full_address, axis=1)

    # Add industry information (if not present)
    if 'industry' not in merged_df.columns:
        merged_df['industry'] = 'Other'

    # Organize final columns
    final_columns = [
        'id', 'PeOrgNr', 'company_name', 'lat', 'lon',
        'size_bucket', 'district', 'industry',
        'street_address', 'postal_code', 'city', 'full_address'
    ]

    # Only include columns that exist
    final_columns = [col for col in final_columns if col in merged_df.columns]
    merged_df = merged_df[final_columns]

    # 8. Handle missing company names
    companies_with_names = merged_df['company_name'].notna().sum()
    logger.info(f"\nCompanies with real names: {companies_with_names}/{len(merged_df)}")

    # For companies without names, create a fallback
    merged_df['company_name'] = merged_df.apply(
        lambda row: row['company_name'] if pd.notna(row['company_name'])
        else f"Org.nr {row['PeOrgNr'][:6]}-{row['PeOrgNr'][6:10]}" if len(str(row['PeOrgNr'])) >= 10
        else f"Company {row['id']}",
        axis=1
    )

    # 9. Save the merged file
    output_file = data_dir / "companies_complete.csv"
    merged_df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"Saved complete company data to {output_file}")

    # Print summary statistics
    logger.info("\nSummary:")
    logger.info(f"Total companies: {len(merged_df)}")
    logger.info(f"Companies with coordinates: {merged_df[['lat', 'lon']].notna().all(axis=1).sum()}")
    logger.info(f"Companies with addresses: {merged_df['full_address'].notna().sum()}")
    logger.info(f"Companies by district: \n{merged_df['district'].value_counts().head()}")

    # Show some examples of companies with real names
    with_names = merged_df[merged_df['company_name'].notna() & ~merged_df['company_name'].str.startswith('Org.nr')]
    if len(with_names) > 0:
        logger.info(f"\nSample companies with real names:")
        print(with_names[['PeOrgNr', 'company_name', 'district']].head(10))

    return merged_df


def investigate_data_coverage(data_dir: Path):
    """Investigate why so few companies match between the datasets."""
    logger.info("\n=== Investigating Data Coverage ===")

    # Load both files
    scb_df = pd.read_csv(
        data_dir / "scb_bulkfil_JE_20250512T094258_21.txt",
        sep='\t',
        encoding='cp1252',  # Try Windows encoding for Swedish data
        usecols=['PeOrgNr', 'Foretagsnamn', 'PostOrt'],
        low_memory=False
    )

    prepared_df = pd.read_csv(data_dir / "companies_prepared.csv")

    # Clean PeOrgNr
    scb_df['PeOrgNr'] = scb_df['PeOrgNr'].astype(str).str.strip()
    prepared_df['PeOrgNr'] = prepared_df['PeOrgNr'].astype(str).str.strip()

    # Filter SCB data to Gothenburg area
    gothenburg_cities = ['GÖTEBORG', 'GOTEBORG', 'MÖLNDAL', 'MOLNDAL', 'PARTILLE',
                         'KUNGÄLV', 'KUNGALV', 'TORSLANDA', 'BILLDAL', 'VÄSTRA FRÖLUNDA',
                         'VASTRA FROLUNDA', 'HISINGS BACKA', 'ANGERED']

    scb_gothenburg = scb_df[scb_df['PostOrt'].str.upper().isin(gothenburg_cities)]
    logger.info(f"SCB file has {len(scb_gothenburg)} companies in Gothenburg area")

    # Check overlap
    common = set(prepared_df['PeOrgNr']).intersection(set(scb_gothenburg['PeOrgNr']))
    logger.info(f"Common PeOrgNr in Gothenburg area: {len(common)}")

    # Check if the issue is with PeOrgNr format
    logger.info("\nChecking PeOrgNr patterns:")
    logger.info(f"Prepared file - First 5 PeOrgNr: {prepared_df['PeOrgNr'].head().tolist()}")
    logger.info(f"SCB file - First 5 PeOrgNr: {scb_gothenburg['PeOrgNr'].head().tolist()}")

    # Check if prepared companies are mostly personal numbers (start with 16)
    personal_numbers = prepared_df[prepared_df['PeOrgNr'].str.startswith('16')]
    logger.info(
        f"\nCompanies with personal number format (16...): {len(personal_numbers)} ({len(personal_numbers) / len(prepared_df) * 100:.1f}%)")

    # The SCB file might contain mostly company org numbers (55...) not personal numbers
    company_numbers = scb_df[scb_df['PeOrgNr'].str.startswith('55')]
    logger.info(
        f"SCB entries with company format (55...): {len(company_numbers)} ({len(company_numbers) / len(scb_df) * 100:.1f}%)")


def main():
    """Run the merge process."""
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    data_dir = project_root / "data"

    logger.info(f"Script location: {script_path}")
    logger.info(f"Looking for data in: {data_dir}")

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    # Check if required files exist
    required_files = [
        "scb_bulkfil_JE_20250512T094258_21.txt",
        "companies_prepared.csv"
    ]

    for file in required_files:
        file_path = data_dir / file
        if not file_path.exists():
            logger.error(f"Required file not found: {file_path}")
            return

    # First, investigate the data coverage issue
    investigate_data_coverage(data_dir)

    # Then run the merge
    logger.info("\n=== Running Merge Process ===")
    merged_df = merge_company_data(data_dir)

    if merged_df is not None:
        logger.info("\nMerge completed successfully!")


if __name__ == "__main__":
    main()