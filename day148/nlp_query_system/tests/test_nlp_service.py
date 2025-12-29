import pytest
from src.nlp.intent_parser import IntentParser
from src.nlp.entity_extractor import EntityExtractor
from src.nlp.query_generator import QueryGenerator
from datetime import datetime, timedelta

def test_intent_parsing():
    parser = IntentParser()
    
    # Test search intent
    result = parser.parse("show me errors from payment service")
    assert result.intent == "search"
    assert result.confidence > 0.5
    
    # Test count intent
    result = parser.parse("how many errors occurred today?")
    assert result.intent == "count"

def test_entity_extraction():
    extractor = EntityExtractor(['timestamp', 'level', 'service', 'message'])
    
    # Test time range extraction
    entities = extractor.extract("show me logs from last 2 hours")
    assert 'time_range' in entities
    time_range = entities['time_range']
    assert isinstance(time_range['start'], datetime)
    assert isinstance(time_range['end'], datetime)
    
    # Test log level extraction
    entities = extractor.extract("find all errors")
    assert entities.get('log_level') == 'error'
    
    # Test service extraction
    entities = extractor.extract("show logs from the payment service")
    assert entities.get('service') == 'payment'

def test_query_generation():
    generator = QueryGenerator()
    
    # Test search query
    entities = {
        'time_range': {
            'start': datetime.now() - timedelta(hours=1),
            'end': datetime.now()
        },
        'log_level': 'error',
        'service': 'payment_service'
    }
    
    query = generator.generate('search', entities)
    assert 'SELECT' in query
    assert 'logs' in query
    assert 'error' in query
    assert 'payment_service' in query
    
    # Test count query
    query = generator.generate('count', entities)
    assert 'COUNT(*)' in query

def test_time_parsing():
    extractor = EntityExtractor([])
    
    test_cases = [
        ("last 30 minutes", 30 * 60),
        ("last 2 hours", 2 * 3600),
        ("last 1 day", 1 * 86400),
    ]
    
    for query, expected_seconds in test_cases:
        entities = extractor.extract(query)
        time_range = entities['time_range']
        duration = (time_range['end'] - time_range['start']).total_seconds()
        assert abs(duration - expected_seconds) < 10  # Allow 10 second tolerance

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
