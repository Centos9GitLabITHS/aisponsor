#!/usr/bin/env python3
"""
sponsor_match/ui/pages/profile.py

Streamlit page for managing club profile.
"""

import streamlit as st

# fix: it's session.py, not sessions.py
from sponsor_match.ui.utils.sessions import get_session_data, set_session_data


def render_profile_page():
    st.markdown(
        "<h2 style='font-size:2rem;font-weight:600;color:var(--primaryColor);'>"
        "Min förening</h2>",
        unsafe_allow_html=True,
    )

    # get_session_data() may return None, so we coalesce to a dict
    club = get_session_data("selected_club") or {}

    if club:
        _render_profile_form(club)
    else:
        st.info(
            "Du har inte valt någon förening. "
            "Använd sökfunktionen för att hitta din förening."
        )
        _render_profile_form(None)

    with st.expander("Sponsorhistorik", expanded=False):
        _render_sponsorship_history()

    with st.expander("Inställningar", expanded=False):
        _render_preferences()


def _render_profile_form(club: dict | None = None):
    with st.form("profile_form"):
        # prefill from club dict or fall back to empty strings
        name    = st.text_input("Föreningens namn", value=club.get("name","") if club else "")
        address = st.text_input("Adress",           value=club.get("address","") if club else "")

        # size bucket select
        size_labels = ["Liten", "Medel", "Stor"]
        rev_map     = {"Liten":"small","Medel":"medium","Stor":"large"}
        # figure out which index to preselect
        if club and club.get("size_bucket") in {"small","medium","large"}:
            pre = {"small":"Liten","medium":"Medel","large":"Stor"}[club["size_bucket"]]
            default_idx = size_labels.index(pre)
        else:
            default_idx = 1  # Medel
        size_sel = st.selectbox("Storlek", size_labels, index=default_idx)

        email = st.text_input("E-post",   value=club.get("email","") if club else "")
        phone = st.text_input("Telefon",  value=club.get("phone","") if club else "")
        desc  = st.text_area("Beskrivning", value=club.get("description","") if club else "")

        if st.form_submit_button("Spara profil"):
            st.success("Profilen har sparats!")
            profile = {
                "name":         name,
                "address":      address,
                "size_bucket":  rev_map[size_sel],
                "email":        email,
                "phone":        phone,
                "description":  desc,
            }
            # preserve id + coords if they existed
            if club:
                for key in ("id","latitude","longitude"):
                    if key in club:
                        profile[key] = club[key]
            set_session_data("selected_club", profile)


def _render_sponsorship_history():
    st.markdown("#### Nuvarande sponsorer")
    history = st.session_state.get("sponsors_history", [])
    if history:
        for s in history:
            st.write(f"**{s['name']}** ({s['contract_date']} – {s['end_date']}) • {s['status']}")
            st.write("---")
    else:
        st.write("Inga aktiva sponsoravtal.")


def _render_preferences():
    st.markdown("#### Notifikationsinställningar")
    st.checkbox("E-postaviseringar",   value=True,  key="email_notifications")
    st.checkbox("SMS-aviseringar",      value=False, key="sms_notifications")

    st.markdown("#### Sekretess")
    st.checkbox("Visa förening publikt",      value=True,  key="public_profile")
    st.checkbox("Tillåt kontakt från företag", value=True,  key="allow_contact")

    if st.button("Spara inställningar", key="save_prefs"):
        st.success("Inställningarna har sparats!")
