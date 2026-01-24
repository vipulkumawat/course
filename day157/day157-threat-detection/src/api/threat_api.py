from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
import json
from datetime import datetime
from src.models import LogEntry, ThreatDetection
from src.engine.rule_engine import RuleEngine
from src.engine.threat_classifier import ThreatClassifier
import structlog

logger = structlog.get_logger()

class ThreatDetectionAPI:
    def __init__(self, rule_engine: RuleEngine):
        self.app = FastAPI(title="Threat Detection API")
        self.rule_engine = rule_engine
        self.classifier = ThreatClassifier()
        self.active_websockets: List[WebSocket] = []
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/api/analyze")
        async def analyze_log(log_entry: LogEntry):
            """Analyze a single log entry"""
            detections = await self.rule_engine.evaluate(log_entry)
            classification = self.classifier.classify_threat_level(detections)
            
            # Broadcast to websockets
            await self._broadcast_detection(detections, classification)
            
            return {
                "log_id": log_entry.metadata.get("id", "unknown"),
                "detections": [d.dict() for d in detections],
                "classification": classification,
                "analyzed_at": datetime.now().isoformat()
            }
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get detection statistics"""
            return {
                "engine_stats": self.rule_engine.get_stats(),
                "classifier_stats": self.classifier.get_classification_stats(),
                "active_connections": len(self.active_websockets)
            }
        
        @self.app.websocket("/ws/threats")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time threat updates"""
            await websocket.accept()
            self.active_websockets.append(websocket)
            
            try:
                while True:
                    await asyncio.sleep(1)
            except WebSocketDisconnect:
                self.active_websockets.remove(websocket)
    
    async def _broadcast_detection(self, detections: List[ThreatDetection], classification: dict):
        """Broadcast detection to all connected websockets"""
        if not detections or not self.active_websockets:
            return
        
        message = {
            "type": "threat_detection",
            "timestamp": datetime.now().isoformat(),
            "detections": [
                {
                    "id": d.detection_id,
                    "severity": d.severity,
                    "rule": d.rule_name,
                    "source_ip": d.log_entry.source_ip,
                    "confidence": d.confidence
                }
                for d in detections
            ],
            "classification": classification
        }
        
        disconnected = []
        for ws in self.active_websockets:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.active_websockets.remove(ws)
