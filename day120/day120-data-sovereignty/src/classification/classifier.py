"""Data classification engine for sovereignty tagging"""
import re
import json
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class DataSensitivity(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class RegulatoryFramework(Enum):
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    LGPD = "lgpd"

class DataClassifier:
    def __init__(self):
        # PII patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        self.credit_card_pattern = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
        self.ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        
        # Region to regulatory framework mapping
        self.region_regulations = {
            'EU': [RegulatoryFramework.GDPR],
            'UK': [RegulatoryFramework.GDPR],
            'US-CA': [RegulatoryFramework.CCPA],
            'US': [RegulatoryFramework.HIPAA],
            'BR': [RegulatoryFramework.LGPD]
        }
    
    def classify_log(self, log_data: Dict) -> Dict:
        """Classify log entry with sovereignty metadata"""
        classification = {
            'timestamp': datetime.utcnow().isoformat(),
            'log_id': log_data.get('id', 'unknown'),
            'sensitivity': self._determine_sensitivity(log_data),
            'contains_pii': self._detect_pii(log_data),
            'data_subject_location': self._extract_location(log_data),
            'applicable_regulations': [],
            'required_encryption': False,
            'cross_border_allowed': True
        }
        
        # Determine applicable regulations
        location = classification['data_subject_location']
        if location in self.region_regulations:
            classification['applicable_regulations'] = [
                reg.value for reg in self.region_regulations[location]
            ]
        
        # Set encryption requirement
        if classification['contains_pii'] or classification['sensitivity'] in [
            DataSensitivity.CONFIDENTIAL.value, DataSensitivity.RESTRICTED.value
        ]:
            classification['required_encryption'] = True
        
        # Determine cross-border transfer rules
        if RegulatoryFramework.GDPR.value in classification['applicable_regulations']:
            classification['cross_border_allowed'] = False
        
        return classification
    
    def _determine_sensitivity(self, log_data: Dict) -> str:
        """Determine data sensitivity level"""
        content = json.dumps(log_data).lower()
        
        if any(term in content for term in ['password', 'secret', 'token', 'key']):
            return DataSensitivity.RESTRICTED.value
        
        if any(term in content for term in ['health', 'medical', 'diagnosis', 'patient']):
            return DataSensitivity.CONFIDENTIAL.value
        
        if any(term in content for term in ['internal', 'confidential', 'proprietary']):
            return DataSensitivity.CONFIDENTIAL.value
        
        if self._detect_pii(log_data):
            return DataSensitivity.CONFIDENTIAL.value
        
        return DataSensitivity.INTERNAL.value
    
    def _detect_pii(self, log_data: Dict) -> bool:
        """Detect presence of PII in log data"""
        content = json.dumps(log_data)
        
        return bool(
            self.email_pattern.search(content) or
            self.ssn_pattern.search(content) or
            self.credit_card_pattern.search(content)
        )
    
    def _extract_location(self, log_data: Dict) -> str:
        """Extract data subject location"""
        # Check for explicit location field
        if 'user_location' in log_data:
            return log_data['user_location']
        
        # Check for IP-based geolocation
        if 'ip_address' in log_data:
            ip = log_data['ip_address']
            # Simplified location mapping
            if ip.startswith('192.168'):
                return 'US'  # Private IP, default
            # In production, use GeoIP2 database
            return self._geolocate_ip(ip)
        
        return 'UNKNOWN'
    
    def _geolocate_ip(self, ip: str) -> str:
        """Geolocate IP address to region"""
        # Simplified mapping for demo
        ip_regions = {
            '185.': 'EU',
            '203.': 'APAC',
            '200.': 'BR',
            '41.': 'AFRICA'
        }
        
        for prefix, region in ip_regions.items():
            if ip.startswith(prefix):
                return region
        
        return 'US'  # Default
