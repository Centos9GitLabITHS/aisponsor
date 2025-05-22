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
from sponsor_match.ui.pages.home import render_home_page
from sponsor_match.ui.pages.search import render_search_page
from sponsor_match.ui.pages.profile import render_profile_page

# -----------------------------------------------------------------------------
# Inject a little responsive-card CSS globally
# -----------------------------------------------------------------------------
_RESPONSIVE_CARD_CSS = """
<style>
.card-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
}
.card-container .card {
  flex: 1 1 calc(33% - 1rem);
  max-width: calc(33% - 1rem);
  min-width: 240px;
  box-sizing: border-box;
  background: var(--secondaryBackgroundColor, #ffffff);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  text-align: center;
}
@media (max-width: 800px) {
  .card-container .card {
    flex: 1 1 100%;
    max-width: 100%;
  }
}
</style>
"""

def apply_global_styles():
    st.markdown(_RESPONSIVE_CARD_CSS, unsafe_allow_html=True)

def set_page_config():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=STREAMLIT_PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

def main():
    # 1) Streamlit/YAML setup
    set_page_config()
    apply_global_styles()

    # 2) Logo + title
    logo = Path(LOGO_PATH)
    if logo.exists():
        try:
            st.image(str(logo), width=120)
        except Exception as e:
            logging.warning(f"Could not load logo: {e}")
    else:
        logging.info(f"Logo file not found at {logo}, skipping.")

    # Big, styled header
    st.markdown(f"<h1 style='color: var(--primaryColor);'>{APP_TITLE}</h1>",
                unsafe_allow_html=True)

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
