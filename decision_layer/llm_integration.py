"""
LLM Integration for Agentic Decision Making

This module provides LLM-powered reasoning capabilities for autonomous decision making,
natural language processing, and agentic coordination.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from .core import DecisionContext, DecisionFunction
from .errors import DecisionLayerError, ValidationError
from .config import DecisionLayerConfig

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    MOCK = "mock"


class ReasoningMode(str, Enum):
    """Reasoning modes for agentic decision making"""

    AUTONOMOUS = "autonomous"  # Full autonomous reasoning
    ASSISTED = "assisted"  # Human-assisted reasoning
    EXPLANATORY = "explanatory"  # Generate explanations only


@dataclass
class AgenticDecision:
    """Result of agentic decision making"""

    decision: Any
    confidence: float
    reasoning_steps: List[str]
    legal_basis: List[str]
    alternatives_considered: List[str]
    risk_assessment: Dict[str, Any]
    trace_id: str


@dataclass
class AgenticContext:
    """Context for agentic reasoning"""

    citizen_id: Optional[str] = None
    service_type: Optional[str] = None
    urgency_level: str = "normal"
    legal_framework: Optional[str] = None
    historical_precedents: List[Dict] = None
    cross_agency_data: Dict[str, Any] = None


class LLMIntegration:
    """LLM integration for agentic decision making"""

    def __init__(self, config: DecisionLayerConfig, registry=None):
        self.config = config
        self.registry = registry
        self.provider = config.integrations.llm.provider
        self.llm_config = config.integrations.llm.config

    async def reason_about_decision(
        self,
        decision_function: DecisionFunction,
        input_data: Dict[str, Any],
        context: AgenticContext,
        reasoning_mode: ReasoningMode = ReasoningMode.AUTONOMOUS,
    ) -> AgenticDecision:
        """
        Use LLM to reason about a decision with full context

        Args:
            decision_function: The decision function to reason about
            input_data: Input data for the decision
            context: Agentic context for reasoning
            reasoning_mode: How autonomous the reasoning should be

        Returns:
            AgenticDecision with reasoning and confidence
        """
        try:
            # Build reasoning prompt
            prompt = await self._build_reasoning_prompt(
                decision_function, input_data, context, reasoning_mode
            )

            # Get LLM response
            response = await self._call_llm(prompt, reasoning_mode)

            # Parse and validate response
            decision = await self._parse_agentic_response(response, input_data)

            return decision

        except Exception as e:
            logger.error(f"Error in agentic reasoning: {e}")
            raise DecisionLayerError(f"Agentic reasoning failed: {e}")

    async def coordinate_with_other_agents(
        self,
        task_description: str,
        required_capabilities: List[str],
        context: AgenticContext,
    ) -> Dict[str, Any]:
        """
        Coordinate with other agents for complex multi-step processes

        Args:
            task_description: Description of the task to coordinate
            required_capabilities: List of capabilities needed
            context: Context for coordination

        Returns:
            Coordination result with agent assignments
        """
        try:
            prompt = f"""
            You are coordinating a government task that requires multiple agents.

            Task: {task_description}
            Required Capabilities: {', '.join(required_capabilities)}
            Context: {json.dumps(context.__dict__, default=str)}

            Design a coordination plan that:
            1. Identifies which agents are needed
            2. Defines the sequence of operations
            3. Establishes communication protocols
            4. Sets up error handling and fallbacks
            5. Ensures compliance with legal requirements

            Return a JSON response with the coordination plan.
            """

            response = await self._call_llm(prompt, ReasoningMode.AUTONOMOUS)
            coordination_plan = json.loads(response)

            return coordination_plan

        except Exception as e:
            logger.error(f"Error in agent coordination: {e}")
            raise DecisionLayerError(f"Agent coordination failed: {e}")

    async def adapt_decision_strategy(
        self,
        decision_function: DecisionFunction,
        feedback: Dict[str, Any],
        performance_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Adapt decision strategy based on feedback and performance

        Args:
            decision_function: The decision function to adapt
            feedback: Feedback from citizens, auditors, or other agents
            performance_metrics: Performance data for the function

        Returns:
            Adaptation recommendations
        """
        try:
            prompt = f"""
            Analyze the performance of this decision function and suggest improvements.

            Function: {decision_function.function_id}
            Current Performance: {json.dumps(performance_metrics)}
            Feedback: {json.dumps(feedback)}

            Suggest specific improvements to:
            1. Decision logic
            2. Input validation
            3. Output quality
            4. Legal compliance
            5. Citizen experience

            Return a JSON response with specific, actionable recommendations.
            """

            response = await self._call_llm(prompt, ReasoningMode.ASSISTED)
            adaptations = json.loads(response)

            return adaptations

        except Exception as e:
            logger.error(f"Error in strategy adaptation: {e}")
            raise DecisionLayerError(f"Strategy adaptation failed: {e}")

    async def generate_citizen_explanation(
        self,
        decision_result: Any,
        decision_context: DecisionContext,
        citizen_language: str = "en",
    ) -> str:
        """
        Generate human-readable explanation for citizens

        Args:
            decision_result: The decision that was made
            decision_context: Context of the decision
            citizen_language: Language for the explanation

        Returns:
            Natural language explanation
        """
        try:
            prompt = f"""
            Explain this government decision in simple, clear language for citizens.

            Decision: {json.dumps(decision_result)}
            Context: {json.dumps(decision_context.__dict__, default=str)}
            Language: {citizen_language}

            The explanation should:
            1. Be clear and jargon-free
            2. Explain the reasoning behind the decision
            3. Reference relevant laws or policies
            4. Provide next steps if applicable
            5. Include contact information for questions

            Write in a helpful, professional tone.
            """

            response = await self._call_llm(prompt, ReasoningMode.EXPLANATORY)
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating citizen explanation: {e}")
            return "Unable to generate explanation at this time."

    async def _build_reasoning_prompt(
        self,
        decision_function: DecisionFunction,
        input_data: Dict[str, Any],
        context: AgenticContext,
        reasoning_mode: ReasoningMode,
    ) -> str:
        """Build the reasoning prompt for the LLM"""

        mode_instructions = {
            ReasoningMode.AUTONOMOUS: "Make the decision autonomously with full reasoning.",
            ReasoningMode.ASSISTED: "Provide reasoning and recommendations for human review.",
            ReasoningMode.EXPLANATORY: "Explain the decision process and reasoning.",
        }

        prompt = f"""
        You are an AI agent making government decisions. {mode_instructions[reasoning_mode]}

        Decision Function: {decision_function.function_id}
        Function Description: {getattr(decision_function, 'description', 'No description available')}

        Input Data: {json.dumps(input_data, indent=2)}

        Context:
        - Citizen ID: {context.citizen_id or 'Not provided'}
        - Service Type: {context.service_type or 'Not specified'}
        - Urgency: {context.urgency_level}
        - Legal Framework: {context.legal_framework or 'Standard government regulations'}

        Historical Precedents: {json.dumps(context.historical_precedents or [], indent=2)}
        Cross-Agency Data: {json.dumps(context.cross_agency_data or {}, indent=2)}

        Requirements:
        1. Consider all relevant factors and context
        2. Ensure compliance with legal requirements
        3. Provide clear reasoning for your decision
        4. Assess risks and alternatives
        5. Maintain consistency with similar cases

        Return your response as JSON with:
        {{
            "decision": <the actual decision>,
            "confidence": <confidence score 0.0-1.0>,
            "reasoning_steps": [<list of reasoning steps>],
            "legal_basis": [<list of legal references>],
            "alternatives_considered": [<list of alternatives>],
            "risk_assessment": {{
                "low_risk": [<list of low-risk factors>],
                "medium_risk": [<list of medium-risk factors>],
                "high_risk": [<list of high-risk factors>]
            }},
            "trace_id": "<unique trace identifier>"
        }}
        """

        return prompt

    async def _call_llm(self, prompt: str, reasoning_mode: ReasoningMode) -> str:
        """Call the configured LLM provider"""

        if self.provider == LLMProvider.MOCK:
            return await self._mock_llm_call(prompt, reasoning_mode)
        elif self.provider == LLMProvider.OPENAI:
            return await self._openai_call(prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_call(prompt)
        elif self.provider == LLMProvider.AZURE:
            return await self._azure_call(prompt)
        else:
            raise DecisionLayerError(f"Unsupported LLM provider: {self.provider}")

    async def _mock_llm_call(self, prompt: str, reasoning_mode: ReasoningMode) -> str:
        """Mock LLM call for testing"""
        await asyncio.sleep(0.1)  # Simulate API call delay

        if reasoning_mode == ReasoningMode.EXPLANATORY:
            return "This is a mock explanation for testing purposes."

        # Return mock decision
        return json.dumps(
            {
                "decision": {"approved": True, "reason": "Mock decision for testing"},
                "confidence": 0.85,
                "reasoning_steps": [
                    "Analyzed input data",
                    "Checked legal requirements",
                    "Applied decision criteria",
                    "Generated decision",
                ],
                "legal_basis": ["Mock Legal Reference 1", "Mock Legal Reference 2"],
                "alternatives_considered": ["Alternative A", "Alternative B"],
                "risk_assessment": {
                    "low_risk": ["Standard case"],
                    "medium_risk": [],
                    "high_risk": [],
                },
                "trace_id": f"mock_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            }
        )

    async def _openai_call(self, prompt: str) -> str:
        """Call OpenAI API"""
        config = self.llm_config.openai

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _anthropic_call(self, prompt: str) -> str:
        """Call Anthropic API"""
        config = self.llm_config.anthropic

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": config.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": config.model,
                    "max_tokens": config.max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def _azure_call(self, prompt: str) -> str:
        """Call Azure OpenAI API"""
        config = self.llm_config.azure

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.endpoint}/openai/deployments/{config.deployment_name}/chat/completions",
                headers={"api-key": config.api_key, "Content-Type": "application/json"},
                params={"api-version": config.api_version},
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _parse_agentic_response(
        self, response: str, input_data: Dict[str, Any]
    ) -> AgenticDecision:
        """Parse and validate LLM response"""
        try:
            data = json.loads(response)

            # Validate required fields
            required_fields = [
                "decision",
                "confidence",
                "reasoning_steps",
                "legal_basis",
            ]
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

            # Generate trace ID if not provided
            trace_id = data.get(
                "trace_id", f"agentic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            return AgenticDecision(
                decision=data["decision"],
                confidence=float(data["confidence"]),
                reasoning_steps=data["reasoning_steps"],
                legal_basis=data["legal_basis"],
                alternatives_considered=data.get("alternatives_considered", []),
                risk_assessment=data.get("risk_assessment", {}),
                trace_id=trace_id,
            )

        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            raise ValidationError(f"Error parsing agentic response: {e}")


def create_llm_integration(
    config: DecisionLayerConfig, registry=None
) -> LLMIntegration:
    """Factory function to create LLM integration"""
    return LLMIntegration(config, registry)
