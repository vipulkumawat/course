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
        
        # Convert metadata from string to dict if needed
        if 'metadata' in training_data.columns:
            import ast
            training_data['metadata'] = training_data['metadata'].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('{') else {}
            )
        
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