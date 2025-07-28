#!/usr/bin/env python3

import pandas as pd
import ast
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from src.feature_extraction.extractor import LogFeatureExtractor
from config.config import ML_CONFIG

def test_data_loading():
    print("Testing data loading...")
    
    # Load training data
    training_data = pd.read_csv("data/training/sample_logs.csv")
    print(f"Loaded {len(training_data)} rows")
    print(f"Columns: {list(training_data.columns)}")
    
    # Check metadata column
    print(f"\nSample metadata: {training_data['metadata'].iloc[0]}")
    print(f"Metadata type: {type(training_data['metadata'].iloc[0])}")
    
    # Convert metadata from string to dict
    print("\nConverting metadata...")
    training_data['metadata'] = training_data['metadata'].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('{') else {}
    )
    
    print(f"After conversion: {training_data['metadata'].iloc[0]}")
    print(f"Type after conversion: {type(training_data['metadata'].iloc[0])}")
    
    # Test feature extraction
    print("\nTesting feature extraction...")
    extractor = LogFeatureExtractor(ML_CONFIG["feature_extraction"])
    
    try:
        X = extractor.fit_transform(training_data)
        print(f"Feature extraction successful! Shape: {X.shape}")
        return True
    except Exception as e:
        print(f"Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_loading()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!") 