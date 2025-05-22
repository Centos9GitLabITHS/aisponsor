#!/usr/bin/env python3
# streamlit_app.py
"""
Entry point for the SponsorMatch AI Streamlit application.
Installs the .env variables, then hands off to the UI module.
"""

from dotenv import load_dotenv
load_dotenv()  # make sure .env is loaded before anything else

from sponsor_match.ui.app import main

if __name__ == "__main__":
    main()
