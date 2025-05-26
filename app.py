#!/usr/bin/env python3
"""Golden Goal AI - Streamlit App"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the app
from golden_goal.ui.simple_app import *
