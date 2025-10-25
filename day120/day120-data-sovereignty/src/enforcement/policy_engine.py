"""Policy enforcement engine for data sovereignty"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class EnforcementAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ANONYMIZE = "anonymize"
    QUARANTINE = "quarantine"

@dataclass
class RegionPolicy:
    region_code: str
    allowed_data_subjects: List[str]
    prohibited_transfers: List[str]
    encryption_required: bool
    retention_days: int
    anonymization_required: bool = False

class PolicyEngine:
    def __init__(self):
        self.policies = self._load_default_policies()
    
    def _load_default_policies(self) -> Dict[str, RegionPolicy]:
        """Load default sovereignty policies per region"""
        return {
            'eu-west-1': RegionPolicy(
                region_code='eu-west-1',
                allowed_data_subjects=['EU', 'UK', 'UNKNOWN'],
                prohibited_transfers=['US', 'CN', 'RU'],
                encryption_required=True,
                retention_days=90
            ),
            'us-east-1': RegionPolicy(
                region_code='us-east-1',
                allowed_data_subjects=['US', 'CA', 'UNKNOWN'],
                prohibited_transfers=['EU', 'CN', 'RU'],
                encryption_required=True,
                retention_days=365
            ),
            'ap-south-1': RegionPolicy(
                region_code='ap-south-1',
                allowed_data_subjects=['IN', 'APAC', 'UNKNOWN'],
                prohibited_transfers=['CN', 'PK'],
                encryption_required=True,
                retention_days=180
            ),
            'sa-east-1': RegionPolicy(
                region_code='sa-east-1',
                allowed_data_subjects=['BR', 'AR', 'CL', 'UNKNOWN'],
                prohibited_transfers=['US', 'EU', 'CN'],
                encryption_required=True,
                retention_days=120
            )
        }
    
    def validate_storage(self, classification: Dict, target_region: str) -> Dict:
        """Validate if log can be stored in target region"""
        policy = self.policies.get(target_region)
        
        if not policy:
            return {
                'allowed': False,
                'action': EnforcementAction.DENY.value,
                'reason': f'No policy defined for region {target_region}'
            }
        
        data_subject = classification.get('data_subject_location', 'UNKNOWN')
        
        # Check if data subject is allowed in this region
        if data_subject not in policy.allowed_data_subjects:
            return {
                'allowed': False,
                'action': EnforcementAction.DENY.value,
                'reason': f'Data subject {data_subject} not allowed in {target_region}'
            }
        
        # Check encryption requirement
        if policy.encryption_required and not classification.get('required_encryption'):
            return {
                'allowed': False,
                'action': EnforcementAction.DENY.value,
                'reason': 'Encryption required but not enabled'
            }
        
        return {
            'allowed': True,
            'action': EnforcementAction.ALLOW.value,
            'reason': 'Compliant with region policy',
            'retention_days': policy.retention_days
        }
    
    def validate_transfer(self, classification: Dict, source_region: str, 
                         target_region: str) -> Dict:
        """Validate cross-border data transfer"""
        source_policy = self.policies.get(source_region)
        
        if not source_policy:
            return {
                'allowed': False,
                'action': EnforcementAction.DENY.value,
                'reason': f'No policy for source region {source_region}'
            }
        
        # Extract region code from target
        target_location = target_region.split('-')[0].upper()
        
        # Check if transfer is prohibited
        if target_location in source_policy.prohibited_transfers:
            # Check if anonymization allows transfer
            if classification.get('contains_pii'):
                return {
                    'allowed': True,
                    'action': EnforcementAction.ANONYMIZE.value,
                    'reason': 'Transfer allowed with anonymization',
                    'required_anonymization': ['email', 'ip_address', 'user_id']
                }
            return {
                'allowed': False,
                'action': EnforcementAction.DENY.value,
                'reason': f'Transfer to {target_location} prohibited by policy'
            }
        
        return {
            'allowed': True,
            'action': EnforcementAction.ALLOW.value,
            'reason': 'Cross-border transfer permitted'
        }
