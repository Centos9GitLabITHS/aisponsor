# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
sponsor_match/data/geocode_with_municipality.py

Comprehensive geocoding system using Göteborg municipality data.
Handles associations and companies with various address formats.
"""

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, List

import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz, process
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GeocodingResult:
    """Store geocoding results with confidence metadata."""
    lat: float
    lon: float
    district: str
    confidence: str  # 'exact', 'fuzzy', 'postcode', 'box', 'external'
    match_details: str
    original_address: str


class MunicipalityGeocoder:
    """
    Intelligent geocoder using Göteborg municipality data as primary source.
    Falls back to external services only when necessary.
    """

    def __init__(self, municipality_csv_path: str):
        """Initialize with municipality data."""
        logger.info("Loading municipality data...")
        # Try reading with UTF-8 encoding first, fall back to Latin-1 if needed
        try:
            self.muni_df = pd.read_csv(municipality_csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning("UTF-8 decoding failed, trying Latin-1...")
            self.muni_df = pd.read_csv(municipality_csv_path, encoding='latin-1')

        # Fix encoding issues if they exist
        self._fix_encoding_issues()

        # Create various indices for efficient lookups
        self._prepare_indices()

        # Initialize external geocoder as fallback
        geolocator = Nominatim(user_agent="sponsor_match_geocoder")
        self.external_geocoder = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        # Cache for Box addresses (will be populated on first use)
        self.box_address_cache = {}

        # Settings for controlling external geocoding
        self.use_external_geocoding = False  # Disable by default to avoid timeouts

    def _fix_encoding_issues(self):
        """Fix common UTF-8/Latin-1 encoding issues in Swedish text."""
        # Common misencoded Swedish character patterns
        encoding_fixes = {
            'ã¥': 'å', 'Ã¥': 'Å',
            'ã¤': 'ä', 'Ã¤': 'Ä',
            'ã¶': 'ö', 'Ã¶': 'Ö',
            'ã©': 'é', 'Ã©': 'É',
            'ã': 'à', 'Ã': 'À'
        }

        # Apply fixes to string columns
        for col in self.muni_df.columns:
            if self.muni_df[col].dtype == 'object':  # String columns
                for wrong, right in encoding_fixes.items():
                    self.muni_df[col] = self.muni_df[col].str.replace(wrong, right, regex=False)

        logger.info("Applied encoding fixes to municipality data")

    def _prepare_indices(self):
        """Prepare various indices for fast lookups."""
        # Clean and standardize street names
        self.muni_df['street_clean'] = (
            self.muni_df['STREET']
            .str.lower()
            .str.strip()
            .fillna('')
        )

        # Create full address for matching
        self.muni_df['full_address'] = (
                self.muni_df['street_clean'] + ' ' +
                self.muni_df['NUMBER'].fillna('').astype(str)
        ).str.strip()

        # Group by street for street-level lookups
        self.street_groups = self.muni_df.groupby('street_clean')

        # Create postcode index
        self.postcode_groups = self.muni_df.groupby('POSTCODE')

        # Get unique streets for fuzzy matching
        self.unique_streets = self.muni_df['street_clean'].unique()

        logger.info(f"Indexed {len(self.muni_df)} addresses across {len(self.unique_streets)} streets")

    def parse_address(self, raw_address: str) -> Dict[str, str]:
        """
        Parse various address formats into components.
        Handles contact names, Box addresses, and standard formats.
        """
        # Handle None or empty addresses
        if not raw_address or pd.isna(raw_address):
            return {'street': '', 'number': '', 'postcode': '', 'city': ''}

        address = str(raw_address).strip()

        # Check if it's a Box address
        box_match = re.search(r'Box\s*(\d+)', address, re.IGNORECASE)
        if box_match:
            return {
                'street': 'BOX',
                'number': box_match.group(1),
                'postcode': self._extract_postcode(address),
                'city': self._extract_city(address),
                'is_box': True
            }

        # Split by comma to separate components
        parts = [p.strip() for p in address.split(',')]

        # For associations, the middle part is often a contact name - skip it
        # Pattern: Street, ContactName, PostCode, City
        if len(parts) >= 4:
            street_part = parts[0]
            # Skip parts[1] as it's likely a contact name
            # Reconstruct address without contact name
            address = f"{parts[0]}, {parts[2]}, {parts[3]}"
        elif len(parts) >= 1:
            street_part = parts[0]
        else:
            street_part = ''

        # Extract postcode (5 digits, possibly with space)
        postcode = self._extract_postcode(address)

        # Extract house number from street part
        street, number = self._split_street_number(street_part)

        # Last part after postcode is usually city
        city = self._extract_city(address)

        return {
            'street': street,
            'number': number,
            'postcode': postcode,
            'city': city,
            'is_box': False
        }

    def _extract_postcode(self, address: str) -> str:
        """Extract Swedish postcode from address."""
        # Match 5 digits with optional space (e.g., "412 76" or "41276")
        match = re.search(r'(\d{3}\s?\d{2})', address)
        if match:
            # Normalize to no-space format
            return match.group(1).replace(' ', '')
        return ''

    def _extract_city(self, address: str) -> str:
        """Extract city name from address."""
        # Common districts/cities in Göteborg area
        cities = ['Göteborg', 'GÖTEBORG', 'Mölndal', 'MÖLNDAL', 'Partille', 'PARTILLE',
                  'Angered', 'ANGERED', 'Västra Frölunda', 'VÄSTRA FRÖLUNDA',
                  'Hisings Backa', 'HISINGS BACKA', 'Torslanda', 'TORSLANDA']

        for city in cities:
            if city in address:
                return city.title()
        return 'Göteborg'  # Default

    def _split_street_number(self, street_part: str) -> Tuple[str, str]:
        """Split street name and house number."""
        # Try to find number at the end
        match = re.match(r'^(.+?)\s+(\d+\s*[A-Za-z]?)$', street_part)
        if match:
            return match.group(1).strip(), match.group(2).strip()

        # No number found
        return street_part.strip(), ''

    def geocode_address(self, raw_address: str) -> Optional[GeocodingResult]:
        """
        Main geocoding method with multiple fallback strategies.
        """
        # Parse the address
        parsed = self.parse_address(raw_address)

        # Handle Box addresses specially
        if parsed.get('is_box'):
            return self._geocode_box_address(parsed, raw_address)

        # Try exact match first
        result = self._try_exact_match(parsed, raw_address)
        if result:
            return result

        # Try fuzzy street matching
        result = self._try_fuzzy_match(parsed, raw_address)
        if result:
            return result

        # Try postcode-based geocoding
        result = self._try_postcode_match(parsed, raw_address)
        if result:
            return result

        # Last resort: external geocoding
        return self._try_external_geocoding(raw_address)

    def _try_exact_match(self, parsed: Dict, original: str) -> Optional[GeocodingResult]:
        """Try exact street + number match."""
        street_clean = parsed['street'].lower().strip()
        number = parsed['number']

        if not street_clean:
            return None

        # Get all addresses on this street
        if street_clean in self.street_groups.groups:
            street_data = self.street_groups.get_group(street_clean)

            if number:
                # Try exact number match
                exact_match = street_data[street_data['NUMBER'].astype(str) == str(number)]
                if not exact_match.empty:
                    row = exact_match.iloc[0]
                    return GeocodingResult(
                        lat=row['LAT'],
                        lon=row['LON'],
                        district=row['DISTRICT'],
                        confidence='exact',
                        match_details=f"Exact match: {row['STREET']} {row['NUMBER']}",
                        original_address=original
                    )

            # No number or no exact match - use street midpoint
            return self._get_street_midpoint(street_data, parsed, original)

        return None

    def _try_fuzzy_match(self, parsed: Dict, original: str) -> Optional[GeocodingResult]:
        """Try fuzzy matching for street names."""
        street_clean = parsed['street'].lower().strip()
        if not street_clean or len(street_clean) < 3:
            return None

        # Find best matching street
        best_match = process.extractOne(
            street_clean,
            self.unique_streets,
            scorer=fuzz.ratio,
            score_cutoff=70  # Lower threshold to handle encoding issues
        )

        if best_match:
            matched_street, score = best_match[0], best_match[1]
            street_data = self.street_groups.get_group(matched_street)

            logger.info(f"Fuzzy matched '{street_clean}' to '{matched_street}' (score: {score})")

            # Try to find specific number or use midpoint
            if parsed['number']:
                number_match = street_data[street_data['NUMBER'].astype(str) == str(parsed['number'])]
                if not number_match.empty:
                    row = number_match.iloc[0]
                    return GeocodingResult(
                        lat=row['LAT'],
                        lon=row['LON'],
                        district=row['DISTRICT'],
                        confidence='fuzzy',
                        match_details=f"Fuzzy match: {row['STREET']} {row['NUMBER']} (score: {score})",
                        original_address=original
                    )

            return self._get_street_midpoint(street_data, parsed, original, confidence='fuzzy')

        return None

    def _get_street_midpoint(self, street_data: pd.DataFrame, parsed: Dict,
                             original: str, confidence: str = 'exact') -> GeocodingResult:
        """Calculate midpoint of all addresses on a street."""
        # Use the centroid of all points on the street
        lat_mean = street_data['LAT'].mean()
        lon_mean = street_data['LON'].mean()

        # Use most common district
        district = street_data['DISTRICT'].mode().iloc[0] if not street_data['DISTRICT'].mode().empty else ''

        return GeocodingResult(
            lat=lat_mean,
            lon=lon_mean,
            district=district,
            confidence=confidence,
            match_details=f"Street midpoint: {street_data.iloc[0]['STREET']} ({len(street_data)} addresses)",
            original_address=original
        )

    def _try_postcode_match(self, parsed: Dict, original: str) -> Optional[GeocodingResult]:
        """Use postcode centroid as fallback."""
        postcode = parsed['postcode']
        if not postcode:
            return None

        if postcode in self.postcode_groups.groups:
            postcode_data = self.postcode_groups.get_group(postcode)

            # Use centroid of all addresses in this postcode
            lat_mean = postcode_data['LAT'].mean()
            lon_mean = postcode_data['LON'].mean()
            district = postcode_data['DISTRICT'].mode().iloc[0] if not postcode_data['DISTRICT'].mode().empty else ''

            return GeocodingResult(
                lat=lat_mean,
                lon=lon_mean,
                district=district,
                confidence='postcode',
                match_details=f"Postcode centroid: {postcode} ({len(postcode_data)} addresses)",
                original_address=original
            )

        return None

    def _geocode_box_address(self, parsed: Dict, original: str) -> Optional[GeocodingResult]:
        """
        Handle Box addresses. In Sweden, these are typically at post offices.
        We'll need external geocoding for these.
        """
        box_number = parsed['number']
        postcode = parsed['postcode']
        city = parsed['city']

        # Create a searchable address
        search_address = f"Box {box_number}, {postcode} {city}, Sverige"

        # Check cache first
        if search_address in self.box_address_cache:
            cached = self.box_address_cache[search_address]
            return GeocodingResult(
                lat=cached['lat'],
                lon=cached['lon'],
                district=cached.get('district', ''),
                confidence='box',
                match_details=f"Box address (cached): {search_address}",
                original_address=original
            )

        # Try external geocoding
        result = self._try_external_geocoding(search_address)
        if result:
            result.confidence = 'box'
            result.match_details = f"Box address (geocoded): {search_address}"
            # Cache for future use
            self.box_address_cache[search_address] = {
                'lat': result.lat,
                'lon': result.lon,
                'district': result.district
            }

        return result

    def _try_external_geocoding(self, address: str) -> Optional[GeocodingResult]:
        """Use external geocoding service as last resort."""
        # Check if external geocoding is enabled
        if not self.use_external_geocoding:
            logger.debug(f"External geocoding disabled, skipping: {address}")
            return None

        try:
            # Add country for better results
            if "Sverige" not in address and "Sweden" not in address:
                address += ", Sverige"

            location = self.external_geocoder(address)
            if location:
                # Try to determine district from coordinates
                district = self._find_district_for_coords(location.latitude, location.longitude)

                return GeocodingResult(
                    lat=location.latitude,
                    lon=location.longitude,
                    district=district,
                    confidence='external',
                    match_details=f"External geocoding: {location.address}",
                    original_address=address
                )
        except Exception as e:
            logger.error(f"External geocoding failed for '{address}': {e}")

        return None

    def _find_district_for_coords(self, lat: float, lon: float, radius_km: float = 1.0) -> str:
        """Find district for given coordinates by finding nearest address."""
        # Calculate distances to all addresses (simplified, not haversine)
        self.muni_df['dist'] = np.sqrt(
            (self.muni_df['LAT'] - lat) ** 2 +
            (self.muni_df['LON'] - lon) ** 2
        )

        # Find nearest address
        nearest = self.muni_df.nsmallest(1, 'dist')
        if not nearest.empty:
            return nearest.iloc[0]['DISTRICT']

        return ''

    def geocode_batch(self, addresses: List[str], desc: str = "Geocoding") -> List[Optional[GeocodingResult]]:
        """Geocode a batch of addresses with progress tracking."""
        results = []

        logger.info(f"Starting batch geocoding of {len(addresses)} addresses...")

        for i, address in enumerate(addresses):
            if i % 100 == 0:
                logger.info(f"{desc}: {i}/{len(addresses)} ({i / len(addresses) * 100:.1f}%)")

            result = self.geocode_address(address)
            results.append(result)

            # Small delay to prevent overwhelming external service
            if result and result.confidence == 'external':
                time.sleep(0.1)

        # Summary statistics
        confidences = [r.confidence for r in results if r]
        for conf in ['exact', 'fuzzy', 'postcode', 'box', 'external']:
            count = confidences.count(conf)
            if count > 0:
                logger.info(f"  {conf}: {count} ({count / len(addresses) * 100:.1f}%)")

        failed = len([r for r in results if r is None])
        if failed > 0:
            logger.warning(f"  Failed: {failed} ({failed / len(addresses) * 100:.1f}%)")

        return results


def geocode_associations(associations_csv: str, municipality_csv: str, output_csv: str):
    """Geocode all associations and save results."""
    logger.info("Loading associations...")
    assoc_df = pd.read_csv(associations_csv, encoding='utf-8')

    # Initialize geocoder
    geocoder = MunicipalityGeocoder(municipality_csv)

    # Extract addresses (handling the specific format)
    addresses = []
    for _, row in assoc_df.iterrows():
        # Combine address components, skipping Co Adress
        address_parts = []
        if pd.notna(row.get('Adress')):
            address_parts.append(str(row['Adress']))
        if pd.notna(row.get('Post Nr')):
            address_parts.append(str(row['Post Nr']))
        if pd.notna(row.get('Postort')):
            address_parts.append(str(row['Postort']))

        address = ', '.join(address_parts)
        addresses.append(address)

    # Geocode all addresses
    results = geocoder.geocode_batch(addresses, desc="Associations")

    # Add results to dataframe
    assoc_df['lat'] = [r.lat if r else None for r in results]
    assoc_df['lon'] = [r.lon if r else None for r in results]
    assoc_df['district'] = [r.district if r else None for r in results]
    assoc_df['geocoding_confidence'] = [r.confidence if r else 'failed' for r in results]
    assoc_df['geocoding_details'] = [r.match_details if r else 'Geocoding failed' for r in results]

    # Save results
    assoc_df.to_csv(output_csv, index=False, encoding='utf-8')
    logger.info(f"Saved geocoded associations to {output_csv}")

    # Report success rate
    success_rate = (assoc_df['lat'].notna().sum() / len(assoc_df)) * 100
    logger.info(f"Successfully geocoded {success_rate:.1f}% of associations")


def geocode_companies(companies_csv: str, municipality_csv: str, output_csv: str):
    """Geocode all companies and save results."""
    logger.info("Loading companies...")
    comp_df = pd.read_csv(companies_csv, encoding='utf-8')

    # Initialize geocoder
    geocoder = MunicipalityGeocoder(municipality_csv)

    # Extract addresses
    addresses = comp_df['registered_address'].tolist()

    # Geocode all addresses
    results = geocoder.geocode_batch(addresses, desc="Companies")

    # Add results to dataframe
    comp_df['lat'] = [r.lat if r else None for r in results]
    comp_df['lon'] = [r.lon if r else None for r in results]
    comp_df['geocoding_confidence'] = [r.confidence if r else 'failed' for r in results]
    comp_df['geocoding_details'] = [r.match_details if r else 'Geocoding failed' for r in results]

    # Verify district matches
    comp_df['district_verified'] = [
        r.district == row['district'] if r and r.district else False
        for r, (_, row) in zip(results, comp_df.iterrows())
    ]

    # Save results
    comp_df.to_csv(output_csv, index=False, encoding='utf-8')
    logger.info(f"Saved geocoded companies to {output_csv}")

    # Report success rate
    success_rate = (comp_df['lat'].notna().sum() / len(comp_df)) * 100
    logger.info(f"Successfully geocoded {success_rate:.1f}% of companies")


def main():
    """Main function to geocode both associations and companies."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"

    municipality_csv = data_dir / "municipality_of_goteborg.csv"
    associations_csv = data_dir / "gothenburg_associations.csv"
    companies_csv = data_dir / "gothenburg_companies_addresses.csv"

    # Output files
    associations_output = data_dir / "associations_geocoded.csv"
    companies_output = data_dir / "companies_geocoded.csv"

    # Geocode associations
    logger.info("=" * 50)
    logger.info("GEOCODING ASSOCIATIONS")
    logger.info("=" * 50)
    geocode_associations(str(associations_csv), str(municipality_csv), str(associations_output))

    # Geocode companies
    logger.info("\n" + "=" * 50)
    logger.info("GEOCODING COMPANIES")
    logger.info("=" * 50)
    geocode_companies(str(companies_csv), str(municipality_csv), str(companies_output))

    logger.info("\nGeocoding complete!")


if __name__ == "__main__":
    main()
