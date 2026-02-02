import sys
sys.path.insert(0, '../backend')

from graph import DependencyGraph
import unittest
from datetime import datetime

class TestDependencyGraph(unittest.TestCase):
    def setUp(self):
        self.graph = DependencyGraph()
    
    def test_add_dependency(self):
        self.graph.add_dependency('A', 'B', 100, 'http', datetime.now())
        
        self.assertIn('A', self.graph.nodes)
        self.assertIn('B', self.graph.nodes)
        self.assertEqual(self.graph.edges['A']['B']['weight'], 1)
        self.assertEqual(self.graph.edges['A']['B']['avg_latency'], 100)
    
    def test_update_dependency(self):
        self.graph.add_dependency('A', 'B', 100, 'http', datetime.now())
        self.graph.add_dependency('A', 'B', 200, 'http', datetime.now())
        
        self.assertEqual(self.graph.edges['A']['B']['weight'], 2)
        self.assertEqual(self.graph.edges['A']['B']['avg_latency'], 150)
    
    def test_find_cycles(self):
        self.graph.add_dependency('A', 'B', 100, 'http', datetime.now())
        self.graph.add_dependency('B', 'C', 100, 'http', datetime.now())
        self.graph.add_dependency('C', 'A', 100, 'http', datetime.now())
        
        cycles = self.graph.find_cycles()
        self.assertTrue(len(cycles) > 0)
    
    def test_single_point_of_failure(self):
        self.graph.add_dependency('A', 'C', 100, 'http', datetime.now())
        self.graph.add_dependency('B', 'C', 100, 'http', datetime.now())
        self.graph.add_dependency('D', 'C', 100, 'http', datetime.now())
        
        spofs = self.graph.find_single_points_of_failure()
        self.assertTrue(any(s[0] == 'C' for s in spofs))

if __name__ == '__main__':
    unittest.main()
