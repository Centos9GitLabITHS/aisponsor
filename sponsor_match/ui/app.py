import streamlit as st
from pathlib import Path
import logging

from sponsor_match.core.config import APP_TITLE, LOGO_PATH, STREAMLIT_PAGE_ICON
from sponsor_match.ui.styles import apply_professional_styles
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
    set_page_config()
    apply_professional_styles()

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🏆 SponsorMatch AI")
        st.markdown("*Find the perfect sponsors for your sports club*")

    with col2:
        logo_path = Path(LOGO_PATH)
        if logo_path.exists():
            try:
                st.image(str(logo_path), width=100)
            except Exception:
                pass

    # Navigation
    tab1, tab2, tab3 = st.tabs(["🏠 Home", "🔍 Find Sponsors", "👤 My Club"])

    with tab1:
        render_home_page()
    with tab2:
        render_search_page()
    with tab3:
        render_profile_page()


if __name__ == "__main__":
    main()
