#!/bin/bash

# Day 78: Machine Learning Pipeline for Log Classification
# Implementation Script for Distributed Log Processing System

set -e  # Exit on any error

echo "🚀 Day 78: Building ML Pipeline for Log Classification"
echo "=================================================="

# Create project structure
echo "📁 Creating project structure..."
mkdir -p ml-log-classifier/{src,tests,data,models,frontend,docker,config}
cd ml-log-classifier

mkdir -p src/{ml_pipeline,feature_extraction,models,api,utils}
mkdir -p tests/{unit,integration,performance}
mkdir -p data/{training,validation,sample_logs}
mkdir -p frontend/{src,public,components}
mkdir -p docker/{ml_service,frontend}

echo "✅ Project structure created"

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

echo "📦 Installing Python dependencies..."
cat > requirements.txt << 'EOF'
# Core ML libraries
scikit-learn==1.4.2
numpy==1.26.4
pandas==2.2.2
joblib==1.4.2

# Text processing
nltk==3.8.1
regex==2024.5.15

# Web framework
fastapi==0.111.0
uvicorn==0.30.1
websockets==12.0

# Database
sqlite3-utils==3.36.0

# Testing
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0

# Utilities
python-dotenv==1.0.1
pydantic==2.7.1
aiofiles==23.2.1
structlog==24.1.0
colorama==0.4.6
EOF

pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

echo "✅ Dependencies installed"

# Create configuration
echo "⚙️ Creating configuration files..."
cat > config/config.py << 'EOF'
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
EOF

echo "✅ Configuration created"

# Create ML Pipeline Core
echo "🧠 Creating ML pipeline components..."

# Feature Extraction Engine
cat > src/feature_extraction/extractor.py << 'EOF'
import re
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import logging

logger = logging.getLogger(__name__)

class LogFeatureExtractor:
    def __init__(self, config):
        self.config = config
        self.vectorizer = TfidfVectorizer(
            max_features=config["max_features"],
            ngram_range=config["ngram_range"],
            min_df=config["min_df"],
            max_df=config["max_df"],
            stop_words='english'
        )
        self.label_encoders = {}
        self.is_fitted = False
        
    def preprocess_text(self, text):
        """Clean and preprocess log text"""
        if not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove timestamps, IPs, and common log patterns
        text = re.sub(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', '', text)
        text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '', text)
        text = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '', text)
        
        # Remove special characters except spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
        
    def extract_temporal_features(self, timestamps):
        """Extract time-based features"""
        features = []
        for ts in timestamps:
            try:
                dt = pd.to_datetime(ts)
                features.append([
                    dt.hour,
                    dt.dayofweek,
                    dt.minute // 15,  # 15-minute buckets
                    1 if 9 <= dt.hour <= 17 else 0,  # business hours
                ])
            except:
                features.append([0, 0, 0, 0])
                
        return np.array(features)
        
    def extract_metadata_features(self, metadata_list):
        """Extract features from log metadata"""
        features = []
        for meta in metadata_list:
            # Extract service, component, etc.
            service_len = len(meta.get('service', ''))
            component_len = len(meta.get('component', ''))
            
            features.append([
                service_len,
                component_len,
                len(str(meta.get('request_id', ''))),
                1 if meta.get('user_id') else 0
            ])
            
        return np.array(features)
        
    def fit_transform(self, logs_df):
        """Fit feature extractors and transform data"""
        logger.info("Fitting feature extractors...")
        
        # Preprocess text
        preprocessed_text = [self.preprocess_text(text) for text in logs_df['message']]
        
        # Fit and transform text features
        text_features = self.vectorizer.fit_transform(preprocessed_text)
        
        # Extract temporal features
        temporal_features = self.extract_temporal_features(logs_df['timestamp'])
        
        # Extract metadata features
        metadata_features = self.extract_metadata_features(logs_df['metadata'])
        
        # Combine all features
        combined_features = np.hstack([
            text_features.toarray(),
            temporal_features,
            metadata_features
        ])
        
        self.is_fitted = True
        logger.info(f"Feature extraction complete. Shape: {combined_features.shape}")
        
        return combined_features
        
    def transform(self, logs_df):
        """Transform new data using fitted extractors"""
        if not self.is_fitted:
            raise ValueError("Feature extractor must be fitted first")
            
        # Preprocess text
        preprocessed_text = [self.preprocess_text(text) for text in logs_df['message']]
        
        # Transform text features
        text_features = self.vectorizer.transform(preprocessed_text)
        
        # Extract other features
        temporal_features = self.extract_temporal_features(logs_df['timestamp'])
        metadata_features = self.extract_metadata_features(logs_df['metadata'])
        
        # Combine features
        combined_features = np.hstack([
            text_features.toarray(),
            temporal_features,
            metadata_features
        ])
        
        return combined_features
EOF

# ML Models Module
cat > src/ml_pipeline/classifier.py << 'EOF'
import numpy as np
import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LogClassifier:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.ensemble_model = None
        self.is_trained = False
        
        # Initialize individual models
        self.models['naive_bayes'] = MultinomialNB(**config["models"]["naive_bayes"])
        self.models['random_forest'] = RandomForestClassifier(**config["models"]["random_forest"], random_state=42)
        self.models['gradient_boosting'] = GradientBoostingClassifier(**config["models"]["gradient_boosting"], random_state=42)
        
    def train(self, X, y_severity, y_category):
        """Train ensemble classifier for both severity and category"""
        logger.info("Training ML models...")
        
        # Split data
        X_train, X_test, y_sev_train, y_sev_test, y_cat_train, y_cat_test = train_test_split(
            X, y_severity, y_category, test_size=0.2, random_state=42, stratify=y_severity
        )
        
        # Train severity classifier
        estimators_severity = [
            ('nb', self.models['naive_bayes']),
            ('rf', self.models['random_forest']),
            ('gb', self.models['gradient_boosting'])
        ]
        
        self.severity_classifier = VotingClassifier(
            estimators=estimators_severity,
            voting=self.config["ensemble"]["voting"],
            weights=self.config["ensemble"]["weights"]
        )
        
        self.severity_classifier.fit(X_train, y_sev_train)
        
        # Train category classifier
        estimators_category = [
            ('nb', MultinomialNB(**self.config["models"]["naive_bayes"])),
            ('rf', RandomForestClassifier(**self.config["models"]["random_forest"], random_state=42)),
            ('gb', GradientBoostingClassifier(**self.config["models"]["gradient_boosting"], random_state=42))
        ]
        
        self.category_classifier = VotingClassifier(
            estimators=estimators_category,
            voting=self.config["ensemble"]["voting"],
            weights=self.config["ensemble"]["weights"]
        )
        
        self.category_classifier.fit(X_train, y_cat_train)
        
        # Evaluate models
        sev_score = self.severity_classifier.score(X_test, y_sev_test)
        cat_score = self.category_classifier.score(X_test, y_cat_test)
        
        logger.info(f"Severity classification accuracy: {sev_score:.3f}")
        logger.info(f"Category classification accuracy: {cat_score:.3f}")
        
        # Detailed evaluation
        sev_pred = self.severity_classifier.predict(X_test)
        cat_pred = self.category_classifier.predict(X_test)
        
        logger.info("Severity Classification Report:")
        logger.info(f"\n{classification_report(y_sev_test, sev_pred)}")
        
        logger.info("Category Classification Report:")
        logger.info(f"\n{classification_report(y_cat_test, cat_pred)}")
        
        self.is_trained = True
        
        return {
            'severity_accuracy': sev_score,
            'category_accuracy': cat_score,
            'severity_report': classification_report(y_sev_test, sev_pred, output_dict=True),
            'category_report': classification_report(y_cat_test, cat_pred, output_dict=True)
        }
        
    def predict(self, X):
        """Predict severity and category for new logs"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")
            
        severity_pred = self.severity_classifier.predict(X)
        category_pred = self.category_classifier.predict(X)
        
        # Get prediction probabilities for confidence scores
        severity_proba = self.severity_classifier.predict_proba(X)
        category_proba = self.category_classifier.predict_proba(X)
        
        return {
            'severity': severity_pred,
            'category': category_pred,
            'severity_confidence': severity_proba.max(axis=1),
            'category_confidence': category_proba.max(axis=1)
        }
        
    def save_models(self, models_dir):
        """Save trained models to disk"""
        models_dir = Path(models_dir)
        models_dir.mkdir(exist_ok=True)
        
        if self.is_trained:
            joblib.dump(self.severity_classifier, models_dir / 'severity_classifier.pkl')
            joblib.dump(self.category_classifier, models_dir / 'category_classifier.pkl')
            logger.info(f"Models saved to {models_dir}")
        else:
            logger.warning("No trained models to save")
            
    def load_models(self, models_dir):
        """Load trained models from disk"""
        models_dir = Path(models_dir)
        
        try:
            self.severity_classifier = joblib.load(models_dir / 'severity_classifier.pkl')
            self.category_classifier = joblib.load(models_dir / 'category_classifier.pkl')
            self.is_trained = True
            logger.info(f"Models loaded from {models_dir}")
        except FileNotFoundError:
            logger.warning(f"No saved models found in {models_dir}")
EOF

# API Service
cat > src/api/main.py << 'EOF'
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import uvicorn

from src.feature_extraction.extractor import LogFeatureExtractor
from src.ml_pipeline.classifier import LogClassifier
from config.config import ML_CONFIG, API_CONFIG, SEVERITY_LABELS, CATEGORY_LABELS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Log Classifier API", version="1.0.0")

# Global state
feature_extractor = None
classifier = None
classification_stats = {
    "total_classified": 0,
    "severity_distribution": {label: 0 for label in SEVERITY_LABELS},
    "category_distribution": {label: 0 for label in CATEGORY_LABELS},
    "accuracy_history": []
}
connected_clients = []

@app.on_event("startup")
async def startup_event():
    global feature_extractor, classifier
    
    logger.info("Starting ML Log Classifier API...")
    
    # Initialize components
    feature_extractor = LogFeatureExtractor(ML_CONFIG["feature_extraction"])
    classifier = LogClassifier(ML_CONFIG)
    
    # Try to load existing models
    models_dir = Path("models")
    if models_dir.exists():
        classifier.load_models(models_dir)
        
        # Load feature extractor state if available
        try:
            import joblib
            feature_extractor.vectorizer = joblib.load(models_dir / 'feature_extractor.pkl')
            feature_extractor.is_fitted = True
            logger.info("Loaded existing feature extractor")
        except:
            logger.info("No existing feature extractor found")
    
    logger.info("API startup complete")

@app.post("/train")
async def train_model():
    """Train the ML model with sample data"""
    global feature_extractor, classifier
    
    try:
        # Load training data
        training_data = pd.read_csv("data/training/sample_logs.csv")
        
        # Extract features
        if not feature_extractor.is_fitted:
            X = feature_extractor.fit_transform(training_data)
        else:
            X = feature_extractor.transform(training_data)
        
        # Train classifier
        results = classifier.train(
            X, 
            training_data['severity'], 
            training_data['category']
        )
        
        # Save models
        models_dir = Path("models")
        classifier.save_models(models_dir)
        
        # Save feature extractor
        import joblib
        joblib.dump(feature_extractor.vectorizer, models_dir / 'feature_extractor.pkl')
        
        return {
            "status": "success",
            "message": "Model trained successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify")
async def classify_log(log_data: dict):
    """Classify a single log entry"""
    global feature_extractor, classifier, classification_stats
    
    try:
        if not classifier.is_trained:
            raise HTTPException(status_code=400, detail="Model not trained yet")
        
        # Convert to DataFrame format
        log_df = pd.DataFrame([{
            'message': log_data.get('message', ''),
            'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
            'metadata': log_data.get('metadata', {})
        }])
        
        # Extract features
        X = feature_extractor.transform(log_df)
        
        # Make prediction
        predictions = classifier.predict(X)
        
        result = {
            "severity": predictions['severity'][0],
            "category": predictions['category'][0],
            "severity_confidence": float(predictions['severity_confidence'][0]),
            "category_confidence": float(predictions['category_confidence'][0]),
            "timestamp": datetime.now().isoformat()
        }
        
        # Update stats
        classification_stats["total_classified"] += 1
        classification_stats["severity_distribution"][result["severity"]] += 1
        classification_stats["category_distribution"][result["category"]] += 1
        
        # Notify connected clients
        await notify_clients(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get classification statistics"""
    return classification_stats

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def notify_clients(data):
    """Notify all connected clients of new classification"""
    if connected_clients:
        message = json.dumps(data)
        disconnected = []
        
        for client in connected_clients:
            try:
                await client.send_text(message)
            except:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            connected_clients.remove(client)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ML Log Classifier Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .stat-item { text-align: center; padding: 15px; }
            .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
            .log-form { margin: 20px 0; }
            .log-form input, .log-form textarea { width: 100%; padding: 10px; margin: 5px 0; }
            .log-form button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            .results { margin: 20px 0; padding: 15px; background: #e8f5e8; border-radius: 4px; }
            .real-time { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 ML Log Classifier Dashboard</h1>
            
            <div class="card">
                <h2>📊 Classification Statistics</h2>
                <div class="stats-grid" id="stats">
                    <div class="stat-item">
                        <div class="stat-value" id="total-classified">0</div>
                        <div>Total Classified</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="model-status">Not Trained</div>
                        <div>Model Status</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🚀 Train Model</h2>
                <button onclick="trainModel()">Train ML Model</button>
                <div id="training-result"></div>
            </div>
            
            <div class="card">
                <h2>🧪 Test Classification</h2>
                <div class="log-form">
                    <textarea id="log-message" placeholder="Enter log message..." rows="3"></textarea>
                    <button onclick="classifyLog()">Classify Log</button>
                </div>
                <div id="classification-result"></div>
            </div>
            
            <div class="card">
                <h2>📈 Real-time Classifications</h2>
                <div class="real-time" id="real-time-logs"></div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addRealTimeLog(data);
            };
            
            function addRealTimeLog(data) {
                const container = document.getElementById('real-time-logs');
                const logDiv = document.createElement('div');
                logDiv.innerHTML = `
                    <strong>[${data.timestamp}]</strong> 
                    Severity: <span style="color: ${getSeverityColor(data.severity)}">${data.severity}</span> | 
                    Category: ${data.category} | 
                    Confidence: ${(data.severity_confidence * 100).toFixed(1)}%
                `;
                container.appendChild(logDiv);
                container.scrollTop = container.scrollHeight;
            }
            
            function getSeverityColor(severity) {
                const colors = {
                    'INFO': 'green',
                    'WARNING': 'orange', 
                    'ERROR': 'red',
                    'CRITICAL': 'darkred'
                };
                return colors[severity] || 'black';
            }
            
            async function trainModel() {
                const button = event.target;
                button.disabled = true;
                button.textContent = 'Training...';
                
                try {
                    const response = await fetch('/train', { method: 'POST' });
                    const result = await response.json();
                    
                    document.getElementById('training-result').innerHTML = `
                        <div class="results">
                            <strong>Training Complete!</strong><br>
                            Severity Accuracy: ${(result.results.severity_accuracy * 100).toFixed(2)}%<br>
                            Category Accuracy: ${(result.results.category_accuracy * 100).toFixed(2)}%
                        </div>
                    `;
                    
                    document.getElementById('model-status').textContent = 'Trained';
                    
                } catch (error) {
                    document.getElementById('training-result').innerHTML = `
                        <div style="color: red;">Training failed: ${error.message}</div>
                    `;
                } finally {
                    button.disabled = false;
                    button.textContent = 'Train ML Model';
                }
            }
            
            async function classifyLog() {
                const message = document.getElementById('log-message').value;
                if (!message.trim()) {
                    alert('Please enter a log message');
                    return;
                }
                
                try {
                    const response = await fetch('/classify', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message: message,
                            timestamp: new Date().toISOString(),
                            metadata: {}
                        })
                    });
                    
                    const result = await response.json();
                    
                    document.getElementById('classification-result').innerHTML = `
                        <div class="results">
                            <strong>Classification Result:</strong><br>
                            Severity: <span style="color: ${getSeverityColor(result.severity)}"><strong>${result.severity}</strong></span><br>
                            Category: <strong>${result.category}</strong><br>
                            Confidence: ${(result.severity_confidence * 100).toFixed(1)}%
                        </div>
                    `;
                    
                } catch (error) {
                    document.getElementById('classification-result').innerHTML = `
                        <div style="color: red;">Classification failed: ${error.message}</div>
                    `;
                }
            }
            
            async function updateStats() {
                try {
                    const response = await fetch('/stats');
                    const stats = await response.json();
                    document.getElementById('total-classified').textContent = stats.total_classified;
                } catch (error) {
                    console.error('Failed to update stats:', error);
                }
            }
            
            // Update stats every 5 seconds
            setInterval(updateStats, 5000);
            updateStats();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host=API_CONFIG["host"], port=API_CONFIG["port"])
EOF

# Create sample training data
echo "📊 Creating sample training data..."
cat > src/utils/data_generator.py << 'EOF'
import pandas as pd
import random
from datetime import datetime, timedelta
import json

def generate_sample_logs(num_logs=1000):
    """Generate sample log data for training"""
    
    # Sample log templates with patterns
    log_templates = {
        'INFO': [
            "User {} logged in successfully",
            "Request processed for endpoint {} in {}ms",
            "Cache hit for key {}",
            "Database connection established",
            "Service {} started successfully"
        ],
        'WARNING': [
            "High memory usage detected: {}%",
            "Slow query detected: {}ms",
            "Connection pool size approaching limit",
            "Deprecated API endpoint {} accessed",
            "Retry attempt {} for operation {}"
        ],
        'ERROR': [
            "Failed to connect to database: {}",
            "Authentication failed for user {}",
            "Invalid request format: {}",
            "Service {} is unavailable",
            "Timeout occurred for operation {}"
        ],
        'CRITICAL': [
            "System out of memory",
            "Database connection lost",
            "Security breach detected from IP {}",
            "Service {} crashed with exit code {}",
            "Disk space critically low: {}% remaining"
        ]
    }
    
    category_mapping = {
        'INFO': ['APPLICATION', 'SYSTEM'],
        'WARNING': ['PERFORMANCE', 'SYSTEM'],
        'ERROR': ['APPLICATION', 'SYSTEM', 'SECURITY'],
        'CRITICAL': ['SYSTEM', 'SECURITY']
    }
    
    services = ['web-server', 'auth-service', 'database', 'cache', 'api-gateway']
    components = ['handler', 'controller', 'repository', 'service', 'middleware']
    
    logs = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(num_logs):
        # Choose severity with realistic distribution
        severity = random.choices(
            ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            weights=[70, 20, 8, 2]
        )[0]
        
        # Choose category based on severity
        category = random.choice(category_mapping[severity])
        
        # Generate message
        template = random.choice(log_templates[severity])
        
        # Fill template with random values
        if '{}' in template:
            if 'user' in template.lower():
                message = template.format(f"user_{random.randint(1000, 9999)}")
            elif 'endpoint' in template.lower():
                message = template.format(f"/api/v1/{random.choice(['users', 'orders', 'products'])}")
            elif 'ms' in template:
                message = template.format(random.randint(10, 2000))
            elif 'service' in template.lower():
                message = template.format(random.choice(services))
            elif 'IP' in template:
                message = template.format(f"192.168.{random.randint(1,255)}.{random.randint(1,255)}")
            elif '%' in template:
                message = template.format(random.randint(50, 99))
            elif 'exit code' in template:
                message = template.format(random.choice([1, 2, 130, 255]))
            else:
                message = template.format(random.choice(['operation', 'request', 'task']))
        else:
            message = template
        
        # Generate timestamp
        timestamp = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Generate metadata
        metadata = {
            'service': random.choice(services),
            'component': random.choice(components),
            'request_id': f"req_{random.randint(100000, 999999)}",
            'user_id': f"user_{random.randint(1000, 9999)}" if random.random() > 0.3 else None
        }
        
        logs.append({
            'timestamp': timestamp.isoformat(),
            'message': message,
            'severity': severity,
            'category': category,
            'metadata': metadata
        })
    
    return pd.DataFrame(logs)

if __name__ == "__main__":
    # Generate training data
    print("Generating sample training data...")
    df = generate_sample_logs(1000)
    
    # Save to CSV
    df.to_csv("data/training/sample_logs.csv", index=False)
    print(f"Generated {len(df)} sample logs saved to data/training/sample_logs.csv")
    
    # Display distribution
    print("\nSeverity distribution:")
    print(df['severity'].value_counts())
    
    print("\nCategory distribution:")
    print(df['category'].value_counts())
EOF

python src/utils/data_generator.py

echo "✅ Sample data generated"

# Create tests
echo "🧪 Creating test suite..."
cat > tests/unit/test_feature_extraction.py << 'EOF'
import pytest
import pandas as pd
import numpy as np
from src.feature_extraction.extractor import LogFeatureExtractor
from config.config import ML_CONFIG

class TestLogFeatureExtractor:
    def setup_method(self):
        self.extractor = LogFeatureExtractor(ML_CONFIG["feature_extraction"])
        
    def test_preprocess_text(self):
        text = "2024-06-16 10:30:45 ERROR: Database connection failed from 192.168.1.100"
        result = self.extractor.preprocess_text(text)
        
        # Should remove timestamp and IP
        assert "2024-06-16" not in result
        assert "192.168.1.100" not in result
        assert "error database connection failed" in result
        
    def test_extract_temporal_features(self):
        timestamps = ["2024-06-16T10:30:45", "2024-06-16T15:20:30"]
        features = self.extractor.extract_temporal_features(timestamps)
        
        assert features.shape == (2, 4)
        assert features[0][0] == 10  # hour
        assert features[1][0] == 15  # hour
        
    def test_fit_transform(self):
        # Create sample data
        data = {
            'message': ['Error occurred', 'Info message', 'Warning detected'],
            'timestamp': ['2024-06-16T10:30:45', '2024-06-16T11:30:45', '2024-06-16T12:30:45'],
            'metadata': [{'service': 'web'}, {'service': 'api'}, {'service': 'db'}]
        }
        df = pd.DataFrame(data)
        
        features = self.extractor.fit_transform(df)
        
        assert features.shape[0] == 3  # 3 samples
        assert features.shape[1] > 10  # Should have many features
        assert self.extractor.is_fitted
EOF

cat > tests/unit/test_classifier.py << 'EOF'
import pytest
import numpy as np
from src.ml_pipeline.classifier import LogClassifier
from config.config import ML_CONFIG

class TestLogClassifier:
    def setup_method(self):
        self.classifier = LogClassifier(ML_CONFIG)
        
    def test_initialization(self):
        assert 'naive_bayes' in self.classifier.models
        assert 'random_forest' in self.classifier.models
        assert 'gradient_boosting' in self.classifier.models
        assert not self.classifier.is_trained
        
    def test_train_predict(self):
        # Create dummy training data
        n_samples = 100
        n_features = 50
        
        X = np.random.rand(n_samples, n_features)
        y_severity = np.random.choice(['INFO', 'WARNING', 'ERROR'], n_samples)
        y_category = np.random.choice(['APPLICATION', 'SYSTEM'], n_samples)
        
        # Train
        results = self.classifier.train(X, y_severity, y_category)
        
        assert self.classifier.is_trained
        assert 'severity_accuracy' in results
        assert 'category_accuracy' in results
        
        # Predict
        predictions = self.classifier.predict(X[:5])
        
        assert len(predictions['severity']) == 5
        assert len(predictions['category']) == 5
        assert all(conf >= 0 and conf <= 1 for conf in predictions['severity_confidence'])
EOF

cat > tests/integration/test_api.py << 'EOF'
import pytest
from fastapi.testclient import TestClient
import pandas as pd
from src.api.main import app
from src.utils.data_generator import generate_sample_logs

client = TestClient(app)

class TestAPI:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "ML Log Classifier Dashboard" in response.text
        
    def test_stats_endpoint(self):
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_classified" in data
        assert "severity_distribution" in data
        
    def test_classification_flow(self):
        # First train the model
        response = client.post("/train")
        assert response.status_code == 200
        
        # Then classify a log
        log_data = {
            "message": "Database connection failed",
            "timestamp": "2024-06-16T10:30:45",
            "metadata": {"service": "database"}
        }
        
        response = client.post("/classify", json=log_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "severity" in data
        assert "category" in data
        assert "severity_confidence" in data
EOF

echo "✅ Tests created"

# Create performance test
cat > tests/performance/test_performance.py << 'EOF'
import time
import asyncio
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import concurrent.futures

client = TestClient(app)

class TestPerformance:
    def test_classification_latency(self):
        """Test single classification latency"""
        # Train model first
        client.post("/train")
        
        log_data = {
            "message": "Error: Database connection timeout",
            "timestamp": "2024-06-16T10:30:45",
            "metadata": {"service": "database"}
        }
        
        # Measure latency
        start_time = time.time()
        response = client.post("/classify", json=log_data)
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert latency < 100  # Should be under 100ms
        print(f"Classification latency: {latency:.2f}ms")
        
    def test_throughput(self):
        """Test classification throughput"""
        # Train model first
        client.post("/train")
        
        log_data = {
            "message": "Error: Service unavailable",
            "timestamp": "2024-06-16T10:30:45",
            "metadata": {"service": "web"}
        }
        
        # Test throughput
        num_requests = 100
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(client.post, "/classify", json=log_data)
                for _ in range(num_requests)
            ]
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = num_requests / duration
        
        assert all(r.status_code == 200 for r in results)
        assert throughput > 50  # Should handle >50 requests/second
        print(f"Throughput: {throughput:.2f} requests/second")
EOF

echo "✅ Performance tests created"

# Create Docker configuration
echo "🐳 Creating Docker configuration..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Copy application code
COPY . .

# Create directories
RUN mkdir -p data/training models

# Generate sample data
RUN python src/utils/data_generator.py

EXPOSE 8000

CMD ["python", "src/api/main.py"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  ml-classifier:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/stats"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

echo "✅ Docker configuration created"

# Create start script
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting ML Log Classifier System"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
    touch venv/installed
fi

# Set Python path
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Generate sample data if needed
if [ ! -f "data/training/sample_logs.csv" ]; then
    echo "Generating sample training data..."
    python src/utils/data_generator.py
fi

# Start the API server
echo "Starting ML Log Classifier API..."
python src/api/main.py &
API_PID=$!

echo "API started with PID: $API_PID"
echo "Dashboard available at: http://localhost:8000"
echo "Press Ctrl+C to stop"

# Store PID for cleanup
echo $API_PID > .api.pid

# Wait for interrupt
wait $API_PID
EOF

chmod +x start.sh

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping ML Log Classifier System"

# Kill API server if running
if [ -f ".api.pid" ]; then
    PID=$(cat .api.pid)
    if ps -p $PID > /dev/null; then
        echo "Stopping API server (PID: $PID)..."
        kill $PID
        rm .api.pid
    fi
fi

echo "✅ System stopped"
EOF

chmod +x stop.sh

echo "✅ Start/stop scripts created"

# Run tests
echo "🧪 Running tests..."
export PYTHONPATH="$(pwd):$PYTHONPATH"
python -m pytest tests/ -v

echo "🎯 Running performance tests..."
python -m pytest tests/performance/ -v -s

echo "✅ All tests completed"

# Build Docker image (optional)
echo "🐳 Building Docker image..."
docker build -t ml-log-classifier:latest .

echo "🎉 Build completed successfully!"

# Show next steps
echo ""
echo "🚀 Next Steps:"
echo "1. Start the system: ./start.sh"
echo "2. Open dashboard: http://localhost:8000"
echo "3. Click 'Train ML Model' to train the classifier"
echo "4. Test classification with sample log messages"
echo "5. Stop the system: ./stop.sh"
echo ""
echo "🐳 Docker alternative:"
echo "1. docker-compose up -d"
echo "2. Open dashboard: http://localhost:8000"
echo "3. docker-compose down"
echo ""
echo "📊 System Features:"
echo "- Real-time log classification"
echo "- Ensemble ML models (Naive Bayes, Random Forest, Gradient Boosting)"
echo "- Feature extraction with TF-IDF and temporal features"
echo "- Web dashboard with real-time updates"
echo "- Performance monitoring and statistics"
echo "- Comprehensive test suite"

echo "✅ Day 78: ML Pipeline Implementation Complete!"