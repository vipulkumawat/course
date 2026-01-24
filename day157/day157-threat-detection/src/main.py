import asyncio
import yaml
from pathlib import Path
import uvicorn
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.models import DetectionRule, SeverityLevel, ThreatCategory
from src.engine.rule_engine import RuleEngine
from src.api.threat_api import ThreatDetectionAPI
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

def load_rules_from_config(config_path: str) -> list:
    """Load detection rules from YAML configuration"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    rules = []
    for category, rule_list in config['detection_rules'].items():
        for rule_dict in rule_list:
            rule = DetectionRule(
                name=rule_dict['name'],
                pattern=rule_dict['pattern'],
                severity=SeverityLevel(rule_dict['severity']),
                category=ThreatCategory(rule_dict['category']),
                action=rule_dict['action'],
                threshold=rule_dict.get('threshold'),
                time_window=rule_dict.get('time_window'),
                distributed=rule_dict.get('distributed', False)
            )
            rules.append(rule)
    
    return rules

def setup_dashboard(app):
    """Setup dashboard route"""
    templates_path = Path(__file__).parent.parent / "web" / "templates"
    templates = Jinja2Templates(directory=str(templates_path))
    
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse("dashboard.html", {"request": request})

async def main():
    logger.info("starting_threat_detection_system")
    
    # Load rules
    config_path = Path(__file__).parent.parent / "config" / "rules_config.yaml"
    rules = load_rules_from_config(str(config_path))
    logger.info("rules_loaded", count=len(rules))
    
    # Initialize rule engine
    rule_engine = RuleEngine(rules)
    
    # Initialize API
    api = ThreatDetectionAPI(rule_engine)
    
    # Add dashboard route
    setup_dashboard(api.app)
    
    # Start API server
    config = uvicorn.Config(
        api.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info("api_server_starting", port=8000)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
