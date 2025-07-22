"""
OptimizationEngine: Adaptive batch size optimization using gradient ascent
"""

import asyncio
import time
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class OptimizationConfig:
    min_batch_size: int = 50
    max_batch_size: int = 5000
    learning_rate: float = 0.1
    gradient_window: int = 5
    stability_threshold: float = 0.05
    max_memory_usage: float = 80.0  # Percentage
    max_cpu_usage: float = 90.0     # Percentage
    target_latency_ms: float = 1000.0

@dataclass
class OptimizationState:
    current_batch_size: int
    current_throughput: float
    current_latency: float
    gradient: float
    stability_score: float
    adjustment_count: int
    last_adjustment_time: float

class OptimizationEngine:
    """Implements adaptive batch size optimization"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.state = OptimizationState(
            current_batch_size=self.config.min_batch_size * 2,  # Start conservatively
            current_throughput=0.0,
            current_latency=0.0,
            gradient=0.0,
            stability_score=0.0,
            adjustment_count=0,
            last_adjustment_time=time.time()
        )
        
        self.throughput_history: List[float] = []
        self.latency_history: List[float] = []
        self.batch_size_history: List[int] = []
        self.optimization_decisions: List[Dict] = []
        
        # Performance tracking
        self.baseline_throughput: Optional[float] = None
        self.best_throughput: float = 0.0
        self.best_batch_size: int = self.state.current_batch_size
        
    def calculate_optimal_batch_size(self, metrics: Dict) -> Tuple[int, Dict]:
        """Calculate optimal batch size using gradient ascent optimization"""
        
        # Extract relevant metrics
        system_metrics = metrics.get("system", {})
        processing_metrics = metrics.get("processing", {})
        
        cpu_usage = system_metrics.get("cpu_usage", 0)
        memory_usage = system_metrics.get("memory_usage", 0)
        current_throughput = processing_metrics.get("throughput", 0)
        current_latency = processing_metrics.get("processing_time", 0) * 1000  # Convert to ms
        
        # Safety checks - respect resource constraints
        if self._violates_constraints(cpu_usage, memory_usage, current_latency):
            return self._emergency_adjustment(cpu_usage, memory_usage, current_latency)
        
        # Calculate gradient for throughput optimization
        gradient = self._calculate_gradient(current_throughput)
        
        # Determine adjustment direction and magnitude
        adjustment_factor = self._calculate_adjustment_factor(gradient, current_throughput)
        
        # Calculate new batch size
        new_batch_size = self._apply_adjustment(adjustment_factor)
        
        # Update state
        self._update_state(new_batch_size, current_throughput, current_latency, gradient)
        
        # Create decision record
        decision = self._create_decision_record(
            new_batch_size, current_throughput, current_latency, 
            gradient, adjustment_factor, cpu_usage, memory_usage
        )
        
        return new_batch_size, decision
    
    def _violates_constraints(self, cpu_usage: float, memory_usage: float, latency: float) -> bool:
        """Check if current metrics violate operational constraints"""
        return (
            cpu_usage > self.config.max_cpu_usage or
            memory_usage > self.config.max_memory_usage or
            latency > self.config.target_latency_ms
        )
    
    def _emergency_adjustment(self, cpu_usage: float, memory_usage: float, latency: float) -> Tuple[int, Dict]:
        """Emergency batch size reduction when constraints are violated"""
        reduction_factor = 0.7  # Reduce by 30%
        new_batch_size = max(
            int(self.state.current_batch_size * reduction_factor),
            self.config.min_batch_size
        )
        
        reason = []
        if cpu_usage > self.config.max_cpu_usage:
            reason.append(f"high_cpu_{cpu_usage:.1f}%")
        if memory_usage > self.config.max_memory_usage:
            reason.append(f"high_memory_{memory_usage:.1f}%")
        if latency > self.config.target_latency_ms:
            reason.append(f"high_latency_{latency:.1f}ms")
        
        decision = {
            "type": "emergency_reduction",
            "reason": "_".join(reason),
            "old_batch_size": self.state.current_batch_size,
            "new_batch_size": new_batch_size,
            "reduction_factor": reduction_factor,
            "timestamp": time.time()
        }
        
        return new_batch_size, decision
    
    def _calculate_gradient(self, current_throughput: float) -> float:
        """Calculate throughput gradient for optimization direction"""
        if len(self.throughput_history) < 2:
            return 0.0
        
        # Use recent history for gradient calculation
        recent_throughputs = self.throughput_history[-self.config.gradient_window:]
        recent_batch_sizes = self.batch_size_history[-self.config.gradient_window:]
        
        if len(recent_throughputs) < 2:
            return 0.0
        
        # Calculate numerical gradient: dThroughput/dBatchSize
        throughput_change = recent_throughputs[-1] - recent_throughputs[-2]
        batch_size_change = recent_batch_sizes[-1] - recent_batch_sizes[-2]
        
        if batch_size_change == 0:
            return 0.0
        
        gradient = throughput_change / batch_size_change
        
        # Apply smoothing to reduce noise
        if hasattr(self, '_last_gradient'):
            gradient = 0.7 * gradient + 0.3 * self._last_gradient
        
        self._last_gradient = gradient
        return gradient
    
    def _calculate_adjustment_factor(self, gradient: float, current_throughput: float) -> float:
        """Calculate batch size adjustment factor based on gradient"""
        
        # Base adjustment using gradient ascent
        base_adjustment = self.config.learning_rate * gradient
        
        # Adaptive learning rate based on performance
        if current_throughput > self.best_throughput:
            # We're improving - be more aggressive
            learning_multiplier = 1.5
            self.best_throughput = current_throughput
            self.best_batch_size = self.state.current_batch_size
        else:
            # Performance is declining - be more conservative
            learning_multiplier = 0.5
        
        adjustment = base_adjustment * learning_multiplier
        
        # Apply damping to prevent oscillation
        stability_factor = max(0.1, 1.0 - self.state.stability_score)
        adjustment *= stability_factor
        
        # Clamp adjustment to reasonable bounds
        max_adjustment = 0.2  # Maximum 20% change per iteration
        adjustment = max(-max_adjustment, min(max_adjustment, adjustment))
        
        return adjustment
    
    def _apply_adjustment(self, adjustment_factor: float) -> int:
        """Apply adjustment factor to current batch size"""
        new_batch_size = int(self.state.current_batch_size * (1 + adjustment_factor))
        
        # Enforce bounds
        new_batch_size = max(self.config.min_batch_size, new_batch_size)
        new_batch_size = min(self.config.max_batch_size, new_batch_size)
        
        return new_batch_size
    
    def _update_state(self, new_batch_size: int, throughput: float, latency: float, gradient: float):
        """Update optimization state with new values"""
        self.throughput_history.append(throughput)
        self.latency_history.append(latency)
        self.batch_size_history.append(new_batch_size)
        
        # Trim history to prevent memory growth
        max_history = 100
        if len(self.throughput_history) > max_history:
            self.throughput_history.pop(0)
            self.latency_history.pop(0)
            self.batch_size_history.pop(0)
        
        # Calculate stability score
        self.state.stability_score = self._calculate_stability_score()
        
        # Update state
        self.state.current_batch_size = new_batch_size
        self.state.current_throughput = throughput
        self.state.current_latency = latency
        self.state.gradient = gradient
        self.state.adjustment_count += 1
        self.state.last_adjustment_time = time.time()
        
        # Set baseline if not established
        if self.baseline_throughput is None and throughput > 0:
            self.baseline_throughput = throughput
    
    def _calculate_stability_score(self) -> float:
        """Calculate system stability score (0-1, higher is more stable)"""
        if len(self.throughput_history) < 5:
            return 0.0
        
        recent_throughputs = self.throughput_history[-5:]
        
        # Calculate coefficient of variation
        mean_throughput = sum(recent_throughputs) / len(recent_throughputs)
        if mean_throughput == 0:
            return 0.0
        
        variance = sum((t - mean_throughput) ** 2 for t in recent_throughputs) / len(recent_throughputs)
        std_dev = math.sqrt(variance)
        coefficient_of_variation = std_dev / mean_throughput
        
        # Convert to stability score (lower variation = higher stability)
        stability = max(0.0, 1.0 - coefficient_of_variation)
        return stability
    
    def _create_decision_record(self, new_batch_size: int, throughput: float, latency: float,
                              gradient: float, adjustment_factor: float, 
                              cpu_usage: float, memory_usage: float) -> Dict:
        """Create detailed record of optimization decision"""
        decision = {
            "timestamp": time.time(),
            "type": "gradient_optimization",
            "old_batch_size": self.state.current_batch_size,
            "new_batch_size": new_batch_size,
            "throughput": throughput,
            "latency": latency,
            "gradient": gradient,
            "adjustment_factor": adjustment_factor,
            "stability_score": self.state.stability_score,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "improvement_vs_baseline": (
                ((throughput - self.baseline_throughput) / self.baseline_throughput * 100)
                if self.baseline_throughput else 0
            )
        }
        
        self.optimization_decisions.append(decision)
        
        # Trim decision history
        if len(self.optimization_decisions) > 1000:
            self.optimization_decisions.pop(0)
        
        return decision
    
    def get_optimization_status(self) -> Dict:
        """Get current optimization status and statistics"""
        return {
            "current_state": {
                "batch_size": self.state.current_batch_size,
                "throughput": self.state.current_throughput,
                "latency": self.state.current_latency,
                "gradient": self.state.gradient,
                "stability_score": self.state.stability_score,
                "adjustment_count": self.state.adjustment_count
            },
            "performance": {
                "baseline_throughput": self.baseline_throughput,
                "best_throughput": self.best_throughput,
                "best_batch_size": self.best_batch_size,
                "improvement_percentage": (
                    ((self.best_throughput - self.baseline_throughput) / self.baseline_throughput * 100)
                    if self.baseline_throughput else 0
                )
            },
            "recent_decisions": self.optimization_decisions[-5:],  # Last 5 decisions
            "configuration": {
                "min_batch_size": self.config.min_batch_size,
                "max_batch_size": self.config.max_batch_size,
                "learning_rate": self.config.learning_rate,
                "target_latency_ms": self.config.target_latency_ms
            }
        }
    
    def reset_optimization(self):
        """Reset optimization state (useful for testing different scenarios)"""
        self.state = OptimizationState(
            current_batch_size=self.config.min_batch_size * 2,
            current_throughput=0.0,
            current_latency=0.0,
            gradient=0.0,
            stability_score=0.0,
            adjustment_count=0,
            last_adjustment_time=time.time()
        )
        
        self.throughput_history.clear()
        self.latency_history.clear()
        self.batch_size_history.clear()
        self.optimization_decisions.clear()
        
        self.baseline_throughput = None
        self.best_throughput = 0.0
        self.best_batch_size = self.state.current_batch_size
