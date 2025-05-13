import streamlit as st
from sponsor_match.recommend import recommend

st.set_page_config(page_title="SponsorMatch AI", layout="wide")
st.title("Find Your Ideal Sponsors")

assoc_id = st.number_input("Association ID", value=1, step=1)
if st.button("Find Sponsors"):
    df = recommend(assoc_id)
    st.dataframe(df[["name", "distance_km", "score", "rank"]])
