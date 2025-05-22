#!/usr/bin/env python3
"""
sponsor_match/ui/app.py

Streamlit UI for SponsorMatch AI.
"""

import streamlit as st
from pathlib import Path
import logging

from sponsor_match.core.config import APP_TITLE, LOGO_PATH, STREAMLIT_PAGE_ICON
from sponsor_match.ui.pages.home import render_home_page
from sponsor_match.ui.pages.search import render_search_page
from sponsor_match.ui.pages.profile import render_profile_page

def set_page_config():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=STREAMLIT_PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

def main():
    # 1) Page setup
    set_page_config()

    # 2) Logo + title
    logo_path = Path(LOGO_PATH)
    if logo_path.exists():
        try:
            st.image(str(logo_path), width=120)
        except (OSError, FileNotFoundError) as e:
            logging.warning(f"Could not load logo at {logo_path}: {e}")
    else:
        logging.info(f"Logo not found at {logo_path}; skipping.")

    st.title(APP_TITLE)

    # 3) Sidebar nav
    choice = st.sidebar.radio("Go to", ["Home", "Search", "Profile"])

    # 4) Dispatch
    if choice == "Home":
        render_home_page()
    elif choice == "Search":
        render_search_page()
    elif choice == "Profile":
        render_profile_page()
    else:
        st.error(f"Unknown page: {choice}")

if __name__ == "__main__":
    main()
