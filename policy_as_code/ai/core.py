"""
AI Core module for Policy as Code

This module provides core AI functionality and interfaces used by
other AI components including LLM integration, conversational interfaces,
workflow orchestration, and monitoring.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AIRequest:
    """Base class for AI requests"""

    prompt: str
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class AIResponse:
    """Base class for AI responses"""

    content: str
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate a response for the given request"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the AI provider is healthy"""
        pass


class LLMProvider(AIProvider):
    """LLM provider implementation"""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name

    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate a response using LLM"""
        # Mock implementation - replace with actual LLM integration
        return AIResponse(
            content=f"Mock LLM response for: {request.prompt}",
            confidence=0.85,
            metadata={"model": self.model_name},
        )

    async def health_check(self) -> bool:
        """Check LLM provider health"""
        return True


class ConversationalAI:
    """Conversational AI interface"""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a conversational message"""
        request = AIRequest(prompt=message, context=context)
        response = await self.provider.generate_response(request)
        return response.content


class WorkflowOrchestrator:
    """AI workflow orchestrator"""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def orchestrate_workflow(
        self, workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate an AI workflow"""
        # Mock implementation
        return {
            "status": "completed",
            "steps_executed": len(workflow_config.get("steps", [])),
            "result": "Workflow completed successfully",
        }


class AIMonitor:
    """AI performance monitor"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}

    def record_metric(self, metric_name: str, value: float):
        """Record a performance metric"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics summary"""
        summary = {}
        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }
        return summary


# Export commonly used classes
__all__ = [
    "AIRequest",
    "AIResponse",
    "AIProvider",
    "LLMProvider",
    "ConversationalAI",
    "WorkflowOrchestrator",
    "AIMonitor",
]
