"""
AI Performance Monitoring Module

This module provides monitoring capabilities for AI agents and workflows,
tracking performance metrics, resource usage, and system health.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from policy_as_code.core.errors import DecisionLayerError


@dataclass
class PerformanceMetric:
    """A performance metric"""

    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """System health status"""

    status: str  # healthy, degraded, unhealthy
    cpu_usage: float
    memory_usage: float
    active_agents: int
    timestamp: datetime
    alerts: Optional[List[str]] = None


class AIMonitor:
    """Monitors AI system performance"""

    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.health_history: List[SystemHealth] = []

    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "count",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a performance metric"""

        metric = PerformanceMetric(
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            metadata=metadata,
        )

        self.metrics.append(metric)

    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of all metrics"""

        summary = {}
        metric_groups = {}

        # Group metrics by name
        for metric in self.metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.value)

        # Calculate summaries
        for metric_name, values in metric_groups.items():
            if values:
                summary[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1],
                }

        return summary

    def check_system_health(self) -> SystemHealth:
        """Check overall system health"""

        # Mock health check
        health = SystemHealth(
            status="healthy",
            cpu_usage=45.2,
            memory_usage=67.8,
            active_agents=3,
            timestamp=datetime.utcnow(),
            alerts=[],
        )

        self.health_history.append(health)
        return health

    def get_health_history(self, limit: int = 100) -> List[SystemHealth]:
        """Get recent health history"""
        return self.health_history[-limit:]


# Export main classes
__all__ = ["PerformanceMetric", "SystemHealth", "AIMonitor"]
