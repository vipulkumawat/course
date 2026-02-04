"""
Core impact analysis engine using graph traversal algorithms
"""
import networkx as nx
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChangeProposal:
    change_type: str  # 'api_modification', 'infrastructure', 'schema_change'
    target_service: str
    change_description: str
    proposed_by: str = "system"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ImpactResult:
    risk_score: float
    blast_radius: int
    affected_services: List[str]
    critical_path: bool
    recommendations: List[str]
    dependency_depth: Dict[str, int]
    
class ImpactAnalyzer:
    def __init__(self, dependency_graph: nx.DiGraph, service_metadata: Dict):
        """
        Initialize impact analyzer with dependency graph
        
        Args:
            dependency_graph: NetworkX directed graph of service dependencies
            service_metadata: Dict of service criticality and SLA requirements
        """
        self.graph = dependency_graph
        self.metadata = service_metadata
        self.analysis_cache = {}
        
    def analyze_change(self, proposal: ChangeProposal) -> ImpactResult:
        """
        Perform comprehensive impact analysis for proposed change
        """
        target = proposal.target_service
        
        # Check cache
        cache_key = f"{proposal.change_type}:{target}"
        if cache_key in self.analysis_cache:
            print(f"📋 Using cached analysis for {target}")
            return self.analysis_cache[cache_key]
        
        # Find all affected services through BFS traversal
        affected_services, depth_map = self._traverse_dependencies(target)
        
        # Calculate blast radius
        blast_radius = len(affected_services)
        
        # Determine if critical path is affected
        critical_path = self._check_critical_path(affected_services)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            proposal, affected_services, depth_map
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            proposal, risk_score, affected_services, critical_path
        )
        
        result = ImpactResult(
            risk_score=risk_score,
            blast_radius=blast_radius,
            affected_services=sorted(affected_services),
            critical_path=critical_path,
            recommendations=recommendations,
            dependency_depth=depth_map
        )
        
        # Cache result
        self.analysis_cache[cache_key] = result
        
        return result
    
    def _traverse_dependencies(self, start_service: str) -> Tuple[Set[str], Dict[str, int]]:
        """
        BFS traversal to find all downstream dependencies
        Returns: (set of affected services, dict of service -> depth)
        """
        if start_service not in self.graph:
            return set(), {}
        
        affected = set()
        depth_map = {start_service: 0}
        queue = [(start_service, 0)]
        visited = set()
        
        while queue:
            service, depth = queue.pop(0)
            
            if service in visited:
                continue
            visited.add(service)
            affected.add(service)
            
            # Get all services that depend on current service
            for successor in self.graph.successors(service):
                if successor not in visited:
                    new_depth = depth + 1
                    depth_map[successor] = new_depth
                    queue.append((successor, new_depth))
        
        return affected, depth_map
    
    def _check_critical_path(self, affected_services: Set[str]) -> bool:
        """
        Check if any critical services are affected
        """
        for service in affected_services:
            metadata = self.metadata.get(service, {})
            if metadata.get('critical', False):
                return True
        return False
    
    def _calculate_risk_score(self, proposal: ChangeProposal, 
                              affected_services: Set[str],
                              depth_map: Dict[str, int]) -> float:
        """
        Calculate risk score (0-100) based on multiple factors
        """
        # Base score from blast radius (40% weight)
        blast_radius_score = min(len(affected_services) * 3, 40)
        
        # Criticality score (40% weight)
        max_criticality = 0
        for service in affected_services:
            criticality = self.metadata.get(service, {}).get('criticality', 1)
            depth_weight = 1.0 / (depth_map.get(service, 1) + 1)
            weighted_criticality = criticality * depth_weight
            max_criticality = max(max_criticality, weighted_criticality)
        
        criticality_score = min(max_criticality * 40, 40)
        
        # Change type risk multiplier (20% weight)
        type_multipliers = {
            'api_modification': 0.6,
            'schema_change': 0.9,
            'infrastructure': 0.8,
            'configuration': 0.4
        }
        type_score = type_multipliers.get(proposal.change_type, 0.5) * 20
        
        total_score = blast_radius_score + criticality_score + type_score
        return round(min(total_score, 100), 2)
    
    def _generate_recommendations(self, proposal: ChangeProposal,
                                 risk_score: float,
                                 affected_services: Set[str],
                                 critical_path: bool) -> List[str]:
        """
        Generate specific, actionable recommendations
        """
        recommendations = []
        
        # Risk-based recommendations
        if risk_score >= 70:
            recommendations.append(
                "Schedule during maintenance window with full team availability"
            )
            recommendations.append(
                "Prepare detailed rollback plan and test rollback procedure"
            )
        elif risk_score >= 40:
            recommendations.append(
                "Deploy with feature flag for gradual rollout"
            )
            recommendations.append(
                "Monitor key metrics for 24 hours post-deployment"
            )
        
        # Critical path recommendations
        if critical_path:
            recommendations.append(
                "Alert on-call team before deployment of critical path change"
            )
        
        # Change type specific recommendations
        if proposal.change_type == 'schema_change':
            recommendations.append(
                f"Update {len(affected_services)} downstream service schemas before deployment"
            )
            recommendations.append(
                "Implement backward compatibility for 2 release cycles"
            )
        elif proposal.change_type == 'api_modification':
            recommendations.append(
                "Maintain API versioning with deprecation notice period"
            )
        elif proposal.change_type == 'infrastructure':
            recommendations.append(
                "Test in staging environment with production traffic patterns"
            )
        
        # Always add monitoring recommendation
        if len(affected_services) > 5:
            recommendations.append(
                f"Set up enhanced monitoring for {len(affected_services)} affected services"
            )
        
        return recommendations

def create_sample_dependency_graph() -> Tuple[nx.DiGraph, Dict]:
    """
    Create sample distributed log processing system dependency graph
    """
    G = nx.DiGraph()
    
    # Add services as nodes
    services = [
        'log-collector',
        'log-enrichment',
        'rabbitmq-cluster',
        'log-processor',
        'analytics-pipeline',
        'real-time-dashboard',
        'alert-processor',
        'data-warehouse-sync',
        'ml-feature-extractor',
        'compliance-auditor',
        'reporting-service',
        'elasticsearch-cluster',
        'redis-cache',
        'metrics-collector',
        'api-gateway'
    ]
    
    G.add_nodes_from(services)
    
    # Add dependency edges (A -> B means B depends on A)
    dependencies = [
        ('log-collector', 'log-enrichment'),
        ('log-enrichment', 'rabbitmq-cluster'),
        ('rabbitmq-cluster', 'log-processor'),
        ('log-processor', 'analytics-pipeline'),
        ('log-processor', 'real-time-dashboard'),
        ('log-processor', 'alert-processor'),
        ('log-processor', 'elasticsearch-cluster'),
        ('analytics-pipeline', 'data-warehouse-sync'),
        ('analytics-pipeline', 'ml-feature-extractor'),
        ('log-enrichment', 'compliance-auditor'),
        ('elasticsearch-cluster', 'reporting-service'),
        ('redis-cache', 'real-time-dashboard'),
        ('api-gateway', 'log-collector'),
        ('metrics-collector', 'analytics-pipeline')
    ]
    
    G.add_edges_from(dependencies)
    
    # Service metadata with criticality
    metadata = {
        'log-collector': {'critical': True, 'criticality': 10, 'sla': '99.9%'},
        'log-enrichment': {'critical': True, 'criticality': 9, 'sla': '99.5%'},
        'rabbitmq-cluster': {'critical': True, 'criticality': 10, 'sla': '99.99%'},
        'log-processor': {'critical': True, 'criticality': 9, 'sla': '99.5%'},
        'analytics-pipeline': {'critical': False, 'criticality': 6, 'sla': '99.0%'},
        'real-time-dashboard': {'critical': True, 'criticality': 8, 'sla': '99.5%'},
        'alert-processor': {'critical': True, 'criticality': 10, 'sla': '99.9%'},
        'data-warehouse-sync': {'critical': False, 'criticality': 4, 'sla': '95.0%'},
        'ml-feature-extractor': {'critical': False, 'criticality': 5, 'sla': '95.0%'},
        'compliance-auditor': {'critical': True, 'criticality': 9, 'sla': '99.5%'},
        'reporting-service': {'critical': False, 'criticality': 6, 'sla': '99.0%'},
        'elasticsearch-cluster': {'critical': True, 'criticality': 9, 'sla': '99.5%'},
        'redis-cache': {'critical': False, 'criticality': 7, 'sla': '99.0%'},
        'metrics-collector': {'critical': False, 'criticality': 5, 'sla': '95.0%'},
        'api-gateway': {'critical': True, 'criticality': 10, 'sla': '99.99%'}
    }
    
    return G, metadata

if __name__ == "__main__":
    # Demo execution
    print("🔍 Initializing Change Impact Analyzer...")
    
    graph, metadata = create_sample_dependency_graph()
    analyzer = ImpactAnalyzer(graph, metadata)
    
    print(f"✅ Loaded dependency graph: {len(graph.nodes)} services, {len(graph.edges)} dependencies")
    
    # Test analysis
    proposal = ChangeProposal(
        change_type='schema_change',
        target_service='log-enrichment',
        change_description='Add new field: user_segment'
    )
    
    print(f"\n📊 Analyzing change: {proposal.change_description}")
    result = analyzer.analyze_change(proposal)
    
    print(f"\n📈 Impact Analysis Results:")
    print(f"  Risk Score: {result.risk_score}/100")
    print(f"  Blast Radius: {result.blast_radius} services")
    print(f"  Critical Path: {'YES' if result.critical_path else 'NO'}")
    print(f"  Affected Services: {', '.join(result.affected_services[:5])}...")
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
