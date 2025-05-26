#!/usr/bin/env python3
"""
sponsor_match/ui/app.py

Streamlit entry-point for SponsorMatch AI:
- Sidebar fully hidden
- Folium map with OpenStreetMap tiles (stable)
- Fixed pixel sizing for the map
- Club search & sponsor discovery UI with navigation
"""

import sys
from pathlib import Path
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sponsor_match.services.service import SponsorMatchService
from sponsor_match.core.db import get_engine

# Constants
DEFAULT_MAX_DISTANCE = 25
DEFAULT_TOP_N = 10
SCORE_THRESHOLD = 0.3
MAP_WIDTH = 700
MAP_HEIGHT = 400

# Page config
st.set_page_config(
    page_title="SponsorMatch AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit sidebar/menu
st.markdown(r"""
<style>
  [data-testid="stSidebar"] { display: none !important; }
  button[aria-label="Toggle sidebar"],
  button[aria-label="Collapse sidebar"],
  button[aria-label="Expand sidebar"] {
    display: none !important;
  }
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Cache SponsorMatch service
@st.cache_resource
def get_service() -> SponsorMatchService:
    engine = get_engine()
    return SponsorMatchService(engine)

# Folium map builder
def create_map(lat: float, lon: float, zoom: int = 12) -> folium.Map:
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,
        control_scale=True
    )
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors",
        name="OpenStreetMap",
        control=False,
        max_zoom=19
    ).add_to(m)
    return m

# Navigation bar

def render_navigation_bar():
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown("### 🎯 SponsorMatch AI")
    with col2:
        if st.button("🏠 Home", key="nav_home"):
            st.session_state.page = "home"
            st.rerun()
    with col3:
        if st.button("🔍 Find", key="nav_find"):
            st.session_state.page = "find"
            st.rerun()
    with col4:
        if st.button("📊 Results", key="nav_results"):
            st.session_state.page = "results"
            st.rerun()

# Pages

def render_home_page():
    st.markdown("## 🏠 Welcome to SponsorMatch AI")
    st.markdown("Use the navigation bar to start finding sponsors or reviewing results.")

def render_results_page():
    sponsors = st.session_state.get("sponsors")
    if sponsors is None or sponsors.empty:
        st.info("No sponsor results yet. Search for a club first.")
    else:
        df_s = sponsors.copy()
        df_s['Match Score'] = (df_s['score']*100).round(0).astype(int).astype(str) + '%'
        df_s['Distance (km)'] = df_s['distance'].round(1).astype(str) + ' km'
        st.subheader(f"Found {len(df_s)} Potential Sponsors")
        st.table(df_s[['name','Match Score','Distance (km)']])

def render_find_page(service):
    col1, _ = st.columns([4, 1])
    with col1:
        st.title("🔍 Find Sponsors for Your Club")
    st.markdown("---")

    left, right = st.columns([2, 3])

    with left:
        st.subheader("Search Your Club")
        club_query = st.text_input("🏆 Enter club name…", key="club_search")

        with st.expander("Search Options", expanded=True):
            max_distance = st.slider("Maximum distance (km)", 5, 100, DEFAULT_MAX_DISTANCE, key="max_distance")
            top_n = st.slider("Number of sponsors to find", 5, 50, DEFAULT_TOP_N, key="top_n")
            min_score = st.slider("Minimum match score", 0.0, 1.0, SCORE_THRESHOLD, step=0.1, format="%.1f", key="min_score")

        if club_query and len(club_query) >= 2:
            df_assoc = service.search(club_query)
            if "type" in df_assoc.columns:
                df_assoc = df_assoc[df_assoc["type"] == "association"]

            if not df_assoc.empty:
                st.markdown("### Select Your Club")
                for _, row in df_assoc.head(5).iterrows():
                    name = row.get("name", "")
                    addr = row.get("address") or row.get("Adress") or row.get("Postort")
                    label = name + (f" — {addr}" if addr else "")
                    if st.button(label, key=f"select_{row['id']}"):
                        st.session_state.selected_club = row.to_dict()
                        st.session_state.sponsors = None
                        st.rerun()
            else:
                st.info("No clubs found. Try another term.")

        club = st.session_state.selected_club
        if club:
            st.success(f"✅ Selected: **{club['name']}**")
            with st.expander("Club Details", expanded=True):
                st.write(f"• Size: {club.get('size_bucket','Unknown').capitalize()}")
                st.write(f"• Members: {club.get('member_count','N/A')}")
                addr = club.get("address") or club.get("Adress") or club.get("Postort")
                if addr:
                    st.write(f"• Address: {addr}")

            if st.button("🎯 Find Sponsors Now"):
                with st.spinner("Finding sponsors…"):
                    recs = service.recommend(
                        association_name=club['name'],
                        top_n=top_n,
                        max_distance=max_distance,
                    )
                    sponsors_df = pd.DataFrame(recs) if isinstance(recs, list) else recs
                    sponsors_df = sponsors_df[sponsors_df['score'] >= min_score]
                    st.session_state.sponsors = sponsors_df
                    st.rerun()

    with right:
        st.subheader("Sponsor Map")
        lat, lon, zoom = 57.7089, 11.9746, 11
        if club:
            club_lat = club.get('lat') or club.get('latitude')
            club_lon = club.get('lon') or club.get('longitude')
            if club_lat is not None and club_lon is not None:
                lat, lon, zoom = float(club_lat), float(club_lon), 13

        m = create_map(lat, lon, zoom)

        if club and lat is not None and lon is not None:
            folium.Marker([
                lat, lon
            ], popup=club.get('name', 'Selected Club'),
               icon=folium.Icon(color='purple', icon='flag', prefix='fa')).add_to(m)

        sponsors = st.session_state.sponsors
        if sponsors is not None and not sponsors.empty:
            for _, sp in sponsors.iterrows():
                popup_html = f"""
                <b>{sp['name']}</b><br>
                Score: {sp['score']*100:.0f}%<br>
                Address: {sp.get('address', 'Unknown')}<br>
                Size: {sp.get('size_bucket', 'Unknown').capitalize()}
                """
                folium.Marker([
                    sp['lat'], sp['lon']
                ], popup=folium.Popup(popup_html, max_width=250),
                   icon=folium.Icon(
                       color='darkgreen' if sp['score'] >= 0.8 else
                             'green' if sp['score'] >= 0.6 else 'orange',
                       icon='building', prefix='fa')).add_to(m)

        folium_static(m, width=MAP_WIDTH, height=MAP_HEIGHT)

# Main app entry

def main():
    if "page" not in st.session_state:
        st.session_state.page = "find"
    if "selected_club" not in st.session_state:
        st.session_state.selected_club = None
    if "sponsors" not in st.session_state:
        st.session_state.sponsors = None

    service = get_service()
    render_navigation_bar()

    if st.session_state.page == "home":
        render_home_page()
    elif st.session_state.page == "results":
        render_results_page()
    else:
        render_find_page(service)

if __name__ == '__main__':
    main()
