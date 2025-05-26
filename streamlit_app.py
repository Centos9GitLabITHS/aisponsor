# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

#!/usr/bin/env python3
"""
streamlit_app.py
Main entry point for the SponsorMatch AI application.
Fixed to work with ML models and 82,776 companies.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import and run the main app
from sponsor_match.ui.simple_app import main

if __name__ == "__main__":
    main()
