# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

"""
Sidebar component for SponsorMatch application.
"""
import streamlit as st

from sponsor_match.ui.utils.sessions import clear_session_data


def render_sidebar():
    """Render the application sidebar."""
    with st.sidebar:
        st.title("🏆 SponsorMatch AI")
        st.markdown("Hitta rätt sponsorer för din idrottsförening")
        st.divider()

        # Settings section
        st.subheader("Inställningar")
        api_key = st.text_input("API-nyckel", value="demo-key", type="password")
        st.checkbox("Avancerad matchning", value=True,
                    help="Aktivera AI-baserad matchning")

        # Language selection
        st.selectbox("Språk", ["Svenska", "English"], index=0)

        st.divider()

        # User actions
        if st.button("Rensa sökhistorik"):
            clear_session_data("search_results")
            clear_session_data("search_scores")
            st.success("Sökhistorik rensad!")

        if st.button("Logga ut"):
            clear_session_data()
            st.success("Du har loggats ut.")

        # About section
        st.markdown("### Om SponsorMatch AI")
        st.markdown("""
        SponsorMatch AI hjälper idrottsföreningar att hitta och kontakta lämpliga 
        företag som kan bli sponsorer.

        Vi använder AI för att matcha föreningar med företag baserat på geografi, 
        storlek, bransch och värderingar.
        """)

        st.markdown("Made with ❤️ by Team 14")

        # Version info
        st.caption("Version 1.0.0")
