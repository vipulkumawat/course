import sys
sys.path.insert(0, '../backend')

from parser import DependencyParser
import unittest

class TestDependencyParser(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
    
    def test_http_pattern(self):
        line = "[2025-01-30 10:00:01] WebApp called AuthService GET /api/validate 45ms"
        result = self.parser.parse_log_line(line)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['caller'], 'WebApp')
        self.assertEqual(result['callee'], 'AuthService')
        self.assertEqual(result['type'], 'http')
        self.assertEqual(result['latency'], 45)
    
    def test_rpc_pattern(self):
        line = "[2025-01-30 10:00:05] OrderService -> InventoryService.checkStock() 80ms"
        result = self.parser.parse_log_line(line)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['caller'], 'OrderService')
        self.assertEqual(result['callee'], 'InventoryService')
        self.assertEqual(result['type'], 'rpc')
        self.assertEqual(result['latency'], 80)
    
    def test_database_pattern(self):
        line = "[2025-01-30 10:00:03] UserService -> PostgreSQL SELECT users 35ms"
        result = self.parser.parse_log_line(line)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['caller'], 'UserService')
        self.assertEqual(result['callee'], 'PostgreSQL')
        self.assertEqual(result['type'], 'database')
        self.assertEqual(result['latency'], 35)
    
    def test_invalid_line(self):
        line = "This is not a valid log line"
        result = self.parser.parse_log_line(line)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
