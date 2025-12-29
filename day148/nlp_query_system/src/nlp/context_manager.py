from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class ContextManager:
    """Manages conversation context for multi-turn queries"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.local_contexts = {}  # Fallback to local storage
        self.context_ttl = 600  # 10 minutes
    
    def save_context(self, session_id: str, context: Dict) -> None:
        """Save conversation context"""
        context['timestamp'] = datetime.now().isoformat()
        
        if self.redis_client:
            self.redis_client.setex(
                f"nlp:context:{session_id}",
                self.context_ttl,
                json.dumps(context)
            )
        else:
            self.local_contexts[session_id] = context
    
    def get_context(self, session_id: str) -> Optional[Dict]:
        """Retrieve conversation context"""
        if self.redis_client:
            data = self.redis_client.get(f"nlp:context:{session_id}")
            if data:
                return json.loads(data)
        else:
            context = self.local_contexts.get(session_id)
            if context:
                # Check if context is still valid
                timestamp = datetime.fromisoformat(context['timestamp'])
                if datetime.now() - timestamp < timedelta(seconds=self.context_ttl):
                    return context
                else:
                    del self.local_contexts[session_id]
        
        return None
    
    def merge_context(self, current_entities: Dict, previous_context: Dict) -> Dict:
        """Merge current query with previous context"""
        merged = previous_context.get('entities', {}).copy()
        merged.update(current_entities)
        return merged
