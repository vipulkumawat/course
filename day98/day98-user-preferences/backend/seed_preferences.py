#!/usr/bin/env python3
"""
Database seeding script for default user preferences
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.orm import Session
from src.database.connection import get_db, create_tables
from src.preferences.models.user import PreferenceTemplate
import json

def seed_default_preferences():
    """Seed the database with default preference templates"""
    
    # Create tables if they don't exist
    create_tables()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if templates already exist
        existing_templates = db.query(PreferenceTemplate).count()
        if existing_templates > 0:
            print(f"Found {existing_templates} existing templates. Skipping seeding.")
            return
        
        # Define default preference templates
        default_templates = [
            {
                "name": "Dashboard Defaults",
                "description": "Default dashboard preferences",
                "category": "dashboard",
                "template_data": {
                    "auto_refresh": True,
                    "refresh_interval": 30,
                    "items_per_page": 20
                },
                "is_system_default": True
            },
            {
                "name": "Notifications Defaults", 
                "description": "Default notification preferences",
                "category": "notifications",
                "template_data": {
                    "notifications_enabled": True,
                    "email_alerts": False,
                    "sound_enabled": True
                },
                "is_system_default": True
            },
            {
                "name": "Theme Defaults",
                "description": "Default theme preferences", 
                "category": "theme",
                "template_data": {
                    "theme": "light"
                },
                "is_system_default": True
            },
            {
                "name": "Privacy Defaults",
                "description": "Default privacy and data preferences",
                "category": "privacy", 
                "template_data": {
                    "data_collection": False,
                    "timezone": "UTC",
                    "language": "en"
                },
                "is_system_default": True
            }
        ]
        
        # Insert templates
        for template_data in default_templates:
            template = PreferenceTemplate(**template_data)
            db.add(template)
        
        db.commit()
        print("✅ Successfully seeded default preference templates!")
        print(f"   - Added {len(default_templates)} preference categories")
        print("   - Dashboard: auto_refresh, refresh_interval, items_per_page")
        print("   - Notifications: notifications_enabled, email_alerts, sound_enabled") 
        print("   - Theme: theme")
        print("   - Privacy: data_collection, timezone, language")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding preferences: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding default user preferences...")
    seed_default_preferences()
    print("🎉 Seeding complete!")
