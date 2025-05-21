from typing import List, Dict, Any, Optional

import streamlit as st
# Folium & Streamlit-Folium imports for the map
from folium import Map, Marker, Popup, Icon
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

# Fallback if st.modal isn't available
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
        # ─── COMBINED CSS: GLOBAL STYLES, GRADIENT BG, FIXED WIDTH & TABS ──────────
        st.markdown(
            """
            <style>
              /* your existing global styles (cards, centering, etc.) */

              /* full-screen Tailwind gradient background */
              [data-testid="stAppViewContainer"] {
                background: linear-gradient(
                  45deg,
                  #DBEAFE 0%,
                  #BFDBFE 50%,
                  #93C5FD 100%
                );
                min-height: 100vh;
              }

              /* make the inner Streamlit container transparent and constrain width */
              .css-18e3th9 {
                background: transparent;
                max-width: 1200px !important;
                margin: auto;
              }

              /* hide default hamburger & footer */
              #MainMenu, footer { visibility: hidden; }

              /* horizontal tab bar styling */
              .stTabs [role="tablist"] {
                background-color: #1e3a8a;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                margin-top: 2rem;
                margin-bottom: 1.5rem;
                display: inline-flex;
              }
              .stTabs [role="tab"] {
                color: white;
                padding: 0.5rem 1rem;
                margin: 0 0.25rem;
                border-radius: 0.25rem;
              }
              .stTabs [aria-selected="true"] {
                background-color: #1e40af;
                color: white;
                box-shadow: none !important;
              }
              .stTabs [role="tab"][aria-selected="true"]::after {
                content: "";
                display: block;
                width: 30%;
                height: 3px;
                background-color: #BFDBFE;
                border-radius: 1px;
                margin: 0.1rem auto 0;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ─── SIDEBAR ────────────────────────────────────────────────────────────
        with st.sidebar:
            st.title("Golden Sugar Daddy Goal")
            if st.button("🔑 Logga in", key="login_button"):
                st.session_state["show_login"] = True

        # ─── HERO / HEADER ─────────────────────────────────────────────────────
        st.markdown(
            "<h1 style='font-size:3.5rem; font-weight:800; text-align:center; color:#1e3a8a;'>Golden Sugar Daddy Goal</h1>",
            unsafe_allow_html=True,
        )

        # ─── HORIZONTAL TABS NAV ───────────────────────────────────────────────
        tabs = st.tabs(["🏠 Hem", "🎯 Hitta sponsorer", "⚙️ Inställningar", "👤 Min sida"])
        with tabs[0]:
            self._render_home()
        with tabs[1]:
            self._render_search()
        with tabs[2]:
            self._render_settings()
        with tabs[3]:
            self._render_profile()

        # ─── MODALS ────────────────────────────────────────────────────────────
        if st.session_state.get("show_login"):
            self._show_login_modal()
        if st.session_state.get("selected_sponsor"):
            self._show_sponsor_modal(st.session_state["selected_sponsor"])

    # ─────────── HOME ────────────────────────────────────────────────────────
    @staticmethod
    def _render_home() -> None:
        # Welcome message or introduction instead of cards
        st.markdown(
            """
            <h2 style='font-size:2rem;font-weight:600;color:#1e40af;'>Välkommen till Golden Sugar Daddy Goal</h2>
            <p style='font-size:1.2rem;color:#4b5563;'>
                Hitta de perfekta sponsorerna för din förening med hjälp av vår
                avancerade matchmaking-plattform.
            </p>
            """,
            unsafe_allow_html=True
        )

        # Empty space
        st.markdown("<br>", unsafe_allow_html=True)

        # Call-to-action
        st.markdown(
            """
            <div style='text-align:center;'>
                <p style='font-size:1.5rem;color:#1e40af;font-weight:500;'>
                    Kom igång genom att klicka på "Hitta sponsorer" fliken ovan
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ─────────── SEARCH (with MAP) ─────────────────────────────────────────
    def _render_search(self) -> None:
        st.markdown(
            "<h2 style='font-size:2rem;font-weight:600;color:#1e40af;'>Sök sponsorer</h2>",
            unsafe_allow_html=True,
        )

        # Database connection to fetch associations
        from sponsor_match.core.db import get_engine
        from sqlalchemy import text
        import pandas as pd

        engine = get_engine()

        # Step 1: Association Search with Autocomplete
        st.markdown("<h3>Steg 1: Hitta din förening</h3>", unsafe_allow_html=True)

        # Get all associations from database
        with engine.connect() as conn:
            associations_df = pd.read_sql("SELECT id, name, member_count, address, lat, lon, size_bucket FROM clubs",
                                          conn)

        # Create association autocomplete
        association_input = st.text_input("Ange din förenings namn", key="association_name")

        # Filter associations based on input
        filtered_associations = []
        if association_input:
            filtered_associations = associations_df[associations_df['name'].str.contains(association_input, case=False)]

        # Display matching associations
        selected_association = None
        new_association = False

        if not filtered_associations.empty:
            association_options = filtered_associations['name'].tolist()
            selected_assoc_name = st.selectbox("Välj din förening från listan", options=[""] + association_options,
                                               key="selected_assoc")

            if selected_assoc_name:
                selected_association = filtered_associations[filtered_associations['name'] == selected_assoc_name].iloc[
                    0]

                # Display association details
                st.markdown(f"""
                <div style="background:#eff6ff;padding:1rem;border-radius:8px;margin-bottom:1rem;">
                    <h4 style="margin:0;color:#1e40af;">Förening: {selected_association['name']}</h4>
                    <p style="margin:0;">Adress: {selected_association['address']}</p>
                    <p style="margin:0;">Storlek: {selected_association['size_bucket'].capitalize()}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            if association_input:
                st.warning("Din förening hittades inte. Vill du registrera den?")
                if st.button("Ja, registrera min förening"):
                    new_association = True

        # Step 2: New Association Registration (if needed)
        if new_association:
            st.markdown("<h3>Steg 2: Registrera din förening</h3>", unsafe_allow_html=True)
            with st.form("new_association_form"):
                assoc_name = st.text_input("Föreningens namn", value=association_input)
                assoc_address = st.text_input("Fullständig adress", help="Gatuadress, postnummer och ort")
                assoc_members = st.number_input("Antal medlemmar", min_value=1, value=100)

                # Determine size bucket based on members
                size_bucket = "small"
                if assoc_members > 500:
                    size_bucket = "large"
                elif assoc_members > 100:
                    size_bucket = "medium"

                st.info(f"Din förening klassificeras som {size_bucket.upper()} baserat på medlemsantalet.")

                submit = st.form_submit_button("Registrera")

                if submit:
                    # Geocode the address
                    from geopy.geocoders import Nominatim
                    from geopy.extra.rate_limiter import RateLimiter

                    geolocator = Nominatim(user_agent="sponsor_match_geo")
                    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

                    with st.spinner('Hämtar din förenings plats...'):
                        location = geocode(assoc_address)

                    if location:
                        lat, lon = location.latitude, location.longitude

                        # Insert new association into database
                        with engine.connect() as conn:
                            conn.execute(text("""
                            INSERT INTO clubs (name, address, member_count, lat, lon, size_bucket)
                            VALUES (:name, :address, :members, :lat, :lon, :size_bucket)
                            """), {
                                "name": assoc_name,
                                "address": assoc_address,
                                "members": assoc_members,
                                "lat": lat,
                                "lon": lon,
                                "size_bucket": size_bucket
                            })
                            conn.commit()

                        # Get the newly created association
                        with engine.connect() as conn:
                            result = conn.execute(text("""
                            SELECT id, name, member_count, address, lat, lon, size_bucket 
                            FROM clubs WHERE name = :name AND address = :address
                            """), {"name": assoc_name, "address": assoc_address})
                            row = result.fetchone()
                            if row:
                                # Convert row to dict with proper keys
                                keys = ["id", "name", "member_count", "address", "lat", "lon", "size_bucket"]
                                selected_association = {keys[i]: value for i, value in enumerate(row)}

                        st.success("Förening registrerad!")
                    else:
                        st.error("Kunde inte hitta adressen. Kontrollera och försök igen.")

        # Step 3: Search Parameters
        if selected_association is not None:
            st.markdown("<h3>Steg 3: Sökparametrar</h3>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                radius = st.slider("Sökradie (km)", 1, 50, 10, key="search_radius")

            # Store association in session state
            st.session_state["current_association"] = selected_association

            # Search button
            if st.button("Sök sponsorer", key="search_sponsors_btn"):
                # Search for companies
                with st.spinner('Söker efter lämpliga sponsorer...'):
                    with engine.connect() as conn:
                        # Get companies matching size and within radius
                        sql = text("""
                        SELECT c.*, 
                               SQRT(POW(111.2 * (c.lat - :lat), 2) + POW(111.2 * (:lon - c.lon) * COS(c.lat / 57.3), 2)) AS distance
                        FROM companies c
                        WHERE c.size_bucket = :size_bucket
                        HAVING distance <= :radius
                        ORDER BY distance ASC
                        """)

                        companies = pd.read_sql(sql, conn, params={
                            "lat": selected_association["lat"],
                            "lon": selected_association["lon"],
                            "size_bucket": selected_association["size_bucket"],
                            "radius": radius
                        })

                        # Save results to session state
                        if not companies.empty:
                            st.session_state["search_results"] = companies.to_dict('records')
                            st.session_state["current_page"] = 0
                        else:
                            st.warning("Inga matchande företag hittades inom den angivna radien.")
                            st.session_state["search_results"] = []

        # Step 4: Display Results
        if "search_results" in st.session_state and st.session_state["search_results"]:
            st.markdown("<h3>Steg 4: Sökresultat</h3>", unsafe_allow_html=True)

            # Pagination
            results = st.session_state["search_results"]
            page_size = 10
            total_pages = (len(results) + page_size - 1) // page_size

            # Display page navigation
            col1, col2, col3 = st.columns([2, 3, 2])

            with col1:
                if st.session_state["current_page"] > 0:
                    if st.button("◀ Föregående", key="prev_page"):
                        st.session_state["current_page"] -= 1

            with col2:
                st.write(f"Sida {st.session_state['current_page'] + 1} av {total_pages}")

            with col3:
                if st.session_state["current_page"] < total_pages - 1:
                    if st.button("Nästa ▶", key="next_page"):
                        st.session_state["current_page"] += 1

            # Get current page results
            start_idx = st.session_state["current_page"] * page_size
            end_idx = min(start_idx + page_size, len(results))
            page_results = results[start_idx:end_idx]

            # Display results and map
            col1, col2 = st.columns([3, 5])

            with col1:
                for company in page_results:
                    # Create clickable result card
                    is_selected = st.session_state.get("selected_company_id") == company["id"]
                    card_style = f"background:{'#e6f2ff' if is_selected else 'white'};padding:1rem;border-radius:8px;margin-bottom:0.5rem;cursor:pointer;border:{'2px solid #2563eb' if is_selected else '1px solid #e5e7eb'};"

                    html = f"""
                    <div style="{card_style}" onclick="this.style.border='2px solid #2563eb';window.parent.postMessage({{company_id: {company['id']}}}, '*');">
                        <div style="font-weight:600;color:#1e40af;">{company['name']}</div>
                        <div style="font-size:0.875rem;color:#4b5563;">Avstånd: {company['distance']:.1f} km</div>
                        <div style="font-size:0.875rem;color:#4b5563;">Storlek: {company['size_bucket'].capitalize()}</div>
                    </div>
                    """

                    st.markdown(html, unsafe_allow_html=True)

                    # JavaScript to handle clicks
                    st.markdown("""
                    <script>
                    window.addEventListener('message', function(e) {
                        if (e.data.company_id) {
                            // Use Streamlit's setComponentValue when available
                            if (window.streamlitTurbo) {
                                window.streamlitTurbo.setComponentValue({name: 'selected_company_id', value: e.data.company_id});
                            }
                        }
                    });
                    </script>
                    """, unsafe_allow_html=True)

            with col2:
                # Render map with association and companies
                self._render_results_map(st.session_state["current_association"], page_results)

    # Add new method to render results map
    @staticmethod
    def _render_results_map(association, companies):
        import folium
        from streamlit_folium import st_folium

        # Create map centered on association
        m = folium.Map(location=[association["lat"], association["lon"]], zoom_start=12)

        # Add association marker
        folium.Marker(
            location=[association["lat"], association["lon"]],
            popup=f"<b>{association['name']}</b><br>({association['size_bucket'].capitalize()})",
            icon=folium.Icon(color="red", icon="home"),
        ).add_to(m)

        # Add markers for each company
        for company in companies:
            folium.Marker(
                location=[company["lat"], company["lon"]],
                popup=f"<b>{company['name']}</b><br>Avstånd: {company['distance']:.1f} km<br>Storlek: {company['size_bucket'].capitalize()}",
                icon=folium.Icon(color="blue", icon="briefcase"),
            ).add_to(m)

        # Create a line from association to selected company if any
        if "selected_company_id" in st.session_state:
            selected = next((c for c in companies if c["id"] == st.session_state["selected_company_id"]), None)
            if selected:
                folium.PolyLine(
                    locations=[[association["lat"], association["lon"]], [selected["lat"], selected["lon"]]],
                    color="blue",
                    weight=2,
                    opacity=0.7,
                    dash_array="5"
                ).add_to(m)

        # Display the map
        st_folium(m, height=500)

    # ─────────── SETTINGS PAGE ───────────────────────────────────────────────
    @staticmethod
    def _render_settings() -> None:
        st.markdown(
            "<h2 style='font-size:2rem;font-weight:600;color:#1e40af;'>Inställningar</h2>",
            unsafe_allow_html=True,
        )

        with st.form("settings_form"):
            st.subheader("Notifikationer")
            # Prefix with underscore to indicate intentionally unused variables
            _email_notifications = st.checkbox("E-postnotifikationer", value=True)
            _sponsorship_alerts = st.checkbox("Sponsringsrekommendationer", value=True)

            st.subheader("Visningsalternativ")
            st.select_slider(
                "Resultat per sida",
                options=[5, 10, 15, 20, 25],
                value=15
            )
            st.select_slider(
                "Kartdetaljnivå",
                options=["Låg", "Medium", "Hög"],
                value="Medium"
            )

            st.subheader("Datainställningar")
            st.checkbox("Spara sökhistorik", value=True)
            st.checkbox("Tillåt anonym användardata", value=True)

            st.form_submit_button("Spara inställningar")

    # ─────────── PROFILE ─────────────────────────────────────────────────────
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
        # Using _ to indicate intentionally unused parameters
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

    # ─────────── MAP METHOD ───────────────────────────────────────────────
    @staticmethod
    def _render_map() -> None:
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
                popup=Popup(f"<b>{club.get('name', 'Din förening')}</b>", max_width=300),
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

    # ─────────── MODALS ────────────────────────────────────────────────────
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