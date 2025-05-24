# examine.py - corrected version
import pandas as pd

# Since we're already in the data directory, just use the filename
df = pd.read_csv('companies_geocoded.csv')

# Filter to failed geocoding
failed = df[df['geocoding_confidence'] == 'failed']

# Look for patterns
print("Common patterns in failed addresses:")
print(failed['registered_address'].value_counts().head(20))

# Let's also understand more about these failures
print(f"\nTotal failed addresses: {len(failed)}")
print(f"Percentage of total: {len(failed) / len(df) * 100:.1f}%")

# Check if certain districts have more failures
print("\nFailed geocoding by district:")
district_failures = failed['district'].value_counts()
print(district_failures.head(10))

# Look for common words in failed addresses
print("\nCommon terms in failed addresses:")
common_terms = {}
for address in failed['registered_address'].dropna():
    words = address.lower().split()
    for word in words:
        if len(word) > 3:  # Skip short words
            common_terms[word] = common_terms.get(word, 0) + 1

# Sort by frequency
sorted_terms = sorted(common_terms.items(), key=lambda x: x[1], reverse=True)
for term, count in sorted_terms[:15]:
    print(f"  '{term}': {count} occurrences")