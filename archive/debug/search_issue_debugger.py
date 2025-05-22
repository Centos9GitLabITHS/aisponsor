import os
from typing import Dict, Any

import pandas as pd
import streamlit as st

# Fallback if st.modal isn't available
_open_modal = getattr(st, "modal", st.expander)


def load_csv_data():
    """Load association data from CSV instead of database connection"""
    # Path to the CSV file - adjust as needed
    csv_path = os.path.join("data", "associations_goteborg_with_coords.csv")

    try:
        # Attempt to load the CSV file
        associations_df = pd.read_csv(csv_path)
        return associations_df
    except Exception as e:
        # If the file can't be loaded, create a sample dataframe with test data
        st.warning(f"Could not load CSV file: {str(e)}")
        st.warning("Using sample data instead.")

        # Create sample data based on the structure you provided
        sample_data = {
            "id": [1, 2, 3, 4, 5],
            "name": ["IFK Göteborg", "GAIS", "BK Häcken", "Örgryte IS", "Göteborgs Roddklubb"],
            "member_count": [1500, 800, 950, 600, 150],
            "address": [
                "Kamratgatan 1, 41528 Göteborg",
                "Gamla Ullevi, 41128 Göteborg",
                "Rambergsvallen, 41752 Göteborg",
                "Kärralundsvallen, 41670 Göteborg",
                "Färjenäsparken, 41804 Göteborg"
            ],
            "lat": [57.7084, 57.7102, 57.7193, 57.7041, 57.6941],
            "lon": [11.9746, 11.9866, 11.9367, 12.0027, 11.9124],
            "size_bucket": ["large", "medium", "medium", "medium", "small"]
        }
        return pd.DataFrame(sample_data)


class SponsorMatchUI:
    def __init__(self) -> None:
        st.set_page_config(
            page_title="Golden Sugar Daddy Goal",
            page_icon="⚽",
            layout="wide",
            initial_sidebar_state="collapsed",
        )

    def render_main_page(self) -> None:
        # Enhanced CSS for better visual appearance
        st.markdown(
            """
            <style>
                /* Core Layout Structure */
                [data-testid="stAppViewContainer"] {
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                }

                /* Main content area */
                .main-content {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    max-width: 1200px;
                    margin: 1rem auto;
                    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
                }

                /* Headings with enhanced styling */
                h1 {
                    color: #1e3a8a !important;
                    font-weight: 800 !important;
                    font-size: 2.5rem !important;
                    text-align: center;
                    margin-bottom: 1.5rem !important;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }

                h2 {
                    color: #1e3a8a !important;
                    font-weight: 700 !important;
                    font-size: 1.8rem !important;
                    margin-bottom: 1.2rem !important;
                    border-bottom: 2px solid #e0f2fe;
                    padding-bottom: 0.5rem;
                }

                h3 {
                    color: #1e40af !important;
                    font-weight: 600 !important;
                    font-size: 1.4rem !important;
                    margin-bottom: 1rem !important;
                    margin-top: 1.5rem !important;
                }

                /* Paragraph text */
                p, label, div:not(.main-content) {
                    color: #334155 !important;
                    line-height: 1.6 !important;
                }

                /* Enhanced tabs styling */
                .stTabs [data-baseweb="tab-list"] {
                    gap: 4px;
                    background-color: #1e3a8a !important;
                    border-radius: 10px;
                    padding: 6px 8px;
                    max-width: 800px;
                    margin: 0 auto 1.5rem auto;
                }

                .stTabs [data-baseweb="tab"] {
                    height: auto;
                    padding: 8px 24px;
                    color: white !important;
                    border-radius: 8px;
                    font-weight: 500;
                    margin: 0 2px;
                }

                .stTabs [aria-selected="true"] {
                    background-color: #2563eb !important;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }

                /* Form elements with better styling */
                [data-testid="stTextInput"] > div > div > input,
                [data-testid="stNumberInput"] > div > div > input,
                [data-testid="stTextArea"] > div > div > textarea {
                    background-color: white;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 12px 16px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                    font-size: 16px;
                }

                /* Button styling */
                .stButton > button {
                    background-color: #1e40af !important;
                    color: white !important;
                    font-weight: 500 !important;
                    padding: 0.625rem 1.5rem !important;
                    border-radius: 8px !important;
                    border: none !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                    transition: all 0.2s !important;
                }

                .stButton > button:hover {
                    background-color: #1e3a8a !important;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
                }

                /* Map container */
                .folium-map {
                    width: 100% !important;
                    min-height: 500px !important;
                    border-radius: 10px !important;
                    border: 1px solid #e2e8f0 !important;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.08) !important;
                }

                /* Card styling */
                .content-card {
                    background: white;
                    border-radius: 10px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                }

                /* Company card styling */
                .company-card {
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    transition: all 0.2s;
                }

                .company-card:hover {
                    border-color: #2563eb;
                    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
                    transform: translateY(-1px);
                }

                .company-card.selected {
                    background-color: #e6f2ff;
                    border: 2px solid #2563eb;
                }

                /* Sidebar styling */
                [data-testid="stSidebar"] {
                    background-color: #1e3a8a !important;
                    background-image: linear-gradient(180deg, #1e3a8a 0%, #2563eb 100%);
                    padding-top: 2rem !important;
                }

                [data-testid="stSidebar"] h1, 
                [data-testid="stSidebar"] h2, 
                [data-testid="stSidebar"] h3 {
                    color: white !important;
                }

                [data-testid="stSidebar"] button {
                    background-color: white !important;
                    color: #1e3a8a !important;
                }

                /* Hide default hamburger & footer */
                #MainMenu, footer { visibility: hidden; }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Center the title
        st.markdown("<h1>Golden Sugar Daddy Goal</h1>", unsafe_allow_html=True)

        # Use Streamlit's native tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Hem", "🎯 Hitta sponsorer", "⚙️ Inställningar", "👤 Min förening"])

        # Main content wrapper for each tab
        with tab1:
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            self._render_home()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            self._render_search()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab3:
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            self._render_settings()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab4:
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            self._render_profile()
            st.markdown('</div>', unsafe_allow_html=True)

        # Sidebar
        with st.sidebar:
            st.title("Golden Sugar Daddy Goal")
            if st.button("🔑 Logga in", key="login_button"):
                st.session_state["show_login"] = True

        # Modals
        if st.session_state.get("show_login"):
            self._show_login_modal()
        if st.session_state.get("selected_sponsor"):
            self._show_sponsor_modal(st.session_state["selected_sponsor"])

    # ─────────── HOME ────────────────────────────────────────────────────────
    @staticmethod
    def _render_home() -> None:
        # Clean and professional layout
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(
                """
                <h2>Välkommen till Golden Sugar Daddy Goal</h2>
                <p style='font-size:1.1rem;line-height:1.6;margin-bottom:1.5rem;'>
                    Hitta de perfekta sponsorerna för din förening med hjälp av vår
                    avancerade matchmaking-plattform.
                </p>

                <div style='margin-top:2rem;'>
                    <h3>Hur det fungerar</h3>
                    <div style='display:flex;align-items:center;margin-bottom:1rem;'>
                        <div style='background:#1e40af;color:white;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:16px;font-weight:bold;'>1</div>
                        <p>Registrera din förening eller hitta den i vår databas</p>
                    </div>
                    <div style='display:flex;align-items:center;margin-bottom:1rem;'>
                        <div style='background:#1e40af;color:white;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:16px;font-weight:bold;'>2</div>
                        <p>Ange dina sponsringsbehov och preferenser</p>
                    </div>
                    <div style='display:flex;align-items:center;margin-bottom:1rem;'>
                        <div style='background:#1e40af;color:white;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:16px;font-weight:bold;'>3</div>
                        <p>Få matchningar med företag som passar din profil</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                """
                <div style='background:#f0f9ff;border-radius:12px;padding:2rem;text-align:center;height:100%;'>
                    <img src="https://via.placeholder.com/150x150" alt="Logo" style="border-radius:50%;margin-bottom:1.5rem;width:150px;height:150px;box-shadow:0 4px 8px rgba(0,0,0,0.1);" />
                    <h3>Hitta sponsorer på ett smartare sätt</h3>
                    <p style='margin-bottom:2rem;'>Vår plattform matchar din förening med sponsorer som har samma värderingar och mål.</p>
                    <button 
                       style='background:#1e40af;color:white;padding:0.75rem 1.5rem;border-radius:8px;text-decoration:none;display:inline-block;font-weight:500;border:none;cursor:pointer;box-shadow:0 2px 4px rgba(0,0,0,0.1);'
                       onclick="document.querySelector('[data-baseweb=tab]').nextElementSibling.click();">
                        Kom igång nu
                    </button>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ─────────── SEARCH (with MAP) ─────────────────────────────────────────
    def _render_search(self) -> None:
        st.markdown("<h2>Hitta sponsorer</h2>", unsafe_allow_html=True)

        # Create two columns for better layout
        col1, col2 = st.columns([3, 5], gap="large")

        with col1:
            # Load data from CSV instead of database connection
            associations_df = load_csv_data()

            # Step 1: Association Search with Autocomplete
            st.markdown("<h3>Steg 1: Hitta din förening</h3>", unsafe_allow_html=True)

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

                            # Instead of inserting into database, create a new association object
                            selected_association = {
                                "id": len(associations_df) + 1,
                                "name": assoc_name,
                                "member_count": int(assoc_members),
                                "address": assoc_address,
                                "lat": float(lat),
                                "lon": float(lon),
                                "size_bucket": str(size_bucket)
                            }
                            st.success("Förening registrerad!")
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
                    # Instead of searching database, generate dummy companies
                    with st.spinner('Söker efter lämpliga sponsorer...'):
                        # Generate mock companies based on the selected association
                        companies = self._generate_mock_companies(selected_association, radius)

                        # Save results to session state
                        if companies:
                            st.session_state["search_results"] = companies
                            st.session_state["current_page"] = 0
                        else:
                            st.warning("Inga matchande företag hittades inom den angivna radien.")
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

                        # Create a visually appealing company card
                        st.markdown(f"""
                        <div class="company-card {'selected' if is_selected else ''}" 
                             onclick="selectCompany({company['id']})">
                            <div style="font-weight:600;color:#1e40af;font-size:1.1rem;margin-bottom:0.5rem;">
                                {company['name']}
                            </div>
                            <div style="display:flex;justify-content:space-between;color:#4b5563;">
                                <div>Avstånd: {company['distance']:.1f} km</div>
                                <div>Storlek: {company['size_bucket'].capitalize()}</div>
                            </div>
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
                        # Find the selected company and store it
                        selected_company = next((c for c in results if c["id"] == int(selected_id)), None)
                        if selected_company:
                            st.session_state["selected_sponsor"] = selected_company
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
                <div style="text-align:center;padding:1.5rem;background:#f8fafc;border-radius:8px;margin-top:1rem;border:1px solid #e2e8f0;">
                    <p style="margin-bottom:1rem;">Välj din förening och klicka på "Sök sponsorer" för att se matchande sponsorer på kartan.</p>
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#93c5fd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                </div>
                """, unsafe_allow_html=True)

    # Generate mock companies for testing
    @staticmethod
    def _generate_mock_companies(association, radius):
        """Generate mock companies around the selected association's location"""
        import random
        import numpy as np

        # Extract association location
        base_lat = float(association["lat"])
        base_lon = float(association["lon"])

        # Company names for testing
        company_names = [
            "Nordea Bank", "Volvo Group", "Ericsson AB", "IKEA Göteborg",
            "H&M Retail", "SEB Bank", "Handelsbanken", "ICA Supermarket",
            "Telia Company", "Elekta AB", "Atlas Copco", "SKF Group",
            "Sandvik AB", "Systembolaget", "Circle K", "Stadium Sports",
            "Max Burgers", "Åhléns", "Clas Ohlson", "Nordnet Bank"
        ]

        # Size buckets with same distribution as association size
        size_buckets = ["small", "medium", "large"]
        size_weights = {"small": 0.2, "medium": 0.5, "large": 0.3}

        # Generate 5-15 companies
        num_companies = random.randint(5, 15)
        companies = []

        for i in range(num_companies):
            # Generate random distance within radius (km)
            distance = random.uniform(0.5, radius)

            # Generate random direction (angle in radians)
            angle = random.uniform(0, 2 * np.pi)

            # Calculate new coordinates (rough approximation)
            # 111.32 km = 1 degree latitude
            # 111.32 * cos(latitude) km = 1 degree longitude
            lat_offset = distance / 111.32 * np.cos(angle)
            lon_offset = distance / (111.32 * np.cos(np.radians(base_lat))) * np.sin(angle)

            new_lat = base_lat + lat_offset
            new_lon = base_lon + lon_offset

            # Assign company size - match with association size for better matches
            # but include some variety
            if random.random() < 0.7:  # 70% chance to match association size
                size_bucket = association["size_bucket"]
            else:
                # Random size from distribution
                size_bucket = random.choices(size_buckets,
                                             weights=[size_weights["small"],
                                                      size_weights["medium"],
                                                      size_weights["large"]])[0]

            # Create company object
            company = {
                "id": i + 1,
                "name": company_names[i % len(company_names)],
                "description": f"Ett {size_bucket} företag inom {random.choice(['teknologi', 'finans', 'handel', 'tillverkning', 'tjänster'])}.",
                "lat": new_lat,
                "lon": new_lon,
                "distance": distance,
                "size_bucket": size_bucket,
                "score": random.randint(40, 95),
                "contact": {
                    "email": f"kontakt@{company_names[i % len(company_names)].lower().replace(' ', '')}.se",
                    "phone": f"0{random.randint(7, 8)}-{random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"
                }
            }

            companies.append(company)

        # Sort by distance
        companies.sort(key=lambda x: x["distance"])

        return companies

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