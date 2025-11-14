"""Context injection providers for automatic log enrichment."""
import os
import socket
import time
from typing import Dict, Any
from datetime import datetime
import threading


class ContextProvider:
    """Base class for context providers."""
    
    def get_context(self) -> Dict[str, Any]:
        """Return context dictionary."""
        raise NotImplementedError


class EnvironmentContextProvider(ContextProvider):
    """Provides environment-based context."""
    
    def __init__(self):
        self.static_context = {
            'hostname': socket.gethostname(),
            'pid': os.getpid(),
            'python_version': os.sys.version.split()[0]
        }
        
    def get_context(self) -> Dict[str, Any]:
        """Get environment context."""
        context = self.static_context.copy()
        context.update({
            'timestamp_ms': int(time.time() * 1000),
            'thread_id': threading.get_ident()
        })
        return context


class ApplicationContextProvider(ContextProvider):
    """Provides application-specific context."""
    
    def __init__(self, app_name: str, version: str, environment: str = "development"):
        self.app_context = {
            'app_name': app_name,
            'version': version,
            'environment': environment
        }
        
    def get_context(self) -> Dict[str, Any]:
        """Get application context."""
        return self.app_context.copy()


class RequestContextProvider(ContextProvider):
    """Provides HTTP request context (thread-local storage)."""
    
    def __init__(self):
        self.local = threading.local()
        
    def set_request_context(self, request_id: str, user_id: str = None, 
                          ip_address: str = None, user_agent: str = None):
        """Set request context for current thread."""
        self.local.request_context = {
            'request_id': request_id,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
    def get_context(self) -> Dict[str, Any]:
        """Get request context from thread-local storage."""
        if hasattr(self.local, 'request_context'):
            return {k: v for k, v in self.local.request_context.items() if v is not None}
        return {}
        
    def clear_context(self):
        """Clear request context."""
        if hasattr(self.local, 'request_context'):
            delattr(self.local, 'request_context')


class PerformanceContextProvider(ContextProvider):
    """Provides performance metrics context."""
    
    def __init__(self):
        self.start_time = time.time()
        
    def get_context(self) -> Dict[str, Any]:
        """Get performance context."""
        return {
            'uptime_seconds': int(time.time() - self.start_time),
            'memory_mb': self._get_memory_usage()
        }
        
    def _get_memory_usage(self) -> int:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return int(process.memory_info().rss / 1024 / 1024)
        except ImportError:
            # Fallback if psutil not available
            return 0


# Context manager for easy setup
class ContextManager:
    """Manages multiple context providers."""
    
    def __init__(self):
        self.providers = []
        
    def add_provider(self, provider: ContextProvider):
        """Add a context provider."""
        self.providers.append(provider)
        
    def get_all_context(self) -> Dict[str, Any]:
        """Get combined context from all providers."""
        combined_context = {}
        
        for provider in self.providers:
            try:
                provider_context = provider.get_context()
                combined_context.update(provider_context)
            except Exception as e:
                combined_context['context_provider_error'] = str(e)
                
        return combined_context
        
    @classmethod
    def create_web_app_context(cls, app_name: str, version: str):
        """Create context manager for web applications."""
        manager = cls()
        manager.add_provider(EnvironmentContextProvider())
        manager.add_provider(ApplicationContextProvider(app_name, version))
        manager.add_provider(RequestContextProvider())
        manager.add_provider(PerformanceContextProvider())
        return manager
