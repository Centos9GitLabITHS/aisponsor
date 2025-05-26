#!/usr/bin/env python3
# pylint: disable=unused-import, unused-variable, duplicate-code
"""
golden_goal/ui/simple_app.py
FINAL VERSION - Streamlit UI for Golden Goal.
"""

import sys
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

# Add parent directory to path for imports
# Since we're running from golden_goal directory, we need to add parent
current_file = Path(__file__).resolve()
golden_goal_dir = current_file.parent.parent  # This gets us to golden_goal directory
sys.path.insert(0, str(golden_goal_dir))

# Import the service - use the correct import path
from golden_goal.services.service import GoldenGoalService

# Page configuration
st.set_page_config(
    page_title="Golden Goal",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"  # Changed to expanded for diagnostics
)

# Hide main menu, footer (but keep sidebar for diagnostics)
st.markdown("""
<style>
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
    return GoldenGoalService(None)


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

    # Process any pending searches FIRST, before creating the map
    if st.session_state.get('pending_search', False):
        assoc = st.session_state.get('selected_association')
        if assoc:
            max_dist = st.session_state.get('last_search_distance', 25)
            sponsors = service.recommend(
                association_name=assoc['name'],
                top_n=50,
                max_distance=max_dist
            )
            if not sponsors.empty:
                if 'rank' not in sponsors.columns:
                    sponsors['rank'] = range(1, len(sponsors) + 1)
                if 'distance' in sponsors.columns and 'distance_km' not in sponsors.columns:
                    sponsors['distance_km'] = sponsors['distance']
                st.session_state.search_results = sponsors
                st.session_state.pending_search = False
                st.success(f"Found {len(sponsors)} potential sponsors!")
            else:
                st.session_state.search_results = pd.DataFrame()  # Empty DataFrame instead of None
                st.session_state.pending_search = False
                st.warning("No sponsors found within the specified distance.")

    st.markdown('<div class="responsive-row">', unsafe_allow_html=True)
    title_col, map_col = st.columns(2)
    with title_col:
        st.title("🔍 Find Sponsors for Your Association")
    with map_col:
        # Default coordinates for Gothenburg
        lat, lon, zoom = 57.7089, 11.9746, 11

        # Get association coordinates if selected
        assoc = st.session_state.get('selected_association')
        if assoc:
            # Try to get valid coordinates
            assoc_lat = assoc.get('latitude', assoc.get('lat'))
            assoc_lon = assoc.get('longitude', assoc.get('lon'))

            # Validate coordinates
            try:
                if assoc_lat is not None and assoc_lon is not None:
                    lat_float = float(assoc_lat)
                    lon_float = float(assoc_lon)
                    # Check if the values are valid numbers and within reasonable bounds
                    if (not pd.isna(lat_float) and not pd.isna(lon_float) and
                            -90 <= lat_float <= 90 and -180 <= lon_float <= 180 and
                            lat_float != 0 and lon_float != 0):  # Exclude 0,0 coordinates
                        lat = lat_float
                        lon = lon_float
                        zoom = 13
                    else:
                        st.sidebar.warning(f"Invalid coordinates for {assoc['name']}: lat={assoc_lat}, lon={assoc_lon}")
            except (ValueError, TypeError) as e:
                st.sidebar.warning(f"Error parsing coordinates: {e}")

        # Create map with validated coordinates
        m = create_map(lat, lon, zoom)

        # Add association marker if selected and has valid coordinates
        if assoc and zoom == 13:  # zoom=13 means we have valid association coordinates
            popup = f"<b>{assoc['name']}</b><br>Size: {assoc['size_bucket']}"
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup, max_width=200),
                tooltip=assoc['name'],
                icon=folium.Icon(color='red', icon='star')
            ).add_to(m)

            # Add search radius circle
            radius = st.session_state.get('last_search_distance', 10) * 1000
            folium.Circle(
                location=[lat, lon],
                radius=radius,
                color='red',
                fill=True,
                fill_opacity=0.1
            ).add_to(m)

        # ADD COMPANY MARKERS FROM SEARCH RESULTS
        search_results = st.session_state.get('search_results')
        if isinstance(search_results, pd.DataFrame) and not search_results.empty:
            sponsors = search_results
            # Debug: Show number of sponsors to add
            st.sidebar.write(f"Debug: Adding {len(sponsors.head(20))} markers to map")

            # Add markers for top companies
            marker_count = 0
            for idx, company in sponsors.head(20).iterrows():  # Show top 20 to avoid cluttering
                company_lat = company.get('latitude', company.get('lat'))
                company_lon = company.get('longitude', company.get('lon'))

                # Validate company coordinates
                try:
                    if company_lat is not None and company_lon is not None:
                        c_lat = float(company_lat)
                        c_lon = float(company_lon)
                        if (not pd.isna(c_lat) and not pd.isna(c_lon) and
                                -90 <= c_lat <= 90 and -180 <= c_lon <= 180 and
                                c_lat != 0 and c_lon != 0):

                            # Color based on score
                            score = company.get('score', 0)
                            if score >= 0.8:
                                color = 'green'
                                icon_name = 'star'
                            elif score >= 0.6:
                                color = 'lightgreen'
                                icon_name = 'info-sign'
                            elif score >= 0.4:
                                color = 'orange'
                                icon_name = 'info-sign'
                            else:
                                color = 'red'
                                icon_name = 'info-sign'

                            company_name = company.get('name',
                                                       company.get('display_name', f'Company_{company.get("id", "")}'))
                            popup_text = f"""
                            <b>{company_name}</b><br>
                            Score: {score * 100:.1f}%<br>
                            Distance: {company.get('distance_km', company.get('distance', 0)):.1f} km<br>
                            Size: {company.get('size_bucket', 'Unknown')}<br>
                            Industry: {company.get('industry', 'Unknown')}
                            """

                            # Use simpler marker creation
                            folium.Marker(
                                location=[c_lat, c_lon],
                                popup=folium.Popup(popup_text, max_width=300),
                                tooltip=f"{company_name} ({score * 100:.0f}%)",
                                icon=folium.Icon(color=color, icon=icon_name)
                            ).add_to(m)
                            marker_count += 1
                except (ValueError, TypeError):
                    continue

            st.sidebar.write(f"Debug: Actually added {marker_count} markers")

            # Test: Add a simple test marker to verify markers work at all
            if st.sidebar.checkbox("Add test marker"):
                test_lat = lat + 0.01
                test_lon = lon + 0.01
                folium.Marker(
                    location=[test_lat, test_lon],
                    popup="TEST MARKER",
                    tooltip="This is a test",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
                st.sidebar.write(f"Test marker added at {test_lat}, {test_lon}")
        else:
            st.sidebar.write("Debug: No search results to display on map")

        # Display the map with unique key based on search results and selection
        search_results = st.session_state.get('search_results')
        if isinstance(search_results, pd.DataFrame):
            result_count = len(search_results)
        else:
            result_count = 0

        # Include both result count and selected association in the key
        assoc_id = assoc.get('id', 'none') if assoc else 'none'
        map_key = f"map_{assoc_id}_{result_count}"

        # Force a complete re-render of the map
        st_folium(m, width=700, height=400, returned_objects=[], key=map_key, use_container_width=False)

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
                    # Use the address field directly from the search results
                    address = row.get('address', '')
                    if address and pd.notna(address) and str(address).strip():
                        st.caption(str(address))
                    else:
                        st.caption("Address not available")
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
            location = assoc.get('city', assoc.get('Postort', 'Göteborg'))
            st.metric("Location", location)
        if st.button("🎯 FIND SPONSORS NOW", key="find_now"):
            st.session_state.last_search_distance = max_dist
            st.session_state.pending_search = True
            st.rerun()

    if isinstance(st.session_state.get('search_results'), pd.DataFrame) and not st.session_state.get(
            'search_results').empty:
        st.markdown("---")
        render_search_results()


# Render the recommendations results
def render_search_results():
    sponsors = st.session_state.search_results
    if 'size_bucket' not in sponsors.columns:
        sponsors['size_bucket'] = 'Unknown'

    # Fix display names - check if names are actually present
    if 'display_name' not in sponsors.columns or sponsors['display_name'].isna().all():
        if 'name' in sponsors.columns and not sponsors['name'].isna().all():
            sponsors['display_name'] = sponsors['name']
        else:
            sponsors['display_name'] = sponsors.apply(lambda r: f"Company_{r.get('id', '')}", axis=1)

    if 'distance_km' not in sponsors.columns and 'distance' in sponsors.columns:
        sponsors['distance_km'] = sponsors['distance']

    tab1, tab2, tab3 = st.tabs(["📊 Grid View", "📋 List View", "📈 Analytics"])
    with tab1:
        cols = st.columns(3)
        for i, sp in sponsors.head(12).iterrows():
            with cols[i % 3]:
                display_name = sp.get('display_name', sp.get('name', f"Company_{sp.get('id', '')}"))
                st.markdown(f"**{display_name}**")
                st.metric("Score", f"{sp['score'] * 100:.1f}%", delta=None)
                st.caption(f"Distance: {sp.get('distance_km', sp.get('distance', 0)):.1f} km")
    with tab2:
        # Create a display dataframe with proper names
        display_df = sponsors[['rank', 'name', 'size_bucket', 'score', 'distance_km']].copy()
        display_df.columns = ['Rank', 'Company Name', 'Size', 'Score', 'Distance (km)']
        display_df['Score'] = display_df['Score'].apply(lambda x: f"{x * 100:.1f}%")
        display_df['Distance (km)'] = display_df['Distance (km)'].apply(lambda x: f"{x:.1f}")
        st.dataframe(display_df, hide_index=True)
    with tab3:
        fig = px.histogram(sponsors, x='score', nbins=10, title="Score Distribution")
        st.plotly_chart(fig)


# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_association" not in st.session_state:
    st.session_state.selected_association = None
if "search_results" not in st.session_state:
    st.session_state.search_results = pd.DataFrame()  # Empty DataFrame instead of None
if "last_search_distance" not in st.session_state:
    st.session_state.last_search_distance = 25
if "pending_search" not in st.session_state:
    st.session_state.pending_search = False


# Add diagnostic mode
def run_diagnostics():
    """Show debug information"""
    with st.sidebar:
        if st.checkbox("🔧 Show Diagnostics"):
            st.write("### Debug Info")

            # Show session state
            search_results = st.session_state.get("search_results")
            if isinstance(search_results, pd.DataFrame):
                search_count = len(search_results)
            else:
                search_count = 0

            st.write("**Session State:**")
            st.json({
                "page": st.session_state.get("page"),
                "selected_association": st.session_state.get("selected_association", {}).get(
                    "name") if st.session_state.get("selected_association") else None,
                "search_results_count": search_count,
                "pending_search": st.session_state.get("pending_search", False)
            })

            # Show data info
            service = get_service()
            st.write("**Data Loaded:**")
            st.write(f"- Associations: {len(getattr(service, 'associations_df', []))} rows")
            st.write(f"- Companies: {len(getattr(service, 'companies_df', []))} rows")

            # Show first association to check columns
            if hasattr(service, 'associations_df') and not service.associations_df.empty:
                st.write("**Association columns:**")
                st.write(list(service.associations_df.columns))

            # Show search results debug info
            if isinstance(st.session_state.get("search_results"), pd.DataFrame) and not st.session_state.get(
                    "search_results").empty:
                st.write("**Search Results Columns:**")
                st.write(list(st.session_state.search_results.columns))
                first_result = st.session_state.search_results.iloc[0]
                st.write("**First result sample:**")
                st.write(f"Name: '{first_result.get('name', 'NO NAME')}'")
                st.write(f"Display Name: '{first_result.get('display_name', 'NO DISPLAY NAME')}'")
                st.write(f"ID: {first_result.get('id', 'NO ID')}")
                st.write(f"Lat: {first_result.get('lat', first_result.get('latitude', 'NO LAT'))}")
                st.write(f"Lon: {first_result.get('lon', first_result.get('longitude', 'NO LON'))}")


run_diagnostics()
render_navigation()
if st.session_state.page == "home":
    render_home_page()
elif st.session_state.page == "find_sponsors":
    render_find_sponsors_page()
else:
    st.write("Page under construction")
