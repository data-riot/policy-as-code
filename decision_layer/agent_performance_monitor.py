"""
Agent Performance Monitoring for Agentic Government Services

This module provides comprehensive monitoring and analytics for agent performance,
including effectiveness tracking, drift detection, and optimization recommendations.
"""

import json
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .llm_integration import LLMIntegration, ReasoningMode

logger = logging.getLogger(__name__)


class PerformanceMetric(str, Enum):
    """Types of performance metrics"""

    DECISION_ACCURACY = "decision_accuracy"
    RESPONSE_TIME = "response_time"
    CITIZEN_SATISFACTION = "citizen_satisfaction"
    LEGAL_COMPLIANCE = "legal_compliance"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    ERROR_RATE = "error_rate"
    UPTIME = "uptime"


class DriftType(str, Enum):
    """Types of agent drift"""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    BEHAVIORAL_DRIFT = "behavioral_drift"
    DECISION_BIAS = "decision_bias"
    CAPABILITY_DRIFT = "capability_drift"


@dataclass
class PerformanceDataPoint:
    """Individual performance data point"""

    timestamp: datetime
    agent_id: str
    metric_type: PerformanceMetric
    value: float
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPerformanceProfile:
    """Performance profile for an agent"""

    agent_id: str
    baseline_metrics: Dict[PerformanceMetric, float]
    current_metrics: Dict[PerformanceMetric, float]
    trend_analysis: Dict[PerformanceMetric, str]  # "improving", "stable", "declining"
    performance_score: float
    last_updated: datetime
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DriftDetectionResult:
    """Result of drift detection analysis"""

    agent_id: str
    drift_type: DriftType
    severity: str  # "low", "medium", "high", "critical"
    confidence: float
    description: str
    affected_metrics: List[PerformanceMetric]
    recommended_actions: List[str]
    detected_at: datetime


@dataclass
class OptimizationRecommendation:
    """Recommendation for agent optimization"""

    agent_id: str
    recommendation_type: str
    priority: str  # "low", "medium", "high", "critical"
    description: str
    expected_improvement: float
    implementation_effort: str  # "low", "medium", "high"
    dependencies: List[str] = field(default_factory=list)


class AgentPerformanceMonitor:
    """Monitors and optimizes agent performance"""

    def __init__(self, llm_integration: LLMIntegration):
        self.llm_integration = llm_integration
        self.performance_data: List[PerformanceDataPoint] = []
        self.agent_profiles: Dict[str, AgentPerformanceProfile] = {}
        self.drift_alerts: List[DriftDetectionResult] = []
        self.optimization_recommendations: List[OptimizationRecommendation] = []

    async def record_performance_metric(
        self,
        agent_id: str,
        metric_type: PerformanceMetric,
        value: float,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record a performance metric for an agent

        Args:
            agent_id: Identifier of the agent
            metric_type: Type of metric being recorded
            value: Metric value
            context: Context in which the metric was recorded
            metadata: Additional metadata
        """
        try:
            data_point = PerformanceDataPoint(
                timestamp=datetime.now(timezone.utc),
                agent_id=agent_id,
                metric_type=metric_type,
                value=value,
                context=context or {},
                metadata=metadata or {},
            )

            self.performance_data.append(data_point)

            # Update agent profile if it exists
            if agent_id in self.agent_profiles:
                await self._update_agent_profile(agent_id)

            logger.debug(
                f"Recorded {metric_type.value} metric for agent {agent_id}: {value}"
            )

        except Exception as e:
            logger.error(f"Error recording performance metric: {e}")

    async def get_agent_effectiveness(self, agent_id: str) -> Dict[str, Any]:
        """
        Get effectiveness metrics for an agent

        Args:
            agent_id: Identifier of the agent

        Returns:
            Effectiveness metrics and analysis
        """
        try:
            # Get recent performance data for the agent
            recent_data = [
                dp
                for dp in self.performance_data
                if dp.agent_id == agent_id
                and dp.timestamp >= datetime.now(timezone.utc) - timedelta(days=30)
            ]

            if not recent_data:
                return {"error": "No performance data available for agent"}

            # Calculate effectiveness metrics
            effectiveness = await self._calculate_effectiveness_metrics(
                agent_id, recent_data
            )

            # Get trend analysis
            trends = await self._analyze_performance_trends(agent_id, recent_data)

            # Get recommendations
            recommendations = await self._generate_effectiveness_recommendations(
                agent_id, effectiveness, trends
            )

            return {
                "agent_id": agent_id,
                "effectiveness_metrics": effectiveness,
                "trend_analysis": trends,
                "recommendations": recommendations,
                "data_points": len(recent_data),
                "analysis_period": "30 days",
            }

        except Exception as e:
            logger.error(f"Error getting agent effectiveness: {e}")
            return {"error": f"Failed to analyze agent effectiveness: {e}"}

    async def detect_agent_drift(self, agent_id: str) -> List[DriftDetectionResult]:
        """
        Detect drift in agent behavior or performance

        Args:
            agent_id: Identifier of the agent

        Returns:
            List of detected drift issues
        """
        try:
            # Get performance data for the agent
            agent_data = [
                dp
                for dp in self.performance_data
                if dp.agent_id == agent_id
                and dp.timestamp >= datetime.now(timezone.utc) - timedelta(days=7)
            ]

            if len(agent_data) < 10:  # Need minimum data points
                return []

            # Analyze different types of drift
            drift_results = []

            # Performance degradation drift
            performance_drift = await self._detect_performance_drift(
                agent_id, agent_data
            )
            if performance_drift:
                drift_results.append(performance_drift)

            # Behavioral drift
            behavioral_drift = await self._detect_behavioral_drift(agent_id, agent_data)
            if behavioral_drift:
                drift_results.append(behavioral_drift)

            # Decision bias drift
            bias_drift = await self._detect_decision_bias_drift(agent_id, agent_data)
            if bias_drift:
                drift_results.append(bias_drift)

            # Store drift alerts
            self.drift_alerts.extend(drift_results)

            return drift_results

        except Exception as e:
            logger.error(f"Error detecting agent drift: {e}")
            return []

    async def optimize_agent_coordination(
        self, coordination_data: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """
        Optimize how agents coordinate with each other

        Args:
            coordination_data: Data about agent coordination patterns

        Returns:
            List of optimization recommendations
        """
        try:
            # Use LLM to analyze coordination patterns
            prompt = f"""
            Analyze agent coordination patterns and suggest optimizations.

            Coordination Data: {json.dumps(coordination_data, indent=2)}

            Analyze:
            1. Communication efficiency between agents
            2. Task handoff patterns
            3. Resource utilization
            4. Bottlenecks and delays
            5. Error propagation patterns

            Suggest specific optimizations for:
            1. Communication protocols
            2. Task scheduling
            3. Resource allocation
            4. Error handling
            5. Performance monitoring

            Return JSON with optimization recommendations.
            """

            response = await self.llm_integration._call_llm(
                prompt, ReasoningMode.AUTONOMOUS
            )
            recommendations_data = json.loads(response)

            # Convert to OptimizationRecommendation objects
            recommendations = []
            for rec_data in recommendations_data.get("recommendations", []):
                recommendation = OptimizationRecommendation(
                    agent_id=rec_data.get("agent_id", "coordination"),
                    recommendation_type=rec_data.get("type", "coordination"),
                    priority=rec_data.get("priority", "medium"),
                    description=rec_data.get("description", ""),
                    expected_improvement=rec_data.get("expected_improvement", 0.0),
                    implementation_effort=rec_data.get(
                        "implementation_effort", "medium"
                    ),
                    dependencies=rec_data.get("dependencies", []),
                )
                recommendations.append(recommendation)

            self.optimization_recommendations.extend(recommendations)

            return recommendations

        except Exception as e:
            logger.error(f"Error optimizing agent coordination: {e}")
            return []

    async def generate_performance_report(
        self, agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report

        Args:
            agent_id: Optional specific agent ID, or None for all agents

        Returns:
            Performance report
        """
        try:
            if agent_id:
                agents = [agent_id]
            else:
                agents = list(set(dp.agent_id for dp in self.performance_data))

            report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "agents_analyzed": len(agents),
                "total_data_points": len(self.performance_data),
                "agent_summaries": {},
                "overall_insights": [],
                "recommendations": [],
            }

            # Analyze each agent
            for agent in agents:
                agent_summary = await self._generate_agent_summary(agent)
                report["agent_summaries"][agent] = agent_summary

            # Generate overall insights
            report["overall_insights"] = await self._generate_overall_insights(agents)

            # Generate recommendations
            report["recommendations"] = await self._generate_global_recommendations(
                agents
            )

            return report

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": f"Failed to generate performance report: {e}"}

    async def _update_agent_profile(self, agent_id: str):
        """Update agent performance profile"""
        try:
            # Get recent performance data
            recent_data = [
                dp
                for dp in self.performance_data
                if dp.agent_id == agent_id
                and dp.timestamp >= datetime.now(timezone.utc) - timedelta(days=7)
            ]

            if not recent_data:
                return

            # Calculate current metrics
            current_metrics = {}
            for metric_type in PerformanceMetric:
                metric_data = [
                    dp.value for dp in recent_data if dp.metric_type == metric_type
                ]
                if metric_data:
                    current_metrics[metric_type] = statistics.mean(metric_data)

            # Update or create profile
            if agent_id in self.agent_profiles:
                profile = self.agent_profiles[agent_id]
                profile.current_metrics = current_metrics
                profile.last_updated = datetime.now(timezone.utc)
            else:
                profile = AgentPerformanceProfile(
                    agent_id=agent_id,
                    baseline_metrics=current_metrics.copy(),
                    current_metrics=current_metrics,
                    trend_analysis={},
                    performance_score=0.0,
                    last_updated=datetime.now(timezone.utc),
                )
                self.agent_profiles[agent_id] = profile

            # Calculate performance score
            profile.performance_score = await self._calculate_performance_score(profile)

        except Exception as e:
            logger.error(f"Error updating agent profile: {e}")

    async def _calculate_effectiveness_metrics(
        self, agent_id: str, data: List[PerformanceDataPoint]
    ) -> Dict[str, Any]:
        """Calculate effectiveness metrics for an agent"""
        metrics = {}

        for metric_type in PerformanceMetric:
            metric_data = [dp.value for dp in data if dp.metric_type == metric_type]
            if metric_data:
                metrics[metric_type.value] = {
                    "mean": statistics.mean(metric_data),
                    "median": statistics.median(metric_data),
                    "std_dev": (
                        statistics.stdev(metric_data) if len(metric_data) > 1 else 0
                    ),
                    "min": min(metric_data),
                    "max": max(metric_data),
                    "count": len(metric_data),
                }

        return metrics

    async def _analyze_performance_trends(
        self, agent_id: str, data: List[PerformanceDataPoint]
    ) -> Dict[str, str]:
        """Analyze performance trends for an agent"""
        trends = {}

        for metric_type in PerformanceMetric:
            metric_data = [
                (dp.timestamp, dp.value) for dp in data if dp.metric_type == metric_type
            ]
            if len(metric_data) < 3:
                continue

            # Simple trend analysis (could be more sophisticated)
            values = [value for _, value in metric_data]
            if len(values) >= 3:
                recent_avg = statistics.mean(values[-3:])
                earlier_avg = statistics.mean(values[:3])

                if recent_avg > earlier_avg * 1.05:
                    trends[metric_type.value] = "improving"
                elif recent_avg < earlier_avg * 0.95:
                    trends[metric_type.value] = "declining"
                else:
                    trends[metric_type.value] = "stable"

        return trends

    async def _generate_effectiveness_recommendations(
        self, agent_id: str, effectiveness: Dict[str, Any], trends: Dict[str, str]
    ) -> List[str]:
        """Generate recommendations for improving agent effectiveness"""
        recommendations = []

        # Analyze trends and suggest improvements
        for metric, trend in trends.items():
            if trend == "declining":
                recommendations.append(f"Address declining performance in {metric}")
            elif trend == "improving":
                recommendations.append(f"Maintain positive trend in {metric}")

        # Check for low performance scores
        for metric, data in effectiveness.items():
            if isinstance(data, dict) and "mean" in data:
                if data["mean"] < 0.7:  # Threshold for low performance
                    recommendations.append(
                        f"Improve {metric} (current: {data['mean']:.2f})"
                    )

        return recommendations

    async def _detect_performance_drift(
        self, agent_id: str, data: List[PerformanceDataPoint]
    ) -> Optional[DriftDetectionResult]:
        """Detect performance degradation drift"""
        # Simple drift detection (could be more sophisticated)
        for metric_type in PerformanceMetric:
            metric_data = [dp.value for dp in data if dp.metric_type == metric_type]
            if len(metric_data) < 5:
                continue

            # Check for significant decline
            recent_avg = statistics.mean(metric_data[-3:])
            earlier_avg = statistics.mean(metric_data[:3])

            if recent_avg < earlier_avg * 0.8:  # 20% decline threshold
                return DriftDetectionResult(
                    agent_id=agent_id,
                    drift_type=DriftType.PERFORMANCE_DEGRADATION,
                    severity="medium",
                    confidence=0.8,
                    description=f"Performance degradation detected in {metric_type.value}",
                    affected_metrics=[metric_type],
                    recommended_actions=[
                        "Review recent changes",
                        "Check resource allocation",
                        "Monitor for errors",
                    ],
                    detected_at=datetime.now(timezone.utc),
                )

        return None

    async def _detect_behavioral_drift(
        self, agent_id: str, data: List[PerformanceDataPoint]
    ) -> Optional[DriftDetectionResult]:
        """Detect behavioral drift in agent"""
        # Mock implementation - would analyze decision patterns, response styles, etc.
        return None

    async def _detect_decision_bias_drift(
        self, agent_id: str, data: List[PerformanceDataPoint]
    ) -> Optional[DriftDetectionResult]:
        """Detect decision bias drift"""
        # Mock implementation - would analyze decision patterns for bias
        return None

    async def _calculate_performance_score(
        self, profile: AgentPerformanceProfile
    ) -> float:
        """Calculate overall performance score for an agent"""
        if not profile.current_metrics:
            return 0.0

        # Simple weighted average (could be more sophisticated)
        weights = {
            PerformanceMetric.DECISION_ACCURACY: 0.3,
            PerformanceMetric.RESPONSE_TIME: 0.2,
            PerformanceMetric.CITIZEN_SATISFACTION: 0.2,
            PerformanceMetric.LEGAL_COMPLIANCE: 0.2,
            PerformanceMetric.ERROR_RATE: 0.1,
        }

        total_score = 0.0
        total_weight = 0.0

        for metric, value in profile.current_metrics.items():
            if metric in weights:
                # Normalize value to 0-1 scale (assuming higher is better)
                normalized_value = min(1.0, max(0.0, value))
                total_score += normalized_value * weights[metric]
                total_weight += weights[metric]

        return total_score / total_weight if total_weight > 0 else 0.0

    async def _generate_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """Generate summary for a specific agent"""
        profile = self.agent_profiles.get(agent_id)
        if not profile:
            return {"error": "No profile available"}

        return {
            "agent_id": agent_id,
            "performance_score": profile.performance_score,
            "current_metrics": profile.current_metrics,
            "trend_analysis": profile.trend_analysis,
            "recommendations": profile.recommendations,
            "last_updated": profile.last_updated.isoformat(),
        }

    async def _generate_overall_insights(self, agents: List[str]) -> List[str]:
        """Generate overall insights across all agents"""
        insights: List[str] = []

        if not agents:
            return insights

        # Calculate average performance
        total_score = sum(
            self.agent_profiles.get(
                agent,
                AgentPerformanceProfile(
                    "", {}, {}, {}, 0.0, datetime.now(timezone.utc)
                ),
            ).performance_score
            for agent in agents
        )
        avg_score = total_score / len(agents)

        if avg_score > 0.8:
            insights.append("Overall agent performance is excellent")
        elif avg_score > 0.6:
            insights.append(
                "Overall agent performance is good with room for improvement"
            )
        else:
            insights.append("Overall agent performance needs attention")

        # Check for common issues
        declining_agents = [
            agent
            for agent in agents
            if agent in self.agent_profiles
            and any(
                trend == "declining"
                for trend in self.agent_profiles[agent].trend_analysis.values()
            )
        ]

        if declining_agents:
            insights.append(f"Performance declining in {len(declining_agents)} agents")

        return insights

    async def _generate_global_recommendations(self, agents: List[str]) -> List[str]:
        """Generate global recommendations"""
        recommendations = []

        # Add recommendations from optimization analysis
        for rec in self.optimization_recommendations:
            if rec.agent_id in agents or rec.agent_id == "coordination":
                recommendations.append(rec.description)

        return recommendations


def create_agent_performance_monitor(
    llm_integration: LLMIntegration,
) -> AgentPerformanceMonitor:
    """Factory function to create agent performance monitor"""
    return AgentPerformanceMonitor(llm_integration)
