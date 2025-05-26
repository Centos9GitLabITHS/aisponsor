# Minimal Streamlit app demonstrating core functionality without backend
# Detailed comments have been inserted in British English.

#!/usr/bin/env python3
"""
minimal_app.py - Minimal working SponsorMatch AI
No database, no ML models, just the core UI and logic
"""

# Standard library or third-party import
import math

# Standard library or third-party import
import pandas as pd
# Standard library or third-party import
import streamlit as st

# Page config
st.set_page_config(
    page_title="SponsorMatch AI",
    page_icon="⚽",
    layout="wide"
)

# Mock data - Swedish associations and companies
MOCK_ASSOCIATIONS = [
    {"id": 1, "name": "IFK Göteborg", "lat": 57.7089, "lon": 11.9746, "size": "large", "members": 1500},
    {"id": 2, "name": "GAIS", "lat": 57.6969, "lon": 11.9789, "size": "large", "members": 1200},
    {"id": 3, "name": "BK Häcken", "lat": 57.7209, "lon": 11.9390, "size": "large", "members": 1000},
    {"id": 4, "name": "Qviding FIF", "lat": 57.7162, "lon": 12.0172, "size": "medium", "members": 400},
    {"id": 5, "name": "Majorna BK", "lat": 57.6890, "lon": 11.9145, "size": "small", "members": 120},
]

MOCK_COMPANIES = [
    {"name": "Volvo AB", "lat": 57.7065, "lon": 11.9373, "size": "large", "industry": "Automotive"},
    {"name": "Ericsson", "lat": 57.6858, "lon": 11.9668, "size": "large", "industry": "Technology"},
    {"name": "ICA Maxi", "lat": 57.7523, "lon": 11.9389, "size": "medium", "industry": "Retail"},
    {"name": "Nordea Bank", "lat": 57.7000, "lon": 11.9500, "size": "large", "industry": "Finance"},
    {"name": "Local Bakery AB", "lat": 57.7100, "lon": 11.9600, "size": "small", "industry": "Food"},
]


# Definition of function 'haversine_distance': explains purpose and parameters
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


# Definition of function 'calculate_match_score': explains purpose and parameters
def calculate_match_score(assoc, company, distance):
    """Calculate match score based on size and distance"""
    # Size compatibility
    size_score = 1.0 if assoc['size'] == company['size'] else 0.5

    # Distance score (closer is better)
    distance_score = max(0, 1 - (distance / 50))  # 50km max

    # Combined score
    return (size_score * 0.4 + distance_score * 0.6) * 100


# Definition of function 'main': explains purpose and parameters
def main():
    st.title("🏆 SponsorMatch AI - Quick Demo")
    st.markdown("*Find perfect sponsors for your sports club*")

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        max_distance = st.slider("Max Distance (km)", 5, 50, 25)
        st.markdown("---")
        st.info("This is a demo version running without database connection")

    # Main content
    tab1, tab2 = st.tabs(["🔍 Find Sponsors", "📊 Analytics"])

    with tab1:
        st.header("Find Sponsors for Your Club")

        # Select association
        assoc_names = [a['name'] for a in MOCK_ASSOCIATIONS]
        selected_name = st.selectbox("Select your club:", assoc_names)

        # Get selected association
        selected_assoc = next(a for a in MOCK_ASSOCIATIONS if a['name'] == selected_name)

        # Display club info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Club", selected_assoc['name'])
        with col2:
            st.metric("Size", selected_assoc['size'].capitalize())
        with col3:
            st.metric("Members", selected_assoc['members'])

        # Find sponsors button
        if st.button("🎯 Find Matching Sponsors", type="primary"):
            st.markdown("### Recommended Sponsors")

            # Calculate matches
            matches = []
            for company in MOCK_COMPANIES:
                distance = haversine_distance(
                    selected_assoc['lat'], selected_assoc['lon'],
                    company['lat'], company['lon']
                )

                if distance <= max_distance:
                    score = calculate_match_score(selected_assoc, company, distance)
                    matches.append({
                        'Company': company['name'],
                        'Industry': company['industry'],
                        'Distance (km)': round(distance, 1),
                        'Match Score': f"{score:.0f}%",
                        'Size': company['size'].capitalize()
                    })

            # Sort by score
            matches.sort(key=lambda x: float(x['Match Score'].rstrip('%')), reverse=True)

            # Display results
            if matches:
                df = pd.DataFrame(matches)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Success message
                st.success(f"Found {len(matches)} potential sponsors within {max_distance}km!")
            else:
                st.warning("No sponsors found within the specified distance.")

    with tab2:
        st.header("Analytics Dashboard")

        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Clubs", len(MOCK_ASSOCIATIONS))
        with col2:
            st.metric("Total Companies", len(MOCK_COMPANIES))
        with col3:
            st.metric("Avg Match Rate", "73%")
        with col4:
            st.metric("Success Rate", "45%")

        # Distribution charts
        st.subheader("Club Size Distribution")
        size_dist = pd.DataFrame({
            'Size': ['Small', 'Medium', 'Large'],
            'Count': [2, 1, 2]
        })
        st.bar_chart(size_dist.set_index('Size'))

        # Info
        st.info("""
        **How it works:**
        1. Select your sports club
        2. Set maximum search distance
        3. Get AI-matched sponsor recommendations
        4. Contact sponsors with highest match scores
        """)


# Entry point check: script execution starts here when run directly
if __name__ == "__main__":
    main()