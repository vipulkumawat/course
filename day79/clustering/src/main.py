#!/usr/bin/env python3
"""
Day 79: Log Clustering for Pattern Discovery
Main application entry point
"""

import asyncio
import json
import logging
import sys
import time
import uvicorn
from typing import Dict, List, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import yaml
import redis
import numpy as np

# Import our modules
from clustering.engine import StreamingClusteringEngine
from feature_extraction.pipeline import LogFeatureExtractor
from visualization.websocket_handler import ConnectionManager, ClusterWebSocketHandler
from utils.sample_data import generate_sample_logs, LogEntry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config_path = Path("config/clustering_config.yaml")
if not config_path.exists():
    logger.error(f"Configuration file not found: {config_path}")
    sys.exit(1)

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize FastAPI app
app = FastAPI(title="Log Clustering Dashboard", version="1.0.0")

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global components
clustering_engine = None
feature_extractor = None
connection_manager = ConnectionManager()
websocket_handler = None
redis_client = None

# Statistics tracking
stats = {
    'total_processed': 0,
    'patterns_discovered': 0,
    'anomalies_detected': 0,
    'processing_rate': 0,
    'last_updated': time.time()
}

async def initialize_components():
    """Initialize all system components"""
    global clustering_engine, feature_extractor, websocket_handler, redis_client
    
    logger.info("Initializing system components...")
    
    # Initialize Redis connection
    redis_config = config['redis']
    redis_client = redis.Redis(
        host=redis_config['host'],
        port=redis_config['port'],
        db=redis_config['db'],
        decode_responses=True
    )
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None
    
    # Initialize clustering engine
    clustering_engine = StreamingClusteringEngine(config)
    
    # Initialize feature extractor
    feature_extractor = LogFeatureExtractor(config)
    
    # Initialize WebSocket handler
    websocket_handler = ClusterWebSocketHandler(connection_manager)
    
    logger.info("System components initialized successfully")

async def train_initial_models():
    """Train models on historical data"""
    logger.info("Training initial clustering models...")
    
    # Generate sample historical data
    sample_logs = generate_sample_logs(1000)
    
    # Fit feature extractor
    log_dicts = [log.to_dict() for log in sample_logs]
    feature_extractor.fit_extractors(log_dicts)
    
    # Extract features for all logs
    features_list = []
    for log_dict in log_dicts:
        features, feature_names = feature_extractor.extract_features(log_dict)
        features_list.append(features)
    
    features_matrix = np.array(features_list)
    
    # Fit clustering models
    fit_results = await clustering_engine.fit_initial_model(features_matrix, feature_names)
    
    logger.info(f"Models trained successfully: {fit_results}")
    
    # Update statistics
    stats['total_processed'] = len(sample_logs)
    stats['last_updated'] = time.time()
    
    return fit_results

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    await initialize_components()
    await train_initial_models()
    logger.info("Application startup completed")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'request_patterns':
                # Send current patterns to client
                cluster_stats = clustering_engine.get_cluster_statistics()
                patterns = cluster_stats.get('recent_patterns', [])
                
                # Convert patterns to serializable format
                serializable_patterns = []
                for pattern in patterns:
                    serializable_patterns.append({
                        'pattern_id': pattern.pattern_id,
                        'pattern_type': pattern.pattern_type,
                        'algorithm': pattern.algorithm,
                        'confidence': pattern.confidence,
                        'sample_logs': pattern.sample_logs,
                        'feature_importance': pattern.feature_importance,
                        'discovered_at': pattern.discovered_at
                    })
                
                response = {
                    'type': 'patterns_response',
                    'data': {
                        'patterns': serializable_patterns,
                        'total_patterns': len(serializable_patterns)
                    }
                }
                
                await websocket.send_text(json.dumps(response))
                
            elif message.get('type') == 'request_stats':
                # Send current stats to client
                current_stats = clustering_engine.get_cluster_statistics()
                response = {
                    'type': 'stats_update',
                    'data': current_stats,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)

@app.get("/api/stats")
async def get_stats():
    """Get current system statistics"""
    cluster_stats = clustering_engine.get_cluster_statistics()
    
    return {
        **stats,
        **cluster_stats,
        'redis_connected': redis_client is not None and redis_client.ping() if redis_client else False
    }

@app.get("/api/clusters")
async def get_clusters():
    """Get cluster information"""
    return clustering_engine.get_cluster_statistics()

@app.get("/api/patterns")
async def get_patterns():
    """Get discovered patterns"""
    try:
        cluster_stats = clustering_engine.get_cluster_statistics()
        patterns = cluster_stats.get('recent_patterns', [])
        
        # Convert patterns to serializable format
        serializable_patterns = []
        for pattern in patterns:
            serializable_patterns.append({
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type,
                'algorithm': pattern.algorithm,
                'confidence': pattern.confidence,
                'sample_logs': pattern.sample_logs,
                'feature_importance': pattern.feature_importance,
                'discovered_at': pattern.discovered_at
            })
        
        return {
            'success': True,
            'patterns': serializable_patterns,
            'total_patterns': len(serializable_patterns)
        }
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        return {'success': False, 'error': str(e)}

@app.post("/api/process_log")
async def process_log(log_data: Dict[str, Any]):
    """Process a single log entry"""
    try:
        # Extract features
        features, feature_names = feature_extractor.extract_features(log_data)
        
        # Predict cluster
        cluster_results = await clustering_engine.predict_cluster(features)
        
        # Update statistics
        stats['total_processed'] += 1
        stats['processing_rate'] = calculate_processing_rate()
        stats['last_updated'] = time.time()
        
        # Check for anomalies
        anomalies = [result for result in cluster_results if result.is_anomaly]
        if anomalies:
            stats['anomalies_detected'] += 1
            for anomaly in anomalies:
                await websocket_handler.handle_anomaly_detection({
                    'algorithm': anomaly.algorithm,
                    'cluster_id': anomaly.cluster_id,
                    'confidence': anomaly.confidence,
                    'pattern_type': 'anomaly',
                    'log_message': log_data.get('message', ''),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Broadcast new cluster results
        for result in cluster_results:
            await websocket_handler.handle_new_cluster({
                'algorithm': result.algorithm,
                'cluster_id': result.cluster_id,
                'confidence': result.confidence,
                'is_anomaly': result.is_anomaly,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            'success': True,
            'cluster_results': [
                {
                    'algorithm': r.algorithm,
                    'cluster_id': r.cluster_id,
                    'confidence': r.confidence,
                    'is_anomaly': r.is_anomaly
                } for r in cluster_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error processing log: {e}")
        return {'success': False, 'error': str(e)}

def calculate_processing_rate():
    """Calculate logs processed per second"""
    current_time = time.time()
    time_diff = current_time - stats['last_updated']
    if time_diff > 0:
        return stats['total_processed'] / time_diff
    return 0

async def run_demo():
    """Run demonstration of clustering system"""
    logger.info("🎯 Starting Log Clustering Demonstration")
    logger.info("=" * 50)
    
    # Generate demo logs
    demo_logs = generate_sample_logs(50)
    
    logger.info(f"📝 Processing {len(demo_logs)} Demo Log Entries:")
    logger.info("=" * 50)
    
    pattern_count = 0
    anomaly_count = 0
    
    for i, log in enumerate(demo_logs[:10], 1):  # Process first 10 for demo
        log_dict = log.to_dict()
        
        logger.info(f"\n📝 Processing Log Entry {i}:")
        logger.info(f"   Service: {log.service}")
        logger.info(f"   Level: {log.level}")
        logger.info(f"   Message: {log.message[:60]}...")
        
        # Extract features
        features, feature_names = feature_extractor.extract_features(log_dict)
        
        # Predict cluster
        cluster_results = await clustering_engine.predict_cluster(features)
        
        logger.info("   🎯 Cluster Results:")
        for result in cluster_results:
            logger.info(f"      {result.algorithm}: Cluster {result.cluster_id} (confidence: {result.confidence:.2f})")
            if result.is_anomaly:
                logger.info("      🚨 ANOMALY DETECTED!")
                anomaly_count += 1
        
        # Simulate pattern discovery
        if i % 3 == 0:  # Every 3rd log discovers a pattern
            pattern_count += 1
            logger.info("   🔍 Discovered Patterns:")
            logger.info(f"      Pattern Type: {log.service}_pattern")
            logger.info(f"      Algorithm: {cluster_results[0].algorithm}")
            logger.info(f"      Confidence: {cluster_results[0].confidence:.2f}")
        
        # Small delay for demo effect
        await asyncio.sleep(0.5)
    
    # Show final statistics
    cluster_stats = clustering_engine.get_cluster_statistics()
    
    logger.info(f"\n📊 Final Cluster Insights:")
    logger.info(f"   Total Patterns Discovered: {pattern_count}")
    logger.info(f"   Anomalies Detected: {anomaly_count}")
    logger.info(f"   Total Clusters: {sum(cluster_stats['algorithms'][algo]['clusters'] for algo in cluster_stats['algorithms'])}")
    logger.info(f"   Algorithms Used: {len(cluster_stats['algorithms'])}")
    
    for algo_name, algo_stats in cluster_stats['algorithms'].items():
        logger.info(f"   {algo_name.upper()}:")
        logger.info(f"      Clusters: {algo_stats['clusters']}")
        logger.info(f"      Avg Size: {algo_stats['total_points'] / max(algo_stats['clusters'], 1):.1f}")
    
    logger.info(f"\n✅ Demo completed successfully!")
    logger.info(f"🌐 Dashboard available at: http://localhost:{config['api']['port']}")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "demo":
            # Run demo
            asyncio.run(run_demo())
        elif command == "train":
            # Run training only
            asyncio.run(initialize_components())
            asyncio.run(train_initial_models())
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)
    else:
        # Run web server
        uvicorn.run(
            "main:app",
            host=config['api']['host'],
            port=config['api']['port'],
            reload=config['api']['debug'],
            log_level="info"
        )

if __name__ == "__main__":
    main()
