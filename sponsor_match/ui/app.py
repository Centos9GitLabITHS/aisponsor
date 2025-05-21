"""
Main Streamlit application entry point for SponsorMatch.
Handles app initialization and page routing.
"""
import streamlit as st
from pathlib import Path

from sponsor_match.ui.pages import home, search, profile
from sponsor_match.ui.components.sidebar import render_sidebar
from sponsor_match.ui.services.data_service import load_initial_data
from sponsor_match.ui.utils.styles import apply_global_styles

def main():
    """Initialize and render the SponsorMatch application."""
    # Configure page
    st.set_page_config(
        page_title="SponsorMatch AI",
        page_icon="🏆",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Apply global styles
    apply_global_styles()

    # Initialize data
    load_initial_data()

    # Render sidebar
    render_sidebar()

    # Page routing based on tabs
    tabs = st.tabs(["🏠 Hem", "🎯 Hitta sponsorer", "👤 Min profil"])

    with tabs[0]:
        home.render_home_page()

    with tabs[1]:
        search.render_search_page()

    with tabs[2]:
        profile.render_profile_page()

if __name__ == "__main__":
    main()