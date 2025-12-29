from typing import Dict, List, Optional
from .intent_parser import IntentParser, ParsedIntent
from .entity_extractor import EntityExtractor
from .query_generator import QueryGenerator
from .context_manager import ContextManager
from .response_formatter import ResponseFormatter

class NLPQueryService:
    """Main NLP query processing service"""
    
    def __init__(self, schema_fields: List[str], redis_client=None):
        self.intent_parser = IntentParser()
        self.entity_extractor = EntityExtractor(schema_fields)
        self.query_generator = QueryGenerator()
        self.context_manager = ContextManager(redis_client)
        self.response_formatter = ResponseFormatter()
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict:
        """Process natural language query end-to-end"""
        
        # Step 1: Parse intent
        parsed_intent = self.intent_parser.parse(query)
        
        # Step 2: Extract entities
        entities = self.entity_extractor.extract(query)
        
        # Step 3: Merge with context if available
        if session_id:
            previous_context = self.context_manager.get_context(session_id)
            if previous_context:
                entities = self.context_manager.merge_context(entities, previous_context)
        
        # Step 4: Generate SQL query
        sql_query = self.query_generator.generate(parsed_intent.intent, entities)
        
        # Step 5: Save context for future queries
        if session_id:
            self.context_manager.save_context(session_id, {
                'intent': parsed_intent.intent,
                'entities': entities,
                'sql_query': sql_query
            })
        
        return {
            'intent': parsed_intent.intent,
            'confidence': parsed_intent.confidence,
            'entities': entities,
            'sql_query': sql_query,
            'needs_clarification': parsed_intent.confidence < 0.6
        }
    
    def format_results(self, intent: str, results: List[Dict], entities: Dict, query: str) -> Dict:
        """Format query results"""
        return self.response_formatter.format(intent, results, entities, query)
