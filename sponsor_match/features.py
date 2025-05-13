from geopy.distance import geodesic
import pandas as pd

def distance_km(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).km

def add_distance(df: pd.DataFrame, lat, lon):
    df = df.copy()
    df["distance_km"] = df.apply(
        lambda r: distance_km(lat, lon, r.lat, r.lon), axis=1
    )
    return df

def assoc_size_bucket(members: int) -> str:
    if members < 200:
        return "small"
    if members < 1000:
        return "medium"
    return "large"
