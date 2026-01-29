import pytest
import asyncio
from src.feeds.feed_manager import ThreatFeedManager
from src.scanner.models import IOCIndicator

@pytest.mark.asyncio
async def test_feed_manager_initialization():
    """Test feed manager initialization"""
    feed_urls = ["https://example.com/feed.txt"]
    manager = ThreatFeedManager(feed_urls)
    
    assert manager.feed_urls == feed_urls
    assert manager.stats["feeds_processed"] == 0

def test_parse_ip_feed():
    """Test IP feed parsing"""
    manager = ThreatFeedManager([])
    content = "# Comment\n192.168.1.100\n10.0.0.50\n"
    
    iocs = manager.parse_ip_feed(content, "test_source")
    
    assert len(iocs) == 2
    assert all(isinstance(ioc, IOCIndicator) for ioc in iocs)
