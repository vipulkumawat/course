"""Pattern matching engine for log analysis."""
import re
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import structlog
from config.database import Alert, LogEntry, AlertRule, get_db
from config.settings import settings
from sqlalchemy.exc import IntegrityError

logger = structlog.get_logger()

class PatternMatcher:
    def __init__(self):
        self.patterns = {}
        self.load_patterns()
    
    def load_patterns(self):
        """Load patterns from database and configuration."""
        db = next(get_db())
        try:
            # Load from database
            rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()
            for rule in rules:
                self.patterns[rule.name] = {
                    'pattern': re.compile(rule.pattern, re.IGNORECASE),
                    'threshold': rule.threshold,
                    'window': rule.window_seconds,
                    'severity': rule.severity
                }
            
            # Load default patterns if none in database
            if not self.patterns:
                for name, config in settings.DEFAULT_PATTERNS.items():
                    self.patterns[name] = {
                        'pattern': re.compile(config['pattern'], re.IGNORECASE),
                        'threshold': config['threshold'],
                        'window': config['window'],
                        'severity': config['severity']
                    }
                    
                    # Save to database
                    rule = AlertRule(
                        name=name,
                        pattern=config['pattern'],
                        threshold=config['threshold'],
                        window_seconds=config['window'],
                        severity=config['severity']
                    )
                    db.add(rule)
                db.commit()
                
        finally:
            db.close()
    
    async def analyze_log(self, log_entry: LogEntry) -> List[Dict]:
        """Analyze a log entry against all patterns."""
        matches = []
        
        for pattern_name, config in self.patterns.items():
            if config['pattern'].search(log_entry.message):
                matches.append({
                    'pattern_name': pattern_name,
                    'severity': config['severity'],
                    'threshold': config['threshold'],
                    'window': config['window'],
                    'log_entry': log_entry
                })
                
                logger.info("Pattern matched", 
                           pattern=pattern_name, 
                           log_id=log_entry.id,
                           message=log_entry.message[:100])
        
        return matches
    
    async def check_threshold(self, pattern_name: str, window: int) -> int:
        """Check if pattern matches exceed threshold in time window."""
        db = next(get_db())
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=window)
            
            # Count recent logs matching this pattern
            count = db.query(LogEntry).filter(
                LogEntry.timestamp >= cutoff_time,
                LogEntry.message.op('~*')(self.patterns[pattern_name]['pattern'].pattern)
            ).count()
            
            return count
        finally:
            db.close()

    def add_pattern(self, name: str, pattern: str, threshold: int, window: int, severity: str):
        """Add a new pattern to the matcher."""
        self.patterns[name] = {
            'pattern': re.compile(pattern, re.IGNORECASE),
            'threshold': threshold,
            'window': window,
            'severity': severity
        }
        
        # Save to database
        db = next(get_db())
        try:
            rule = AlertRule(
                name=name,
                pattern=pattern,
                threshold=threshold,
                window_seconds=window,
                severity=severity
            )
            db.add(rule)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                logger.warning(f"Pattern with name '{name}' already exists in the database.")
        finally:
            db.close()
