#!/usr/bin/env python3
"""
sponsor_match/ui/app_v2.py
---------------------------
Streamlit UI (v2) for SponsorMatch AI.
"""

import logging
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium import Map, Icon, Marker
from folium.map import Popup
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

from sponsor_match.core.config import config
from sponsor_match.core.db import get_engine
from sponsor_match.services.service_v2 import RecommendationRequest, SponsorMatchService

# ─── Logging ────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

# ─── UI CLASS ───────────────────────────────────────────────────────────────
class SponsorMatchUI:
    def __init__(self) -> None:
        st.set_page_config(
            page_title="SponsorMatch AI",
            page_icon="⚽",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        self.engine = get_engine()
        self.clubs_df = self._load_clubs()

    def _load_clubs(self) -> pd.DataFrame:
        query = """
            SELECT id, name, member_count, address, lat, lon, size_bucket
            FROM clubs
            ORDER BY name
        """
        return pd.read_sql(query, self.engine)

    @staticmethod
    def _marker_color(score: float) -> str:
        if score >= 80:
            return "green"
        if score >= 50:
            return "blue"
        return "lightgray"

    @staticmethod
    def _club_popup(club: dict) -> str:
        return f"""
        <div>
          <h4>{club.get('name','')}</h4>
          <p>Members: {club.get('member_count','')}</p>
          <p>Size: {club.get('size_bucket','')}</p>
          <p>Address: {club.get('address','')}</p>
        </div>
        """

    @staticmethod
    def _company_popup(comp: dict) -> str:
        return f"""
        <div>
          <h4>{comp.get('name','')}</h4>
          <p>Score: {comp.get('score',0)}%</p>
          <p>Industry: {comp.get('industry','')}</p>
          <p>Distance: {comp.get('dist_km',0):.1f} km</p>
        </div>
        """

    @staticmethod
    def _radar_chart(factors: dict) -> go.Figure:
        cats = list(factors.keys())
        vals = list(factors.values())
        theta = cats + cats[:1]
        r = vals + vals[:1]
        fig = go.Figure(
            data=go.Scatterpolar(r=r, theta=theta, fill="toself")
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
        )
        return fig

    def _run_search(self, club_name: str, size_bucket: str, industries: list[str], max_distance: float):
        # find club
        row = self.clubs_df[self.clubs_df["name"] == club_name].iloc[0]
        lat, lon = float(row["lat"]), float(row["lon"])
        club_id = int(row["id"])
        st.session_state["club_data"] = row.to_dict()

        # prepare request
        req = RecommendationRequest(
            club_id=club_id,
            lat=lat,
            lon=lon,
            size_bucket=size_bucket,
            filters={"industries": industries, "max_distance": max_distance},
        )

        # load whatever KMeans models exist
        cluster_models: dict[str, joblib.Memory] = {}
        for b in ("small", "medium", "large"):
            path = Path(config.models_dir) / f"kmeans_{b}.joblib"
            if path.exists():
                cluster_models[b] = joblib.load(path)
            else:
                logger.warning("No model file for bucket %s → skipping", b)

        service = SponsorMatchService(self.engine, cluster_models=cluster_models)
        res = service.recommend(req)
        st.session_state["results"] = res.companies.to_dict("records")

    def _render_recommendations(self):
        recs = st.session_state.get("results", [])
        if not recs:
            st.info("👆 Select filters and click **Search** to find sponsors")
            return

        df = pd.DataFrame(recs)
        st.metric("Matches Found", len(df))
        st.dataframe(df[["name","revenue_ksek","employees","dist_km","industry","score"]])

        for i, comp in enumerate(recs):
            with st.expander(f"#{i+1} {comp['name']} — {comp['score']}%"):
                c0, c1 = st.columns([2,1])
                c0.markdown(f"**Industry:** {comp['industry']}")
                c0.markdown(f"**Revenue:** {comp['revenue_ksek']}")
                c0.markdown(f"**Employees:** {comp['employees']}")
                c0.markdown(f"**Distance:** {comp['dist_km']:.1f} km")
                c1.plotly_chart(self._radar_chart(comp.get("match_factors", {})), use_container_width=True)

    @staticmethod
    def _render_analytics():
        recs = st.session_state.get("results", [])
        if not recs:
            st.info("No data for analytics")
            return
        df = pd.DataFrame(recs)
        st.plotly_chart(px.histogram(df, x="industry", title="Sponsors by Industry"), use_container_width=True)
        st.plotly_chart(px.scatter(df, x="dist_km", y="score", title="Score vs. Distance"), use_container_width=True)

    def _render_map(self):
        club = st.session_state.get("club_data", {"lat":57.7089,"lon":11.9746})
        recs = st.session_state.get("results", [])

        center = [club.get("lat",57.7089), club.get("lon",11.9746)]
        m = Map(location=center, zoom_start=11)

        # club marker
        if "id" in club:
            Marker(
                location=[club["lat"], club["lon"]],
                popup=Popup(self._club_popup(club), max_width=300),
                icon=Icon(color="red", icon="home"),
            ).add_to(m)

        # sponsors
        if recs:
            cluster = MarkerCluster().add_to(m)
            heat = []
            for comp in recs:
                lat = comp.get("lat")
                lon = comp.get("lon")
                if lat and lon:
                    Marker(
                        location=[lat, lon],
                        popup=Popup(self._company_popup(comp), max_width=300),
                        icon=Icon(color=self._marker_color(comp.get("score",0))),
                    ).add_to(cluster)
                    heat.append([lat, lon, comp.get("score",0)])
            if heat:
                HeatMap(heat).add_to(m)

        st_folium(m, use_container_width=True, height=600)

    @staticmethod
    def _render_insights():
        recs = st.session_state.get("results", [])
        if not recs:
            st.info("No insights available")
            return
        df = pd.DataFrame(recs)
        st.metric("Average Score", f"{df['score'].mean():.1f}%")
        st.metric("Average Distance", f"{df['dist_km'].mean():.1f} km")

    def render_main_page(self):
        # Header
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.image(Path("assets/logo.png"), width=180)
            st.title("SponsorMatch AI")

        # Sidebar
        st.sidebar.header("🔍 Search Filters")
        clubs = ["— choose —"] + self.clubs_df["name"].tolist()
        choice = st.sidebar.selectbox("Club Name", clubs)
        default_bucket = (
            self.clubs_df.loc[self.clubs_df["name"]==choice, "size_bucket"].iat[0]
            if choice!="— choose —" else "medium"
        )
        bucket = st.sidebar.selectbox("Club Size", ["small","medium","large"], index=["small","medium","large"].index(default_bucket))
        industries = st.sidebar.multiselect("Industries", [])  # you can wire this up later
        max_dist = st.sidebar.slider("Max distance (km)", 0, 100, 25)

        if st.sidebar.button("Search") and choice!="— choose —":
            self._run_search(choice, bucket, industries, max_dist)

        # Tabs
        t1, t2, t3, t4 = st.tabs(["🎯 Recommendations","📊 Analytics","🗺️ Map View","📈 Insights"])
        with t1: self._render_recommendations()
        with t2: self._render_analytics()
        with t3: self._render_map()
        with t4: self._render_insights()

# ─── ENTRYPOINT ───────────────────────────────────────────────────────────────
def main():
    SponsorMatchUI().render_main_page()

if __name__ == "__main__":
    main()
