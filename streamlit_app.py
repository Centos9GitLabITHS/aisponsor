#!/usr/bin/env python3
"""Streamlit Cloud Launcher for Golden Goal AI"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
from golden_goal.ui.simple_app import *
