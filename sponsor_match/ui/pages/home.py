# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
sponsor_match/ui/pages/home.py

Home page for SponsorMatch application.
"""

import streamlit as st

def render_home_page():
    """Render the home page with responsive cards."""
    st.markdown(
        "<h2 style='font-size:2rem;font-weight:600;color:var(--primaryColor);'>"
        "Välkommen till SponsorMatch</h2>",
        unsafe_allow_html=True,
    )

    # open the flex container
    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    # each card
    cards = [
        ("✨", "Tips & tricks", "Råd för att locka sponsorer snabbare."),
        ("⚙️", "Inställningar",       "Justera profil, sekretess och synlighet."),
        ("ℹ️", "Om SponsorMatch",     "Så fungerar plattformen och affärsmodellen."),
    ]
    for icon, title, desc in cards:
        st.markdown(
            f"""
            <div class="card">
              <div style="font-size:2rem;color:var(--primaryColor);">{icon}</div>
              <h3 style="margin:0.5rem 0;color:var(--primaryColor);">{title}</h3>
              <p style="margin:0;color:var(--textColor);">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # close the flex container
    st.markdown('</div>', unsafe_allow_html=True)
