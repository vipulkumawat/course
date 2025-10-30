"""Windows Event Log Collection Agent"""
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path

# Conditional Windows imports
try:
    import win32evtlog
    import win32api
    import win32con
    import wmi
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    # Mock for testing on non-Windows systems
    class MockWin32:
        @staticmethod
        def OpenEventLog(server, source):
            return 1
        @staticmethod
        def ReadEventLog(handle, flags, offset):
            return []
        @staticmethod
        def CloseEventLog(handle):
            pass
    
    win32evtlog = MockWin32()
    win32api = MockWin32()
    win32con = type('obj', (object,), {
        'EVENTLOG_BACKWARDS_READ': 1,
        'EVENTLOG_SEQUENTIAL_READ': 2
    })

from config.agent_config import config
from monitoring.metrics import EVENTS_COLLECTED, ERRORS_TOTAL, LAST_COLLECTION_TIMESTAMP
from web.dashboard_app import broadcast_event  # for real-time UI updates

logger = logging.getLogger(__name__)

class WindowsEventAgent:
    """Main Windows Event Log collection agent"""
    
    def __init__(self, event_callback: Optional[Callable] = None):
        self.config = config
        self.event_callback = event_callback
        self.active_subscriptions = {}
        self.is_running = False
        self.bookmarks = {}
        self.stats = {
            'events_collected': 0,
            'events_sent': 0,
            'errors': 0,
            'last_collection_time': None
        }
        
    async def initialize(self):
        """Initialize the agent and prepare for collection"""
        logger.info("Initializing Windows Event Log Agent")
        
        # Create necessary directories
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
        Path("data/bookmarks").mkdir(parents=True, exist_ok=True)
        Path("data/state").mkdir(parents=True, exist_ok=True)
        
        # Load bookmarks for resume capability
        await self._load_bookmarks()
        
        # Check Windows availability
        if not WINDOWS_AVAILABLE:
            logger.warning("Windows APIs not available - using mock mode for testing")
        
        logger.info(f"Agent initialized for {len(self.config.channels)} channels")
        
    async def start_collection(self):
        """Start collecting events from all configured channels"""
        logger.info("Starting event collection")
        self.is_running = True
        
        # Start collection for each channel
        tasks = []
        for channel in self.config.channels:
            task = asyncio.create_task(self._collect_channel_events(channel))
            tasks.append(task)
            self.active_subscriptions[channel] = task
            
        # Start health monitoring
        health_task = asyncio.create_task(self._health_monitor())
        tasks.append(health_task)
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Collection error: {e}")
            await self.stop_collection()
            
    async def stop_collection(self):
        """Stop event collection gracefully"""
        logger.info("Stopping event collection")
        self.is_running = False
        
        # Cancel all active subscriptions
        for channel, task in self.active_subscriptions.items():
            if not task.done():
                task.cancel()
                
        # Save bookmarks before shutdown
        await self._save_bookmarks()
        
        logger.info("Event collection stopped")
        
    async def _collect_channel_events(self, channel: str):
        """Collect events from a specific channel"""
        logger.info(f"Starting collection for channel: {channel}")
        
        while self.is_running:
            try:
                events = await self._read_channel_events(channel)
                
                if events:
                    logger.debug(f"Collected {len(events)} events from {channel}")
                    await self._process_events(channel, events)
                    
                # Wait before next collection cycle
                await asyncio.sleep(self.config.batch_timeout_seconds)
                
            except Exception as e:
                logger.error(f"Error collecting from {channel}: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(5)  # Wait before retry
                
    async def _read_channel_events(self, channel: str) -> List[Dict]:
        """Read events from Windows Event Log channel"""
        events = []
        
        try:
            if WINDOWS_AVAILABLE:
                # Open event log
                handle = win32evtlog.OpenEventLog(None, channel)
                
                # Read events
                flags = win32con.EVENTLOG_BACKWARDS_READ | win32con.EVENTLOG_SEQUENTIAL_READ
                raw_events = win32evtlog.ReadEventLog(handle, flags, 0)
                
                # Convert to structured format
                for raw_event in raw_events[-self.config.max_events_per_batch:]:
                    event = await self._parse_event(raw_event, channel)
                    if event:
                        events.append(event)
                        
                win32evtlog.CloseEventLog(handle)
                
            else:
                # Mock events for testing
                events = await self._generate_mock_events(channel)
                
        except Exception as e:
            logger.error(f"Error reading {channel} events: {e}")
            
        return events
        
    async def _parse_event(self, raw_event, channel: str) -> Optional[Dict]:
        """Parse raw Windows event into structured format"""
        try:
            # Extract event fields
            if WINDOWS_AVAILABLE and hasattr(raw_event, 'EventID'):
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'channel': channel,
                    'event_id': raw_event.EventID,
                    'level': self._get_event_level(raw_event.EventType),
                    'source': getattr(raw_event, 'SourceName', 'Unknown'),
                    'computer': getattr(raw_event, 'ComputerName', 'localhost'),
                    'message': str(raw_event.StringInserts) if raw_event.StringInserts else '',
                    'raw_data': str(raw_event.Data) if raw_event.Data else None,
                    'record_number': raw_event.RecordNumber,
                    'user_sid': raw_event.Sid.GetAccountName()[0] if raw_event.Sid else None
                }
            else:
                # Mock event structure
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'channel': channel,
                    'event_id': 1000,
                    'level': 'Information',
                    'source': 'TestSource',
                    'computer': 'test-machine',
                    'message': f'Mock event from {channel}',
                    'raw_data': None,
                    'record_number': self.stats['events_collected'] + 1,
                    'user_sid': None
                }
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None
            
    def _get_event_level(self, event_type) -> str:
        """Convert Windows event type to level string"""
        level_map = {
            1: "Error",
            2: "Warning", 
            4: "Information",
            8: "Success",
            16: "Failure"
        }
        return level_map.get(event_type, "Unknown")
        
    async def _generate_mock_events(self, channel: str) -> List[Dict]:
        """Generate mock events for testing on non-Windows systems"""
        import random
        
        mock_events = []
        num_events = random.randint(1, 5)
        
        for i in range(num_events):
            event = {
                'timestamp': datetime.now().isoformat(),
                'channel': channel,
                'event_id': random.randint(1000, 9999),
                'level': random.choice(['Information', 'Warning', 'Error']),
                'source': f'Mock-{channel}-Source',
                'computer': 'mock-windows-machine',
                'message': f'Mock event {i+1} from {channel} channel',
                'raw_data': f'mock_data_{i}',
                'record_number': self.stats['events_collected'] + i + 1,
                'user_sid': 'S-1-5-21-mock-user'
            }
            mock_events.append(event)
            
        return mock_events
        
    async def _process_events(self, channel: str, events: List[Dict]):
        """Process collected events"""
        for event in events:
            try:
                # Update statistics
                self.stats['events_collected'] += 1
                self.stats['last_collection_time'] = datetime.now().isoformat()
                # Metrics
                EVENTS_COLLECTED.inc()
                LAST_COLLECTION_TIMESTAMP.set_to_current_time()
                
                # Send to callback if provided
                if self.event_callback:
                    await self.event_callback(event)
                    self.stats['events_sent'] += 1

                # Broadcast to dashboard WebSocket clients
                try:
                    await broadcast_event({
                        **event,
                        'channel': channel
                    })
                except Exception as broadcast_error:
                    logger.debug(f"Broadcast failed (non-fatal): {broadcast_error}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                self.stats['errors'] += 1
                ERRORS_TOTAL.inc()
                
    async def _health_monitor(self):
        """Monitor agent health and performance"""
        while self.is_running:
            try:
                logger.info(f"Agent Stats: {self.stats}")
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)
                
    async def _load_bookmarks(self):
        """Load event bookmarks for resume capability"""
        try:
            bookmark_file = Path(self.config.bookmark_file)
            if bookmark_file.exists():
                with open(bookmark_file, 'r') as f:
                    self.bookmarks = json.load(f)
                logger.info(f"Loaded bookmarks for {len(self.bookmarks)} channels")
        except Exception as e:
            logger.warning(f"Could not load bookmarks: {e}")
            
    async def _save_bookmarks(self):
        """Save event bookmarks for resume capability"""
        try:
            bookmark_file = Path(self.config.bookmark_file)
            bookmark_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(bookmark_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
                
            logger.info("Bookmarks saved successfully")
        except Exception as e:
            logger.error(f"Could not save bookmarks: {e}")
            
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return self.stats.copy()
