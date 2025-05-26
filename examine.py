# examine.py
"""
Analyse failures in geocoded company addresses to identify common patterns.
"""
import pandas as pd  # Data analysis

# Load geocoded companies CSV from current directory
df = pd.read_csv('data/companies_geocoded.csv')

# Filter entries marked as 'failed' in geocoding confidence
failed = df[df['geocoding_confidence'] == 'failed']

# Show most frequent failed addresses for manual inspection
print("Common patterns in failed addresses:")
print(failed['registered_address'].value_counts().head(20))

# Summary statistics on failure rate
total_failures = len(failed)
print(f"\nTotal failed addresses: {total_failures}")
print(f"Percentage of total: {total_failures / len(df) * 100:.1f}%")

# Group failures by district to see geographic trends
print("\nFailed geocoding by district:")
print(failed['district'].value_counts().head(10))

# Identify common terms in failed addresses (length > 3 characters)
common_terms = {}
for address in failed['registered_address'].dropna():
    for word in address.lower().split():
        if len(word) > 3:
            common_terms[word] = common_terms.get(word, 0) + 1

print("\nCommon terms in failed addresses:")
for term, count in sorted(common_terms.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  '{term}': {count} occurrences")
