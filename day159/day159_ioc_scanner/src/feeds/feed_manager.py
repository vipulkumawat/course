import aiohttp
import asyncio
from typing import List
from datetime import datetime
import re
import structlog
from src.scanner.models import IOCIndicator, IOCType, Severity

logger = structlog.get_logger()

class ThreatFeedManager:
    """Manages threat intelligence feed downloads and parsing"""
    
    def __init__(self, feed_urls: List[str]):
        self.feed_urls = feed_urls
        self.last_update = None
        self.stats = {
            "feeds_processed": 0,
            "iocs_extracted": 0,
            "errors": 0
        }
    
    async def fetch_feed(self, url: str) -> str:
        """Fetch threat feed content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info("Feed fetched successfully", url=url, size=len(content))
                        return content
                    else:
                        logger.warning("Feed fetch failed", url=url, status=response.status)
                        self.stats["errors"] += 1
                        return ""
        except Exception as e:
            logger.error("Feed fetch error", url=url, error=str(e))
            self.stats["errors"] += 1
            return ""
    
    def parse_ip_feed(self, content: str, source: str) -> List[IOCIndicator]:
        """Parse IP address feed"""
        iocs = []
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        
        for line in content.split('\n'):
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            # Extract IP addresses
            ips = ip_pattern.findall(line)
            for ip in ips:
                iocs.append(IOCIndicator(
                    value=ip,
                    ioc_type=IOCType.IP_ADDRESS,
                    severity=Severity.MEDIUM,
                    source=source,
                    description="Malicious IP from threat feed",
                    confidence=0.8
                ))
        
        logger.info("Parsed IP feed", source=source, count=len(iocs))
        return iocs
    
    async def update_feeds(self) -> List[IOCIndicator]:
        """Update all threat feeds"""
        all_iocs = []
        
        for url in self.feed_urls:
            content = await self.fetch_feed(url)
            if content:
                # Simple IP feed parsing (can be extended for other types)
                source = url.split('/')[-1]
                iocs = self.parse_ip_feed(content, source)
                all_iocs.extend(iocs)
                self.stats["feeds_processed"] += 1
        
        self.stats["iocs_extracted"] = len(all_iocs)
        self.last_update = datetime.now()
        
        logger.info("Feed update complete", 
                   feeds=self.stats["feeds_processed"],
                   iocs=len(all_iocs))
        
        return all_iocs
    
    def get_stats(self) -> dict:
        """Get feed manager statistics"""
        return {
            **self.stats,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
