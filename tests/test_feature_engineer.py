# test_feature_engineer.py
from sponsor_match.models.features import FeatureEngineer
import pandas as pd

# Create test data
clubs_df = pd.DataFrame({
    'name': ['Test Club'],
    'lat': [57.7089],
    'lon': [11.9746],
    'size_bucket': ['medium']
})

companies_df = pd.DataFrame({
    'name': ['Company A', 'Company B', 'Company C'],
    'lat': [57.7200, 57.6900, 57.7500],
    'lon': [11.9800, 11.9600, 12.0000],
    'revenue_ksek': [5000, 10000, 2000],
    'employees': [50, 100, 20],
    'size_bucket': ['medium', 'large', 'small']
})

# Initialize FeatureEngineer and calculate features
engineer = FeatureEngineer()
features = engineer.create_features(
    pd.concat([clubs_df] * len(companies_df)).reset_index(drop=True),
    companies_df
)

# Print results
print(features)

# Test individual methods
print("\nDistance calculation:")
print(FeatureEngineer.calculate_distance_km(57.7089, 11.9746, 57.7200, 11.9800))

print("\nSize matching:")
print(FeatureEngineer.calculate_size_match(
    pd.Series(['small', 'medium', 'large']),
    pd.Series(['small', 'large', 'medium'])
))

