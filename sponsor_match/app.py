# sponsor_match/app.py  – v1.1 (handles blanks, adds map & nicer UX)
import streamlit as st, pandas as pd, folium, pathlib
from streamlit_folium import st_folium
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from sponsor_match.service import recommend

DATA = pathlib.Path(__file__).parents[1] / "data" / "associations_goteborg_with_coords.csv"
clubs = pd.read_csv(DATA).sort_values("name")

# derive size bucket on-the-fly if column absent
if "size_bucket" not in clubs.columns:
    clubs["size_bucket"] = pd.cut(
        clubs["member_count"], [0, 100, 500, float("inf")],
        labels=["small", "medium", "large"]
    )

st.set_page_config(page_title="⚽ SponsorMatch AI", layout="wide")
st.title("Find matching sponsors in Göteborg")

col1, col2 = st.columns(2)
club_sel = col1.selectbox("Choose your club", ["— choose —", *clubs.name])
addr_txt = col2.text_input("…or type an address / post-code in Göteborg")

if club_sel != "— choose —":
    default_bucket = clubs.loc[clubs.name == club_sel, "size_bucket"].iat[0]
else:
    default_bucket = "medium"

size_bucket = st.selectbox(
    "Club size", ["small", "medium", "large"],
    index=["small","medium","large"].index(default_bucket)
)

if st.button("Search"):
    with st.spinner("Geocoding & matching…"):
        # resolve coordinates
        if club_sel != "— choose —":
            row = clubs.loc[clubs.name == club_sel].iloc[0]
            if pd.isna(row.lat) or pd.isna(row.lon):
                st.error("That club is still missing coordinates – run build_associations_csv again.")
                st.stop()
            lat, lon = float(row.lat), float(row.lon)
        else:
            if not addr_txt:
                st.warning("Enter an address or pick a club first.")
                st.stop()
            geo = RateLimiter(Nominatim(user_agent="sponsormatch").geocode)
            loc = geo(addr_txt + ", Göteborg, Sweden")
            if not loc:
                st.error("Could not geocode that address.")
                st.stop()
            lat, lon = loc.latitude, loc.longitude

        matches = recommend(lat, lon, size_bucket)
    if matches.empty:
        st.info("No matches yet for this cluster.")
    else:
        st.success(f"Top {len(matches)} suggested sponsors")
        st.dataframe(matches)

        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon], popup="Your club").add_to(m)
        for _, r in matches.iterrows():
            folium.Marker([r.lat, r.lon], popup=r.company_name).add_to(m)
        st_folium(m, use_container_width=True)
