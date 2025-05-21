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
        # ─── ENHANCED CSS WITH FIXES FOR IDENTIFIED ISSUES ───────────────────────
        st.markdown(
            """
            <style>
                /* Core Layout Structure */
                [data-testid="stAppViewContainer"] {
                    background: linear-gradient(to bottom, #f0f9ff, #e0f2fe);
                }

                /* Main content area with white background and proper centering */
                .main-content {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    max-width: 1000px;
                    margin: 1rem auto;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                }

                /* Improved heading contrast */
                h1, h2, h3 {
                    color: #0f2652 !important;
                    font-weight: 700 !important;
                    margin-bottom: 1rem !important;
                }

                /* Body text improvements */
                p, label, div:not(.main-content) {
                    color: #334155 !important;
                    font-size: 16px !important;
                }

                /* IMPROVED NAVIGATION BAR - Moved to top, wider, and more prominent */
                .navigation-container {
                    display: flex;
                    justify-content: center;
                    width: 100%;
                    margin: 0.5rem 0 2rem 0;
                    padding: 0.5rem 0;
                    background: rgba(255, 255, 255, 0.7);
                    backdrop-filter: blur(10px);
                    position: sticky;
                    top: 0;
                    z-index: 100;
                }

                .nav-tabs {
                    display: flex;
                    background: #1e3a8a;
                    border-radius: 8px;
                    padding: 0.5rem;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    margin: 0 auto;
                    width: 80%;
                    max-width: 800px;
                    justify-content: center;
                }

                .nav-tab {
                    padding: 0.75rem 1.5rem;
                    margin: 0 0.25rem;
                    border-radius: 6px;
                    color: white;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .nav-tab.active {
                    background: #2563eb;
                    color: white;
                }

                .nav-tab:hover:not(.active) {
                    background: rgba(255, 255, 255, 0.2);
                }

                /* Form elements styling - clearer boundaries and better contrast */
                input[type="text"], input[type="number"], input[type="email"], 
                textarea, select, .stSelectbox > div > div {
                    background: white !important;
                    border: 1px solid #cbd5e1 !important;
                    border-radius: 6px !important;
                    padding: 0.75rem 1rem !important;
                    color: #1e293b !important;
                    max-width: 500px !important;
                    box-shadow: none !important;
                }

                /* Focused input styling */
                input:focus, textarea:focus, select:focus {
                    border-color: #3b82f6 !important;
                    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
                }

                /* Button styling - more visible */
                .stButton > button {
                    background-color: #1e40af !important;
                    color: white !important;
                    font-weight: 500 !important;
                    padding: 0.75rem 1.5rem !important;
                    border-radius: 6px !important;
                    border: none !important;
                    transition: all 0.2s !important;
                    text-transform: none !important;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
                }

                .stButton > button:hover {
                    background-color: #1e3a8a !important;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
                }

                /* Fixed slider width with better color */
                .stSlider {
                    max-width: 400px !important;
                }

                .stSlider > div > div > div {
                    background-color: #1e40af !important;
                }

                /* Reposition sidebar with improved contrast */
                [data-testid="stSidebar"] {
                    background-color: #1e3a8a !important;
                    color: white !important;
                    padding-top: 2rem !important;
                }

                [data-testid="stSidebar"] button {
                    background-color: white !important;
                    color: #1e3a8a !important;
                }

                [data-testid="stSidebar"] h1, 
                [data-testid="stSidebar"] h2, 
                [data-testid="stSidebar"] h3 {
                    color: white !important;
                }

                /* Fix for checkbox styling - better visibility */
                .stCheckbox > label {
                    color: #1e293b !important;
                    font-weight: 500 !important;
                }

                .stCheckbox > div[role="checkbox"] {
                    border-color: #3b82f6 !important;
                }

                /* Make sure map is visible - added height and border */
                .folium-map {
                    width: 100% !important;
                    min-height: 450px !important;
                    margin-top: 1rem !important;
                    border-radius: 8px !important;
                    border: 1px solid #e2e8f0 !important;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
                }

                /* Helper classes */
                .mb-4 {
                    margin-bottom: 1rem !important;
                }

                .mt-4 {
                    margin-top: 1rem !important;
                }

                .text-center {
                    text-align: center !important;
                }

                /* Card styling for content sections */
                .content-card {
                    background: white;
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }

                /* Hide default hamburger & footer */
                #MainMenu, footer { visibility: hidden; }

                /* Fix for sidebar toggle button */
                button[kind="header"] {
                    background-color: transparent !important;
                    color: #1e293b !important;
                }

                /* Improve select dropdown visibility */
                .stSelectbox > div > div[data-baseweb="select"] > div {
                    background-color: white !important;
                    color: #1e293b !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ─── CUSTOM NAVIGATION (REPLACES TABS) ────────────────────────────────────
        # This creates a more styled, centered navigation at the top

        # Get the current tab from session state or default to Home
        if "current_tab" not in st.session_state:
            st.session_state["current_tab"] = "home"

        # Create centered heading
        st.markdown("<h1 class='text-center'>Golden Sugar Daddy Goal</h1>", unsafe_allow_html=True)

        nav_html = """
        <div class="navigation-container">
            <div class="nav-tabs">
                <div class="nav-tab {home_active}" onclick="setTab('home')">🏠 Hem</div>
                <div class="nav-tab {search_active}" onclick="setTab('search')">🎯 Hitta sponsorer</div>
                <div class="nav-tab {settings_active}" onclick="setTab('settings')">⚙️ Inställningar</div>
                <div class="nav-tab {profile_active}" onclick="setTab('profile')">👤 Min förening</div>
            </div>
        </div>

        <script>
        function setTab(tab) {
            // Use Streamlit's setState mechanism
            window.parent.postMessage({{
                type: "streamlit:setComponentValue",
                value: tab,
                dataType: "str",
                componentId: "nav_tab_state"
            }}, "*");
        }
        </script>
        """.format(
            home_active="active" if st.session_state["current_tab"] == "home" else "",
            search_active="active" if st.session_state["current_tab"] == "search" else "",
            settings_active="active" if st.session_state["current_tab"] == "settings" else "",
            profile_active="active" if st.session_state["current_tab"] == "profile" else ""
        )

        # Display the navigation
        st.markdown(nav_html, unsafe_allow_html=True)

        # This enables the JavaScript to communicate tab changes back to Streamlit
        nav_tab = st.text_input("", key="nav_tab_state", label_visibility="collapsed")
        if nav_tab and nav_tab != st.session_state["current_tab"]:
            st.session_state["current_tab"] = nav_tab
            st.experimental_rerun()

        # ─── MAIN CONTENT AREA ─────────────────────────────────────────────────────
        # Wrap main content in a white card with proper width
        st.markdown('<div class="main-content">', unsafe_allow_html=True)

        # Show the appropriate tab content based on state
        if st.session_state["current_tab"] == "home":
            self._render_home()
        elif st.session_state["current_tab"] == "search":
            self._render_search()
        elif st.session_state["current_tab"] == "settings":
            self._render_settings()
        elif st.session_state["current_tab"] == "profile":
            self._render_profile()

        # Close the main content div
        st.markdown('</div>', unsafe_allow_html=True)

        # ─── SIDEBAR ────────────────────────────────────────────────────────────
        with st.sidebar:
            st.title("Golden Sugar Daddy Goal")
            if st.button("🔑 Logga in", key="login_button"):
                st.session_state["show_login"] = True

        # ─── MODALS ────────────────────────────────────────────────────────────
        if st.session_state.get("show_login"):
            self._show_login_modal()
        if st.session_state.get("selected_sponsor"):
            self._show_sponsor_modal(st.session_state["selected_sponsor"])

    # ─────────── HOME ────────────────────────────────────────────────────────
    @staticmethod
    def _render_home() -> None:
        # Welcome message with improved styling
        st.markdown(
            """
            <h2>Välkommen till Golden Sugar Daddy Goal</h2>
            <p style='font-size:1.1rem;margin-bottom:2rem;'>
                Hitta de perfekta sponsorerna för din förening med hjälp av vår
                avancerade matchmaking-plattform.
            </p>

            <div class="content-card" style="text-align:center;padding:2rem;">
                <img src="https://via.placeholder.com/150x150" alt="Logo" style="border-radius:50%;margin-bottom:1.5rem;" />
                <h3>Hitta sponsorer på ett smartare sätt</h3>
                <p>Vår plattform matchar din förening med sponsorer som har samma värderingar och mål.</p>
                <div style="margin-top:2rem;">
                    <button onclick="setTab('search')" style="background:#1e40af;color:white;padding:0.75rem 1.5rem;border:none;border-radius:6px;font-weight:500;cursor:pointer;">
                        Kom igång nu
                    </button>
                </div>
            </div>

            <script>
            function setTab(tab) {
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: tab,
                    dataType: "str",
                    componentId: "nav_tab_state"
                }, "*");
            }
            </script>
            """,
            unsafe_allow_html=True
        )

    # ─────────── SEARCH (with MAP) ─────────────────────────────────────────
    def _render_search(self) -> None:
        st.markdown("<h2>Hitta sponsorer</h2>", unsafe_allow_html=True)

        # Create two columns for better layout
        col1, col2 = st.columns([3, 5], gap="large")

        with col1:
            # Database connection to fetch associations
            from sponsor_match.core.db import get_engine
            from sqlalchemy import text
            import pandas as pd

            engine = get_engine()

            # Step 1: Association Search with Autocomplete
            st.markdown("<h3>Steg 1: Hitta din förening</h3>", unsafe_allow_html=True)

            # Get all associations from database
            try:
                with engine.connect() as conn:
                    associations_df = pd.read_sql(
                        "SELECT id, name, member_count, address, lat, lon, size_bucket FROM clubs",
                        conn)
            except Exception as e:
                st.error(f"Kunde inte ansluta till databasen: {str(e)}")
                associations_df = pd.DataFrame(
                    columns=['id', 'name', 'member_count', 'address', 'lat', 'lon', 'size_bucket'])

            # Create association autocomplete
            association_input = st.text_input("Ange din förenings namn", key="association_name")

            # Filter associations based on input
            filtered_associations = pd.DataFrame()
            if association_input:
                filtered_associations = associations_df[
                    associations_df['name'].str.contains(association_input, case=False)]

            # Display matching associations
            selected_association = None
            new_association = False

            if not filtered_associations.empty:
                association_options = filtered_associations['name'].tolist()
                selected_assoc_name = st.selectbox("Välj din förening från listan", options=[""] + association_options,
                                                   key="selected_assoc")

                if selected_assoc_name:
                    # FIX: Added proper error handling for DataFrame access
                    filtered_result = filtered_associations[filtered_associations['name'] == selected_assoc_name]
                    if not filtered_result.empty:
                        # Now we can safely use .iloc[0]
                        selected_association = filtered_result.iloc[0]

                        # Display association details
                        st.markdown(f"""
                        <div class="content-card">
                            <h4 style="margin-top:0;color:#1e40af;">Förening: {selected_association['name']}</h4>
                            <p>Adress: {selected_association['address']}</p>
                            <p>Storlek: {selected_association['size_bucket'].capitalize()}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Ingen exakt matchning hittades")
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
                            try:
                                with engine.connect() as conn:
                                    conn.execute(text("""
                                    INSERT INTO clubs (name, address, member_count, lat, lon, size_bucket)
                                    VALUES (:name, :address, :members, :lat, :lon, :size_bucket)
                                    """), {
                                        "name": assoc_name,
                                        "address": assoc_address,
                                        "members": int(assoc_members),
                                        "lat": float(lat),
                                        "lon": float(lon),
                                        "size_bucket": str(size_bucket)
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
                            except Exception as e:
                                st.error(f"Kunde inte registrera föreningen: {str(e)}")
                        else:
                            st.error("Kunde inte hitta adressen. Kontrollera och försök igen.")

            # Step 3: Search Parameters
            if selected_association is not None:
                st.markdown("<h3>Steg 3: Sökparametrar</h3>", unsafe_allow_html=True)

                radius = st.slider("Sökradie (km)", 1, 50, 10, key="search_radius")

                # Store association in session state
                st.session_state["current_association"] = selected_association

                # Search button
                if st.button("Sök sponsorer", key="search_sponsors_btn"):
                    # Search for companies
                    with st.spinner('Söker efter lämpliga sponsorer...'):
                        try:
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

                                # FIX: Ensure proper type conversion in parameters
                                companies = pd.read_sql(sql, conn, params={
                                    "lat": float(selected_association["lat"]),
                                    "lon": float(selected_association["lon"]),
                                    "size_bucket": str(selected_association["size_bucket"]),
                                    "radius": float(radius)
                                })

                                # Save results to session state
                                if not companies.empty:
                                    st.session_state["search_results"] = companies.to_dict('records')
                                    st.session_state["current_page"] = 0
                                else:
                                    st.warning("Inga matchande företag hittades inom den angivna radien.")
                                    st.session_state["search_results"] = []
                        except Exception as e:
                            st.error(f"Kunde inte söka efter företag: {str(e)}")
                            st.session_state["search_results"] = []

        with col2:
            # Map section header
            st.markdown("<h3>Karta över sponsorer</h3>", unsafe_allow_html=True)

            # Always show map, either with selected association or default view of Sweden
            if "current_association" in st.session_state and st.session_state.get("search_results"):
                # Show map with search results
                page_size = 10
                current_page = st.session_state.get("current_page", 0)
                results = st.session_state["search_results"]
                start_idx = current_page * page_size
                end_idx = min(start_idx + page_size, len(results))
                page_results = results[start_idx:end_idx]

                self._render_results_map(st.session_state["current_association"], page_results)

                # Show pagination and results below map
                if results:
                    total_pages = max(1, (len(results) + page_size - 1) // page_size)

                    # Display page navigation
                    cols = st.columns([2, 3, 2])

                    with cols[0]:
                        if current_page > 0:
                            if st.button("◀ Föregående", key="prev_page"):
                                st.session_state["current_page"] = current_page - 1
                                st.experimental_rerun()

                    with cols[1]:
                        st.markdown(f"<p style='text-align:center'>Sida {current_page + 1} av {total_pages}</p>",
                                    unsafe_allow_html=True)

                    with cols[2]:
                        if current_page < total_pages - 1:
                            if st.button("Nästa ▶", key="next_page"):
                                st.session_state["current_page"] = current_page + 1
                                st.experimental_rerun()

                    # Show result cards
                    for company in page_results:
                        is_selected = st.session_state.get("selected_company_id") == company["id"]
                        st.markdown(f"""
                        <div style="background:{'#e6f2ff' if is_selected else 'white'};padding:1rem;border-radius:8px;
                                    margin-bottom:0.5rem;border:{'2px solid #2563eb' if is_selected else '1px solid #e5e7eb'};
                                    cursor:pointer;" onclick="selectCompany({company['id']})">
                            <div style="font-weight:600;color:#1e40af;">{company['name']}</div>
                            <div style="font-size:0.875rem;color:#4b5563;">Avstånd: {company['distance']:.1f} km</div>
                            <div style="font-size:0.875rem;color:#4b5563;">Storlek: {company['size_bucket'].capitalize()}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # JavaScript to handle company selection
                    st.markdown("""
                    <script>
                    function selectCompany(id) {
                        window.parent.postMessage({
                            type: "streamlit:setComponentValue",
                            value: id,
                            dataType: "int",
                            componentId: "selected_company_id"
                        }, "*");
                    }
                    </script>
                    """, unsafe_allow_html=True)

                    # Hidden input to capture selected company
                    selected_id = st.text_input("", key="selected_company_id", label_visibility="collapsed")
                    if selected_id and selected_id != st.session_state.get("selected_company_id"):
                        st.session_state["selected_company_id"] = int(selected_id)
                        st.experimental_rerun()

            else:
                # Show default map centered on Sweden
                default_association = {
                    "lat": 59.3293,
                    "lon": 18.0686,
                    "name": "Sverige",
                    "size_bucket": "medium"
                }
                self._render_results_map(default_association, [])

                # Show helper text when no search has been performed
                st.markdown("""
                <div style="text-align:center;padding:1rem;background:#f8fafc;border-radius:8px;margin-top:1rem;">
                    <p>Välj din förening och klicka på "Sök sponsorer" för att se matchande sponsorer på kartan.</p>
                </div>
                """, unsafe_allow_html=True)

    # Add new method to render results map
    @staticmethod
    def _render_results_map(association, companies):
        import folium
        from streamlit_folium import st_folium

        # Create map centered on association
        try:
            # FIX: Ensure proper type conversion for map coordinates
            lat = float(association["lat"])
            lon = float(association["lon"])
            m = folium.Map(location=[lat, lon], zoom_start=12)

            # Add association marker
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{association['name']}</b><br>({association['size_bucket'].capitalize()})",
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(m)

            # Add markers for each company
            for company in companies:
                try:
                    comp_lat = float(company["lat"])
                    comp_lon = float(company["lon"])
                    folium.Marker(
                        location=[comp_lat, comp_lon],
                        popup=f"<b>{company['name']}</b><br>Avstånd: {company['distance']:.1f} km<br>Storlek: {company['size_bucket'].capitalize()}",
                        icon=folium.Icon(color="blue", icon="briefcase"),
                    ).add_to(m)
                except (KeyError, ValueError, TypeError):
                    # Skip this company if there's an issue with its coordinates
                    continue

            # Create a line from association to selected company if any
            if "selected_company_id" in st.session_state:
                # FIX: Use safe lookup with next() and a default value
                selected = next((c for c in companies if c["id"] == st.session_state["selected_company_id"]), None)
                if selected:  # Only proceed if we found a matching company
                    try:
                        folium.PolyLine(
                            locations=[[lat, lon], [float(selected["lat"]), float(selected["lon"])]],
                            color="#1e40af",
                            weight=3,
                            opacity=0.7,
                            dash_array="5"
                        ).add_to(m)
                    except (KeyError, ValueError, TypeError):
                        # Skip drawing line if there's an issue
                        pass

            # Display the map
            # FIX: Simplified st_folium call to avoid unexpected arguments
            st_folium(m, height=500)
        except Exception as e:
            st.error(f"Kunde inte visa kartan: {str(e)}")

    # ─────────── SETTINGS PAGE ───────────────────────────────────────────────
    @staticmethod
    def _render_settings() -> None:
        st.markdown("<h2>Inställningar</h2>", unsafe_allow_html=True)

        # Use columns for better layout
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown("<h3>Notifikationer</h3>", unsafe_allow_html=True)
            st.checkbox("E-postnotifikationer", value=True)
            st.checkbox("Sponsringsrekommendationer", value=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown("<h3>Datainställningar</h3>", unsafe_allow_html=True)
            st.checkbox("Spara sökhistorik", value=True)
            st.checkbox("Tillåt anonym användardata", value=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown("<h3>Visningsalternativ</h3>", unsafe_allow_html=True)
            st.markdown("<p>Resultat per sida</p>", unsafe_allow_html=True)
            st.select_slider(
                "Antal resultat",
                options=[5, 10, 15, 20, 25],
                value=15,
                key="results_per_page",
                label_visibility="collapsed"
            )

            st.markdown("<p>Kartdetaljnivå</p>", unsafe_allow_html=True)
            st.select_slider(
                "Detaljnivå",
                options=["Låg", "Medium", "Hög"],
                value="Medium",
                key="map_detail_level",
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Add save button at the bottom
        st.markdown('<div style="text-align:center;margin-top:2rem;">', unsafe_allow_html=True)
        if st.button("Spara inställningar", key="save_settings"):
            st.success("Inställningarna har sparats!")
        st.markdown('</div>', unsafe_allow_html=True)

    # ─────────── PROFILE ─────────────────────────────────────────────────────
    @staticmethod
    def _render_profile() -> None:
        st.markdown("<h2>Min förening</h2>", unsafe_allow_html=True)

        st.markdown('<div class="content-card">', unsafe_allow_html=True)

        # Use columns for form layout
        col1, col2 = st.columns(2, gap="medium")

        with col1:
            st.text_input("Föreningens namn", value="", key="profile_name")
            st.text_input("Ort", value="", key="profile_city")

        with col2:
            st.text_input("E-post", value="", key="profile_email")
            st.text_input("Telefon", value="", key="profile_phone")

        # Full width for sponsorship needs
        st.text_area("Sponsringsbehov", value="", key="profile_needs", height=150)

        # Add save button
        st.markdown('<div style="text-align:center;margin-top:1.5rem;">', unsafe_allow_html=True)
        if st.button("Spara", key="save_profile"):
            st.success("Profilen har sparats!")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

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

        # FIX: Simplified st_folium call to avoid unexpected arguments
        st_folium(m, height=400)

    # ─────────── MODALS ────────────────────────────────────────────────────
    @staticmethod
    def _show_login_modal() -> None:
        with _open_modal("Logga in"):
            st.markdown('<div style="padding:1rem;">', unsafe_allow_html=True)
            st.text_input("E-post", value="", key="login_email")
            st.text_input("Lösenord", value="", type="password", key="login_pw")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Logga in", key="login_submit"):
                    st.session_state["show_login"] = False
            with col2:
                if st.button("Avbryt", key="login_cancel"):
                    st.session_state["show_login"] = False
            st.markdown('</div>', unsafe_allow_html=True)

    @staticmethod
    def _show_sponsor_modal(sponsor: Dict[str, Any]) -> None:
        # FIX: Added safety check for sponsor structure
        if not isinstance(sponsor, dict):
            st.error("Ogiltig sponsor-data")
            return

        with _open_modal(sponsor.get("name", "Sponsor")):
            st.markdown('<div style="padding:1rem;">', unsafe_allow_html=True)

            # Company details
            st.markdown(f"""
            <div style="margin-bottom:1.5rem;">
                <p style="font-size:1rem;">{sponsor.get("description", "")}</p>
            </div>
            """, unsafe_allow_html=True)

            # Contact information
            contact = sponsor.get("contact", {})
            st.markdown(f"""
            <div style="margin-bottom:1.5rem;">
                <h4 style="margin-bottom:0.5rem;">Kontaktuppgifter</h4>
                <p><strong>E-post:</strong> {contact.get('email', 'N/A')}</p>
                <p><strong>Telefon:</strong> {contact.get('phone', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

            # Message form
            st.markdown("<h4>Skicka meddelande</h4>", unsafe_allow_html=True)
            st.text_area("Meddelande", value="", key="msg_to_sponsor", height=150)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Skicka", key="msg_submit"):
                    st.success("Meddelande skickat!")
                    st.session_state["selected_sponsor"] = None
            with col2:
                if st.button("Avbryt", key="msg_cancel"):
                    st.session_state["selected_sponsor"] = None

            st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    SponsorMatchUI().render_main_page()


if __name__ == "__main__":
    main()