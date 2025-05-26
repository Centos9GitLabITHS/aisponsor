#!/usr/bin/env python3
"""Launcher for Streamlit Cloud - DO NOT MODIFY"""
import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the actual app
from golden_goal.ui.simple_app import *
