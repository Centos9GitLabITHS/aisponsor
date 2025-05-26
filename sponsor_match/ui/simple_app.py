#!/usr/bin/env python3
# pylint: disable=unused-import, unused-variable, duplicate-code
"""
sponsor_match/ui/simple_app.py
FINAL VERSION - Streamlit UI for Golden Goal.
"""

import sys
from pathlib import Path

import folium
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the service and database engine
from sponsor_match.services.service import SponsorMatchService

# Page configuration
st.set_page_config(
    page_title="Golden Goal",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar, main menu, footer
st.markdown("""
<style>
section[data-testid="stSidebar"] {display: none;}
button[data-testid="collapsedControl"] {display: none !important;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Navigation buttons styling
st.markdown("""
<style>
div.stButton > button {
    background-color: #2563eb;
    color: white;
    width: 120px; height: 40px;
    font-size: 1rem;
    border-radius: 0.5rem;
    border: none;
    transition: all 0.3s;
}
div.stButton > button:hover {
    background-color: #1d4ed8;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}
h1 { font-size: clamp(1.5rem, 4vw, 2.5rem) !important; color: #1e40af; }
h2 { font-size: clamp(1.25rem, 3vw, 2rem) !important; color: #1e40af; }
h3 { font-size: clamp(1rem, 2vw, 1.5rem) !important; color: #2563eb; }
@media screen and (max-width: 768px) {
  .block-container .responsive-row { display: block !important; }
  .block-container .responsive-row > div { width: 100% !important; margin-bottom: 1rem; }
}
</style>
""", unsafe_allow_html=True)


# Initialize or cache the SponsorMatchService
@st.cache_resource
def get_service():
    """Initialize SponsorMatchService once."""
    # For Streamlit Cloud, pass None to use CSV mode
    return SponsorMatchService(None)


# Navigation helpers
def navigate_to(page: str):
    st.session_state.page = page
    st.rerun()


def render_navigation():
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("### 🎯 Golden Goal")
    with col2:
        if st.button("🏠 Home", key="nav_home"):
            st.session_state.page = "home"
            st.rerun()
    with col3:
        if st.button("🔍 Find", key="nav_find"):
            st.session_state.page = "find_sponsors"
            st.rerun()
    with col4:
        if st.button("👤 Profile", key="nav_profile"):
            st.session_state.page = "profile"
            st.rerun()


# Home page rendering
def render_home_page():
    st.title("Welcome to Golden Goal")
    st.markdown("### Find sponsors for your club/association using AI-powered matching")
    st.markdown("""
- 📍 **Geographic proximity**  
- 📏 **Size compatibility**  
- 🎯 **Smart scoring**  
- 🗺️ **Interactive map**

**Database:** 169 associations, 82,776 companies
""")
    if st.button("🎯 FIND SPONSORS NOW", key="home_find_now"):
        st.session_state.last_search_distance = 25
        navigate_to('find_sponsors')


# Utility to create a base map
def create_map(center_lat=57.7089, center_lon=11.9746, zoom=11):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom,
                   tiles=None, control_scale=True)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors",
        name="OpenStreetMap", control=False, max_zoom=19
    ).add_to(m)
    return m


# Find sponsors page rendering
def render_find_sponsors_page():
    service = get_service()
    st.markdown('<div class="responsive-row">', unsafe_allow_html=True)
    title_col, map_col = st.columns(2)
    with title_col:
        st.title("🔍 Find Sponsors for Your Association")
    with map_col:
        lat, lon, zoom = 57.7089, 11.9746, 11
        assoc = st.session_state.get('selected_association')
        if assoc:
            lat = assoc.get('latitude', assoc.get('lat'))
            lon = assoc.get('longitude', assoc.get('lon'))
            zoom = 13
        m = create_map(lat, lon, zoom)

        # Add association marker if selected
        if assoc:
            popup = f"<b>{assoc['name']}</b><br>Size: {assoc['size_bucket']}"
            folium.Marker([lat, lon], popup=popup,
                          icon=folium.Icon(color='red', icon='star')).add_to(m)
            radius = st.session_state.get('last_search_distance', 0) * 1000
            folium.Circle([lat, lon], radius=radius, color='red',
                          fill=True, fill_opacity=0.1).add_to(m)

        # ADD COMPANY MARKERS FROM SEARCH RESULTS
        if st.session_state.get('search_results') is not None:
            sponsors = st.session_state.search_results
            # Add markers for top companies
            for idx, company in sponsors.head(20).iterrows():  # Show top 20 to avoid cluttering
                company_lat = company.get('latitude', company.get('lat'))
                company_lon = company.get('longitude', company.get('lon'))
                if company_lat and company_lon:
                    # Color based on score
                    score = company.get('score', 0)
                    if score >= 0.8:
                        color = 'green'
                    elif score >= 0.6:
                        color = 'lightgreen'
                    elif score >= 0.4:
                        color = 'orange'
                    else:
                        color = 'lightred'

                    popup_text = f"""
                    <b>{company.get('name', 'Unknown')}</b><br>
                    Score: {score * 100:.1f}%<br>
                    Distance: {company.get('distance_km', company.get('distance', 0)):.1f} km<br>
                    Size: {company.get('size_bucket', 'Unknown')}<br>
                    Industry: {company.get('industry', 'Unknown')}
                    """

                    folium.Marker(
                        [company_lat, company_lon],
                        popup=popup_text,
                        icon=folium.Icon(color=color, icon='briefcase', prefix='fa')
                    ).add_to(m)

        # Display the map
        st_folium(m, width=700, height=400, returned_objects=[])
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Search for your association", key="assoc_search")
    with col2:
        max_dist = st.slider("Max distance (km)", 5, 50, 10, key="max_distance_slider")

    # Perform search when user enters a query
    if query and len(query) >= 1:
        df = service.search(query)
        if 'type' in df.columns:
            df = df[df['type'] == 'association']
        if not df.empty:
            st.markdown("### Select Your Association")
            for _, row in df.head(5).iterrows():
                emoji = {'small': '🏠', 'medium': '🏢', 'large': '🏛️'}.get(row['size_bucket'], '🏠')
                c1, c2, c3 = st.columns([1, 3, 1])
                with c1:
                    st.markdown(f"### {emoji}")
                with c2:
                    st.markdown(f"**{row['name']}**")
                    addr_parts = [row.get('address'), row.get('Adress'), row.get('Postort')]
                    caption = ", ".join(filter(None, addr_parts)) or "No address available"
                    st.caption(caption)
                with c3:
                    if st.button("Select", key=f"sel_{row['id']}"):
                        st.session_state.selected_association = row.to_dict()
                        st.session_state.last_search_distance = max_dist
                        st.rerun()
        else:
            st.info("No associations found. Try a different search term.")

    assoc = st.session_state.get('selected_association')
    if assoc:
        st.markdown("---")
        st.markdown("### Selected Association")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Name", assoc['name'])
        size_desc = {'small': 'Small (0-399)', 'medium': 'Medium (400-799)', 'large': 'Large (800+)'}
        with c2:
            st.metric("Size", size_desc.get(assoc['size_bucket'], assoc['size_bucket']))
        with c3:
            st.metric("Location", assoc.get('Postort', 'Göteborg'))
        if st.button("🎯 FIND SPONSORS NOW", key="find_now"):
            st.session_state.last_search_distance = max_dist
            sponsors = service.recommend(association_name=assoc['name'],
                                         top_n=50, max_distance=max_dist)
            if not sponsors.empty:
                if 'rank' not in sponsors.columns:
                    sponsors['rank'] = range(1, len(sponsors) + 1)
                if 'distance' in sponsors.columns and 'distance_km' not in sponsors.columns:
                    sponsors['distance_km'] = sponsors['distance']
                st.session_state.search_results = sponsors
                st.success(f"Found {len(sponsors)} potential sponsors!")
                st.rerun()
            else:
                st.warning("No sponsors found within the specified distance.")

    if st.session_state.get('search_results') is not None:
        st.markdown("---")
        render_search_results()


# Render the recommendations results
def render_search_results():
    sponsors = st.session_state.search_results
    if 'size_bucket' not in sponsors.columns:
        sponsors['size_bucket'] = 'Unknown'
    if 'display_name' not in sponsors.columns:
        sponsors['display_name'] = sponsors.apply(lambda r: r.get('name', f"Company_{r.get('id', '')}"), axis=1)
    if 'distance_km' not in sponsors.columns and 'distance' in sponsors.columns:
        sponsors['distance_km'] = sponsors['distance']

    tab1, tab2, tab3 = st.tabs(["📊 Grid View", "📋 List View", "📈 Analytics"])
    with tab1:
        cols = st.columns(3)
        for i, sp in sponsors.head(12).iterrows():
            with cols[i % 3]:
                st.markdown(f"**{sp['display_name']}**")
                st.metric("Score", f"{sp['score'] * 100:.1f}%", delta=None)
                st.caption(f"Distance: {sp.get('distance_km', sp.get('distance', 0)):.1f} km")
    with tab2:
        st.dataframe(sponsors[['rank', 'display_name', 'size_bucket', 'score', 'distance_km']])
    with tab3:
        fig = px.histogram(sponsors, x='score', nbins=10, title="Score Distribution")
        st.plotly_chart(fig, use_container_width=True)


if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_association" not in st.session_state:
    st.session_state.selected_association = None
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "last_search_distance" not in st.session_state:
    st.session_state.last_search_distance = 25

render_navigation()
if st.session_state.page == "home":
    render_home_page()
elif st.session_state.page == "find_sponsors":
    render_find_sponsors_page()
else:
    st.write("Page under construction")
