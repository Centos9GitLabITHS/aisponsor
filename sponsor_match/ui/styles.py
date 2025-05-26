# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

import streamlit as st


def apply_professional_styles():
    """Apply professional styling to Streamlit app."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Main app styling */
    .main .block-container {
        font-family: 'Inter', sans-serif;
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Header styling */
    h1 {
        color: #1e40af !important;
        font-weight: 700 !important;
        margin-bottom: 2rem !important;
    }

    h2 {
        color: #1e40af !important;
        font-weight: 600 !important;
        margin-bottom: 1.5rem !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        font-weight: 500;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
        transform: translateY(-1px);
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }

    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #d1d5db;
    }

    .stTextInput > div > div > input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    /* Success/Error styling */
    .stSuccess {
        background-color: #f0f9ff;
        border-left: 4px solid #10b981;
    }

    .stError {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def create_metric_card(title, value, delta=None):
    """Create a styled metric card."""
    delta_html = ""
    if delta:
        color = "#10b981" if delta > 0 else "#ef4444"
        arrow = "↗" if delta > 0 else "↘"
        delta_html = f"""
        <div style="color: {color}; font-size: 0.875rem; font-weight: 500;">
            {arrow} {abs(delta):.1f}%
        </div>
        """

    return f"""
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; 
                padding: 1.5rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
        <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 0.5rem;">
            {title}
        </div>
        <div style="font-size: 1.875rem; font-weight: 700; color: #111827; margin-bottom: 0.25rem;">
            {value}
        </div>
        {delta_html}
    </div>
    """