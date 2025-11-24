import sys
import os
# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from datetime import datetime
import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models.webhook import Base, WebhookEndpoint, WebhookDelivery
from src.core.webhook_engine import WebhookEngine
from config.config import settings

# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title=settings.app_name)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class WebhookEndpointCreate(BaseModel):
    name: str
    url: str
    method: str = "POST"
    auth_type: str = "none"
    auth_config: Dict = {}
    payload_template: Optional[str] = None
    event_filters: List[Dict] = []

class LogEvent(BaseModel):
    type: str
    timestamp: str
    level: str
    message: str
    source: str
    metadata: Dict = {}

@app.get("/")
async def dashboard():
    """Serve dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Webhook Integration Dashboard</title>
        <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }
            .dashboard { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }
            .title { margin: 0; color: #2d3748; font-size: 28px; font-weight: 700; }
            .subtitle { margin: 5px 0 0; color: #718096; font-size: 16px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
            .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .card h3 { margin: 0 0 20px; color: #2d3748; font-size: 20px; }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 8px; color: #4a5568; font-weight: 500; }
            .form-control { width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 14px; }
            .form-control:focus { outline: none; border-color: #4299e1; }
            .btn { padding: 12px 20px; background: #4299e1; color: white; border: none; border-radius: 8px; font-weight: 500; cursor: pointer; }
            .btn:hover { background: #3182ce; }
            .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; }
            .stat { background: #f7fafc; padding: 20px; border-radius: 10px; text-align: center; }
            .stat-value { font-size: 24px; font-weight: 700; color: #2d3748; }
            .stat-label { color: #718096; font-size: 14px; margin-top: 5px; }
            .webhook-list { margin-top: 25px; }
            .webhook-item { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
            .webhook-info h4 { margin: 0; color: #2d3748; }
            .webhook-info p { margin: 5px 0 0; color: #718096; font-size: 13px; }
            .status { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }
            .status-active { background: #c6f6d5; color: #22543d; }
            .status-inactive { background: #fed7d7; color: #742a2a; }
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel">
            function Dashboard() {
                const [webhooks, setWebhooks] = React.useState([]);
                const [stats, setStats] = React.useState({ total: 0, active: 0, deliveries: 0 });
                const [formData, setFormData] = React.useState({
                    name: '', url: '', auth_type: 'none', auth_config: {}, event_filters: []
                });

                React.useEffect(() => {
                    fetchWebhooks();
                    fetchStats();
                    const interval = setInterval(fetchStats, 5000);
                    return () => clearInterval(interval);
                }, []);

                const fetchWebhooks = async () => {
                    try {
                        const response = await fetch('/api/webhooks');
                        const data = await response.json();
                        setWebhooks(data);
                    } catch (error) {
                        console.error('Error fetching webhooks:', error);
                    }
                };

                const fetchStats = async () => {
                    try {
                        const response = await fetch('/api/stats');
                        const data = await response.json();
                        setStats(data);
                    } catch (error) {
                        console.error('Error fetching stats:', error);
                    }
                };

                const handleSubmit = async (e) => {
                    e.preventDefault();
                    try {
                        const response = await fetch('/api/webhooks', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(formData)
                        });
                        
                        if (response.ok) {
                            setFormData({ name: '', url: '', auth_type: 'none', auth_config: {}, event_filters: [] });
                            fetchWebhooks();
                            alert('Webhook created successfully!');
                        }
                    } catch (error) {
                        alert('Error creating webhook: ' + error.message);
                    }
                };

                const testWebhook = async () => {
                    try {
                        const response = await fetch('/api/test-event', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                type: 'test_event',
                                timestamp: new Date().toISOString(),
                                level: 'info',
                                message: 'Test webhook delivery from dashboard',
                                source: 'webhook_dashboard',
                                metadata: { test: true }
                            })
                        });
                        
                        if (response.ok) {
                            alert('Test event sent to all active webhooks!');
                            fetchStats();
                        }
                    } catch (error) {
                        alert('Error sending test event: ' + error.message);
                    }
                };

                return React.createElement('div', { className: 'dashboard' }, [
                    React.createElement('div', { className: 'header', key: 'header' }, [
                        React.createElement('h1', { className: 'title', key: 'title' }, 'Webhook Integration System'),
                        React.createElement('p', { className: 'subtitle', key: 'subtitle' }, 'Universal webhook dispatcher for distributed log processing')
                    ]),
                    
                    React.createElement('div', { className: 'stats', key: 'stats' }, [
                        React.createElement('div', { className: 'stat', key: 'total' }, [
                            React.createElement('div', { className: 'stat-value', key: 'value' }, stats.total),
                            React.createElement('div', { className: 'stat-label', key: 'label' }, 'Total Webhooks')
                        ]),
                        React.createElement('div', { className: 'stat', key: 'active' }, [
                            React.createElement('div', { className: 'stat-value', key: 'value' }, stats.active),
                            React.createElement('div', { className: 'stat-label', key: 'label' }, 'Active Endpoints')
                        ]),
                        React.createElement('div', { className: 'stat', key: 'deliveries' }, [
                            React.createElement('div', { className: 'stat-value', key: 'value' }, stats.deliveries),
                            React.createElement('div', { className: 'stat-label', key: 'label' }, 'Deliveries Today')
                        ])
                    ]),

                    React.createElement('div', { className: 'grid', key: 'grid' }, [
                        React.createElement('div', { className: 'card', key: 'form' }, [
                            React.createElement('h3', { key: 'title' }, 'Add New Webhook'),
                            React.createElement('form', { onSubmit: handleSubmit, key: 'form' }, [
                                React.createElement('div', { className: 'form-group', key: 'name' }, [
                                    React.createElement('label', { key: 'label' }, 'Name'),
                                    React.createElement('input', {
                                        key: 'input',
                                        className: 'form-control',
                                        type: 'text',
                                        value: formData.name,
                                        onChange: e => setFormData({...formData, name: e.target.value}),
                                        required: true
                                    })
                                ]),
                                React.createElement('div', { className: 'form-group', key: 'url' }, [
                                    React.createElement('label', { key: 'label' }, 'Webhook URL'),
                                    React.createElement('input', {
                                        key: 'input',
                                        className: 'form-control',
                                        type: 'url',
                                        value: formData.url,
                                        onChange: e => setFormData({...formData, url: e.target.value}),
                                        required: true
                                    })
                                ]),
                                React.createElement('div', { className: 'form-group', key: 'auth' }, [
                                    React.createElement('label', { key: 'label' }, 'Authentication'),
                                    React.createElement('select', {
                                        key: 'select',
                                        className: 'form-control',
                                        value: formData.auth_type,
                                        onChange: e => setFormData({...formData, auth_type: e.target.value})
                                    }, [
                                        React.createElement('option', { key: 'none', value: 'none' }, 'None'),
                                        React.createElement('option', { key: 'bearer', value: 'bearer' }, 'Bearer Token'),
                                        React.createElement('option', { key: 'api_key', value: 'api_key' }, 'API Key'),
                                        React.createElement('option', { key: 'hmac', value: 'hmac' }, 'HMAC Signature')
                                    ])
                                ]),
                                React.createElement('button', { 
                                    key: 'submit', 
                                    type: 'submit', 
                                    className: 'btn' 
                                }, 'Create Webhook')
                            ])
                        ]),

                        React.createElement('div', { className: 'card', key: 'list' }, [
                            React.createElement('div', { key: 'header', style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } }, [
                                React.createElement('h3', { key: 'title' }, 'Active Webhooks'),
                                React.createElement('button', { 
                                    key: 'test', 
                                    className: 'btn', 
                                    onClick: testWebhook,
                                    style: { padding: '8px 16px', fontSize: '14px' }
                                }, 'Test All')
                            ]),
                            React.createElement('div', { className: 'webhook-list', key: 'list' }, 
                                webhooks.map(webhook => 
                                    React.createElement('div', { className: 'webhook-item', key: webhook.id }, [
                                        React.createElement('div', { className: 'webhook-info', key: 'info' }, [
                                            React.createElement('h4', { key: 'name' }, webhook.name),
                                            React.createElement('p', { key: 'url' }, webhook.url)
                                        ]),
                                        React.createElement('span', { 
                                            key: 'status',
                                            className: `status ${webhook.is_active ? 'status-active' : 'status-inactive'}`
                                        }, webhook.is_active ? 'Active' : 'Inactive')
                                    ])
                                )
                            )
                        ])
                    ])
                ]);
            }

            ReactDOM.render(React.createElement(Dashboard), document.getElementById('root'));
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/webhooks")
async def create_webhook(webhook: WebhookEndpointCreate, db: Session = Depends(get_db)):
    """Create new webhook endpoint"""
    db_webhook = WebhookEndpoint(
        name=webhook.name,
        url=webhook.url,
        method=webhook.method,
        auth_type=webhook.auth_type,
        auth_config=webhook.auth_config,
        payload_template=webhook.payload_template,
        event_filters=webhook.event_filters
    )
    
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    
    return {"id": db_webhook.id, "message": "Webhook created successfully"}

@app.get("/api/webhooks")
async def get_webhooks(db: Session = Depends(get_db)):
    """Get all webhook endpoints"""
    webhooks = db.query(WebhookEndpoint).all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "url": w.url,
            "method": w.method,
            "auth_type": w.auth_type,
            "is_active": w.is_active,
            "created_at": w.created_at.isoformat()
        }
        for w in webhooks
    ]

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get webhook system statistics"""
    from sqlalchemy import func
    from datetime import date
    
    total_webhooks = db.query(WebhookEndpoint).count()
    active_webhooks = db.query(WebhookEndpoint).filter(WebhookEndpoint.is_active == True).count()
    
    # Count deliveries today
    today = date.today()
    deliveries_today = db.query(WebhookDelivery).filter(
        func.date(WebhookDelivery.created_at) == today
    ).count()
    
    return {
        "total": total_webhooks,
        "active": active_webhooks,
        "deliveries": deliveries_today
    }

@app.post("/api/events")
async def process_event(event: LogEvent, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Process incoming log event and trigger webhooks"""
    webhook_engine = WebhookEngine(db)
    
    event_data = {
        "type": event.type,
        "timestamp": event.timestamp,
        "level": event.level,
        "message": event.message,
        "source": event.source,
        "metadata": event.metadata
    }
    
    # Process event asynchronously
    background_tasks.add_task(webhook_engine.process_event, event_data)
    
    return {"status": "accepted", "message": "Event processing initiated"}

@app.post("/api/test-event")
async def send_test_event(event: LogEvent, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Send test event to all active webhooks"""
    webhook_engine = WebhookEngine(db)
    
    event_data = {
        "type": event.type,
        "timestamp": event.timestamp,
        "level": event.level,
        "message": event.message,
        "source": event.source,
        "metadata": event.metadata
    }
    
    delivery_ids = await webhook_engine.process_event(event_data)
    
    return {
        "status": "success", 
        "message": f"Test event sent to {len(delivery_ids)} webhook(s)",
        "deliveries": delivery_ids
    }

@app.get("/api/deliveries")
async def get_deliveries(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent webhook deliveries"""
    deliveries = db.query(WebhookDelivery).order_by(
        WebhookDelivery.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": d.id,
            "endpoint_id": d.endpoint_id,
            "status": d.status,
            "response_code": d.response_code,
            "attempt_count": d.attempt_count,
            "created_at": d.created_at.isoformat(),
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None
        }
        for d in deliveries
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
