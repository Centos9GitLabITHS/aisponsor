# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

"""
sponsor_match/services/simple_service.py
FINAL FIX - Service layer that handles Swedish company data correctly
"""

import logging
import math
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleSponsorService:
    """Enhanced service that integrates with ML models and handles Swedish data correctly."""

    def __init__(self):
        """Load data and models once at startup."""
        print("Loading prepared data and ML models...")

        # Get the project root directory
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent

        # Build paths to data files
        assoc_path = project_root / 'data' / 'associations_prepared.csv'
        comp_path = project_root / 'data' / 'companies_prepared.csv'

        # Check if prepared files exist
        if not assoc_path.exists():
            raise FileNotFoundError(f"Associations file not found at {assoc_path}. Run prepare_all_data.py first!")
        if not comp_path.exists():
            raise FileNotFoundError(f"Companies file not found at {comp_path}. Run prepare_all_data.py first!")

        # Load prepared data
        self.associations = pd.read_csv(assoc_path)
        self.companies = pd.read_csv(comp_path)

        # Create display names for companies
        self._create_company_names()

        # Load ML models
        self.models = self._load_models(project_root)

        # Define enhanced size compatibility matrix
        self.size_compatibility = {
            # Association size -> Company size compatibility scores
            # Small associations work best with small/medium companies
            ('small', 'small'): 1.0,
            ('small', 'medium'): 0.9,
            ('small', 'large'): 0.6,
            ('small', 'enterprise'): 0.4,

            # Medium associations have more flexibility
            ('medium', 'small'): 0.7,
            ('medium', 'medium'): 1.0,
            ('medium', 'large'): 0.9,
            ('medium', 'enterprise'): 0.7,

            # Large associations need substantial sponsors
            ('large', 'small'): 0.4,
            ('large', 'medium'): 0.7,
            ('large', 'large'): 1.0,
            ('large', 'enterprise'): 0.95,
        }

        print(f"Loaded {len(self.associations)} associations and {len(self.companies)} companies")
        print(f"ML models loaded: {list(self.models.keys())}")

    def _create_company_names(self):
        """Create readable display names for companies."""
        # For Swedish companies, create names from district and org number
        if 'name' not in self.companies.columns or self.companies['name'].str.startswith('Company_').any():
            self.companies['display_name'] = self.companies.apply(
                lambda row: self._generate_company_name(row), axis=1
            )
        else:
            self.companies['display_name'] = self.companies['name']

    def _generate_company_name(self, row):
        """Generate a readable company name from available data."""
        # Try to use district + last 6 digits of org number
        district = row.get('district', 'Göteborg')
        org_nr = str(row.get('PeOrgNr', row.get('id', '')))

        # Common Swedish company types based on size
        company_types = {
            'small': ['Handelsbolag', 'Enskild Firma', 'HB', 'EF'],
            'medium': ['AB', 'Aktiebolag', 'Trading'],
            'large': ['AB', 'Group', 'International'],
            'enterprise': ['Group', 'International', 'Nordic']
        }

        # Get a company type based on size
        size = row.get('size_bucket', 'small')
        types = company_types.get(size, ['AB'])
        company_type = np.random.choice(types)

        # Create a more realistic name
        if district and district != 'Unknown':
            return f"{district} {company_type} ({org_nr[-6:]})"
        else:
            return f"Company {company_type} ({org_nr[-6:]})"

    def _load_models(self, project_root: Path) -> Dict:
        """Load clustering models if available."""
        models = {}
        models_dir = project_root / 'models'

        try:
            # Try to load default model
            default_path = models_dir / 'kmeans.joblib'
            if default_path.exists():
                models['default'] = joblib.load(default_path)
                logger.info("Loaded default clustering model")

            # Try to load large model
            large_path = models_dir / 'kmeans_large.joblib'
            if large_path.exists():
                models['large'] = joblib.load(large_path)
                logger.info("Loaded large clustering model")

        except Exception as e:
            logger.warning(f"Could not load ML models: {e}. Using distance-based scoring only.")

        return models

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance in kilometers between two points."""
        try:
            # Validate coordinates
            if any(pd.isna([lat1, lon1, lat2, lon2])):
                return float('inf')

            # Ensure coordinates are floats
            lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)

            # Radius of Earth in kilometers
            R = 6371.0

            # Convert to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))

            return R * c
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return float('inf')

    def search_associations(self, query):
        """Find associations by name with intelligent matching."""
        if not query or len(query) < 1:
            return pd.DataFrame()

        # Case-insensitive search with multiple strategies
        query_lower = query.lower()

        # Exact match
        exact_mask = self.associations['name'].str.lower() == query_lower

        # Contains match
        contains_mask = self.associations['name'].str.contains(query, case=False, na=False)

        # Starts with match
        starts_mask = self.associations['name'].str.lower().str.startswith(query_lower)

        # Combine matches with priority
        results = pd.concat([
            self.associations[exact_mask],
            self.associations[starts_mask & ~exact_mask],
            self.associations[contains_mask & ~starts_mask & ~exact_mask]
        ]).drop_duplicates()

        # Limit results
        return results.head(20)

    def _predict_cluster(self, lat: float, lon: float, size_bucket: str) -> Optional[int]:
        """Predict cluster for a given location using ML models."""
        if not self.models:
            return None

        try:
            # Choose model based on size
            model_key = 'large' if size_bucket == 'large' else 'default'
            model = self.models.get(model_key)

            if not model:
                return None

            # Handle both dict format (with scaler) and direct model
            if isinstance(model, dict):
                scaler = model.get('scaler')
                kmeans = model.get('kmeans')
                if scaler and kmeans:
                    features = np.array([[lat, lon]])
                    features_scaled = scaler.transform(features)
                    return int(kmeans.predict(features_scaled)[0])
            else:
                # Direct model (backward compatibility)
                features = np.array([[lat, lon]])
                return int(model.predict(features)[0])

        except Exception as e:
            logger.debug(f"Cluster prediction failed: {e}")
            return None

    def _calculate_cluster_score(self, assoc_cluster: Optional[int], comp_cluster: Optional[int]) -> float:
        """Calculate cluster matching score."""
        if assoc_cluster is None or comp_cluster is None:
            return 0.5  # Neutral score if no cluster info

        # Same cluster = high score
        if assoc_cluster == comp_cluster:
            return 1.0
        else:
            return 0.3  # Different cluster = lower score

    def find_sponsors(self, association_id, max_distance_km=25, limit=50):
        """
        Find companies near an association with ML-enhanced scoring.
        Returns companies with proper display names.
        """
        # Get association
        assoc = self.associations[self.associations['id'] == association_id]
        if assoc.empty:
            return pd.DataFrame()

        assoc = assoc.iloc[0]
        assoc_lat = assoc['latitude']
        assoc_lon = assoc['longitude']
        assoc_size = assoc['size_bucket']

        # Get association's cluster if ML models are available
        assoc_cluster = self._predict_cluster(assoc_lat, assoc_lon, assoc_size)

        # Calculate approximate lat/lon bounds for pre-filtering
        lat_degree_km = 111.0
        lon_degree_km = 111.0 * math.cos(math.radians(assoc_lat))

        # Add buffer to ensure we don't miss edge cases
        buffer = 1.2  # 20% buffer
        lat_delta = (max_distance_km * buffer) / lat_degree_km
        lon_delta = (max_distance_km * buffer) / lon_degree_km

        # Pre-filter companies by bounding box
        min_lat = assoc_lat - lat_delta
        max_lat = assoc_lat + lat_delta
        min_lon = assoc_lon - lon_delta
        max_lon = assoc_lon + lon_delta

        # Filter companies within bounding box first
        companies_in_bounds = self.companies[
            (self.companies['latitude'] >= min_lat) &
            (self.companies['latitude'] <= max_lat) &
            (self.companies['longitude'] >= min_lon) &
            (self.companies['longitude'] <= max_lon)
        ].copy()

        logger.info(f"Pre-filtered to {len(companies_in_bounds)} companies in bounding box (from {len(self.companies)} total)")

        # Calculate exact distances only for pre-filtered companies
        distances = []
        for _, company in companies_in_bounds.iterrows():
            dist = self.haversine_distance(
                assoc_lat, assoc_lon,
                company['latitude'], company['longitude']
            )
            distances.append(dist)

        companies_in_bounds['distance_km'] = distances

        # Filter by exact distance
        nearby = companies_in_bounds[companies_in_bounds['distance_km'] <= max_distance_km].copy()

        if nearby.empty:
            return pd.DataFrame()

        # Calculate enhanced scores
        scores = []
        for _, company in nearby.iterrows():
            # 1. Size compatibility score
            size_score = self.size_compatibility.get(
                (assoc_size, company['size_bucket']), 0.5
            )

            # 2. Distance score (exponential decay)
            distance_score = math.exp(-2 * company['distance_km'] / max_distance_km)

            # 3. Cluster matching score (if ML models available)
            comp_cluster = self._predict_cluster(
                company['latitude'],
                company['longitude'],
                company['size_bucket']
            )
            cluster_score = self._calculate_cluster_score(assoc_cluster, comp_cluster)

            # 4. Combined score with weights
            if self.models:
                # With ML models: 40% distance, 30% size, 30% cluster
                final_score = (
                    0.4 * distance_score +
                    0.3 * size_score +
                    0.3 * cluster_score
                )
            else:
                # Without ML models: 60% distance, 40% size
                final_score = (
                    0.6 * distance_score +
                    0.4 * size_score
                )

            scores.append({
                'final_score': final_score,
                'distance_score': distance_score,
                'size_score': size_score,
                'cluster_score': cluster_score
            })

        # Add scores to dataframe
        for key in ['final_score', 'distance_score', 'size_score', 'cluster_score']:
            nearby[key] = [s[key] for s in scores]

        # Rename final_score to score for compatibility
        nearby['score'] = nearby['final_score']

        # Sort by score (highest first)
        nearby = nearby.sort_values('score', ascending=False)

        # Add rank
        nearby['rank'] = range(1, len(nearby) + 1)

        # Ensure display_name is included
        if 'display_name' not in nearby.columns:
            nearby['display_name'] = nearby['name'] if 'name' in nearby.columns else nearby.apply(
                lambda row: self._generate_company_name(row), axis=1
            )

        # Return top results with all necessary columns
        return nearby.head(limit)

    def get_association_by_id(self, assoc_id):
        """Get single association details."""
        assoc = self.associations[self.associations['id'] == assoc_id]
        if not assoc.empty:
            return assoc.iloc[0].to_dict()
        return None

    def get_stats(self):
        """Get basic statistics for display."""
        assoc_sizes = self.associations['size_bucket'].value_counts().to_dict()
        comp_sizes = self.companies['size_bucket'].value_counts().to_dict()

        return {
            'total_associations': len(self.associations),
            'total_companies': len(self.companies),
            'associations_by_size': assoc_sizes,
            'companies_by_size': comp_sizes,
            'model_status': 'ML Enhanced' if self.models else 'Distance-based'
        }


# Test the service if run directly
if __name__ == "__main__":
    print("Testing SimpleSponsorService with ML integration...")

    try:
        service = SimpleSponsorService()

        # Test search
        print("\nSearching for 'IFK'...")
        results = service.search_associations("IFK")
        print(f"Found {len(results)} associations")
        if not results.empty:
            print(results[['name', 'id', 'size_bucket']].head())

            # Test sponsor finding with ML scoring
            first_id = results.iloc[0]['id']
            first_size = results.iloc[0]['size_bucket']
            print(f"\nFinding sponsors for association ID {first_id} (size: {first_size})...")
            sponsors = service.find_sponsors(first_id, max_distance_km=25)
            print(f"Found {len(sponsors)} sponsors")

            if not sponsors.empty:
                print("\nTop 5 sponsors with ML-enhanced scoring:")
                for _, sponsor in sponsors.head().iterrows():
                    print(f"\n  {sponsor.get('display_name', sponsor.get('name', 'Unknown'))} ({sponsor['size_bucket']})")
                    print(f"    Distance: {sponsor['distance_km']:.1f} km")
                    print(f"    Distance score: {sponsor['distance_score']:.2f}")
                    print(f"    Size score: {sponsor['size_score']:.2f}")
                    print(f"    Cluster score: {sponsor['cluster_score']:.2f}")
                    print(f"    Total score: {sponsor['score']*100:.0f}%")

        # Show stats
        stats = service.get_stats()
        print("\nSystem statistics:")
        print(f"Model status: {stats['model_status']}")
        print(f"Associations by size: {stats['associations_by_size']}")
        print(f"Companies by size: {stats['companies_by_size']}")

    except Exception as e:
        print(f"Error testing service: {e}")
        import traceback
        traceback.print_exc()
