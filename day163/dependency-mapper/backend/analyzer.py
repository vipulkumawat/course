"""
Impact analyzer for dependency graphs
Simulates failure scenarios and computes blast radius
"""
from typing import Set, Dict, List

class ImpactAnalyzer:
    def __init__(self, graph):
        self.graph = graph
    
    def simulate_failure(self, service: str) -> Dict:
        """Simulate service failure and find impacted services"""
        impacted = set()
        
        def propagate_failure(node, visited=set()):
            if node in visited:
                return
            visited.add(node)
            impacted.add(node)
            
            # Find all services that depend on this node
            for caller, deps in self.graph.edges.items():
                if node in deps:
                    propagate_failure(caller, visited)
        
        propagate_failure(service)
        impacted.discard(service)  # Don't count the failed service itself
        
        return {
            'failed_service': service,
            'impacted_services': list(impacted),
            'impact_count': len(impacted),
            'blast_radius': self._calculate_blast_radius(impacted)
        }
    
    def _calculate_blast_radius(self, impacted: Set[str]) -> str:
        """Categorize impact severity"""
        count = len(impacted)
        if count == 0:
            return 'none'
        elif count <= 2:
            return 'low'
        elif count <= 5:
            return 'medium'
        elif count <= 10:
            return 'high'
        else:
            return 'critical'
    
    def analyze_all_failures(self) -> List[Dict]:
        """Analyze failure impact for all services"""
        results = []
        for service in self.graph.nodes:
            impact = self.simulate_failure(service)
            results.append(impact)
        
        return sorted(results, key=lambda x: x['impact_count'], reverse=True)
