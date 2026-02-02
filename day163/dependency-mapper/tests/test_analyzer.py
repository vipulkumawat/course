import sys
sys.path.insert(0, '../backend')

from graph import DependencyGraph
from analyzer import ImpactAnalyzer
import unittest
from datetime import datetime

class TestImpactAnalyzer(unittest.TestCase):
    def setUp(self):
        self.graph = DependencyGraph()
        self.graph.add_dependency('A', 'B', 100, 'http', datetime.now())
        self.graph.add_dependency('B', 'C', 100, 'http', datetime.now())
        self.graph.add_dependency('B', 'D', 100, 'http', datetime.now())
        self.analyzer = ImpactAnalyzer(self.graph)
    
    def test_simulate_failure(self):
        impact = self.analyzer.simulate_failure('B')
        
        self.assertEqual(impact['failed_service'], 'B')
        self.assertIn('A', impact['impacted_services'])
        self.assertTrue(impact['impact_count'] > 0)
    
    def test_blast_radius(self):
        impact = self.analyzer.simulate_failure('B')
        self.assertIn(impact['blast_radius'], ['none', 'low', 'medium', 'high', 'critical'])

if __name__ == '__main__':
    unittest.main()
