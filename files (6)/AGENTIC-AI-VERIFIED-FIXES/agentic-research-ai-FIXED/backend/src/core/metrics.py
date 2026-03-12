"""
Application Metrics Collection
==============================
Prometheus-compatible metrics for monitoring.
"""

from datetime import datetime
from typing import Dict, Any
from collections import defaultdict
import time


class MetricsCollector:
    """
    Collect application metrics.
    
    Metrics tracked:
    - API request counts and latencies
    - Agent execution counts and durations
    - Database query counts
    - Error rates
    - WebSocket connections
    """
    
    def __init__(self):
        self.metrics: Dict[str, Any] = defaultdict(lambda: defaultdict(int))
        self.histograms: Dict[str, list] = defaultdict(list)
        self.start_time = datetime.utcnow()
    
    # HTTP Metrics
    def record_http_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Record HTTP request metrics."""
        self.metrics["http_requests_total"][f"{method}_{path}"] += 1
        self.metrics["http_status_codes"][status_code] += 1
        self.histograms["http_request_duration_ms"].append(duration_ms)
    
    # Agent Metrics
    def record_agent_execution(self, agent_name: str, duration_seconds: float, success: bool):
        """Record agent execution metrics."""
        self.metrics["agent_executions_total"][agent_name] += 1
        if success:
            self.metrics["agent_successes"][agent_name] += 1
        else:
            self.metrics["agent_failures"][agent_name] += 1
        
        self.histograms[f"agent_duration_{agent_name}"].append(duration_seconds)
    
    # Database Metrics
    def record_db_query(self, query_type: str, duration_ms: float):
        """Record database query metrics."""
        self.metrics["db_queries_total"][query_type] += 1
        self.histograms["db_query_duration_ms"].append(duration_ms)
    
    # WebSocket Metrics
    def record_websocket_connection(self, connected: bool):
        """Record WebSocket connection/disconnection."""
        if connected:
            self.metrics["websocket"]["active_connections"] += 1
            self.metrics["websocket"]["total_connections"] += 1
        else:
            self.metrics["websocket"]["active_connections"] -= 1
    
    def record_websocket_message(self, message_type: str):
        """Record WebSocket message."""
        self.metrics["websocket_messages"][message_type] += 1
    
    # Error Metrics
    def record_error(self, error_type: str, component: str):
        """Record application error."""
        self.metrics["errors_total"][f"{component}_{error_type}"] += 1
    
    # Summary Methods
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime_seconds,
            "counters": dict(self.metrics),
            "histograms": {
                key: {
                    "count": len(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "p95": self._percentile(values, 95) if values else 0
                }
                for key, values in self.histograms.items()
            }
        }
    
    def _percentile(self, values: list, percentile: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.histograms.clear()


# Global metrics instance
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics
