#!/usr/bin/env python3
"""
sponsor_match/ui/pages/search.py

Complete search page implementation with proper score display, map integration,
and comprehensive error handling. This fixes the 108% display issue.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium, folium_static
from folium.plugins import MarkerCluster, HeatMap

from sponsor_match.core.db import get_engine
from sponsor_match.services.service import SponsorMatchService
from sponsor_match.ml.pipeline import score_and_rank

# Configure logging
logger = logging.getLogger(__name__)

# Constants for UI
DEFAULT_MAX_DISTANCE = 25  # km
DEFAULT_TOP_N = 10
MAP_HEIGHT = 500
SCORE_THRESHOLD = 0.3  # Minimum score to display

# Color scheme for match quality
MATCH_COLORS = {
    'excellent': '#10b981',  # Green
    'good': '#3b82f6',  # Blue
    'fair': '#f59e0b',  # Orange
    'possible': '#6b7280'  # Gray
}


def validate_score(score: float, entity_name: str = "") -> float:
    """
    Validate and clamp score to [0, 1] range.

    This function ensures that all scores displayed in the UI are valid percentages.
    It logs warnings when invalid scores are detected for debugging purposes.
    """
    if not isinstance(score, (int, float)):
        logger.error(f"Invalid score type {type(score)} for {entity_name}")
        return 0.0

    if np.isnan(score) or np.isinf(score):
        logger.error(f"NaN or Inf score for {entity_name}")
        return 0.0

    if score < 0 or score > 1:
        logger.warning(f"Score {score} out of range for {entity_name}, clamping")
        return np.clip(score, 0.0, 1.0)

    return float(score)


def format_percentage(score: float) -> str:
    """
    Format score as percentage with validation.

    This function ensures that percentage displays never exceed 100%.
    """
    validated_score = validate_score(score)
    percentage = validated_score * 100

    # Extra safety check
    if percentage > 100:
        logger.error(f"Percentage {percentage}% exceeds 100% after validation!")
        percentage = 100.0

    return f"{percentage:.1f}%"


def get_match_quality(score: float) -> Tuple[str, str]:
    """
    Get match quality label and color based on score.

    Returns tuple of (quality_label, color_hex).
    """
    score = validate_score(score)

    if score >= 0.8:
        return 'Excellent Match', MATCH_COLORS['excellent']
    elif score >= 0.6:
        return 'Good Match', MATCH_COLORS['good']
    elif score >= 0.4:
        return 'Fair Match', MATCH_COLORS['fair']
    else:
        return 'Possible Match', MATCH_COLORS['possible']


def load_associations_service() -> Optional[SponsorMatchService]:
    """Initialize and return the sponsor match service."""
    try:
        engine = get_engine()
        return SponsorMatchService(engine)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        logger.error(f"Failed to initialize service: {e}")
        return None


def search_associations(service: SponsorMatchService, query: str) -> pd.DataFrame:
    """Search for associations using the service."""
    if not service:
        return pd.DataFrame()

    try:
        # Use the service search method
        results = service.search(query)

        # Filter to only associations
        if not results.empty:
            return results[results['type'] == 'association'].copy()
        return pd.DataFrame()

    except Exception as e:
        st.error(f"Search error: {e}")
        logger.error(f"Association search failed: {e}")
        return pd.DataFrame()


def render_search_results(sponsors: List[Dict], selected_idx: Optional[int] = None) -> Optional[int]:
    """
    Render sponsor search results with proper score formatting.

    This function creates the visual representation of search results,
    ensuring all scores are displayed correctly as percentages ≤ 100%.
    """
    if not sponsors:
        return None

    # Create results container
    st.subheader(f"Found {len(sponsors)} Potential Sponsors")

    # Add statistics
    scores = [validate_score(s['score']) for s in sponsors]
    avg_score = np.mean(scores)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Match", format_percentage(avg_score))
    with col2:
        st.metric("Best Match", format_percentage(max(scores)))
    with col3:
        excellent_count = sum(1 for s in scores if s >= 0.8)
        st.metric("Excellent Matches", excellent_count)

    st.divider()

    # Render each result
    clicked_idx = None

    for idx, sponsor in enumerate(sponsors):
        # Validate score
        score = validate_score(sponsor.get('score', 0), sponsor.get('name', 'Unknown'))
        quality_label, quality_color = get_match_quality(score)

        # Create result card
        is_selected = (selected_idx == idx)

        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                # Company name and info
                st.markdown(f"### {sponsor.get('name', 'Unknown Company')}")

                # Industry and size info
                industry = sponsor.get('industry', 'Unknown')
                size = sponsor.get('size_bucket', 'unknown').capitalize()
                st.caption(f"📊 {industry} | 📏 {size} company")

            with col2:
                # Score display with color coding
                st.markdown(f"""
                <div style="text-align: center; padding: 10px;">
                    <div style="font-size: 24px; font-weight: bold; color: {quality_color};">
                        {format_percentage(score)}
                    </div>
                    <div style="font-size: 12px; color: {quality_color};">
                        {quality_label}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                # Distance and action button
                distance = sponsor.get('distance', 0)
                st.metric("Distance", f"{distance:.1f} km")

                if st.button("View Details", key=f"view_{idx}"):
                    clicked_idx = idx

            # Score breakdown (expandable)
            with st.expander("Score Breakdown"):
                components = sponsor.get('components', {})

                # Create score breakdown chart
                if components:
                    breakdown_data = []
                    for component, value in components.items():
                        # Validate each component score
                        validated_value = validate_score(value, f"{sponsor['name']} - {component}")
                        breakdown_data.append({
                            'Component': component.replace('_', ' ').title(),
                            'Score': validated_value,
                            'Percentage': format_percentage(validated_value)
                        })

                    breakdown_df = pd.DataFrame(breakdown_data)

                    # Display as horizontal bar chart
                    st.bar_chart(breakdown_df.set_index('Component')['Score'])

                    # Show exact values
                    for row in breakdown_data:
                        st.caption(f"{row['Component']}: {row['Percentage']}")
                else:
                    st.info("Detailed score breakdown not available")

            st.divider()

    return clicked_idx


def render_map(
        selected_club: Optional[Dict],
        sponsors: List[Dict],
        selected_sponsor_idx: Optional[int] = None
) -> Dict:
    """
    Render interactive map with club and sponsor markers.

    This function creates a folium map showing the geographic distribution
    of the club and potential sponsors, with visual indicators of match quality.
    """
    # Default center on Gothenburg
    center_lat, center_lon = 57.7089, 11.9746
    zoom = 11

    # Center on selected club if available
    if selected_club and selected_club.get('lat') and selected_club.get('lon'):
        center_lat = float(selected_club['lat'])
        center_lon = float(selected_club['lon'])
        zoom = 12

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )

    # Add club marker
    if selected_club and selected_club.get('lat') and selected_club.get('lon'):
        club_popup = folium.Popup(
            f"""
            <div style='width: 200px'>
                <h4>{selected_club['name']}</h4>
                <p><b>Members:</b> {selected_club.get('member_count', 'N/A')}</p>
                <p><b>Size:</b> {selected_club.get('size_bucket', '').title()}</p>
                <p>{selected_club.get('address', '')}</p>
            </div>
            """,
            max_width=250
        )

        folium.Marker(
            location=[float(selected_club['lat']), float(selected_club['lon'])],
            popup=club_popup,
            icon=folium.Icon(color='purple', icon='star', prefix='fa'),
            tooltip=selected_club['name']
        ).add_to(m)

        # Add search radius circle
        if st.session_state.get('max_distance'):
            folium.Circle(
                location=[float(selected_club['lat']), float(selected_club['lon'])],
                radius=st.session_state.get('max_distance', DEFAULT_MAX_DISTANCE) * 1000,  # Convert km to m
                color='purple',
                fill=True,
                fillOpacity=0.1,
                tooltip=f"Search radius: {st.session_state.get('max_distance')} km"
            ).add_to(m)

    # Add sponsor markers
    if sponsors:
        # Create marker cluster for better performance with many markers
        marker_cluster = MarkerCluster().add_to(m)

        # Prepare heat map data
        heat_data = []

        for idx, sponsor in enumerate(sponsors):
            if sponsor.get('lat') and sponsor.get('lon'):
                # Validate score
                score = validate_score(sponsor.get('score', 0), sponsor['name'])
                quality_label, quality_color = get_match_quality(score)

                # Determine marker color based on score
                if score >= 0.8:
                    marker_color = 'darkgreen'
                elif score >= 0.6:
                    marker_color = 'green'
                elif score >= 0.4:
                    marker_color = 'orange'
                else:
                    marker_color = 'lightgray'

                # Create popup content
                popup_html = f"""
                <div style='width: 250px'>
                    <h4>{sponsor['name']}</h4>
                    <div style='background: {quality_color}; color: white; padding: 5px; margin: 5px 0; text-align: center; border-radius: 5px;'>
                        Match: {format_percentage(score)} - {quality_label}
                    </div>
                    <p><b>Distance:</b> {sponsor['distance']:.1f} km</p>
                    <p><b>Industry:</b> {sponsor.get('industry', 'N/A')}</p>
                    <p><b>Size:</b> {sponsor.get('size_bucket', '').title()}</p>
                </div>
                """

                # Special styling for selected sponsor
                if selected_sponsor_idx == idx:
                    icon = folium.Icon(color=marker_color, icon='building', prefix='fa', icon_color='yellow')
                else:
                    icon = folium.Icon(color=marker_color, icon='building', prefix='fa')

                # Add marker
                folium.Marker(
                    location=[float(sponsor['lat']), float(sponsor['lon'])],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=icon,
                    tooltip=f"{sponsor['name']} ({format_percentage(score)})"
                ).add_to(marker_cluster)

                # Add to heat map data (weight by score)
                heat_data.append([float(sponsor['lat']), float(sponsor['lon']), score])

        # Add heat map layer
        if heat_data:
            HeatMap(heat_data, radius=15, blur=10, max_zoom=13).add_to(m)

    # Display map
    map_data = st_folium(m, height=MAP_HEIGHT, width=None, key="search_map", returned_objects=["last_object_clicked"])

    return map_data


def render_sponsor_details(sponsor: Dict):
    """
    Render detailed sponsor information in a modal/expander.

    This function shows comprehensive information about a selected sponsor,
    including contact details and match analysis.
    """
    st.subheader(f"Sponsor Details: {sponsor['name']}")

    # Validate and display score prominently
    score = validate_score(sponsor.get('score', 0), sponsor['name'])
    quality_label, quality_color = get_match_quality(score)

    # Score display
    st.markdown(f"""
    <div style="background: {quality_color}; color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
        <h1 style="margin: 0; color: white;">{format_percentage(score)}</h1>
        <h3 style="margin: 0; color: white;">{quality_label}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Company information
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Company Information")
        st.write(f"**Industry:** {sponsor.get('industry', 'N/A')}")
        st.write(f"**Size:** {sponsor.get('size_bucket', 'unknown').capitalize()}")
        st.write(f"**Revenue:** {sponsor.get('revenue_ksek', 'N/A')} KSEK")
        st.write(f"**Employees:** {sponsor.get('employees', 'N/A')}")

    with col2:
        st.markdown("### Location")
        st.write(f"**Distance:** {sponsor.get('distance', 0):.1f} km")
        st.write(f"**Coordinates:** {sponsor.get('lat', 0):.4f}, {sponsor.get('lon', 0):.4f}")

    # Match analysis
    st.markdown("### Match Analysis")

    components = sponsor.get('components', {})
    if components:
        # Create detailed breakdown
        analysis_data = []

        for component, value in components.items():
            validated_value = validate_score(value, f"{sponsor['name']} - {component}")

            # Provide interpretation
            if component == 'distance_score':
                interpretation = "Closer sponsors score higher"
            elif component == 'size_score':
                interpretation = "Similar-sized organizations match better"
            elif component == 'cluster_score':
                interpretation = "Geographic clustering indicates market synergy"
            elif component == 'industry_score':
                interpretation = "Industry alignment with sports/community"
            else:
                interpretation = ""

            analysis_data.append({
                'Factor': component.replace('_', ' ').title(),
                'Score': format_percentage(validated_value),
                'Interpretation': interpretation
            })

        # Display as table
        analysis_df = pd.DataFrame(analysis_data)
        st.table(analysis_df)

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📧 Contact Sponsor", key="contact_sponsor"):
            st.info("Contact feature coming soon!")

    with col2:
        if st.button("📄 Generate Proposal", key="generate_proposal"):
            st.info("Proposal generation feature coming soon!")

    with col3:
        if st.button("📊 View Similar Sponsors", key="similar_sponsors"):
            st.info("Similar sponsors feature coming soon!")


def render_search_page():
    """
    Main function to render the search page.

    This orchestrates the entire search experience, from club selection
    through sponsor discovery and detailed analysis.
    """
    st.title("🔍 Find Sponsors for Your Club")

    # Initialize session state
    if 'selected_club' not in st.session_state:
        st.session_state.selected_club = None
    if 'sponsors' not in st.session_state:
        st.session_state.sponsors = []
    if 'selected_sponsor_idx' not in st.session_state:
        st.session_state.selected_sponsor_idx = None

    # Initialize service
    service = load_associations_service()

    # Create layout
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("### Search Your Club")

        # Search interface
        search_query = st.text_input(
            "🏆 Enter club name...",
            placeholder="Type at least 2 characters",
            key="club_search"
        )

        # Search parameters
        with st.expander("Search Options", expanded=True):
            max_distance = st.slider(
                "Maximum distance (km)",
                min_value=5,
                max_value=100,
                value=DEFAULT_MAX_DISTANCE,
                key="max_distance"
            )

            top_n = st.slider(
                "Number of sponsors to find",
                min_value=5,
                max_value=50,
                value=DEFAULT_TOP_N,
                key="top_n"
            )

            min_score = st.slider(
                "Minimum match score",
                min_value=0.0,
                max_value=1.0,
                value=SCORE_THRESHOLD,
                step=0.1,
                format="%.1f",
                key="min_score"
            )

        # Search for clubs
        if search_query and len(search_query) >= 2 and service:
            associations_df = search_associations(service, search_query)

            if not associations_df.empty:
                st.markdown("### Select Your Club")

                # Display search results
                for _, assoc in associations_df.iterrows():
                    display_name = f"{assoc['name']}"
                    if pd.notna(assoc.get('address')):
                        display_name += f" - {assoc['address']}"

                    if st.button(display_name, key=f"club_{assoc['id']}", use_container_width=True):
                        # Get full association details
                        club_details = service.get_association_by_name(assoc['name'])
                        if club_details:
                            st.session_state.selected_club = club_details
                            st.rerun()
            else:
                st.info("No clubs found. Try different search terms.")

        # Show selected club
        if st.session_state.selected_club:
            st.success(f"✅ Selected: **{st.session_state.selected_club['name']}**")

            # Club details
            with st.expander("Club Details", expanded=True):
                st.write(f"**Size:** {st.session_state.selected_club.get('size_bucket', 'unknown').capitalize()}")
                st.write(f"**Members:** {st.session_state.selected_club.get('member_count', 'N/A')}")
                st.write(f"**Address:** {st.session_state.selected_club.get('address', 'N/A')}")

            # Find sponsors button
            if st.button("🎯 Find Sponsors", type="primary", use_container_width=True):
                with st.spinner("Searching for matching sponsors..."):
                    try:
                        # Use ML pipeline for recommendations
                        sponsors = score_and_rank(
                            association_id=st.session_state.selected_club['id'],
                            bucket=st.session_state.selected_club.get('size_bucket', 'medium'),
                            max_distance=max_distance,
                            top_n=top_n
                        )

                        # Filter by minimum score
                        sponsors = [s for s in sponsors if s['score'] >= min_score]

                        st.session_state.sponsors = sponsors

                        if sponsors:
                            st.success(f"Found {len(sponsors)} potential sponsors!")
                        else:
                            st.warning("No sponsors found matching your criteria. Try adjusting the search parameters.")

                    except Exception as e:
                        st.error(f"Error finding sponsors: {e}")
                        logger.error(f"Sponsor search failed: {e}", exc_info=True)
                        st.session_state.sponsors = []

    with col2:
        # Map section
        st.markdown("### Sponsor Map")

        # Display map
        map_data = render_map(
            st.session_state.selected_club,
            st.session_state.sponsors,
            st.session_state.selected_sponsor_idx
        )

        # Handle map clicks
        if map_data.get('last_object_clicked'):
            # Process map click to select sponsor
            clicked_popup = map_data['last_object_clicked'].get('popup')
            if clicked_popup:
                # Extract sponsor from popup (simplified - in production use proper ID mapping)
                for idx, sponsor in enumerate(st.session_state.sponsors):
                    if sponsor['name'] in clicked_popup:
                        st.session_state.selected_sponsor_idx = idx
                        break

    # Results section (below the columns)
    if st.session_state.sponsors:
        st.divider()

        # Render search results
        clicked_idx = render_search_results(
            st.session_state.sponsors,
            st.session_state.selected_sponsor_idx
        )

        # Update selected sponsor if clicked
        if clicked_idx is not None:
            st.session_state.selected_sponsor_idx = clicked_idx
            st.rerun()

    # Sponsor details modal
    if (st.session_state.selected_sponsor_idx is not None and
            st.session_state.selected_sponsor_idx < len(st.session_state.sponsors)):
        with st.expander("Sponsor Details", expanded=True):
            selected_sponsor = st.session_state.sponsors[st.session_state.selected_sponsor_idx]
            render_sponsor_details(selected_sponsor)

    # Debug information (only in development)
    if st.checkbox("Show Debug Info", value=False):
        st.markdown("### Debug Information")

        if st.session_state.sponsors:
            # Check for any scores > 1.0
            invalid_scores = [s for s in st.session_state.sponsors if s['score'] > 1.0]

            if invalid_scores:
                st.error(f"⚠️ Found {len(invalid_scores)} sponsors with scores > 100%!")
                for s in invalid_scores:
                    st.write(f"- {s['name']}: {s['score'] * 100:.1f}%")
            else:
                st.success("✅ All scores are valid (≤ 100%)")

        # Score validation results
        if service:
            with st.spinner("Running score validation..."):
                validation_stats = service.validate_all_scores()

                st.json(validation_stats)


# Entry point
if __name__ == "__main__":
    render_search_page()
