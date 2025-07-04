"""
SQL-like query parser for distributed log search
Handles SELECT, WHERE, GROUP BY, ORDER BY, and LIMIT clauses
"""
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

class OperatorType(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "CONTAINS"
    IN = "IN"
    BETWEEN = "BETWEEN"

@dataclass
class SelectField:
    name: str
    alias: Optional[str] = None
    aggregation: Optional[str] = None  # COUNT, SUM, AVG, etc.

@dataclass
class WhereCondition:
    field: str
    operator: OperatorType
    value: Union[str, int, float, List[Any]]
    logical_operator: Optional[str] = None  # AND, OR for chaining

@dataclass
class OrderByClause:
    field: str
    direction: str = "ASC"  # ASC or DESC

@dataclass
class GroupByClause:
    fields: List[str]
    having: Optional[WhereCondition] = None

@dataclass
class QueryAST:
    """Abstract Syntax Tree for parsed SQL queries"""
    select_fields: List[SelectField]
    from_table: str
    where_conditions: List[WhereCondition] = field(default_factory=list)
    group_by: Optional[GroupByClause] = None
    order_by: List[OrderByClause] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None

class SQLParser:
    """
    Parses SQL-like queries into AST for distributed log search
    
    Supported syntax:
    SELECT field1, COUNT(*) as count_val
    FROM logs
    WHERE timestamp > '2025-01-01' AND level = 'ERROR'
    GROUP BY service
    ORDER BY timestamp DESC
    LIMIT 100
    """
    
    def __init__(self):
        self.keywords = {
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'LIMIT', 'OFFSET',
            'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'CONTAINS', 'AS', 'ASC', 'DESC',
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'HAVING'
        }
        
    def parse(self, query: str) -> QueryAST:
        """Parse SQL query string into AST"""
        query = query.strip()
        if not query:
            raise ValueError("Empty query")
            
        # Tokenize query
        tokens = self._tokenize(query)
        
        # Parse different clauses
        ast = QueryAST(select_fields=[], from_table="")
        
        i = 0
        while i < len(tokens):
            token = tokens[i].upper()
            
            if token == 'SELECT':
                i = self._parse_select(tokens, i, ast)
            elif token == 'FROM':
                i = self._parse_from(tokens, i, ast)
            elif token == 'WHERE':
                i = self._parse_where(tokens, i, ast)
            elif token == 'GROUP':
                i = self._parse_group_by(tokens, i, ast)
            elif token == 'ORDER':
                i = self._parse_order_by(tokens, i, ast)
            elif token == 'LIMIT':
                i = self._parse_limit(tokens, i, ast)
            elif token == 'OFFSET':
                i = self._parse_offset(tokens, i, ast)
            else:
                i += 1
                
        return ast
    
    def _tokenize(self, query: str) -> List[str]:
        """Tokenize SQL query into individual tokens"""
        # Handle quoted strings
        query = re.sub(r"'([^']*)'", r'"\1"', query)
        
        # Split on whitespace and common SQL operators
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+\.?[0-9]*|"[^"]*"|[<>=!]+|[(),]|\S', query)
        
        return [token for token in tokens if token.strip()]
    
    def _parse_select(self, tokens: List[str], start: int, ast: QueryAST) -> int:
        """Parse SELECT clause"""
        i = start + 1
        
        while i < len(tokens) and tokens[i].upper() != 'FROM':
            if tokens[i] == ',':
                i += 1
                continue
                
            field_name = tokens[i]
            alias = None
            aggregation = None
            
            # Check for aggregation functions
            if i + 1 < len(tokens) and tokens[i + 1] == '(':
                aggregation = field_name.upper()
                i += 2  # Skip function name and opening paren
                if i < len(tokens) and tokens[i] != ')':
                    field_name = tokens[i]
                    i += 1
                else:
                    field_name = '*'
                if i < len(tokens) and tokens[i] == ')':
                    i += 1
            
            # Check for alias
            if i + 1 < len(tokens) and tokens[i + 1].upper() == 'AS':
                alias = tokens[i + 2]
                i += 3
            elif i + 1 < len(tokens) and tokens[i + 1] not in [',', 'FROM']:
                alias = tokens[i + 1]
                i += 2
            else:
                i += 1
            
            ast.select_fields.append(SelectField(field_name, alias, aggregation))
        
        return i
    
    def _parse_from(self, tokens: List[str], start: int, ast: QueryAST) -> int:
        """Parse FROM clause"""
        ast.from_table = tokens[start + 1]
        return start + 2
    
    def _parse_where(self, tokens: List[str], start: int, ast: QueryAST) -> int:
        """Parse WHERE clause"""
        i = start + 1
        
        while i < len(tokens):
            if tokens[i].upper() in ['GROUP', 'ORDER', 'LIMIT', 'OFFSET']:
                break
                
            # Parse condition
            field = tokens[i]
            i += 1
            
            if i >= len(tokens):
                break
                
            operator_str = tokens[i]
            operator = self._parse_operator(operator_str)
            i += 1
            
            if i >= len(tokens):
                break
                
            value = self._parse_value(tokens[i])
            i += 1
            
            condition = WhereCondition(field, operator, value)
            
            # Check for logical operator
            if i < len(tokens) and tokens[i].upper() in ['AND', 'OR']:
                condition.logical_operator = tokens[i].upper()
                i += 1
            
            ast.where_conditions.append(condition)
        
        return i
    
    def _parse_group_by(self, tokens: List[str], start: int, ast: QueryAST) -> int:
        """Parse GROUP BY clause"""
        i = start + 1
        if i < len(tokens) and tokens[i].upper() == 'BY':
            i += 1
            
        fields = []
        while i < len(tokens) and tokens[i].upper() not in ['ORDER', 'LIMIT', 'OFFSET', 'HAVING']:
            if tokens[i] != ',':
                fields.append(tokens[i])
            i += 1
        
        ast.group_by = GroupByClause(fields)
        return i
    
    def _parse_order_by(self, tokens: List[str], start: int, ast: QueryAST) -> int:
        """Parse ORDER BY clause"""
        i = start + 1
        if i < len(tokens) and tokens[i].upper() == 'BY':
            i += 1
            
        while i < len(tokens) and tokens[i].upper() not in ['LIMIT', 'OFFSET']:
            if tokens[i] == ',':
                i += 1
                continue
                
            field = tokens[i]
            direction = "ASC"
            
            if i + 1 < len(tokens) and tokens[i + 1].upper() in ['ASC', 'DESC']:
                direction = tokens[i + 1].upper()
                i += 2
            else:
                i += 1
            
            ast.order_by.append(OrderByClause(field, direction))
        
        return i
    
    def _parse_limit(self, tokens: List[str], start: int, ast: QueryAST) -> int:
        """Parse LIMIT clause"""
        if start + 1 < len(tokens):
            ast.limit = int(tokens[start + 1])
        return start + 2
    
    def _parse_offset(self, tokens: List[str], start: int, ast: QueryAST) -> int:
        """Parse OFFSET clause"""
        if start + 1 < len(tokens):
            ast.offset = int(tokens[start + 1])
        return start + 2
    
    def _parse_operator(self, operator_str: str) -> OperatorType:
        """Parse operator string to OperatorType"""
        operator_map = {
            '=': OperatorType.EQUALS,
            '!=': OperatorType.NOT_EQUALS,
            '>': OperatorType.GREATER_THAN,
            '<': OperatorType.LESS_THAN,
            '>=': OperatorType.GREATER_EQUAL,
            '<=': OperatorType.LESS_EQUAL,
            'CONTAINS': OperatorType.CONTAINS,
            'IN': OperatorType.IN,
            'BETWEEN': OperatorType.BETWEEN
        }
        
        return operator_map.get(operator_str.upper(), OperatorType.EQUALS)
    
    def _parse_value(self, value_str: str) -> Union[str, int, float]:
        """Parse value string to appropriate type"""
        # Remove quotes if present
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            return value_str

    def validate_query(self, ast: QueryAST) -> bool:
        """Validate parsed query AST"""
        if not ast.select_fields:
            raise ValueError("SELECT clause is required")
        
        if not ast.from_table:
            raise ValueError("FROM clause is required")
        
        return True
