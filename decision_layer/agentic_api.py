"""
Agentic AI API Endpoints

This module provides REST API endpoints for the new agentic AI capabilities
including LLM reasoning, conversational interfaces, workflow orchestration,
and performance monitoring.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .llm_integration import (
    LLMIntegration,
    create_llm_integration,
    AgenticContext,
    ReasoningMode,
)
from .conversational_interface import (
    ConversationalInterface,
    create_conversational_interface,
    ConversationChannel,
)
from .workflow_orchestration import (
    WorkflowOrchestrator,
    create_workflow_orchestrator,
    WorkflowDefinition,
    WorkflowTask,
    TaskStatus,
)
from .agent_performance_monitor import (
    AgentPerformanceMonitor,
    create_agent_performance_monitor,
    PerformanceMetric,
)
from .core import DecisionEngine
from .config import DecisionLayerConfig, load_config

logger = logging.getLogger(__name__)

# Create router for agentic endpoints
agentic_router = APIRouter(prefix="/agentic", tags=["Agentic AI"])


# Request/Response Models
class AgenticDecisionRequest(BaseModel):
    """Request model for agentic decision making"""

    function_id: str = Field(..., description="Decision function ID")
    input_data: Dict[str, Any] = Field(..., description="Input data for the decision")
    citizen_id: Optional[str] = Field(None, description="Citizen identifier")
    service_type: Optional[str] = Field(None, description="Type of service")
    urgency_level: str = Field(
        "normal", description="Urgency level (low, normal, high, critical)"
    )
    reasoning_mode: str = Field(
        "autonomous", description="Reasoning mode (autonomous, assisted, explanatory)"
    )
    legal_framework: Optional[str] = Field(None, description="Legal framework to apply")


class ConversationRequest(BaseModel):
    """Request model for conversational interface"""

    message: str = Field(..., description="Citizen message")
    session_id: str = Field(..., description="Session identifier")
    citizen_id: Optional[str] = Field(None, description="Citizen identifier")
    channel: str = Field("web_chat", description="Communication channel")
    language: str = Field("en", description="Language preference")


class WorkflowRequest(BaseModel):
    """Request model for workflow orchestration"""

    workflow_definition: Dict[str, Any] = Field(..., description="Workflow definition")
    initial_context: Optional[Dict[str, Any]] = Field(
        None, description="Initial context data"
    )


class PerformanceMetricsRequest(BaseModel):
    """Request model for performance metrics"""

    agent_id: str = Field(..., description="Agent identifier")
    metric_type: str = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    context: Optional[Dict[str, Any]] = Field(None, description="Context data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AgenticDecisionResponse(BaseModel):
    """Response model for agentic decisions"""

    decision: Dict[str, Any] = Field(..., description="Decision result")
    confidence: float = Field(..., description="Confidence score")
    reasoning_steps: List[str] = Field(..., description="Reasoning steps")
    legal_basis: List[str] = Field(..., description="Legal basis")
    alternatives_considered: List[str] = Field(
        ..., description="Alternatives considered"
    )
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment")
    trace_id: str = Field(..., description="Trace identifier")


class ConversationResponse(BaseModel):
    """Response model for conversational interface"""

    message: str = Field(..., description="Agent response message")
    actions: List[Dict[str, Any]] = Field(..., description="Actions to take")
    next_steps: List[str] = Field(..., description="Next steps")
    requires_human: bool = Field(..., description="Whether human assistance is needed")
    confidence: float = Field(..., description="Confidence score")
    trace_id: str = Field(..., description="Trace identifier")


class WorkflowResponse(BaseModel):
    """Response model for workflow orchestration"""

    execution_id: str = Field(..., description="Workflow execution ID")
    status: str = Field(..., description="Execution status")
    started_at: str = Field(..., description="Start timestamp")
    progress: Dict[str, Any] = Field(..., description="Progress information")


class PerformanceReportResponse(BaseModel):
    """Response model for performance reports"""

    agent_id: str = Field(..., description="Agent identifier")
    performance_score: float = Field(..., description="Overall performance score")
    effectiveness_metrics: Dict[str, Any] = Field(
        ..., description="Effectiveness metrics"
    )
    trend_analysis: Dict[str, str] = Field(..., description="Trend analysis")
    recommendations: List[str] = Field(..., description="Recommendations")
    data_points: int = Field(..., description="Number of data points")


# Global instances (would be injected in production)
_llm_integration: Optional[LLMIntegration] = None
_conversational_interface: Optional[ConversationalInterface] = None
_workflow_orchestrator: Optional[WorkflowOrchestrator] = None
_performance_monitor: Optional[AgentPerformanceMonitor] = None


def get_llm_integration() -> LLMIntegration:
    """Get LLM integration instance"""
    global _llm_integration
    if _llm_integration is None:
        config = DecisionLayerConfig()
        _llm_integration = create_llm_integration(config)
    return _llm_integration


def get_conversational_interface() -> ConversationalInterface:
    """Get conversational interface instance"""
    global _conversational_interface
    if _conversational_interface is None:
        # This would need a decision engine in production
        from .core import create_decision_engine

        engine = create_decision_engine()
        llm_integration = get_llm_integration()
        _conversational_interface = create_conversational_interface(
            engine, llm_integration
        )
    return _conversational_interface


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get workflow orchestrator instance"""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        from .core import create_decision_engine

        engine = create_decision_engine()
        llm_integration = get_llm_integration()
        _workflow_orchestrator = create_workflow_orchestrator(engine, llm_integration)
    return _workflow_orchestrator


def get_performance_monitor() -> AgentPerformanceMonitor:
    """Get performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        llm_integration = get_llm_integration()
        _performance_monitor = create_agent_performance_monitor(llm_integration)
    return _performance_monitor


# API Endpoints


@agentic_router.post("/decisions", response_model=AgenticDecisionResponse)
async def make_agentic_decision(
    request: AgenticDecisionRequest,
    llm_integration: LLMIntegration = Depends(get_llm_integration),
):
    """
    Make an agentic decision using LLM reasoning

    This endpoint demonstrates autonomous decision-making with full reasoning,
    legal basis, and risk assessment.
    """
    try:
        # Create agentic context
        agentic_context = AgenticContext(
            citizen_id=request.citizen_id,
            service_type=request.service_type,
            urgency_level=request.urgency_level,
            legal_framework=request.legal_framework,
        )

        # Convert reasoning mode string to enum
        reasoning_mode = ReasoningMode(request.reasoning_mode)

        # Create a mock decision function (in production, this would come from registry)
        def mock_decision_function(
            input_data: Dict[str, Any], context
        ) -> Dict[str, Any]:
            return {"approved": True, "reason": "Mock decision for demo"}

        # Use LLM reasoning
        decision = await llm_integration.reason_about_decision(
            decision_function=mock_decision_function,
            input_data=request.input_data,
            context=agentic_context,
            reasoning_mode=reasoning_mode,
        )

        return AgenticDecisionResponse(
            decision=decision.decision,
            confidence=decision.confidence,
            reasoning_steps=decision.reasoning_steps,
            legal_basis=decision.legal_basis,
            alternatives_considered=decision.alternatives_considered,
            risk_assessment=decision.risk_assessment,
            trace_id=decision.trace_id,
        )

    except Exception as e:
        logger.error(f"Error making agentic decision: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to make agentic decision: {e}"
        )


@agentic_router.post("/conversations", response_model=ConversationResponse)
async def process_conversation(
    request: ConversationRequest,
    conversational_interface: ConversationalInterface = Depends(
        get_conversational_interface
    ),
):
    """
    Process a citizen conversation using natural language

    This endpoint handles natural language interactions with citizens,
    providing intelligent responses and appropriate actions.
    """
    try:
        # Convert channel string to enum
        channel = ConversationChannel(request.channel)

        # Process the conversation
        response = await conversational_interface.process_citizen_message(
            message=request.message,
            session_id=request.session_id,
            channel=channel,
            citizen_id=request.citizen_id,
            language=request.language,
        )

        return ConversationResponse(
            message=response.message,
            actions=response.actions,
            next_steps=response.next_steps,
            requires_human=response.requires_human,
            confidence=response.confidence,
            trace_id=response.trace_id,
        )

    except Exception as e:
        logger.error(f"Error processing conversation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process conversation: {e}"
        )


@agentic_router.post("/workflows", response_model=WorkflowResponse)
async def start_workflow(
    request: WorkflowRequest,
    workflow_orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
):
    """
    Start a new workflow execution

    This endpoint starts autonomous workflow orchestration with intelligent
    resource allocation and task management.
    """
    try:
        # Convert workflow definition dict to WorkflowDefinition object
        workflow_def = WorkflowDefinition(
            workflow_id=request.workflow_definition.get(
                "workflow_id", "default_workflow"
            ),
            name=request.workflow_definition.get("name", "Default Workflow"),
            description=request.workflow_definition.get(
                "description", "Default workflow description"
            ),
            version=request.workflow_definition.get("version", "1.0"),
            tasks=[
                WorkflowTask(
                    task_id=task.get("task_id", f"task_{i}"),
                    name=task.get("name", f"Task {i}"),
                    description=task.get("description", f"Task {i} description"),
                    task_type=task.get("task_type", "generic"),
                    required_capabilities=task.get("required_capabilities", []),
                    estimated_duration=task.get("estimated_duration", 5),
                    dependencies=task.get("dependencies", []),
                    input_data=task.get("input_data", {}),
                )
                for i, task in enumerate(request.workflow_definition.get("tasks", []))
            ],
            success_criteria=request.workflow_definition.get("success_criteria", []),
            sla_requirements=request.workflow_definition.get("sla_requirements", {}),
        )

        # Start workflow
        execution_id = await workflow_orchestrator.start_workflow(
            workflow_definition=workflow_def,
            initial_context=request.initial_context or {},
        )

        # Get initial status
        status = await workflow_orchestrator.get_workflow_status(execution_id)

        return WorkflowResponse(
            execution_id=execution_id,
            status=status["status"],
            started_at=status["started_at"],
            progress=status["progress"],
        )

    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {e}")


@agentic_router.get("/workflows/{execution_id}")
async def get_workflow_status(
    execution_id: str,
    workflow_orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
):
    """
    Get workflow execution status

    This endpoint provides real-time status of workflow executions.
    """
    try:
        status = await workflow_orchestrator.get_workflow_status(execution_id)
        return status

    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get workflow status: {e}"
        )


@agentic_router.post("/performance/metrics")
async def record_performance_metric(
    request: PerformanceMetricsRequest,
    performance_monitor: AgentPerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Record a performance metric for an agent

    This endpoint records performance data for monitoring and analysis.
    """
    try:
        # Convert metric type string to enum
        metric_type = PerformanceMetric(request.metric_type)

        # Record the metric
        await performance_monitor.record_performance_metric(
            agent_id=request.agent_id,
            metric_type=metric_type,
            value=request.value,
            context=request.context or {},
            metadata=request.metadata or {},
        )

        return {"status": "success", "message": "Performance metric recorded"}

    except Exception as e:
        logger.error(f"Error recording performance metric: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to record performance metric: {e}"
        )


@agentic_router.get("/performance/agents/{agent_id}")
async def get_agent_performance(
    agent_id: str,
    performance_monitor: AgentPerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get performance report for a specific agent

    This endpoint provides detailed performance analysis for agents.
    """
    try:
        effectiveness = await performance_monitor.get_agent_effectiveness(agent_id)

        if "error" in effectiveness:
            raise HTTPException(status_code=404, detail=effectiveness["error"])

        return PerformanceReportResponse(
            agent_id=agent_id,
            performance_score=effectiveness.get("effectiveness_metrics", {})
            .get("decision_accuracy", {})
            .get("mean", 0.0),
            effectiveness_metrics=effectiveness.get("effectiveness_metrics", {}),
            trend_analysis=effectiveness.get("trend_analysis", {}),
            recommendations=effectiveness.get("recommendations", []),
            data_points=effectiveness.get("data_points", 0),
        )

    except Exception as e:
        logger.error(f"Error getting agent performance: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent performance: {e}"
        )


@agentic_router.get("/performance/drift/{agent_id}")
async def detect_agent_drift(
    agent_id: str,
    performance_monitor: AgentPerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Detect drift in agent behavior or performance

    This endpoint analyzes agent behavior for signs of drift or degradation.
    """
    try:
        drift_results = await performance_monitor.detect_agent_drift(agent_id)

        return {
            "agent_id": agent_id,
            "drift_detected": len(drift_results) > 0,
            "drift_issues": [
                {
                    "drift_type": drift.drift_type.value,
                    "severity": drift.severity,
                    "confidence": drift.confidence,
                    "description": drift.description,
                    "affected_metrics": [m.value for m in drift.affected_metrics],
                    "recommended_actions": drift.recommended_actions,
                    "detected_at": drift.detected_at.isoformat(),
                }
                for drift in drift_results
            ],
        }

    except Exception as e:
        logger.error(f"Error detecting agent drift: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to detect agent drift: {e}"
        )


@agentic_router.get("/performance/report")
async def get_performance_report(
    agent_id: Optional[str] = None,
    performance_monitor: AgentPerformanceMonitor = Depends(get_performance_monitor),
):
    """
    Get comprehensive performance report

    This endpoint provides overall performance analysis across all agents.
    """
    try:
        report = await performance_monitor.generate_performance_report(agent_id)
        return report

    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate performance report: {e}"
        )


@agentic_router.post("/coordination")
async def coordinate_agents(
    task_description: str,
    required_capabilities: List[str],
    llm_integration: LLMIntegration = Depends(get_llm_integration),
):
    """
    Coordinate multiple agents for complex tasks

    This endpoint demonstrates multi-agent coordination for complex government processes.
    """
    try:
        # Create agentic context
        context = AgenticContext(
            service_type="multi_agent_coordination", urgency_level="normal"
        )

        # Coordinate agents
        coordination_result = await llm_integration.coordinate_with_other_agents(
            task_description=task_description,
            required_capabilities=required_capabilities,
            context=context,
        )

        return coordination_result

    except Exception as e:
        logger.error(f"Error coordinating agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to coordinate agents: {e}")


@agentic_router.get("/health")
async def health_check():
    """
    Health check for agentic AI services

    This endpoint verifies that all agentic AI services are operational.
    """
    try:
        # Check if all services are initialized
        llm_integration = get_llm_integration()
        conversational_interface = get_conversational_interface()
        workflow_orchestrator = get_workflow_orchestrator()
        performance_monitor = get_performance_monitor()

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "llm_integration": "operational",
                "conversational_interface": "operational",
                "workflow_orchestrator": "operational",
                "performance_monitor": "operational",
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")
