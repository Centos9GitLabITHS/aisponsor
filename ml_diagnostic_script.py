#!/usr/bin/env python3
"""
diagnose_ml.py - Diagnostic script to check ML models and scoring
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from golden_goal.ml.pipeline import load_models, score_and_rank_optimized
from golden_goal.core.db import get_engine
from sqlalchemy import text


def check_ml_models():
    """Check if ML models are loading correctly."""
    print("="*60)
    print("ML MODEL DIAGNOSTIC")
    print("="*60)
    
    # Check model files
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "golden_goal" / "models"
    
    print(f"\n1. Checking models directory: {models_dir}")
    if models_dir.exists():
        print("   ✓ Models directory exists")
        model_files = list(models_dir.glob("*.joblib"))
        print(f"   Found {len(model_files)} model files:")
        for f in model_files:
            print(f"     - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    else:
        print("   ✗ Models directory NOT FOUND!")
        print("   Run: python utils/train_clustering_models.py")
        return False
    
    # Try loading models
    print("\n2. Testing model loading...")
    models = load_models()
    if models:
        print(f"   ✓ Loaded {len(models)} models: {list(models.keys())}")
        for key, model in models.items():
            if isinstance(model, dict):
                print(f"     - {key}: dict with keys {list(model.keys())}")
            else:
                print(f"     - {key}: {type(model).__name__}")
    else:
        print("   ✗ No models loaded!")
        return False
    
    return True

def test_scoring():
    """Test the scoring function with a sample association."""
    print("\n3. Testing scoring function...")
    
    engine = get_engine()
    with engine.connect() as conn:
        # Get a sample association
        result = conn.execute(text("""
            SELECT id, name, lat, lon, size_bucket 
            FROM associations 
            WHERE lat IS NOT NULL AND lon IS NOT NULL 
            LIMIT 1
        """)).fetchone()
        
        if not result:
            print("   ✗ No associations found in database!")
            return
        
        assoc_id, assoc_name, lat, lon, size_bucket = result
        print(f"   Testing with: {assoc_name} (ID: {assoc_id})")
        
        # Get recommendations
        recommendations = score_and_rank_optimized(
            association_id=assoc_id,
            bucket=size_bucket,
            max_distance=25,
            top_n=10
        )
        
        if recommendations:
            print(f"   ✓ Got {len(recommendations)} recommendations")
            
            # Check score distribution
            scores = [r['score'] for r in recommendations]
            unique_scores = len(set(scores))
            
            print(f"\n   Score Analysis:")
            print(f"   - Unique scores: {unique_scores}")
            print(f"   - Min score: {min(scores):.4f}")
            print(f"   - Max score: {max(scores):.4f}")
            print(f"   - Avg score: {sum(scores)/len(scores):.4f}")
            
            if unique_scores == 1:
                print("   ✗ WARNING: All scores are identical!")
                print("     This indicates scoring is not working properly.")
                
                # Show detailed breakdown
                if recommendations:
                    print("\n   Sample recommendation details:")
                    rec = recommendations[0]
                    for key, value in rec.items():
                        print(f"     - {key}: {value}")
            else:
                print("   ✓ Scores are properly distributed")
                
                # Show score distribution
                print("\n   Top 5 recommendations:")
                for i, rec in enumerate(recommendations[:5]):
                    print(f"     {i+1}. {rec['name']}: {rec['score']:.4f} "
                          f"(distance: {rec.get('distance', 'N/A')}km)")
        else:
            print("   ✗ No recommendations returned!")

def check_scoring_components():
    """Test individual scoring components."""
    print("\n4. Testing scoring components...")
    
    from golden_goal.ml.pipeline import (
        calculate_distance_score,
        calculate_size_match_score
    )
    
    # Test distance scoring
    print("\n   Distance scoring (max_distance=25km):")
    for dist in [0, 5, 10, 15, 20, 25, 30]:
        score = calculate_distance_score(dist, 25)
        print(f"     {dist}km -> {score:.3f}")
    
    # Test size matching
    print("\n   Size match scoring:")
    sizes = ['small', 'medium', 'large']
    for s1 in sizes:
        for s2 in sizes:
            score = calculate_size_match_score(s1, s2)
            print(f"     {s1} <-> {s2}: {score:.1f}")

def check_database_indexes():
    """Check if spatial indexes exist."""
    print("\n5. Checking database indexes...")
    
    engine = get_engine()
    with engine.connect() as conn:
        # Check indexes
        for table in ['associations', 'companies']:
            print(f"\n   Indexes on {table}:")
            try:
                indexes = conn.execute(text(f"SHOW INDEXES FROM {table}")).fetchall()
                for idx in indexes:
                    print(f"     - {idx[2]} on {idx[4]}")
            except Exception as e:
                print(f"     ✗ Error: {e}")

if __name__ == "__main__":
    # Run all diagnostics
    models_ok = check_ml_models()
    
    if models_ok:
        test_scoring()
        check_scoring_components()
    else:
        print("\n✗ Fix model loading issues before testing scoring!")
    
    check_database_indexes()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)