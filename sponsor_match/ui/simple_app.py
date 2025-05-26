#!/usr/bin/env python3
# pylint: disable=unused-import, unused-variable, duplicate-code
"""
sponsor_match/ui/simple_app.py
FINAL VERSION - Map always visible on search page, sidebar disabled, fixed-button sizing, stable Folium tiles
"""

import sys
from pathlib import Path
import folium
import plotly.express as px
import streamlit as st
from streamlit_folium import folium_static

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import your services
from sponsor_match.services.service import SponsorMatchService
from sponsor_match.core.db import get_engine

# --- Page configuration & CSS tweaks ---
st.set_page_config(
    page_title="SponsorMatch AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar, main menu, footer
st.markdown("""
<style>
/* Hide entire sidebar */
section[data-testid="stSidebar"] {display: none;}
/* Hide collapsedControl (hamburger) */
button[data-testid="collapsedControl"] {display: none !important;}
/* Hide Streamlit menu and footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Hide Streamlit's sidebar expand/collapse control */
[data-testid="collapsedControl"] { display: none; }

/* Fixed-size navigation buttons */
div.stButton > button {
    background-color: #2563eb;
    color: white;
    width: 120px;
    height: 40px;
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

/* Responsive typography */
h1 { font-size: clamp(1.5rem, 4vw, 2.5rem) !important; color: #1e40af; }
h2 { font-size: clamp(1.25rem, 3vw, 2rem) !important; color: #1e40af; }
h3 { font-size: clamp(1rem, 2vw, 1.5rem) !important; color: #2563eb; }

/* Mobile layout fix for title/map columns */
@media screen and (max-width: 768px) {
  .block-container .responsive-row {
    display: block !important;
  }
  .block-container .responsive-row > div {
    width: 100% !important;
    margin-bottom: 1rem;
  }
}
</style>
""", unsafe_allow_html=True)

# --- Service initialization ---
@st.cache_resource
def get_service():
    """Initialize SponsorMatchService once and cache it"""
    engine = get_engine()
    return SponsorMatchService(engine)

# --- Navigation bar ---
def navigate_to(page: str):
    st.session_state.page = page
    st.rerun()

def render_navigation():
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("### 🎯 SponsorMatch AI")
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

# --- Page Rendering ---
def render_home_page():
    st.title("Welcome to SponsorMatch AI")
    st.markdown("### Find the perfect sponsors for your sports association using AI-powered matching")
    st.markdown("""
- 📍 **Geographic proximity**
- 📏 **Size compatibility**
- 🎯 **Smart scoring**
- 🗺️ **Interactive visualization**

**Database:** 169 associations, 82,776 companies
""")
    clicked = st.markdown("""
        <div style="text-align:center; margin-top: 1rem;">
            <form action="" method="post">
                <button type="submit" name="find_now" style="
                    background-color: #2563eb;
                    color: white;
                    padding: 0.75rem 1.5rem;
                    font-size: 1rem;
                    font-weight: 600;
                    border: none;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    transition: background 0.3s;
                ">
                    🎯 FIND SPONSORS NOW
                </button>
            </form>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("find_now") or st.query_params.get("find_now"):
        with st.spinner(f"Finding sponsors within {st.session_state.last_search_distance} km..."):
            navigate_to('find_sponsors')


def create_map(center_lat=57.7089, center_lon=11.9746, zoom=11):
    m = folium.Map(
        location=[center_lat, center_lon],
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
        if assoc:
            popup = f"<b>{assoc['name']}</b><br>Size: {assoc['size_bucket']}"
            folium.Marker([lat, lon], popup=popup, icon=folium.Icon(color='red', icon='star')).add_to(m)
            radius = st.session_state.get('last_search_distance', 0) * 1000
            folium.Circle([lat, lon], radius=radius, color='red', fill=True, fill_opacity=0.1).add_to(m)
        results = st.session_state.get('search_results')
        if results is not None:
            for _, s in results.head(20).iterrows():
                s_lat = s.get('latitude', s.get('lat', 0))
                s_lon = s.get('longitude', s.get('lon', 0))
                score = s.get('score', 0)
                color = 'darkgreen' if score>=0.8 else 'green' if score>=0.6 else 'orange' if score>=0.4 else 'lightgray'
                name = s.get('display_name', s.get('name', 'Company'))
                dist = s.get('distance_km', s.get('distance', 0))
                popup = f"<b>{name}</b><br>Score: {score*100:.0f}%<br>Distance: {dist:.1f}km"
                folium.Marker([s_lat, s_lon], popup=popup,
                              icon=folium.Icon(color=color, icon='building', prefix='fa')).add_to(m)
        folium_static(m, width=0, height=400)

    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Search for your association", key="assoc_search")
    with col2:
        max_dist = st.slider("Max distance (km)", 5, 50, 25, key="max_distance_slider")
    if query and len(query)>=1:
        df = service.search(query)
        if 'type' in df.columns:
            df = df[df['type']=='association']
        if not df.empty:
            st.markdown("### Select Your Association")
            for _, row in df.head(5).iterrows():
                emoji = {'small':'🏠','medium':'🏢','large':'🏛️'}.get(row['size_bucket'], '🏠')
                c1, c2, c3 = st.columns([1,3,1])
                with c1: st.markdown(f"### {emoji}")
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
        with c1: st.metric("Name", assoc['name'])
        size_desc = {'small':'Small (0-399)','medium':'Medium (400-799)','large':'Large (800+)'}
        with c2: st.metric("Size", size_desc.get(assoc['size_bucket'], assoc['size_bucket']))
        with c3: st.metric("Location", assoc.get('Postort','Göteborg'))
        if st.button("🎯 FIND SPONSORS NOW", key="find_now"):
            with st.spinner(f"Finding sponsors within {st.session_state.last_search_distance} km..."):
                sponsors = service.recommend(association_name=assoc['name'], top_n=50, max_distance=st.session_state.last_search_distance)
                if not sponsors.empty:
                    if 'rank' not in sponsors.columns:
                        sponsors['rank'] = range(1, len(sponsors)+1)
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


def render_search_results():
    sponsors = st.session_state.search_results
    # Ensure size_bucket exists to prevent KeyError if missing
    if 'size_bucket' not in sponsors.columns:
        sponsors['size_bucket'] = 'Unknown'
    if 'display_name' not in sponsors.columns:
        sponsors['display_name'] = sponsors.apply(
            lambda r: r.get('name', f"Company_{r.get('id','') }"), axis=1)
    if 'distance_km' not in sponsors.columns and 'distance' in sponsors.columns:
        sponsors['distance_km'] = sponsors['distance']
    tab1, tab2, tab3 = st.tabs(["📊 Grid View","📋 List View","📈 Analytics"])
    with tab1:
        cols = st.columns(3)
        for i, sp in sponsors.head(12).iterrows():
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:white;padding:1rem;border-radius:0.5rem;
                            box-shadow:0 2px 4px rgba(0,0,0,0.1);margin-bottom:1rem;">
                    <h4>{sp['display_name']}</h4>
                    <p><strong>Size:</strong> {sp['size_bucket'].capitalize()}</p>
                    <p><strong>Distance:</strong> {sp['distance_km']:.1f} km</p>
                    <p><strong>Score:</strong> {sp['score']*100:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
    with tab2:
        cols, col_names = [], []
        if 'rank' in sponsors.columns:
            cols.append('rank'); col_names.append('Rank')
        cols.extend(['display_name']); col_names.append('Company Name')
        if 'size_bucket' in sponsors.columns:
            cols.append('size_bucket'); col_names.append('Size')
        cols.append('distance_km'); col_names.append('Distance')
        cols.append('score'); col_names.append('Match Score')
        df_display = sponsors[cols].copy()
        df_display['score'] = (df_display['score']*100).round(0).astype(int).astype(str) + '%'
        df_display['distance_km'] = df_display['distance_km'].round(1).astype(str) + ' km'
        df_display.columns = col_names
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            hist = px.histogram(sponsors, x='score', nbins=20, title='Score Distribution')
            hist.update_xaxes(tickformat='.0%')
            st.plotly_chart(hist, use_container_width=True)
        with c2:
            dist_counts = sponsors['size_bucket'].value_counts()
            pie = px.pie(values=dist_counts.values, names=dist_counts.index, title='Sponsor Size Distribution')
            st.plotly_chart(pie, use_container_width=True)


def render_profile_page():
    st.title("👤 Association Profile")
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            _name = st.text_input("Association Name")
            _address = st.text_input("Address")
            _city = st.text_input("City", value="Göteborg")
        with c2:
            members = st.number_input("Number of Members", min_value=1, value=100)
            size_cat = 'Small (0-399)' if members<400 else 'Medium (400-799)' if members<800 else 'Large (800+)'
            st.info(f"Size Category: {size_cat}")
            _founded_year = st.number_input("Founded Year", min_value=1800, max_value=2024, value=2000)
        sub = st.form_submit_button("Save Profile")
        if sub:
            st.success("Profile saved successfully!")


def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'selected_association' not in st.session_state:
        st.session_state.selected_association = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'last_search_distance' not in st.session_state:
        st.session_state.last_search_distance = 25

    render_navigation()

    if st.session_state.page == 'home':
        render_home_page()
    elif st.session_state.page == 'find_sponsors':
        render_find_sponsors_page()
    elif st.session_state.page == 'profile':
        render_profile_page()


if __name__ == '__main__':
    main()
