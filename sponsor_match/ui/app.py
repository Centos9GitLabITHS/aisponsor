import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional

# Folium & Streamlit-Folium imports for the map
from folium import Map, Marker, Popup, Icon
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

# Fallback if st.modal isn’t available
_open_modal = getattr(st, "modal", st.expander)


class SponsorMatchUI:
    def __init__(self) -> None:
        st.set_page_config(
            page_title="Golden Sugar Daddy Goal",
            page_icon="⚽",
            layout="wide",
            initial_sidebar_state="collapsed",
        )

    def render_main_page(self) -> None:
        # ─── GLOBAL STYLES ───────────────────────────────────────────────
        st.markdown(
            """
            <style>
              /* gradient, centering, card styling, etc. (omitted here for brevity) */
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ─── CUSTOM CSS FOR HORIZONTAL TABS ──────────────────────────────
        st.markdown(
            """
            <style>
              /* hide default hamburger menu & footer */
              #MainMenu, footer { visibility: hidden; }

              /* style the horizontal tabs container */
              .stTabs [role="tablist"] {
                background-color: #1e3a8a;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                margin: 1rem 0;
                display: inline-flex;
              }
              /* unselected tabs */
              .stTabs [role="tab"] {
                color: white;
                padding: 0.5rem 1rem;
                margin: 0 0.25rem;
                border-radius: 0.25rem;
              }
              /* selected tab */
              .stTabs [aria-selected="true"] {
                background-color: #1e40af;
                color: white;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ─── SIDEBAR (login, title) ───────────────────────────────────────
        with st.sidebar:
            st.title("Golden Sugar Daddy Goal")
            if st.button("🔑 Logga in", key="login_button"):
                st.session_state["show_login"] = True

        # ─── HERO / HEADER ───────────────────────────────────────────────
        logo_path = Path(__file__).parent / "assets" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=180)
        st.markdown(
            "<h1 style='font-size:3rem; font-weight:800; text-align:center; color:#1e3a8a;'>Sponsorly</h1>",
            unsafe_allow_html=True,
        )

        # ─── HORIZONTAL TABS NAV ─────────────────────────────────────────
        tabs = st.tabs(["🏠 Hem", "🎯 Hitta sponsorer"])
        with tabs[0]:
            self._render_home()
        with tabs[1]:
            self._render_search()

        # ─── MODALS ─────────────────────────────────────────────────────
        if st.session_state.get("show_login"):
            self._show_login_modal()
        if st.session_state.get("selected_sponsor"):
            self._show_sponsor_modal(st.session_state["selected_sponsor"])

    # ─────────── HOME ─────────────────────────────────────────────────────
    @staticmethod
    def _render_home() -> None:
        cards = [
            ("✨", "Tips & tricks", "Råd för att locka sponsorer snabbare."),
            ("⚙️", "Inställningar", "Justera profil, sekretess och synlighet."),
            ("ℹ️", "Om Sponsorly", "Så fungerar plattformen och affärsmodellen."),
            ("🤝", "Partnerskap", "Framgångscase och inspirerande stories."),
            ("📣", "Nyheter", "Senaste uppdateringar och releaser."),
            ("❓", "Support & FAQ", "Hjälp, guider och vanliga frågor."),
        ]
        cols = st.columns(3, gap="large")
        for i, (icon, title, text) in enumerate(cards):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
                                padding:1.5rem;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,0.05);">
                      <div style="font-size:2rem;color:#2563eb;margin-bottom:0.5rem;">{icon}</div>
                      <div style="font-size:1.125rem;font-weight:600;color:#1e40af;margin-bottom:0.5rem;">{title}</div>
                      <div style="font-size:0.875rem;color:#4b5563;">{text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ─────────── SEARCH (with MAP) ───────────────────────────────────────
    def _render_search(self) -> None:
        st.markdown(
            "<h2 style='font-size:2rem;font-weight:600;color:#1e40af;'>Sök sponsorer</h2>",
            unsafe_allow_html=True,
        )
        f1, f2 = st.columns(2, gap="large")
        with f1:
            city     = st.text_input("Ort", value="", key="filter_city")
            radius   = st.slider("Radie (km)", 0, 100, 25, key="filter_radius")
            industry = st.selectbox("Bransch", ["Bank", "Energi", "IT"], key="filter_industry")
            size     = st.selectbox("Storlek", ["Liten", "Medel", "Stor"], key="filter_size")
            if st.button("Sök", key="do_search"):
                st.session_state["results"] = self._get_dummy_sponsors(city, radius, industry, size)

        with f2:
            results = st.session_state.get("results", [])
            if not results:
                st.info("Välj filter och klicka på Sök")
            else:
                cols = st.columns(2, gap="large")
                for i, s in enumerate(results):
                    with cols[i % 2]:
                        st.markdown(
                            f"""
                            <div style="background:white;padding:1.5rem;border-radius:8px;
                                        box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                              <div style="font-size:1.125rem;font-weight:700;color:#1e40af;">
                                {s['name']}
                              </div>
                              <div style="font-size:0.875rem;color:#4b5563;">
                                {s['description']}
                              </div>
                              <div style="margin-top:1rem;">
                                <button style="background:#2563eb;color:white;padding:0.5rem 1rem;
                                               border:none;border-radius:4px;">
                                  📧 Kontakta
                                </button>
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                st.markdown("### Kartvy", unsafe_allow_html=True)
                self._render_map()

    # ─────────── PROFILE ────────────────────────────────────────────────────
    @staticmethod
    def _render_profile() -> None:
        st.markdown(
            "<h2 style='font-size:2rem;font-weight:600;color:#1e40af;'>Min förening</h2>",
            unsafe_allow_html=True,
        )
        with st.form("profile_form"):
            st.text_input("Föreningens namn", value="", key="profile_name")
            st.text_input("Ort", value="", key="profile_city")
            st.text_input("E-post", value="", key="profile_email")
            st.text_input("Telefon", value="", key="profile_phone")
            st.text_area("Sponsringsbehov", value="", key="profile_needs")
            st.form_submit_button("Spara")

    # ─────────── SUGGESTIONS ───────────────────────────────────────────────
    def _render_suggestions(self) -> None:
        st.markdown(
            "<h2 style='font-size:2rem;font-weight:600;color:#1e40af;'>Rekommenderade sponsorer</h2>",
            unsafe_allow_html=True,
        )
        for i, s in enumerate(self._get_dummy_sponsors()):
            col = st.columns(2, gap="large")[i % 2]
            with col:
                st.markdown(
                    f"""
                    <div style="background:#eff6ff;border:1px solid #bfdbfe;
                                border-radius:8px;padding:1.5rem;text-align:center;
                                box-shadow:0 1px 2px rgba(0,0,0,0.05);">
                      <div style="font-size:1.125rem;font-weight:600;color:#1e40af;">
                        {s['name']}
                      </div>
                      <div style="font-size:0.875rem;color:#4b5563;">
                        {s['description']}
                      </div>
                      <div style="margin-top:1rem;">
                        <button style="background:#2563eb;color:white;padding:0.5rem 1rem;
                                       border:none;border-radius:4px;">
                          📩 Kontakta
                        </button>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ─────────── DUMMY DATA ────────────────────────────────────────────────
    @staticmethod
    def _get_dummy_sponsors(
        city: Optional[str] = None,
        radius: Optional[int] = None,
        industry: Optional[str] = None,
        size: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        _ = (city, radius, industry, size)
        return [
            {
                "id": 1,
                "name": "Nordic Bank",
                "description": "Vill stötta lokal ungdomsidrott.",
                "lat": 57.70,
                "lon": 11.97,
                "score": 75,
                "contact": {"email": "kontakt@nordicbank.se", "phone": "08-123456"},
            },
            {
                "id": 2,
                "name": "Energigruppen AB",
                "description": "Söker gröna partners.",
                "lat": 57.71,
                "lon": 11.98,
                "score": 50,
                "contact": {"email": "info@energi.se", "phone": "031-987654"},
            },
            {
                "id": 3,
                "name": "Techify Solutions",
                "description": "Digital inkludering för unga.",
                "lat": 57.72,
                "lon": 11.99,
                "score": 90,
                "contact": {"email": "hej@techify.solutions", "phone": "070-112233"},
            },
        ]

    # ─────────── MAP METHOD ──────────────────────────────────────────────────
    def _render_map(self) -> None:
        club = st.session_state.get(
            "club_data", {"lat": 57.7089, "lon": 11.9746}
        )
        recs = st.session_state.get("results", [])

        center = [club.get("lat", 57.7089), club.get("lon", 11.9746)]
        m = Map(location=center, zoom_start=11)

        # Club marker
        if "id" in club:
            Marker(
                location=[club["lat"], club["lon"]],
                popup=Popup(f"<b>{club.get('name','Din förening')}</b>", max_width=300),
                icon=Icon(color="red", icon="home"),
            ).add_to(m)

        # Sponsors cluster + heatmap
        if recs:
            cluster = MarkerCluster().add_to(m)
            heat = []
            for comp in recs:
                lat = comp.get("lat")
                lon = comp.get("lon")
                if lat and lon:
                    Marker(
                        location=[lat, lon],
                        popup=Popup(
                            f"<b>{comp['name']}</b><br/>{comp['description']}", max_width=300
                        ),
                        icon=Icon(color="blue", icon="industry"),
                    ).add_to(cluster)
                    heat.append([lat, lon, comp.get("score", 0)])
            if heat:
                HeatMap(heat).add_to(m)

        st_folium(m, use_container_width=True, height=400)

    # ─────────── MODALS ─────────────────────────────────────────────────────
    @staticmethod
    def _show_login_modal() -> None:
        with _open_modal("Logga in"):
            st.text_input("E-post", value="", key="login_email")
            st.text_input("Lösenord", value="", type="password", key="login_pw")
            if st.button("Logga in", key="login_submit"):
                st.session_state["show_login"] = False

    @staticmethod
    def _show_sponsor_modal(sponsor: Dict[str, Any]) -> None:
        with _open_modal(sponsor["name"]):
            st.write(sponsor["description"])
            st.write(f"📧  {sponsor['contact']['email']}")
            st.write(f"📞  {sponsor['contact']['phone']}")
            st.text_area("Meddelande", value="", key="msg_to_sponsor")
            if st.button("Skicka", key="msg_submit"):
                st.success("Meddelande skickat!")
                st.session_state["selected_sponsor"] = None


def main() -> None:
    SponsorMatchUI().render_main_page()


if __name__ == "__main__":
    main()
