"""
Distributed Logging Library for Python
High-performance async logging client for distributed log processing system
"""

__version__ = "1.0.0"
__author__ = "Day 128 Implementation"

from .logger import DistributedLogger
from .config import LogConfig
from .models import LogLevel, LogEntry

__all__ = ['DistributedLogger', 'LogConfig', 'LogLevel', 'LogEntry']
