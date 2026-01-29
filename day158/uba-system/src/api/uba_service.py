"""Main UBA service API"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from feature_extraction.log_parser import LogParser
from feature_extraction.feature_engine import FeatureEngine
from feature_extraction.baseline_manager import BaselineManager
from detection.zscore_detector import ZScoreDetector
from detection.isolation_forest_detector import IsolationForestDetector
from detection.temporal_detector import TemporalDetector
from detection.ensemble_scorer import EnsembleScorer

app = FastAPI(title="User Behavior Analytics Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
log_parser = LogParser()
feature_engine = FeatureEngine()
baseline_manager = BaselineManager()
zscore_detector = ZScoreDetector(threshold=3.0)
isolation_detector = IsolationForestDetector(contamination=0.1)
temporal_detector = TemporalDetector()
ensemble_scorer = EnsembleScorer()

# Storage
user_risk_scores = {}
alerts = []

class LogEntry(BaseModel):
    user: str
    event_type: str
    timestamp: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

class AnomalyResult(BaseModel):
    user: str
    risk_score: float
    risk_level: str
    anomalies: List[str]
    timestamp: str

@app.get("/")
async def root():
    return {
        "service": "User Behavior Analytics",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/api/analyze")
async def analyze_behavior(log_entry: LogEntry):
    """Analyze user behavior from log entry"""
    
    # Parse log
    event = log_parser.parse_structured(log_entry.dict())
    user = event['user']
    
    if not user:
        raise HTTPException(status_code=400, detail="User required")
    
    # Add to history
    feature_engine.add_event(user, event)
    
    # Learn temporal patterns
    temporal_detector.learn_pattern(user, event['timestamp'])
    
    # Extract features
    features = feature_engine.extract_features(user, event)
    
    # Update baseline (in training mode)
    baseline_manager.update_baseline(user, features)
    baseline = baseline_manager.get_baseline(user)
    
    # Run detectors if baseline is trained
    if baseline_manager.is_trained(user, min_samples=50):
        # Z-score detection
        zscore_score, zscore_anomalies = zscore_detector.detect(features, baseline)
        
        # Temporal detection
        temporal_score, temporal_anomalies = temporal_detector.detect(user, event['timestamp'])
        
        # Combine scores
        detector_scores = {
            'zscore': (zscore_score, zscore_anomalies),
            'temporal': (temporal_score, temporal_anomalies)
        }
        
        result = ensemble_scorer.compute_score(detector_scores)
        
        # Store risk score
        user_risk_scores[user] = result
        
        # Generate alert if risk level is medium or higher (for demo: also include low for visibility)
        # Lower threshold for demo purposes to show alerts on dashboard
        if result['risk_level'] in ['high', 'critical', 'medium'] or result['final_score'] >= 20:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'user': user,
                'risk_score': result['final_score'],
                'risk_level': result['risk_level'],
                'anomalies': result['anomalies']
            }
            alerts.append(alert)
            # Keep only last 100 alerts
            if len(alerts) > 100:
                alerts = alerts[-100:]
        
        return {
            "user": user,
            "risk_score": result['final_score'],
            "risk_level": result['risk_level'],
            "anomalies": result['anomalies'],
            "features": features,
            "baseline_trained": True
        }
    else:
        # Still in baseline learning phase
        return {
            "user": user,
            "risk_score": 0,
            "risk_level": "learning",
            "message": f"Building baseline ({baseline['sample_count']}/50 samples)",
            "features": features,
            "baseline_trained": False
        }

@app.get("/api/users/{user}/risk-score")
async def get_user_risk(user: str):
    """Get current risk score for user"""
    if user in user_risk_scores:
        return user_risk_scores[user]
    return {"user": user, "risk_score": 0, "risk_level": "unknown"}

@app.get("/api/alerts")
async def get_alerts(limit: int = 10):
    """Get recent alerts"""
    return {"alerts": alerts[-limit:], "total": len(alerts)}

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    # Count high risk users from user_risk_scores
    high_risk_from_scores = sum(1 for s in user_risk_scores.values() if s.get('risk_level') in ['high', 'critical'])
    
    # Also count from recent alerts as fallback (users with high/critical alerts in last hour)
    # This ensures we capture users even if their risk_scores weren't updated
    from datetime import datetime, timedelta
    recent_cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
    high_risk_from_alerts = len(set(
        alert['user'] for alert in alerts
        if alert.get('risk_level') in ['high', 'critical'] 
        and alert.get('timestamp', '') >= recent_cutoff
    ))
    
    # Use the maximum of both to ensure accuracy
    high_risk_users = max(high_risk_from_scores, high_risk_from_alerts)
    
    return {
        "total_users": len(baseline_manager.baselines),
        "trained_users": sum(1 for u in baseline_manager.baselines if baseline_manager.is_trained(u, min_samples=50)),
        "total_alerts": len(alerts),
        "high_risk_users": high_risk_users
    }

@app.post("/api/simulate-anomaly")
async def simulate_anomaly(data: Dict[str, Any]):
    """Simulate anomalous behavior for testing"""
    user = data.get('user', 'test_user')
    anomaly_type = data.get('anomaly_type', 'unusual_access')
    
    # Create anomalous log entry
    if anomaly_type == 'unusual_access':
        log_entry = LogEntry(
            user=user,
            event_type='access',
            details={'resource': '/sensitive/database', 'count': 1000},
            timestamp=datetime.now().isoformat()
        )
    elif anomaly_type == 'unusual_time':
        # 3 AM access
        dt = datetime.now().replace(hour=3, minute=0)
        log_entry = LogEntry(
            user=user,
            event_type='login',
            timestamp=dt.isoformat()
        )
    else:
        log_entry = LogEntry(
            user=user,
            event_type='download',
            details={'bytes': 10000000000},  # 10GB
            timestamp=datetime.now().isoformat()
        )
    
    return await analyze_behavior(log_entry)

@app.post("/api/demo/add-test-alerts")
async def add_test_alerts(count: int = 5):
    """Add test alerts for dashboard demo with varied, realistic data"""
    import random
    from datetime import timedelta
    
    test_users = ['alice', 'bob', 'charlie', 'david', 'eve']
    anomaly_types = [
        ['unusual_access_pattern', 'time_of_day_anomaly'],
        ['data_volume_anomaly', 'geographic_entropy'],
        ['failed_login_attempts', 'session_duration'],
        ['resource_diversity', 'hourly_access_rate'],
        ['time_of_day_anomaly', 'weekend_activity'],
        ['unusual_access_pattern', 'geographic_entropy', 'time_of_day_anomaly'],
        ['data_volume_anomaly', 'failed_login_attempts'],
        ['session_duration', 'resource_diversity']
    ]
    
    for i in range(count):
        # Vary users
        user = test_users[i % len(test_users)]
        
        # Vary risk scores (35-95 range)
        base_score = random.uniform(35, 95)
        risk_score = round(base_score, 1)
        
        # Determine risk level based on score
        if risk_score >= 80:
            risk_level = 'critical'
        elif risk_score >= 60:
            risk_level = 'high'
        elif risk_score >= 40:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Vary timestamps (spread over last 2 hours)
        minutes_ago = random.randint(0, 120)
        timestamp = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
        
        # Vary anomalies
        selected_anomalies = random.choice(anomaly_types)
        
        # Create alert
        alert = {
            'timestamp': timestamp,
            'user': user,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'anomalies': selected_anomalies
        }
        alerts.append(alert)
        
        # Also update user_risk_scores so high_risk_users count is correct
        # Only update if this is a higher risk than current
        if user not in user_risk_scores or user_risk_scores[user].get('final_score', 0) < risk_score:
            user_risk_scores[user] = {
                'final_score': risk_score,
                'risk_level': risk_level,
                'anomalies': selected_anomalies,
                'detector_details': {}
            }
    
    # Sort alerts by timestamp (newest first) and keep only last 100
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    if len(alerts) > 100:
        alerts[:] = alerts[:100]
    
    high_risk_count = sum(1 for s in user_risk_scores.values() if s.get('risk_level') in ['high', 'critical'])
    
    return {
        "message": f"Added {count} varied test alerts",
        "total_alerts": len(alerts),
        "high_risk_users": high_risk_count
    }

@app.get("/dashboard")
async def dashboard():
    """Serve dashboard HTML"""
    html_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'index.html')
    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
