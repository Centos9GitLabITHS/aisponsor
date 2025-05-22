# temp_ingest.py
import pandas as pd
from sponsor_match.core.db import get_engine

df = pd.read_csv('data/gothenburg_associations.csv')
df_clean = pd.DataFrame({
    'name': df['Namn'],
    'address': df['Adress'] + ', ' + df['Post Nr'].fillna('') + ' ' + df['Postort'].fillna(''),
    'member_count': 100,  # Default value
    'lat': 57.7089,  # Default Gothenburg coordinates
    'lon': 11.9746,
    'size_bucket': 'medium',
    'founded_year': 2000
})

engine = get_engine()
df_clean.to_sql('associations', engine, if_exists='replace', index=False)
print(f"Loaded {len(df_clean)} associations")
