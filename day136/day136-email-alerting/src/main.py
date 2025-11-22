import asyncio
import schedule
import time
from datetime import datetime, timedelta
import logging
import redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import threading

from email_service.email_manager import EmailManager, EmailMessage, EmailConfig
from email_service.alert_evaluator import AlertEvaluator, AlertCondition, AlertSeverity, Alert
from reports.report_generator import ReportGenerator, ReportConfig
from config.email_config import get_email_config, get_default_alert_conditions, get_default_report_configs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI app
app = FastAPI(title="Email Alerting and Reporting System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
email_config = get_email_config()
email_manager = EmailManager(email_config)
alert_evaluator = AlertEvaluator(redis_client)
report_generator = ReportGenerator(redis_client)

# Add default alert conditions
for condition in get_default_alert_conditions().values():
    alert_evaluator.add_condition(condition)

# Pydantic models for API
class MetricsUpdate(BaseModel):
    metrics: Dict[str, float]
    timestamp: str = None

class EmailRequest(BaseModel):
    to_emails: List[str]
    subject: str
    template: str
    context: Dict[str, Any] = {}
    priority: str = "normal"

class ReportRequest(BaseModel):
    report_type: str
    recipients: List[str]
    time_range_hours: int = 24

# Global state for metrics simulation
current_metrics = {
    'requests_per_second': 150.0,
    'error_rate': 2.5,
    'response_time_ms': 180.0
}

@app.get("/")
async def dashboard():
    """Serve the main dashboard"""
    return FileResponse('frontend/public/index.html')

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    # Return a simple 204 No Content to avoid 404 errors
    from fastapi.responses import Response
    return Response(status_code=204)

@app.post("/api/metrics")
async def update_metrics(metrics_update: MetricsUpdate, background_tasks: BackgroundTasks):
    """Update system metrics and trigger alert evaluation"""
    try:
        global current_metrics
        current_metrics.update(metrics_update.metrics)
        
        # Store metrics in Redis with timestamp
        timestamp = metrics_update.timestamp or datetime.now().isoformat()
        try:
            redis_client.setex(f"metrics:{timestamp}", 3600, str(metrics_update.metrics))
        except Exception as e:
            logging.warning(f"⚠️ Failed to store metrics in Redis: {str(e)}")
            # Continue even if Redis fails
        
        # Trigger alert evaluation in background
        try:
            background_tasks.add_task(evaluate_alerts, metrics_update.metrics)
        except Exception as e:
            logging.warning(f"⚠️ Failed to schedule alert evaluation: {str(e)}")
        
        logging.info(f"📊 Updated metrics: {metrics_update.metrics}")
        return {"status": "updated", "timestamp": timestamp}
    except Exception as e:
        logging.error(f"❌ Failed to update metrics: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_current_metrics():
    """Get current system metrics"""
    return {
        "current_metrics": current_metrics,
        "timestamp": datetime.now().isoformat(),
        "alert_summary": alert_evaluator.get_alert_summary()
    }

@app.post("/api/send_email")
async def send_email(email_request: EmailRequest):
    """Send custom email using template"""
    try:
        # Process context to convert string timestamps to datetime objects
        processed_context = email_request.context.copy()
        
        # Convert timestamp strings to datetime objects
        if 'timestamp' in processed_context and isinstance(processed_context['timestamp'], str):
            try:
                processed_context['timestamp'] = datetime.fromisoformat(processed_context['timestamp'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # If parsing fails, use current time
                processed_context['timestamp'] = datetime.now()
        
        # Process alert timestamp if present
        if 'alert' in processed_context and isinstance(processed_context['alert'], dict):
            if 'timestamp' in processed_context['alert']:
                alert_ts = processed_context['alert']['timestamp']
                if isinstance(alert_ts, str):
                    try:
                        processed_context['alert']['timestamp'] = datetime.fromisoformat(alert_ts.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        processed_context['alert']['timestamp'] = datetime.now()
                elif not isinstance(alert_ts, datetime):
                    processed_context['alert']['timestamp'] = datetime.now()
        
        # Add default title if not present
        if 'title' not in processed_context:
            processed_context['title'] = email_request.subject
        
        # Render template
        if email_request.template.endswith('.html'):
            html_body = email_manager.render_template(email_request.template, processed_context)
        else:
            html_body = email_request.template
        
        # Create email message
        message = EmailMessage(
            to_emails=email_request.to_emails,
            subject=email_request.subject,
            html_body=html_body,
            priority=email_request.priority
        )
        
        # Send email
        result = await email_manager.send_email(message)
        
        # If email sending failed, return the error but don't raise HTTPException
        # This allows the frontend to handle the error gracefully
        if result.get("status") == "failed":
            return result
        
        return result
        
    except Exception as e:
        logging.error(f"❌ Failed to send email: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        # Return error response instead of raising exception
        return {"status": "failed", "error": str(e)}

@app.post("/api/generate_report")
async def generate_report(report_request: ReportRequest):
    """Generate and send report"""
    try:
        report_configs = get_default_report_configs()
        
        if report_request.report_type not in report_configs:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        config = report_configs[report_request.report_type]
        config.recipients = report_request.recipients
        config.time_range_hours = report_request.time_range_hours
        
        # Generate report
        report_data = await report_generator.generate_daily_report(config)
        
        if "error" in report_data:
            raise HTTPException(status_code=500, detail=report_data["error"])
        
        # Send report via email
        html_body = email_manager.render_template('daily_report.html', report_data)
        
        message = EmailMessage(
            to_emails=config.recipients,
            subject=f"📊 {config.title} - {datetime.now().strftime('%Y-%m-%d')}",
            html_body=html_body,
            priority="normal"
        )
        
        result = await email_manager.send_email(message)
        
        return {
            "status": "success",
            "report": report_data,
            "email_result": result
        }
        
    except Exception as e:
        logging.error(f"❌ Failed to generate report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts():
    """Get recent alerts"""
    recent_alerts = alert_evaluator.get_recent_alerts(24)
    return {
        "alerts": [
            {
                "condition_name": alert.condition_name,
                "severity": alert.severity.value,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in recent_alerts
        ],
        "summary": alert_evaluator.get_alert_summary()
    }

@app.get("/api/email_stats")
async def get_email_stats():
    """Get email delivery statistics"""
    return email_manager.get_delivery_stats()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": "connected",
                "email": "configured",
                "alerts": f"{len(alert_evaluator.conditions)} conditions active"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

async def evaluate_alerts(metrics: Dict[str, float]):
    """Evaluate metrics and send alerts if needed"""
    try:
        triggered_alerts = await alert_evaluator.evaluate_metrics(metrics)
        
        for alert in triggered_alerts:
            # Send alert email
            html_body = email_manager.render_template('alert_email.html', {'alert': alert})
            
            message = EmailMessage(
                to_emails=['admin@company.com'],  # In production, get from alert condition
                subject=f"🚨 {alert.severity.value.title()} Alert: {alert.condition_name}",
                html_body=html_body,
                priority="critical" if alert.severity == AlertSeverity.CRITICAL else "high"
            )
            
            await email_manager.send_email(message)
            logging.info(f"🚨 Sent alert email for: {alert.condition_name}")
            
    except Exception as e:
        logging.error(f"❌ Alert evaluation failed: {str(e)}")

def run_scheduled_reports():
    """Run scheduled reports in background thread"""
    def job():
        asyncio.run(generate_scheduled_reports())
    
    schedule.every().day.at("09:00").do(job)  # Daily at 9 AM
    schedule.every().monday.at("08:00").do(lambda: asyncio.run(generate_weekly_report()))  # Weekly on Monday
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

async def generate_scheduled_reports():
    """Generate and send daily scheduled reports"""
    try:
        report_configs = get_default_report_configs()
        
        for report_name, config in report_configs.items():
            if report_name == 'daily_summary':
                report_data = await report_generator.generate_daily_report(config)
                
                html_body = email_manager.render_template('daily_report.html', report_data)
                
                message = EmailMessage(
                    to_emails=config.recipients,
                    subject=f"📊 {config.title} - {datetime.now().strftime('%Y-%m-%d')}",
                    html_body=html_body,
                    priority="normal"
                )
                
                await email_manager.send_email(message)
                logging.info(f"📊 Sent scheduled report: {report_name}")
                
    except Exception as e:
        logging.error(f"❌ Scheduled report generation failed: {str(e)}")

async def generate_weekly_report():
    """Generate weekly executive report"""
    try:
        config = get_default_report_configs()['weekly_executive']
        report_data = await report_generator.generate_daily_report(config)
        
        html_body = email_manager.render_template('daily_report.html', report_data)
        
        message = EmailMessage(
            to_emails=config.recipients,
            subject=f"📈 Weekly Executive Summary - Week of {datetime.now().strftime('%Y-%m-%d')}",
            html_body=html_body,
            priority="normal"
        )
        
        await email_manager.send_email(message)
        logging.info("📈 Sent weekly executive report")
        
    except Exception as e:
        logging.error(f"❌ Weekly report generation failed: {str(e)}")

# Start background scheduler thread
scheduler_thread = threading.Thread(target=run_scheduled_reports, daemon=True)
scheduler_thread.start()

# Simulate periodic metrics updates
async def simulate_metrics():
    """Simulate realistic metrics changes for demo"""
    import random
    import math
    
    while True:
        await asyncio.sleep(30)  # Update every 30 seconds
        
        # Simulate realistic metric variations
        hour = datetime.now().hour
        
        # Vary metrics based on time of day
        base_requests = 100 + 50 * math.sin((hour - 9) * math.pi / 12)
        base_errors = 2.0 + math.sin(hour * math.pi / 12)
        base_response = 150 + 50 * math.sin((hour - 12) * math.pi / 8)
        
        current_metrics['requests_per_second'] = max(10, base_requests + random.uniform(-20, 20))
        current_metrics['error_rate'] = max(0.1, base_errors + random.uniform(-1, 1))
        current_metrics['response_time_ms'] = max(50, base_response + random.uniform(-30, 30))
        
        # Occasionally trigger alerts for demo
        if random.random() < 0.1:  # 10% chance
            current_metrics['error_rate'] = random.uniform(6, 12)  # Trigger error alert

# Start metrics simulation
if __name__ == "__main__":
    import uvicorn
    
    # Start metrics simulation in background
    asyncio.create_task(simulate_metrics())
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
