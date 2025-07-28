import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# ML Configuration
ML_CONFIG = {
    "feature_extraction": {
        "max_features": 5000,
        "ngram_range": (1, 3),
        "min_df": 2,
        "max_df": 0.95
    },
    "models": {
        "naive_bayes": {"alpha": 1.0},
        "random_forest": {"n_estimators": 100, "max_depth": 10},
        "gradient_boosting": {"n_estimators": 100, "learning_rate": 0.1}
    },
    "ensemble": {
        "voting": "soft",
        "weights": [1, 2, 2]  # NB, RF, GB
    }
}

# API Configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 1
}

# Classification labels
SEVERITY_LABELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]
CATEGORY_LABELS = ["APPLICATION", "SYSTEM", "SECURITY", "PERFORMANCE"] 