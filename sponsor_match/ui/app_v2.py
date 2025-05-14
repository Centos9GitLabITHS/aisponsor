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
import joblib
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict

from sponsor_match.core.config import config
from sponsor_match.core.db import get_engine
from sponsor_match.services.service_v2 import RecommendationRequest, SponsorMatchService

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class SponsorMatchUI:
    def __init__(self) -> None:
        """Initialize DB connection and preload clubs."""
        st.set_page_config(
            page_title="SponsorMatch AI",
            page_icon="⚽",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        self.engine = get_engine()
        self.clubs_df = self._load_clubs()

    def _load_clubs(self) -> pd.DataFrame:
        """Load club data from the `clubs` table."""
        sql = """
            SELECT id, name, member_count, address, lat, lon, size_bucket
            FROM clubs
            ORDER BY name
        """
        return pd.read_sql(sql, self.engine)

    @staticmethod
    def _marker_color(score: float) -> str:
        if score >= 80:
            return "green"
        if score >= 50:
            return "blue"
        return "lightgray"

    @staticmethod
    def _club_popup(club: Dict) -> str:
        return f"""
        <div>
            <h4>{club['name']}</h4>
            <p>Members: {club['member_count']}</p>
            <p>Size: {club['size_bucket']}</p>
            <p>Address: {club['address']}</p>
        </div>
        """

    @staticmethod
    def _company_popup(comp: Dict) -> str:
        return f"""
        <div>
            <h4>{comp['name']}</h4>
            <p>Score: {comp['score']}%</p>
            <p>Industry: {comp['industry']}</p>
            <p>Distance: {comp['dist_km']:.1f} km</p>
        </div>
        """

    @staticmethod
    def _make_radar(factors: Dict[str, float]) -> go.Figure:
        cats = list(factors.keys())
        vals = list(factors.values())
        theta = cats + cats[:1]
        r = vals + vals[:1]
        fig = go.Figure(go.Scatterpolar(r=r, theta=theta, fill="toself"))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
        )
        return fig

    def _run_search(
        self,
        club_name: str,
        size_bucket: str,
        industries: List[str],
        max_distance: float,
    ) -> None:
        # grab club row
        row = self.clubs_df[self.clubs_df["name"] == club_name].iloc[0]
        lat, lon = float(row["lat"]), float(row["lon"])
        club_id = int(row["id"])
        st.session_state["club_data"] = row.to_dict()

        req = RecommendationRequest(
            club_id=club_id,
            lat=lat,
            lon=lon,
            size_bucket=size_bucket,
            filters={"industries": industries, "max_distance": max_distance},
        )

        # load k-means for each bucket
        models = {}
        for b in ["small", "medium", "large"]:
            path = Path(config.models_dir) / f"kmeans_{b}.joblib"
            models[b] = joblib.load(path)

        svc = SponsorMatchService(self.engine, cluster_models=models)
        result = svc.recommend(req)
        st.session_state["results"] = result.companies.to_dict("records")

    def _render_recs(self) -> None:
        recs = st.session_state.get("results", [])
        if not recs:
            st.info("👆 Choose a club and click Search")
            return

        df = pd.DataFrame(recs)
        st.metric("Matches Found", len(df))
        st.dataframe(df[["name", "revenue_ksek", "employees", "dist_km", "industry", "score"]])

        for i, comp in enumerate(recs, 1):
            with st.expander(f"#{i} {comp['name']} — {comp['score']}%"):
                c0, c1 = st.columns([2, 1])
                c0.write(f"**Industry:** {comp['industry']}")
                c0.write(f"**Revenue:** {comp['revenue_ksek']}")
                c0.write(f"**Employees:** {comp['employees']}")
                c0.write(f"**Distance:** {comp['dist_km']:.1f} km")
                c1.plotly_chart(self._make_radar(comp["match_factors"]), use_container_width=True)

    @staticmethod
    def _render_analytics() -> None:
        recs = st.session_state.get("results", [])
        if not recs:
            st.info("No data for analytics")
            return
        df = pd.DataFrame(recs)
        st.plotly_chart(px.histogram(df, x="industry", title="Sponsors by Industry"), use_container_width=True)
        st.plotly_chart(px.scatter(df, x="dist_km", y="score", title="Score vs. Distance"), use_container_width=True)

    def _render_map(self) -> None:
        club = st.session_state["club_data"]
        recs = st.session_state.get("results", [])
        center = [club["lat"], club["lon"]]
        m = folium.Map(location=center, zoom_start=11)

        folium.Marker(
            location=center,
            popup=Popup(self._club_popup(club), max_width=300),
            icon=folium.Icon(color="red", icon="home"),
        ).add_to(m)

        if recs:
            cluster = MarkerCluster().add_to(m)
            heat = []
            for comp in recs:
                lat, lon = comp["lat"], comp["lon"]
                folium.Marker(
                    location=[lat, lon],
                    popup=Popup(self._company_popup(comp), max_width=300),
                    icon=folium.Icon(color=self._marker_color(comp["score"])),
                ).add_to(cluster)
                heat.append([lat, lon, comp["score"]])
            if heat:
                HeatMap(heat).add_to(m)

        st_folium(m, height=600, use_container_width=True)

    @staticmethod
    def _render_insights() -> None:
        recs = st.session_state.get("results", [])
        if not recs:
            st.info("No insights available")
            return
        df = pd.DataFrame(recs)
        st.metric("Average Score", f"{df['score'].mean():.1f}%")
        st.metric("Average Distance", f"{df['dist_km'].mean():.1f} km")

    def render(self) -> None:
        # **HEADER**
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(Path("assets/logo.png"), width=180)
            st.title("SponsorMatch AI")

        # **SIDEBAR**
        st.sidebar.header("🔍 Search Filters")
        clubs = ["— choose —"] + self.clubs_df["name"].tolist()
        sel = st.sidebar.selectbox("Club Name", clubs)
        bucket = (
            self.clubs_df.loc[self.clubs_df["name"] == sel, "size_bucket"].iat[0]
            if sel != "— choose —" else "medium"
        )
        size = st.sidebar.selectbox("Club Size", ["small", "medium", "large"], index=["small","medium","large"].index(bucket))
        industries: List[str] = []
        dist = st.sidebar.slider("Max distance (km)", 0, 100, 25)

        if st.sidebar.button("Search") and sel != "— choose —":
            self._run_search(sel, size, industries, dist)

        # **TABS**
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Recs","📊 Analytics","🗺️ Map","📈 Insights"])
        with tab1:
            self._render_recs()
        with tab2:
            self._render_analytics()
        with tab3:
            self._render_map()
        with tab4:
            self._render_insights()


def main() -> None:
    ui = SponsorMatchUI()
    ui.render()


if __name__ == "__main__":
    main()
