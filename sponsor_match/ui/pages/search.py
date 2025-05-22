import streamlit as st
import pandas as pd
from sqlalchemy import text
from sponsor_match.core.db import get_engine
from sponsor_match.ui.services.search_services import recommend_sponsors
import folium
from streamlit_folium import st_folium


def load_clubs_df() -> pd.DataFrame:
    """Load all associations from the database into a DataFrame."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df = pd.read_sql(
                "SELECT id, name, size_bucket, lat, lon, address FROM associations",
                conn
            )
        return df[df["name"].notna()]
    except Exception as e:
        st.error(f"Database error: {e}")
        # Fallback to sample data
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['IFK Göteborg', 'GAIS', 'BK Häcken', 'Örgryte IS', 'Ahlafors IF'],
            'size_bucket': ['large', 'medium', 'medium', 'medium', 'small'],
            'lat': [57.7089, 57.6969, 57.7209, 57.7041, 57.6941],
            'lon': [11.9746, 11.9789, 11.9390, 12.0027, 11.9124],
            'address': ['Göteborg', 'Göteborg', 'Göteborg', 'Göteborg', 'Alafors']
        })


def render_search_page():
    st.title("🔍 Sponsor Match Search")

    # Load clubs data
    clubs_df = load_clubs_df()

    # Search input with autocomplete
    col1, col2 = st.columns([2, 1])

    with col1:
        search_query = st.text_input("🏆 Search for your association...",
                                     placeholder="Type at least 2 characters")

    with col2:
        size_bucket = st.selectbox("Size:", ["small", "medium", "large"], index=1)
        max_distance = st.slider("Max distance (km):", 1, 100, 15)

    # Initialize session state for selected club
    if 'selected_club' not in st.session_state:
        st.session_state.selected_club = None
    if 'sponsors' not in st.session_state:
        st.session_state.sponsors = []

    # Autocomplete logic
    if search_query and len(search_query) >= 2:
        # Filter clubs based on search
        filtered_clubs = clubs_df[
            clubs_df['name'].str.contains(search_query, case=False, na=False)
        ].head(10)

        if not filtered_clubs.empty:
            st.write("**Select your association:**")
            for _, club in filtered_clubs.iterrows():
                if st.button(f"{club['name']} - {club['address']}",
                             key=f"club_{club['id']}",
                             use_container_width=True):
                    st.session_state.selected_club = club.to_dict()
                    st.rerun()
        else:
            st.warning("No associations found. Try different search terms.")

    # Show selected club and search button
    if st.session_state.selected_club:
        club = st.session_state.selected_club

        st.success(f"✅ Selected: **{club['name']}** ({club.get('size_bucket', 'unknown')} size)")

        if st.button("🎯 Find Sponsors", type="primary", use_container_width=True):
            with st.spinner("Searching for sponsors..."):
                try:
                    sponsors = recommend_sponsors(
                        club_id=club['id'],
                        club_bucket=size_bucket,
                        max_distance=max_distance,
                        top_n=10
                    )
                    st.session_state.sponsors = sponsors
                    if sponsors:
                        st.success(f"Found {len(sponsors)} potential sponsors!")
                    else:
                        st.warning("No sponsors found in this area.")
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    st.session_state.sponsors = []

    # Single map showing everything
    render_main_map(st.session_state.selected_club, st.session_state.sponsors)

    # Show sponsor results
    if st.session_state.sponsors:
        st.subheader("🏢 Potential Sponsors")

        for i, sponsor in enumerate(st.session_state.sponsors):
            with st.expander(f"{i + 1}. {sponsor['name']} - {sponsor['distance']:.1f}km away"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Distance", f"{sponsor['distance']:.1f} km")
                with col2:
                    st.metric("Match Score", f"{sponsor['score']:.2f}")
                with col3:
                    st.button(f"Contact {sponsor['name']}",
                              key=f"contact_{sponsor['id']}")


def render_main_map(selected_club, sponsors):
    """Render a single map showing club and sponsors."""

    # Default center on Gothenburg
    center_lat, center_lon = 57.7089, 11.9746
    zoom = 11

    # If club is selected, center on it
    if selected_club and selected_club.get('lat') and selected_club.get('lon'):
        center_lat = float(selected_club['lat'])
        center_lon = float(selected_club['lon'])
        zoom = 12

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="OpenStreetMap"
    )

    # Add club marker if selected
    if selected_club and selected_club.get('lat') and selected_club.get('lon'):
        folium.Marker(
            location=[float(selected_club['lat']), float(selected_club['lon'])],
            popup=folium.Popup(f"<b>{selected_club['name']}</b><br>{selected_club.get('address', '')}",
                               max_width=200),
            icon=folium.Icon(color='red', icon='home', prefix='fa'),
            tooltip=selected_club['name']
        ).add_to(m)

    # Add sponsor markers
    if sponsors:
        for sponsor in sponsors:
            if sponsor.get('lat') and sponsor.get('lon'):
                # Color based on score
                if sponsor['score'] > 0.8:
                    color = 'green'
                elif sponsor['score'] > 0.5:
                    color = 'orange'
                else:
                    color = 'blue'

                folium.Marker(
                    location=[float(sponsor['lat']), float(sponsor['lon'])],
                    popup=folium.Popup(
                        f"<b>{sponsor['name']}</b><br>"
                        f"Distance: {sponsor['distance']:.1f}km<br>"
                        f"Score: {sponsor['score']:.2f}",
                        max_width=200
                    ),
                    icon=folium.Icon(color=color, icon='building', prefix='fa'),
                    tooltip=f"{sponsor['name']} ({sponsor['distance']:.1f}km)"
                ).add_to(m)

    # Display map
    st.subheader("📍 Map")
    st_folium(m, width=700, height=500)


if __name__ == "__main__":
    render_search_page()