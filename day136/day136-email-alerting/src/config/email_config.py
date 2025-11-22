import os
from typing import Dict, Any
from src.email_service.email_manager import EmailConfig
from src.email_service.alert_evaluator import AlertCondition, AlertSeverity
from src.reports.report_generator import ReportConfig

def get_email_config() -> EmailConfig:
    """Get email configuration from environment variables"""
    return EmailConfig(
        smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        username=os.getenv('SMTP_USERNAME', 'demo@example.com'),
        password=os.getenv('SMTP_PASSWORD', 'demo_password'),
        from_email=os.getenv('FROM_EMAIL', 'noreply@logprocessing.com'),
        from_name=os.getenv('FROM_NAME', 'Log Processing System')
    )

def get_default_alert_conditions() -> Dict[str, AlertCondition]:
    """Get default alert conditions for log processing system"""
    return {
        'high_error_rate': AlertCondition(
            name='High Error Rate',
            threshold=5.0,  # 5% error rate
            metric_key='error_rate',
            severity=AlertSeverity.ERROR,
            cooldown_minutes=30,
            notification_channels=['email', 'slack']
        ),
        'critical_error_rate': AlertCondition(
            name='Critical Error Rate',
            threshold=10.0,  # 10% error rate
            metric_key='error_rate',
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=15,
            notification_channels=['email', 'slack', 'pagerduty']
        ),
        'slow_response_time': AlertCondition(
            name='Slow Response Time',
            threshold=1000.0,  # 1000ms response time
            metric_key='response_time_ms',
            severity=AlertSeverity.WARNING,
            cooldown_minutes=45,
            notification_channels=['email']
        ),
        'high_request_volume': AlertCondition(
            name='High Request Volume',
            threshold=1000.0,  # 1000 requests per second
            metric_key='requests_per_second',
            severity=AlertSeverity.WARNING,
            cooldown_minutes=60,
            notification_channels=['email']
        )
    }

def get_default_report_configs() -> Dict[str, ReportConfig]:
    """Get default report configurations"""
    return {
        'daily_summary': ReportConfig(
            title='Daily System Performance Report',
            description='Comprehensive overview of system metrics and performance for the last 24 hours',
            metrics=['requests_per_second', 'error_rate', 'response_time_ms'],
            time_range_hours=24,
            chart_types=['line', 'bar'],
            recipients=['ops-team@company.com', 'dev-team@company.com']
        ),
        'weekly_executive': ReportConfig(
            title='Weekly Executive Summary',
            description='High-level system performance summary for executive stakeholders',
            metrics=['requests_per_second', 'error_rate'],
            time_range_hours=168,  # 7 days
            chart_types=['line', 'pie'],
            recipients=['executives@company.com', 'product-team@company.com']
        )
    }
