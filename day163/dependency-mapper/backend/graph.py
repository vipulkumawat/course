"""
Dependency graph builder and analyzer
Uses in-memory graph structure for fast lookups
"""
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import json

class DependencyGraph:
    def __init__(self):
        self.edges = defaultdict(lambda: defaultdict(lambda: {
            'weight': 0,
            'latencies': [],
            'avg_latency': 0,
            'type': 'unknown',
            'first_seen': None,
            'last_seen': None
        }))
        self.nodes = set()
    
    def add_dependency(self, caller: str, callee: str, latency: int, 
                      dep_type: str = 'generic', timestamp=None):
        """Add or update a dependency edge"""
        self.nodes.add(caller)
        self.nodes.add(callee)
        
        edge = self.edges[caller][callee]
        edge['weight'] += 1
        edge['latencies'].append(latency)
        edge['avg_latency'] = sum(edge['latencies']) / len(edge['latencies'])
        edge['type'] = dep_type
        
        if edge['first_seen'] is None:
            edge['first_seen'] = timestamp
        edge['last_seen'] = timestamp
    
    def get_dependencies(self, service: str) -> Dict:
        """Get all dependencies for a service"""
        return {
            'outgoing': dict(self.edges.get(service, {})),
            'incoming': {
                caller: deps
                for caller, deps in self.edges.items()
                if service in deps
            }
        }
    
    def find_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.edges.get(node, {}):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            
            path.pop()
            rec_stack.remove(node)
        
        for node in self.nodes:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def find_single_points_of_failure(self) -> List[Tuple[str, int]]:
        """Find services with high outgoing dependencies"""
        spofs = []
        for node in self.nodes:
            incoming_count = sum(1 for n in self.edges if node in self.edges[n])
            if incoming_count > 2:  # More than 2 services depend on it
                spofs.append((node, incoming_count))
        return sorted(spofs, key=lambda x: x[1], reverse=True)
    
    def get_critical_paths(self) -> List[Tuple[List[str], int]]:
        """Find longest dependency chains"""
        def dfs_longest_path(node, visited=set()):
            if node in visited:
                return []
            
            visited.add(node)
            longest = []
            
            for neighbor in self.edges.get(node, {}):
                path = dfs_longest_path(neighbor, visited.copy())
                if len(path) > len(longest):
                    longest = path
            
            visited.remove(node)
            return [node] + longest
        
        paths = []
        for node in self.nodes:
            path = dfs_longest_path(node)
            if path:
                total_latency = sum(
                    self.edges[path[i]][path[i+1]]['avg_latency']
                    for i in range(len(path)-1)
                    if path[i+1] in self.edges[path[i]]
                )
                paths.append((path, int(total_latency)))
        
        return sorted(paths, key=lambda x: len(x[0]), reverse=True)[:5]
    
    def to_json(self) -> str:
        """Export graph to JSON for visualization"""
        nodes_list = [{'id': node, 'label': node} for node in self.nodes]
        edges_list = []
        
        for caller, callees in self.edges.items():
            for callee, data in callees.items():
                edges_list.append({
                    'source': caller,
                    'target': callee,
                    'weight': data['weight'],
                    'avgLatency': data['avg_latency'],
                    'type': data['type']
                })
        
        return json.dumps({
            'nodes': nodes_list,
            'edges': edges_list
        })
