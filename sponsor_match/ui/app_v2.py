#!/usr/bin/env python3
"""
sponsor_match/ui/app_v2.py
---------------------------
Streamlit UI (v2) for SponsorMatch AI.

Usage:
    streamlit run sponsor_match/ui/app_v2.py
"""

import logging
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.map import Popup
from folium.plugins import MarkerCluster, HeatMap
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
import joblib
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from sponsor_match.core.config import config
from sponsor_match.core.db import get_engine
from sponsor_match.services.service_v2 import RecommendationRequest, SponsorMatchService  # :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
from typing import Optional, List, Dict

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)


class SponsorMatchUI:
    def __init__(self) -> None:
        """Initialize DB connection and preload clubs."""
        st.set_page_config(
            page_title="SponsorMatch AI",
            page_icon="⚽",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        self.engine = get_engine()
        self.clubs_df = self.load_clubs()

    def load_clubs(self) -> pd.DataFrame:
        """Load club data from the `clubs` table."""
        query = """
            SELECT id, name, member_count, address, lat, lon, size_bucket
            FROM clubs
            ORDER BY name
        """
        return pd.read_sql(query, self.engine)

    @staticmethod
    def geocode_location(address: str) -> (float, float):
        """Geocode an address in Göteborg, Sweden."""
        geocoder = RateLimiter(
            Nominatim(user_agent="sponsormatch").geocode,
            min_delay_seconds=1.1
        )
        loc = geocoder(f"{address}, Göteborg, Sweden", exactly_one=True)
        if not loc:
            raise ValueError(f"Could not geocode address: {address}")
        return loc.latitude, loc.longitude

    @staticmethod
    def get_marker_color(score: float) -> str:
        """Return Folium marker color based on match score."""
        if score >= 80:
            return "green"
        if score >= 50:
            return "blue"
        return "lightgray"

    @staticmethod
    def render_club_popup(club: Dict) -> str:
        """HTML for a club marker popup."""
        return f"""
        <div>
            <h4>{club.get('name', '')}</h4>
            <p>Members: {club.get('member_count', '')}</p>
            <p>Size: {club.get('size_bucket', '')}</p>
            <p>Address: {club.get('address', '')}</p>
        </div>
        """

    @staticmethod
    def render_company_popup(comp: Dict) -> str:
        """HTML for a company marker popup."""
        return f"""
        <div>
            <h4>{comp.get('name', '')}</h4>
            <p>Score: {comp.get('score', '')}%</p>
            <p>Industry: {comp.get('industry', '')}</p>
            <p>Distance: {comp.get('dist_km', 0):.1f} km</p>
        </div>
        """

    @staticmethod
    def create_match_radar(factors: Dict[str, float]) -> go.Figure:
        """Radar chart of match-factor scores."""
        categories = list(factors.keys())
        values = list(factors.values())
        # close the loop
        theta = categories + categories[:1]
        r = values + values[:1]

        fig = go.Figure(
            data=go.Scatterpolar(r=r, theta=theta, fill="toself")
        )
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30)
        )
        return fig

    def handle_search(
        self,
        club_name: Optional[str],
        use_current: bool,
        address: str,
        size_bucket: str,
        industries: List[str],
        max_distance: float
    ) -> None:
        """Run recommendation and stash results in session state."""
        # Determine lat/lon & club_id
        if club_name:
            row = self.clubs_df[self.clubs_df["name"] == club_name].iloc[0]
            lat, lon = float(row["lat"]), float(row["lon"])
            club_id = int(row["id"])
            st.session_state["club_data"] = row.to_dict()
        elif use_current:
            # Placeholder: implement geolocation if desired
            st.error("Current-location search not yet implemented.")
            return
        else:
            lat, lon = self.geocode_location(address)
            club_id = None
            st.session_state["club_data"] = {"lat": lat, "lon": lon}

        # Build and send request
        req = RecommendationRequest(
            club_id=club_id,
            lat=lat,
            lon=lon,
            size_bucket=size_bucket,
            filters={"industries": industries, "max_distance": max_distance}
        )
        cluster_models = {}
        for bucket in ["small", "medium", "large"]:
            model_path = Path(config.models_dir) / f"kmeans_{bucket}.joblib"
            cluster_models[bucket] = joblib.load(model_path)

        # pass them into the service
        service = SponsorMatchService(self.engine, cluster_models=cluster_models)
        # run the recommendation
        result = service.recommend(req)
        # Store results
        df = result.companies
        st.session_state["results"] = df.to_dict("records")

    def render_recommendations(self) -> None:
        """Tab 1: show list and details of matched sponsors."""
        records = st.session_state.get("results", [])
        if not records:
            st.info("👆 Use the filters and click Search to find sponsors")
            return

        df = pd.DataFrame(records)
        st.metric("Matches Found", len(df))
        st.dataframe(df[["name", "revenue_ksek", "employees", "dist_km", "industry", "score"]])

        for i, comp in enumerate(records):
            with st.expander(f"#{i+1} {comp['name']} — {comp['score']}%"):
                cols = st.columns([2, 1])
                cols[0].write(f"**Industry:** {comp['industry']}")
                cols[0].write(f"**Revenue:** {comp['revenue_ksek']}")
                cols[0].write(f"**Employees:** {comp['employees']}")
                cols[0].write(f"**Distance:** {comp['dist_km']:.1f} km")
                factors = comp.get("match_factors", {})
                cols[1].plotly_chart(self.create_match_radar(factors), use_container_width=True)

    @staticmethod
    def render_analytics() -> None:
        """Tab 2: show charts of the result set."""
        records = st.session_state.get("results", [])
        if not records:
            st.info("No data for analytics")
            return

        df = pd.DataFrame(records)
        fig1 = px.histogram(df, x="industry", title="Sponsors by Industry")
        fig2 = px.scatter(df, x="dist_km", y="score", title="Score vs. Distance")
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

    def render_map(self) -> None:
        """Tab 3: folium map with club & sponsor markers."""
        club = st.session_state.get("club_data", {})
        records = st.session_state.get("results", [])

        center = [club.get("lat", 57.7089), club.get("lon", 11.9746)]
        m = folium.Map(location=center, zoom_start=11)

        if club:
            folium.Marker(
                location=[club["lat"], club["lon"]],
                popup=Popup(self.render_club_popup(club), max_width=300),
                icon=folium.Icon(color="red", icon="home")
            ).add_to(m)

        if records:
            cluster = MarkerCluster().add_to(m)
            heat_data = []
            for comp in records:
                lat, lon = comp.get("lat"), comp.get("lon")
                if lat and lon:
                    folium.Marker(
                        location=[lat, lon],
                        popup=Popup(self.render_company_popup(comp), max_width=300),
                        icon=folium.Icon(color=self.get_marker_color(comp.get("score", 0)))
                    ).add_to(cluster)
                    heat_data.append([lat, lon, comp.get("score", 0)])
            if heat_data:
                HeatMap(heat_data).add_to(m)

        st_folium(m, use_container_width=True, height=600)

    @staticmethod
    def render_insights() -> None:
        """Tab 4: key metrics / summary of the results."""
        records = st.session_state.get("results", [])
        if not records:
            st.info("No insights available")
            return

        df = pd.DataFrame(records)
        st.metric("Average Score", f"{df['score'].mean():.1f}%")
        st.metric("Average Distance", f"{df['dist_km'].mean():.1f} km")

    def render_main_page(self) -> None:
        """Assemble header, sidebar, and all tabs."""
        # Header
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.image(Path("assets/logo.png"), width=180)
            st.title("SponsorMatch AI")

        # Sidebar filters
        st.sidebar.header("🔍 Search Filters")
        club_names = ["— choose —"] + self.clubs_df["name"].tolist()
        selected = st.sidebar.selectbox("Club Name", club_names)
        use_current = st.sidebar.checkbox("Use my location")
        address = st.sidebar.text_input("Address / Post-code")
        default_bucket = (
            self.clubs_df.loc[self.clubs_df["name"] == selected, "size_bucket"].iat[0]
            if selected != "— choose —" else "medium"
        )
        size_bucket = st.sidebar.selectbox(
            "Club Size",
            ["small", "medium", "large"],
            index=["small", "medium", "large"].index(default_bucket)
        )
        industries = st.sidebar.multiselect("Industries", [])
        max_distance = st.sidebar.slider("Max distance (km)", 0, 100, 25)

        if st.sidebar.button("Search"):
            self.handle_search(
                selected if selected != "— choose —" else None,
                use_current,
                address,
                size_bucket,
                industries,
                max_distance
            )

        # Tabs
        t1, t2, t3, t4 = st.tabs(
            ["🎯 Recommendations", "📊 Analytics", "🗺️ Map View", "📈 Insights"]
        )
        with t1:
            self.render_recommendations()
        with t2:
            self.render_analytics()
        with t3:
            self.render_map()
        with t4:
            self.render_insights()


def main() -> None:
    ui = SponsorMatchUI()
    ui.render_main_page()


if __name__ == "__main__":
    main()
