from typing import Dict, List, Optional
from datetime import datetime

class QueryGenerator:
    """Generates SQL queries from parsed intent and entities"""
    
    def __init__(self, table_name: str = "logs"):
        self.table_name = table_name
        self.query_templates = {
            'search': self._generate_search_query,
            'count': self._generate_count_query,
            'aggregate': self._generate_aggregate_query,
            'compare': self._generate_compare_query,
            'investigate': self._generate_investigate_query
        }
    
    def generate(self, intent: str, entities: Dict[str, any]) -> str:
        """Generate SQL query based on intent and entities"""
        generator = self.query_templates.get(intent, self._generate_search_query)
        return generator(entities)
    
    def _generate_search_query(self, entities: Dict[str, any]) -> str:
        """Generate search query"""
        query = f"SELECT * FROM {self.table_name} WHERE 1=1"
        
        # Add time range filter
        if 'time_range' in entities:
            time_range = entities['time_range']
            query += f" AND timestamp >= '{time_range['start'].isoformat()}'"
            query += f" AND timestamp <= '{time_range['end'].isoformat()}'"
        
        # Add log level filter
        if 'log_level' in entities:
            query += f" AND level = '{entities['log_level']}'"
        
        # Add service filter
        if 'service' in entities:
            query += f" AND service = '{entities['service']}'"
        
        # Add field filters with quoted values
        if 'fields' in entities and '_quoted' in entities.get('values', {}):
            for field, value in zip(entities['fields'], entities['values']['_quoted']):
                query += f" AND {field} LIKE '%{value}%'"
        
        # Add search term filters - search in message field if no specific fields mentioned
        if '_search_terms' in entities.get('values', {}):
            search_terms = entities['values']['_search_terms']
            if search_terms:
                # If specific fields are mentioned, search in those
                if 'fields' in entities and entities['fields']:
                    for field in entities['fields']:
                        for term in search_terms:
                            query += f" AND {field} LIKE '%{term}%'"
                else:
                    # Default to searching in message field
                    for term in search_terms:
                        query += f" AND message LIKE '%{term}%'"
        
        query += " ORDER BY timestamp DESC LIMIT 100"
        return query
    
    def _generate_count_query(self, entities: Dict[str, any]) -> str:
        """Generate count query"""
        query = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE 1=1"
        
        if 'time_range' in entities:
            time_range = entities['time_range']
            query += f" AND timestamp >= '{time_range['start'].isoformat()}'"
            query += f" AND timestamp <= '{time_range['end'].isoformat()}'"
        
        if 'log_level' in entities:
            query += f" AND level = '{entities['log_level']}'"
        
        if 'service' in entities:
            query += f" AND service = '{entities['service']}'"
        
        return query
    
    def _generate_aggregate_query(self, entities: Dict[str, any]) -> str:
        """Generate aggregate query"""
        group_by = entities.get('service', 'level')
        query = f"SELECT {group_by}, COUNT(*) as count FROM {self.table_name} WHERE 1=1"
        
        if 'time_range' in entities:
            time_range = entities['time_range']
            query += f" AND timestamp >= '{time_range['start'].isoformat()}'"
            query += f" AND timestamp <= '{time_range['end'].isoformat()}'"
        
        query += f" GROUP BY {group_by} ORDER BY count DESC LIMIT 20"
        return query
    
    def _generate_compare_query(self, entities: Dict[str, any]) -> str:
        """Generate comparison query"""
        # For now, return a simple search query
        return self._generate_search_query(entities)
    
    def _generate_investigate_query(self, entities: Dict[str, any]) -> str:
        """Generate investigation query (errors with context)"""
        query = f"SELECT * FROM {self.table_name} WHERE level IN ('error', 'warn')"
        
        if 'time_range' in entities:
            time_range = entities['time_range']
            query += f" AND timestamp >= '{time_range['start'].isoformat()}'"
            query += f" AND timestamp <= '{time_range['end'].isoformat()}'"
        
        if 'service' in entities:
            query += f" AND service = '{entities['service']}'"
        
        query += " ORDER BY timestamp DESC LIMIT 50"
        return query
