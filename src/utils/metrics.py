import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PerformanceMetrics:
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def stop(self) -> float:
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self.duration
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration, 3) if self.duration else None,
            "metadata": self.metadata
        }

class MetricsCollector:
    def __init__(self):
        self._metrics: Dict[str, list[PerformanceMetrics]] = {}
        self._counters: Dict[str, int] = {}
    
    def start_operation(self, operation: str, **metadata) -> PerformanceMetrics:
        metric = PerformanceMetrics(operation=operation, metadata=metadata)
        if operation not in self._metrics:
            self._metrics[operation] = []
        self._metrics[operation].append(metric)
        return metric
    
    def increment_counter(self, counter_name: str, amount: int = 1) -> int:
        if counter_name not in self._counters:
            self._counters[counter_name] = 0
        self._counters[counter_name] += amount
        return self._counters[counter_name]
    
    def get_counter(self, counter_name: str) -> int:
        return self._counters.get(counter_name, 0)
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        if operation not in self._metrics:
            return {}
        metrics = self._metrics[operation]
        completed = [m for m in metrics if m.duration is not None]
        if not completed:
            return {
                "operation": operation,
                "total_calls": len(metrics),
                "completed": 0,
                "in_progress": len(metrics)
            }
        durations = [m.duration for m in completed]
        return {
            "operation": operation,
            "total_calls": len(metrics),
            "completed": len(completed),
            "in_progress": len(metrics) - len(completed),
            "avg_duration": round(sum(durations) / len(durations), 3),
            "min_duration": round(min(durations), 3),
            "max_duration": round(max(durations), 3),
            "total_duration": round(sum(durations), 3)
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        return {
            "operations": {
                op: self.get_operation_stats(op)
                for op in self._metrics.keys()
            },
            "counters": self._counters.copy()
        }
    
    def reset(self) -> None:
        self._metrics.clear()
        self._counters.clear()

metrics_collector = MetricsCollector()

class timer:
    def __init__(self, operation: str, **metadata):
        self.operation = operation
        self.metadata = metadata
        self.metric: Optional[PerformanceMetrics] = None
    
    def __enter__(self) -> PerformanceMetrics:
        self.metric = metrics_collector.start_operation(self.operation, **self.metadata)
        return self.metric
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.metric:
            duration = self.metric.stop()
