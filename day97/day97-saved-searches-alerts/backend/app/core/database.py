"""
Database configuration and initialization
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
import sqlite3
import os
import logging

from models.schemas import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saved_searches_alerts.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Enable foreign keys for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def init_db():
    """Initialize database tables"""
    try:
        logger.info("🗄️  Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized successfully")
        
        # Insert sample data
        await insert_sample_data()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def insert_sample_data():
    """Insert sample searches and alerts for demonstration"""
    db = SessionLocal()
    try:
        from models.schemas import SavedSearch, Alert
        
        # Check if sample data already exists
        if db.query(SavedSearch).first():
            logger.info("📊 Sample data already exists")
            return
        
        # Sample saved searches
        sample_searches = [
            SavedSearch(
                name="Error Rate Monitoring",
                description="Monitor error rates across all services",
                user_id="demo_user",
                query_params={
                    "query_text": "level:ERROR",
                    "time_range": {"last": "1h"},
                    "filters": {},
                    "service_filters": [],
                    "log_level_filters": ["ERROR"],
                    "sort_by": "timestamp",
                    "sort_order": "desc",
                    "limit": 100
                },
                visualization_config={
                    "chart_type": "line",
                    "x_axis": "timestamp",
                    "y_axis": "count",
                    "time_granularity": "minute"
                },
                folder="monitoring",
                tags=["error", "monitoring", "ops"]
            ),
            SavedSearch(
                name="Database Performance",
                description="Database query performance and slow queries",
                user_id="demo_user",
                query_params={
                    "query_text": "service:database AND duration:>1000",
                    "time_range": {"last": "6h"},
                    "filters": {"duration": {"gt": 1000}},
                    "service_filters": ["database"],
                    "log_level_filters": ["INFO", "WARN"],
                    "sort_by": "duration",
                    "sort_order": "desc",
                    "limit": 50
                },
                visualization_config={
                    "chart_type": "bar",
                    "x_axis": "query_type",
                    "y_axis": "avg_duration",
                    "grouping": "service"
                },
                folder="performance",
                tags=["database", "performance", "slow-queries"]
            ),
            SavedSearch(
                name="User Authentication Events",
                description="Track user login/logout and authentication failures",
                user_id="demo_user",
                query_params={
                    "query_text": "service:auth AND (event:login OR event:logout OR event:auth_failure)",
                    "time_range": {"last": "24h"},
                    "filters": {"event": {"in": ["login", "logout", "auth_failure"]}},
                    "service_filters": ["auth"],
                    "log_level_filters": ["INFO", "WARN", "ERROR"],
                    "sort_by": "timestamp",
                    "sort_order": "desc",
                    "limit": 200
                },
                folder="security",
                tags=["auth", "security", "users"],
                is_shared=True,
                shared_with=["security_team"]
            )
        ]
        
        for search in sample_searches:
            db.add(search)
        
        db.commit()
        
        # Sample alerts
        search_ids = [s.id for s in db.query(SavedSearch).all()]
        
        sample_alerts = [
            Alert(
                name="High Error Rate Alert",
                description="Alert when error rate exceeds 5% in 5 minutes",
                user_id="demo_user",
                saved_search_id=search_ids[0],
                condition_type="threshold",
                threshold_value="5",
                comparison_operator=">",
                time_window_minutes=5,
                notification_channels=["email", "in_app"],
                notification_emails=["ops@company.com"],
                cooldown_minutes=15
            ),
            Alert(
                name="Database Slow Query Alert",
                description="Alert when query duration exceeds 5 seconds",
                user_id="demo_user",
                saved_search_id=search_ids[1],
                condition_type="threshold",
                threshold_value="5000",
                comparison_operator=">",
                time_window_minutes=10,
                notification_channels=["webhook", "in_app"],
                webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                cooldown_minutes=30
            )
        ]
        
        for alert in sample_alerts:
            db.add(alert)
        
        db.commit()
        logger.info("✅ Sample data inserted successfully")
        
    except Exception as e:
        logger.error(f"❌ Sample data insertion failed: {e}")
        db.rollback()
    finally:
        db.close()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
