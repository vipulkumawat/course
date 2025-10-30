"""Event Transport and Shipping Layer"""
import asyncio
import json
import logging
from typing import Dict, List
from datetime import datetime
import aiohttp
import ssl
from config.agent_config import config
from monitoring.metrics import EVENTS_SENT, ERRORS_TOTAL

logger = logging.getLogger(__name__)

class EventShipper:
    """Handles secure transport of events to central system"""
    
    def __init__(self):
        self.config = config
        self.session = None
        self.batch_buffer = []
        self.stats = {
            'events_sent': 0,
            'batches_sent': 0,
            'failures': 0,
            'last_send_time': None
        }
        
    async def initialize(self):
        """Initialize transport layer"""
        # Create SSL context
        ssl_context = None
        if self.config.enable_tls:
            ssl_context = ssl.create_default_context()
            if not self.config.cert_verify:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
        # Create HTTP session
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=self.config.transport_timeout)
        
        headers = {'Content-Type': 'application/json'}
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
            
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        logger.info("Event transport initialized")
        
    async def ship_event(self, event: Dict):
        """Ship a single event"""
        self.batch_buffer.append(event)
        
        # Check if batch is ready to send
        if (len(self.batch_buffer) >= self.config.max_events_per_batch):
            await self._send_batch()
            
    async def ship_events(self, events: List[Dict]):
        """Ship multiple events"""
        for event in events:
            await self.ship_event(event)
            
    async def flush(self):
        """Force send any buffered events"""
        if self.batch_buffer:
            await self._send_batch()
            
    async def _send_batch(self):
        """Send current batch of events"""
        if not self.batch_buffer:
            return
            
        batch = self.batch_buffer.copy()
        self.batch_buffer.clear()
        
        # Prepare batch payload
        payload = {
            'source': 'windows-event-agent',
            'timestamp': datetime.now().isoformat(),
            'events': batch,
            'batch_size': len(batch),
            'agent_stats': self.stats
        }
        
        # Attempt to send with retries
        for attempt in range(self.config.retry_attempts):
            try:
                await self._send_payload(payload)
                self.stats['events_sent'] += len(batch)
                self.stats['batches_sent'] += 1
                self.stats['last_send_time'] = datetime.now().isoformat()
                EVENTS_SENT.inc(len(batch))
                
                logger.debug(f"Successfully sent batch of {len(batch)} events")
                return
                
            except Exception as e:
                logger.warning(f"Send attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        # All retries failed
        self.stats['failures'] += 1
        logger.error(f"Failed to send batch after {self.config.retry_attempts} attempts")
        ERRORS_TOTAL.inc()
        
        # Could implement dead letter queue here
        await self._handle_failed_batch(batch)
        
    async def _send_payload(self, payload: Dict):
        """Send payload to transport endpoint"""
        if not self.session:
            raise Exception("Transport not initialized")
            
        async with self.session.post(
            self.config.transport_url,
            json=payload
        ) as response:
            response.raise_for_status()
            result = await response.json()
            logger.debug(f"Transport response: {result}")
            
    async def _handle_failed_batch(self, batch: List[Dict]):
        """Handle failed batch - could save to disk or DLQ"""
        try:
            failed_file = f"logs/errors/failed_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(failed_file, 'w') as f:
                json.dump(batch, f, indent=2)
                
            logger.info(f"Saved failed batch to {failed_file}")
        except Exception as e:
            logger.error(f"Could not save failed batch: {e}")
            
    async def close(self):
        """Close transport layer"""
        await self.flush()  # Send any remaining events
        
        if self.session:
            await self.session.close()
            
        logger.info("Event transport closed")
        
    def get_stats(self) -> Dict:
        """Get transport statistics"""
        return self.stats.copy()
