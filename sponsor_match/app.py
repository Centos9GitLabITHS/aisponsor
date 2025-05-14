#!/usr/bin/env python3
"""
sponsor_match/app.py
---------------------
Streamlit app entrypoint for SponsorMatch AI (v1).

Run with:
    streamlit run sponsor_match/app.py
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

from sponsor_match.services.recommendation import RecommendationService
from sponsor_match.services.service_v2 import RecommendationRequest
from sponsor_match.core.db import get_engine

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

DATA_FILE = Path(__file__).parents[1] / "data" / "associations_goteborg_with_coords.csv"

def load_clubs(data_file: Path) -> pd.DataFrame:
    """Load and preprocess club data from CSV."""
    df = pd.read_csv(data_file)
    df = df.sort_values("name")
    if "size_bucket" not in df.columns:
        bins = [0, 100, 500, float("inf")]
        labels = ["small", "medium", "large"]
        df["size_bucket"] = pd.cut(df["member_count"], bins=bins, labels=labels)
    return df

def geocode_location(address: str) -> tuple[float, float]:
    """Geocode an address in Göteborg, Sweden, returning (lat, lon)."""
    geocoder = RateLimiter(Nominatim(user_agent="sponsormatch").geocode)
    loc = geocoder(f"{address}, Göteborg, Sweden")
    if not loc:
        raise ValueError(f"Could not geocode address: {address}")
    return loc.latitude, loc.longitude

def main() -> None:
    """Render the Streamlit UI and handle user interactions."""
    st.set_page_config(page_title="⚽ SponsorMatch AI", layout="wide")
    st.title("Find matching sponsors in Göteborg")

    clubs = load_clubs(DATA_FILE)
    club_names = ["— choose —", *clubs["name"]]

    col1, col2 = st.columns(2)
    club_sel = col1.selectbox("Choose your club", club_names)
    address_input = col2.text_input("…or type an address / post-code in Göteborg")

    if club_sel != "— choose —":
        default_bucket = clubs.loc[clubs["name"] == club_sel, "size_bucket"].iat[0]
    else:
        default_bucket = "medium"

    size_bucket = st.selectbox(
        "Club size",
        ["small", "medium", "large"],
        index=["small", "medium", "large"].index(default_bucket)
    )

    if st.button("Search"):
        with st.spinner("Geocoding & matching…"):
            try:
                if club_sel != "— choose —":
                    row = clubs.loc[clubs["name"] == club_sel].iloc[0]
                    lat, lon = float(row["lat"]), float(row["lon"])
                    if pd.isna(lat) or pd.isna(lon):
                        st.error("That club is still missing coordinates – run the ingest pipeline.")
                        return
                    club_id = int(row["id"]) if "id" in row else None
                else:
                    if not address_input:
                        st.warning("Enter an address or pick a club first.")
                        return
                    lat, lon = geocode_location(address_input)
                    club_id = None

                service = RecommendationService(get_engine(), models=None)
                request = RecommendationRequest(
                    club_id=club_id,
                    lat=lat,
                    lon=lon,
                    size_bucket=size_bucket
                )
                result = service.recommend(request)
                matches = result.companies

                if matches.empty:
                    st.info("No matches found for these parameters.")
                    return

                st.success(f"Top {len(matches)} suggested sponsors")
                st.dataframe(matches)

                # Render map
                m = folium.Map(location=[lat, lon], zoom_start=11)
                folium.Marker([lat, lon], popup="Your club").add_to(m)
                for _, comp in matches.iterrows():
                    folium.Marker(
                        [comp["lat"], comp["lon"]],
                        popup=comp.get("name", "")
                    ).add_to(m)
                st_folium(m, use_container_width=True)

            except Exception as e:
                logger.exception("Error during search: %s", e)
                st.error(str(e))

if __name__ == "__main__":
    main()
