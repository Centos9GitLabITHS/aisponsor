# sponsor_match/app.py
import streamlit as st, pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
from sponsor_match.service import recommend

# ──────────────────────────────────────────────
# 1. Load clubs once per session
# ──────────────────────────────────────────────
DATA  = Path(__file__).resolve().parents[1] / "data" / "associations_goteborg.csv"
clubs = pd.read_csv(DATA)          # may contain: name, lat, lon, (optionally) size_bucket

# if the CSV has no size_bucket → derive a default (≤100 small, 101-500 medium, else large)
if "size_bucket" not in clubs.columns:
    # feel free to tweak these thresholds later
    EMP_COL = "members"           # change if you add a member-count column
    if EMP_COL in clubs.columns:
        bins   = [0, 100, 500, float("inf")]
        labels = ["small", "medium", "large"]
        clubs["size_bucket"] = pd.cut(clubs[EMP_COL], bins=bins, labels=labels)
    else:
        clubs["size_bucket"] = "small"   # fallback – mark everyone as small

# tidy & sort
clubs = clubs.sort_values("name").reset_index(drop=True)


# ──────────────────────────────────────────────
# 2.  UI  – choose club OR enter address
# ──────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    club_name = st.selectbox(
        "Pick your association (optional)",
        ["— choose —"] + clubs["name"].tolist(),
        index=0,
    )
with c2:
    free_addr = st.text_input("…or paste an address / post-code")

size_bucket = st.selectbox(
    "Association size",
    ["small", "medium", "large"],
    index=1 if club_name == "— choose —" else
           ["small", "medium", "large"].index(
               clubs.loc[clubs.name.eq(club_name), "size_bucket"].iloc[0]
           )
           if club_name != "— choose —" else 0
)

if st.button("Search"):
    # ── Figure out coordinates ──────────────────
    if club_name != "— choose —":
        row = clubs.loc[clubs["name"] == club_name].iloc[0]

        # adapt the keys below to *exactly* match your CSV headers
        lat = float(row["lat"])  # or row["latitude"]
        lon = float(row["lon"])  # or row["longitude"]
    elif free_addr:
        geo = Nominatim(user_agent="sponsormatch_demo").geocode(free_addr + ", Sweden")
        if not geo:
            st.error("Couldn’t geocode that address – try something else.")
            st.stop()
        lat, lon = geo.latitude, geo.longitude
    else:
        st.warning("Pick a club or enter an address first.")
        st.stop()

    # ── Call recommender ─────────────────────────
    matches = recommend(lat, lon, size_bucket)
    if matches.empty:
        st.info("No suitable companies found in this cluster yet.")
    else:
        st.subheader("Suggested sponsors")
        st.dataframe(matches, use_container_width=True)
