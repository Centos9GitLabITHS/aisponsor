#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sponsor_match.utils.train_clustering_models import train_all_models, test_models

if __name__ == "__main__":
    train_all_models()
    test_models()
