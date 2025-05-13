# sponsor_match/app.py  (shortened)
import streamlit as st, pandas as pd
from pathlib import Path
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from sponsor_match.service import recommend

DATA = Path(__file__).parents[1] / "data" / "associations_goteborg_with_coords.csv"
clubs = (pd.read_csv(DATA)
           .assign(size_bucket=lambda d:
                   pd.cut(d.member_count, [0,100,500,float("inf")],
                          labels=["small","medium","large"]))
           .sort_values("name"))

st.set_page_config("SponsorMatch AI", layout="wide")
st.title("⚽ SponsorMatch AI")

# ── input row ──────────────────────────────────────────
club_name = st.selectbox("Pick your club", ["— choose —", *clubs.name])
addr_in   = st.text_input("…or enter an address / post-code in Göteborg")
if club_name != "— choose —":
    size = clubs.loc[clubs.name.eq(club_name), "size_bucket"].iat[0]
else:
    size = st.selectbox("Club size", ["small","medium","large"], index=1)

# ── resolve lat/lon ────────────────────────────────────
if st.button("Find sponsors"):
    with st.spinner("Geocoding / matching…"):
        if club_name != "— choose —":
            lat, lon = clubs.loc[clubs.name.eq(club_name), ["lat","lon"]].iloc[0]
        else:
            geo = RateLimiter(Nominatim(user_agent="sponsormatch").geocode)
            loc = geo(addr_in+", Göteborg, Sweden")
            if not loc:
                st.error("Could not geocode that address.")
                st.stop()
            lat, lon = loc.latitude, loc.longitude

        matches = recommend(lat, lon, size)
    if matches.empty:
        st.info("No matches yet.")
    else:
        st.success(f"Top {len(matches)} suggested sponsors")
        st.dataframe(matches)

        # optional: map view
        import folium
        m = folium.Map(location=[lat, lon], zoom_start=11)
        for _, r in matches.iterrows():
            folium.Marker([r.lat, r.lon], popup=r.company_name).add_to(m)
        st_folium(m, use_container_width=True)
