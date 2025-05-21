#!/usr/bin/env python3
"""
sponsor_match/ui/app.py

Streamlit UI for SponsorMatch AI.
"""

import streamlit as st
from pathlib import Path
import logging

from sponsor_match.core.config import (
    APP_TITLE,
    LOGO_PATH,
    STREAMLIT_PAGE_ICON,
)
from sponsor_match.core.db import get_engine
from sponsor_match.services.service import search, recommend

def set_page_config():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=STREAMLIT_PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

def main():
    # 1) Configure the page
    set_page_config()

    # 2) Header with logo
    logo_file = Path(LOGO_PATH)
    if logo_file.exists():
        try:
            st.image(str(logo_file), width=120)
        except (FileNotFoundError, OSError) as e:
            logging.warning(f"Could not load logo image at {logo_file}: {e}")
    else:
        logging.info(f"Logo file not found at {logo_file}, skipping image.")

    # 3) Title
    st.title(APP_TITLE)

    # 4) Prepare DB engine
    engine = get_engine()

    # 5) Sidebar controls
    st.sidebar.header("Options")
    mode = st.sidebar.radio("Mode", ["Search", "Recommend"])

    if mode == "Search":
        query = st.sidebar.text_input("Search clubs or sponsors")
        if st.sidebar.button("Go"):
            if not query:
                st.sidebar.warning("Please enter a search term.")
            else:
                results = search(engine, query)
                if not results.empty:
                    st.write(f"Found {len(results)} results for “{query}”:")
                    st.dataframe(results)
                else:
                    st.warning(f"No results found for “{query}.”")

    else:  # Recommend mode
        club_name = st.sidebar.text_input("Club name")
        top_n = st.sidebar.number_input(
            "How many sponsors?", min_value=1, max_value=50, value=10
        )
        if st.sidebar.button("Recommend"):
            if not club_name:
                st.sidebar.warning("Please enter a club name.")
            else:
                recs = recommend(engine, club_name, top_n)
                if not recs.empty:
                    st.write(f"Top {len(recs)} recommendations for “{club_name}”:")
                    st.dataframe(recs)
                    if {"latitude", "longitude"}.issubset(recs.columns):
                        st.map(
                            recs.rename(columns={"latitude": "lat", "longitude": "lon"})
                        )
                else:
                    st.warning(f"No sponsor recommendations for “{club_name}.”")
