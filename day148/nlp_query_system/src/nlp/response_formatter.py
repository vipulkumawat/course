from typing import Dict, List, Any
from datetime import datetime

class ResponseFormatter:
    """Formats query results into natural language responses"""
    
    def format(self, intent: str, results: List[Dict], entities: Dict, query: str) -> Dict[str, Any]:
        """Format results based on intent"""
        formatters = {
            'search': self._format_search_results,
            'count': self._format_count_results,
            'aggregate': self._format_aggregate_results,
            'compare': self._format_compare_results,
            'investigate': self._format_investigate_results
        }
        
        formatter = formatters.get(intent, self._format_search_results)
        response = formatter(results, entities)
        
        # Add metadata
        response['metadata'] = {
            'query': query,
            'intent': intent,
            'timestamp': datetime.now().isoformat(),
            'result_count': len(results)
        }
        
        return response
    
    def _format_search_results(self, results: List[Dict], entities: Dict) -> Dict:
        """Format search results"""
        if not results:
            return {
                'message': "No logs found matching your query.",
                'suggestions': ["Try expanding the time range", "Check service name spelling"],
                'results': []
            }
        
        time_range = entities.get('time_range', {})
        time_desc = self._format_time_range(time_range)
        
        message = f"Found {len(results)} logs {time_desc}"
        if 'service' in entities:
            message += f" from {entities['service']} service"
        if 'log_level' in entities:
            message += f" with level {entities['log_level']}"
        
        return {
            'message': message,
            'results': results,
            'suggestions': ["View more details", "Filter by field", "Export results"]
        }
    
    def _format_count_results(self, results: List[Dict], entities: Dict) -> Dict:
        """Format count results"""
        if not results or 'count' not in results[0]:
            count = 0
        else:
            count = results[0]['count']
        
        time_range = entities.get('time_range', {})
        time_desc = self._format_time_range(time_range)
        
        message = f"Found {count} logs {time_desc}"
        if 'service' in entities:
            message += f" from {entities['service']} service"
        if 'log_level' in entities:
            message += f" with level {entities['log_level']}"
        
        return {
            'message': message,
            'count': count,
            'results': [],
            'suggestions': ["Show me these logs", "Break down by service", "Compare with previous period"]
        }
    
    def _format_aggregate_results(self, results: List[Dict], entities: Dict) -> Dict:
        """Format aggregate results"""
        if not results:
            return {
                'message': "No data available for aggregation.",
                'results': []
            }
        
        message = f"Here's the breakdown by {list(results[0].keys())[0]}:"
        
        return {
            'message': message,
            'results': results,
            'suggestions': ["Show details for top item", "Export as CSV"]
        }
    
    def _format_compare_results(self, results: List[Dict], entities: Dict) -> Dict:
        """Format comparison results"""
        return self._format_search_results(results, entities)
    
    def _format_investigate_results(self, results: List[Dict], entities: Dict) -> Dict:
        """Format investigation results"""
        if not results:
            return {
                'message': "No errors or warnings found in the specified period.",
                'results': []
            }
        
        error_count = sum(1 for r in results if r.get('level') == 'error')
        warn_count = len(results) - error_count
        
        message = f"Found {error_count} errors and {warn_count} warnings"
        if 'service' in entities:
            message += f" in {entities['service']} service"
        
        return {
            'message': message,
            'results': results,
            'error_count': error_count,
            'warn_count': warn_count,
            'suggestions': ["Group by error type", "Show error timeline"]
        }
    
    def _format_time_range(self, time_range: Dict) -> str:
        """Format time range description"""
        if not time_range:
            return "in the last hour"
        
        start = time_range.get('start')
        end = time_range.get('end')
        
        if start and end:
            duration = end - start
            if duration.days > 0:
                return f"in the last {duration.days} days"
            elif duration.seconds >= 3600:
                hours = duration.seconds // 3600
                return f"in the last {hours} hours"
            else:
                minutes = duration.seconds // 60
                return f"in the last {minutes} minutes"
        
        return "in the specified time range"
