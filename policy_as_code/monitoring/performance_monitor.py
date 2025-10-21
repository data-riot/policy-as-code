"""
Performance Monitoring and Metrics Collection
Provides comprehensive monitoring, alerting, and performance analytics
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricPoint:
    """A single metric data point"""

    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    metric_name: str
    condition: str  # e.g., "value > 100", "rate > 0.5"
    threshold: float
    duration: int  # seconds
    enabled: bool = True
    last_triggered: Optional[datetime] = None


@dataclass
class Alert:
    """Alert instance"""

    rule_name: str
    metric_name: str
    value: float
    threshold: float
    timestamp: datetime
    message: str
    severity: str = "warning"


class MetricsCollector:
    """Collects and stores metrics"""

    def __init__(self, max_history_size: int = 10000):
        self.metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history_size)
        )
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)

    def record_counter(
        self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None
    ):
        """Record a counter metric"""
        self.counters[name] += value
        self._record_metric(name, self.counters[name], MetricType.COUNTER, tags)

    def record_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a gauge metric"""
        self.gauges[name] = value
        self._record_metric(name, value, MetricType.GAUGE, tags)

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a histogram metric"""
        self.histograms[name].append(value)
        self._record_metric(name, value, MetricType.HISTOGRAM, tags)

    def record_timer(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a timer metric"""
        self.timers[name].append(duration)
        self._record_metric(name, duration, MetricType.TIMER, tags)

    def _record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]],
    ):
        """Record a metric point"""
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            metric_type=metric_type,
        )
        self.metrics[name].append(point)

    def get_metric_summary(
        self, name: str, duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if name not in self.metrics:
            return {"error": f"Metric {name} not found"}

        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_points = [
            point for point in self.metrics[name] if point.timestamp >= cutoff_time
        ]

        if not recent_points:
            return {
                "error": f"No data for {name} in the last {duration_minutes} minutes"
            }

        values = [point.value for point in recent_points]

        summary = {
            "name": name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "duration_minutes": duration_minutes,
            "first_timestamp": recent_points[0].timestamp.isoformat(),
            "last_timestamp": recent_points[-1].timestamp.isoformat(),
        }

        # Add percentile calculations
        if len(values) >= 10:
            sorted_values = sorted(values)
            summary["p95"] = sorted_values[int(len(sorted_values) * 0.95)]
            summary["p99"] = sorted_values[int(len(sorted_values) * 0.99)]

        return summary

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histogram_counts": {
                name: len(values) for name, values in self.histograms.items()
            },
            "timer_counts": {name: len(values) for name, values in self.timers.items()},
            "total_metric_points": sum(
                len(metrics) for metrics in self.metrics.values()
            ),
        }


class AlertManager:
    """Manages alert rules and notifications"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []

    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules[rule.name] = rule

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add a callback for alert notifications"""
        self.alert_callbacks.append(callback)

    async def check_alerts(self):
        """Check all alert rules and trigger alerts if needed"""
        current_time = datetime.now()

        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue

            # Check if rule should be evaluated
            if (
                rule.last_triggered
                and (current_time - rule.last_triggered).seconds < rule.duration
            ):
                continue

            # Get metric summary
            summary = self.metrics_collector.get_metric_summary(
                rule.metric_name, 5
            )  # Last 5 minutes

            if "error" in summary:
                continue

            # Evaluate condition
            if self._evaluate_condition(
                summary["mean"], rule.condition, rule.threshold
            ):
                alert = Alert(
                    rule_name=rule_name,
                    metric_name=rule.metric_name,
                    value=summary["mean"],
                    threshold=rule.threshold,
                    timestamp=current_time,
                    message=f"{rule.metric_name} {rule.condition} (value: {summary['mean']:.2f}, threshold: {rule.threshold})",
                    severity=(
                        "critical"
                        if summary["mean"] > rule.threshold * 2
                        else "warning"
                    ),
                )

                self.active_alerts.append(alert)
                rule.last_triggered = current_time

                # Notify callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        print(f"Alert callback error: {e}")

    def _evaluate_condition(
        self, value: float, condition: str, threshold: float
    ) -> bool:
        """Evaluate alert condition"""
        if ">" in condition:
            return value > threshold
        elif "<" in condition:
            return value < threshold
        elif ">=" in condition:
            return value >= threshold
        elif "<=" in condition:
            return value <= threshold
        elif "==" in condition:
            return abs(value - threshold) < 0.001
        else:
            return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return self.active_alerts.copy()

    def clear_alerts(self):
        """Clear all active alerts"""
        self.active_alerts.clear()


class PerformanceMonitor:
    """Main performance monitoring system"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.start_time = datetime.now()
        self.monitoring_enabled = True

        # Setup default alert rules
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="high_execution_time",
                metric_name="decision_execution_time_ms",
                condition=">",
                threshold=5000,  # 5 seconds
                duration=60,
            ),
            AlertRule(
                name="high_error_rate",
                metric_name="decision_error_rate",
                condition=">",
                threshold=0.1,  # 10%
                duration=300,
            ),
            AlertRule(
                name="low_success_rate",
                metric_name="decision_success_rate",
                condition="<",
                threshold=0.95,  # 95%
                duration=300,
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="memory_usage_mb",
                condition=">",
                threshold=1000,  # 1GB
                duration=60,
            ),
        ]

        for rule in default_rules:
            self.alert_manager.add_rule(rule)

    def record_decision_execution(
        self,
        function_id: str,
        execution_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Record decision execution metrics"""
        tags = {"function_id": function_id}

        # Record execution time
        self.metrics_collector.record_timer(
            "decision_execution_time_ms", execution_time_ms, tags
        )
        self.metrics_collector.record_histogram(
            "decision_execution_time_ms", execution_time_ms, tags
        )

        # Record success/failure
        self.metrics_collector.record_counter("decisions_total", 1, tags)
        if success:
            self.metrics_collector.record_counter("decisions_success", 1, tags)
        else:
            self.metrics_collector.record_counter("decisions_failure", 1, tags)

        # Record error if present
        if error_message:
            self.metrics_collector.record_counter("decisions_with_errors", 1, tags)

    def record_function_registration(self, function_id: str):
        """Record function registration metrics"""
        self.metrics_collector.record_counter(
            "functions_registered", 1, {"function_id": function_id}
        )

    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics"""
        tags = {"operation": operation, "hit": str(hit)}
        self.metrics_collector.record_counter("cache_operations", 1, tags)

    def record_storage_operation(self, operation: str, duration_ms: float):
        """Record storage operation metrics"""
        tags = {"operation": operation}
        self.metrics_collector.record_timer(
            "storage_operation_time_ms", duration_ms, tags
        )

    def record_system_metrics(self):
        """Record system-level metrics"""
        import psutil

        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics_collector.record_gauge(
            "memory_usage_mb", memory.used / 1024 / 1024
        )
        self.metrics_collector.record_gauge("memory_usage_percent", memory.percent)

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics_collector.record_gauge("cpu_usage_percent", cpu_percent)

        # Disk usage
        disk = psutil.disk_usage("/")
        self.metrics_collector.record_gauge("disk_usage_percent", disk.percent)

    async def start_monitoring(self, interval_seconds: int = 60):
        """Start the monitoring loop"""
        while self.monitoring_enabled:
            try:
                # Record system metrics
                self.record_system_metrics()

                # Check alerts
                await self.alert_manager.check_alerts()

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(interval_seconds)

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_enabled = False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        # Get decision metrics
        decision_summary = self.metrics_collector.get_metric_summary(
            "decision_execution_time_ms", 60
        )

        # Calculate success rate
        total_decisions = self.metrics_collector.counters.get("decisions_total", 0)
        successful_decisions = self.metrics_collector.counters.get(
            "decisions_success", 0
        )
        success_rate = (
            successful_decisions / total_decisions if total_decisions > 0 else 0
        )

        # Calculate error rate
        failed_decisions = self.metrics_collector.counters.get("decisions_failure", 0)
        error_rate = failed_decisions / total_decisions if total_decisions > 0 else 0

        return {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "total_decisions": total_decisions,
            "successful_decisions": successful_decisions,
            "failed_decisions": failed_decisions,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_execution_time_ms": decision_summary.get("mean", 0),
            "p95_execution_time_ms": decision_summary.get("p95", 0),
            "p99_execution_time_ms": decision_summary.get("p99", 0),
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "registered_functions": self.metrics_collector.counters.get(
                "functions_registered", 0
            ),
            "system_metrics": {
                "memory_usage_mb": self.metrics_collector.gauges.get(
                    "memory_usage_mb", 0
                ),
                "memory_usage_percent": self.metrics_collector.gauges.get(
                    "memory_usage_percent", 0
                ),
                "cpu_usage_percent": self.metrics_collector.gauges.get(
                    "cpu_usage_percent", 0
                ),
                "disk_usage_percent": self.metrics_collector.gauges.get(
                    "disk_usage_percent", 0
                ),
            },
        }

    def get_metrics_for_function(self, function_id: str) -> Dict[str, Any]:
        """Get metrics for a specific function"""
        tags = {"function_id": function_id}

        # Get execution time metrics
        execution_times = [
            point.value
            for point in self.metrics_collector.metrics["decision_execution_time_ms"]
            if point.tags.get("function_id") == function_id
        ]

        if not execution_times:
            return {"error": f"No metrics found for function {function_id}"}

        return {
            "function_id": function_id,
            "total_executions": len(execution_times),
            "avg_execution_time_ms": statistics.mean(execution_times),
            "min_execution_time_ms": min(execution_times),
            "max_execution_time_ms": max(execution_times),
            "p95_execution_time_ms": (
                sorted(execution_times)[int(len(execution_times) * 0.95)]
                if len(execution_times) >= 20
                else max(execution_times)
            ),
            "p99_execution_time_ms": (
                sorted(execution_times)[int(len(execution_times) * 0.99)]
                if len(execution_times) >= 100
                else max(execution_times)
            ),
        }

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert notification callback"""
        self.alert_manager.add_alert_callback(callback)

    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts"""
        return self.alert_manager.get_active_alerts()
