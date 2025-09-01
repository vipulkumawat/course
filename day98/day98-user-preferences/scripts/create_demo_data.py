#!/usr/bin/env python3

import asyncio
import json
from backend.src.preferences.models.user import User, UserPreference, PreferenceTemplate
from backend.src.database.connection import SessionLocal, create_tables

async def create_demo_data():
    """Create demo user and preferences"""
    db = SessionLocal()
    
    try:
        # Create tables
        create_tables()
        
        # Create demo user
        demo_user = User(
            username="demo_user",
            email="demo@example.com",
            hashed_password="hashed_password_here"
        )
        db.add(demo_user)
        db.flush()
        
        # Create demo preferences
        preferences = [
            UserPreference(
                user_id=demo_user.id,
                category="dashboard",
                key="auto_refresh",
                value=True
            ),
            UserPreference(
                user_id=demo_user.id,
                category="dashboard",
                key="refresh_interval",
                value=30
            ),
            UserPreference(
                user_id=demo_user.id,
                category="theme",
                key="theme",
                value="light"
            ),
            UserPreference(
                user_id=demo_user.id,
                category="notifications",
                key="email_alerts",
                value=True
            ),
            UserPreference(
                user_id=demo_user.id,
                category="notifications",
                key="sound_enabled",
                value=False
            )
        ]
        
        for pref in preferences:
            db.add(pref)
        
        # Create default templates
        templates = [
            PreferenceTemplate(
                name="Default Dashboard",
                category="dashboard",
                template_data={
                    "auto_refresh": False,
                    "refresh_interval": 60,
                    "items_per_page": 25
                },
                is_system_default=True
            ),
            PreferenceTemplate(
                name="Default Theme",
                category="theme",
                template_data={
                    "theme": "light"
                },
                is_system_default=True
            )
        ]
        
        for template in templates:
            db.add(template)
        
        db.commit()
        print("✅ Demo data created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating demo data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_demo_data())
