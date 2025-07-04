"""
Tests for SQL parser functionality
"""
import pytest
from src.parser.sql_parser import SQLParser, QueryAST, SelectField, WhereCondition, OperatorType

class TestSQLParser:
    def setUp(self):
        self.parser = SQLParser()
    
    def test_simple_select(self):
        parser = SQLParser()
        query = "SELECT service, level FROM logs WHERE timestamp > '2025-01-15'"
        ast = parser.parse(query)
        
        assert len(ast.select_fields) == 2
        assert ast.select_fields[0].name == "service"
        assert ast.select_fields[1].name == "level"
        assert ast.from_table == "logs"
        assert len(ast.where_conditions) == 1
        assert ast.where_conditions[0].field == "timestamp"
        assert ast.where_conditions[0].operator == OperatorType.GREATER_THAN
    
    def test_aggregation_query(self):
        parser = SQLParser()
        query = "SELECT service, COUNT(*) as count FROM logs GROUP BY service"
        ast = parser.parse(query)
        
        assert len(ast.select_fields) == 2
        assert ast.select_fields[0].name == "service"
        assert ast.select_fields[1].name == "*"
        assert ast.select_fields[1].aggregation == "COUNT"
        assert ast.select_fields[1].alias == "count"
        assert ast.group_by is not None
        assert "service" in ast.group_by.fields
    
    def test_complex_where_conditions(self):
        parser = SQLParser()
        query = "SELECT * FROM logs WHERE level = 'ERROR' AND timestamp > '2025-01-15' AND service = 'user-service'"
        ast = parser.parse(query)
        
        assert len(ast.where_conditions) == 3
        assert ast.where_conditions[0].field == "level"
        assert ast.where_conditions[0].value == "ERROR"
        assert ast.where_conditions[1].logical_operator == "AND"
    
    def test_order_by_and_limit(self):
        parser = SQLParser()
        query = "SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100"
        ast = parser.parse(query)
        
        assert len(ast.order_by) == 1
        assert ast.order_by[0].field == "timestamp"
        assert ast.order_by[0].direction == "DESC"
        assert ast.limit == 100
    
    def test_invalid_query(self):
        parser = SQLParser()
        with pytest.raises(ValueError):
            parser.parse("")
        
        with pytest.raises(Exception):
            parser.parse("INVALID QUERY SYNTAX")

if __name__ == "__main__":
    pytest.main([__file__])
