from typing import Dict, List, Any
from datetime import datetime
import hashlib
import json
import os

class EvidenceEntry:
    def __init__(self, evidence_id: str, log_event: Dict[str, Any],
                 compliance_matches: List[Dict[str, Any]], 
                 collected_at: datetime):
        self.evidence_id = evidence_id
        self.log_event = log_event
        self.compliance_matches = compliance_matches
        self.collected_at = collected_at
        self.integrity_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute integrity hash for tamper detection"""
        data = json.dumps({
            "evidence_id": self.evidence_id,
            "log_event": self.log_event,
            "compliance_matches": self.compliance_matches,
            "collected_at": self.collected_at.isoformat()
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify evidence hasn't been tampered with"""
        current_hash = self._compute_hash()
        return current_hash == self.integrity_hash
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "log_event": self.log_event,
            "compliance_matches": self.compliance_matches,
            "collected_at": self.collected_at.isoformat(),
            "integrity_hash": self.integrity_hash
        }

class EvidenceCollector:
    def __init__(self, storage_path: str = "data/evidence"):
        self.storage_path = storage_path
        self.evidence_store: List[EvidenceEntry] = []
        self.evidence_index: Dict[str, List[str]] = {}
        os.makedirs(storage_path, exist_ok=True)
        # Load existing evidence from disk
        self._load_existing_evidence()
    
    def collect(self, log_event: Dict[str, Any], 
                compliance_matches: List[Dict[str, Any]]) -> str:
        """Collect evidence for compliance"""
        evidence_id = f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.evidence_store)}"
        
        entry = EvidenceEntry(
            evidence_id=evidence_id,
            log_event=log_event,
            compliance_matches=compliance_matches,
            collected_at=datetime.now()
        )
        
        self.evidence_store.append(entry)
        
        # Index by framework and requirement
        for match in compliance_matches:
            framework = match["framework"]
            req_id = match["requirement_id"]
            key = f"{framework}:{req_id}"
            
            if key not in self.evidence_index:
                self.evidence_index[key] = []
            self.evidence_index[key].append(evidence_id)
        
        # Persist to disk
        self._persist_evidence(entry)
        
        return evidence_id
    
    def _persist_evidence(self, entry: EvidenceEntry):
        """Persist evidence to disk"""
        filename = f"{entry.evidence_id}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)
    
    def _load_existing_evidence(self):
        """Load existing evidence from disk"""
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json') and filename.startswith('EVD-'):
                filepath = os.path.join(self.storage_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Recreate EvidenceEntry from saved data
                    from dateutil import parser
                    collected_at = parser.parse(data['collected_at'])
                    
                    entry = EvidenceEntry(
                        evidence_id=data['evidence_id'],
                        log_event=data['log_event'],
                        compliance_matches=data['compliance_matches'],
                        collected_at=collected_at
                    )
                    
                    # Restore integrity hash
                    entry.integrity_hash = data.get('integrity_hash', entry.integrity_hash)
                    
                    self.evidence_store.append(entry)
                    
                    # Rebuild index
                    for match in data['compliance_matches']:
                        framework = match["framework"]
                        req_id = match["requirement_id"]
                        key = f"{framework}:{req_id}"
                        
                        if key not in self.evidence_index:
                            self.evidence_index[key] = []
                        if entry.evidence_id not in self.evidence_index[key]:
                            self.evidence_index[key].append(entry.evidence_id)
                            
                except Exception as e:
                    # Skip corrupted files
                    print(f"Warning: Could not load evidence file {filename}: {e}")
                    continue
    
    def get_evidence_by_requirement(self, framework: str, 
                                   requirement_id: str, 
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve evidence for specific requirement"""
        key = f"{framework}:{requirement_id}"
        evidence_ids = self.evidence_index.get(key, [])[:limit]
        
        evidence_list = []
        for evidence_id in evidence_ids:
            for entry in self.evidence_store:
                if entry.evidence_id == evidence_id:
                    evidence_list.append(entry.to_dict())
                    break
        
        return evidence_list
    
    def get_evidence_count(self, framework: str, requirement_id: str) -> int:
        """Get count of evidence for requirement"""
        key = f"{framework}:{requirement_id}"
        return len(self.evidence_index.get(key, []))
    
    def verify_all_integrity(self) -> Dict[str, Any]:
        """Verify integrity of all stored evidence"""
        total = len(self.evidence_store)
        verified = sum(1 for entry in self.evidence_store if entry.verify_integrity())
        
        return {
            "total_evidence": total,
            "verified_evidence": verified,
            "integrity_status": "PASS" if verified == total else "FAIL",
            "verification_timestamp": datetime.now().isoformat()
        }
