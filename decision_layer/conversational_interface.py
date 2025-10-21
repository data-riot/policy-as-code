"""
Conversational Interface for Agentic Government Services

This module provides a conversational interface that allows citizens to interact
with government services using natural language, with seamless handoff to
appropriate decision functions and agents.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from .core import DecisionContext, DecisionEngine
from .llm_integration import LLMIntegration, AgenticContext, ReasoningMode
from .errors import DecisionLayerError, ValidationError

logger = logging.getLogger(__name__)


class ConversationChannel(str, Enum):
    """Supported conversation channels"""

    WEB_CHAT = "web_chat"
    VOICE = "voice"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    API = "api"


class ConversationState(str, Enum):
    """Conversation states"""

    ACTIVE = "active"
    WAITING_FOR_INPUT = "waiting_for_input"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationContext:
    """Context for ongoing conversations"""

    session_id: str
    citizen_id: Optional[str]
    channel: ConversationChannel
    language: str = "en"
    state: ConversationState = ConversationState.ACTIVE
    conversation_history: List[Dict[str, Any]] = None
    current_intent: Optional[str] = None
    pending_actions: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.pending_actions is None:
            self.pending_actions = []


@dataclass
class ConversationResponse:
    """Response from conversational interface"""

    message: str
    actions: List[Dict[str, Any]]
    next_steps: List[str]
    requires_human: bool = False
    confidence: float = 1.0
    trace_id: str = ""


class ConversationalInterface:
    """Conversational interface for agentic government services"""

    def __init__(
        self, decision_engine: DecisionEngine, llm_integration: LLMIntegration
    ):
        self.decision_engine = decision_engine
        self.llm_integration = llm_integration
        self.active_conversations: Dict[str, ConversationContext] = {}

    async def process_citizen_message(
        self,
        message: str,
        session_id: str,
        channel: ConversationChannel = ConversationChannel.WEB_CHAT,
        citizen_id: Optional[str] = None,
        language: str = "en",
    ) -> ConversationResponse:
        """
        Process a citizen message and return appropriate response

        Args:
            message: The citizen's message
            session_id: Unique session identifier
            channel: Communication channel
            citizen_id: Optional citizen identifier
            language: Language preference

        Returns:
            ConversationResponse with message and actions
        """
        try:
            # Get or create conversation context
            context = await self._get_conversation_context(
                session_id, citizen_id, channel, language
            )

            # Add message to history
            context.conversation_history.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "role": "citizen",
                    "message": message,
                    "channel": channel.value,
                }
            )

            # Determine intent and required actions
            intent_analysis = await self._analyze_citizen_intent(message, context)
            context.current_intent = intent_analysis.get("intent")

            # Process the intent
            response = await self._process_intent(intent_analysis, context)

            # Add response to history
            context.conversation_history.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "role": "assistant",
                    "message": response.message,
                    "actions": response.actions,
                    "confidence": response.confidence,
                }
            )

            # Update conversation state
            context.state = (
                ConversationState.ACTIVE
                if not response.requires_human
                else ConversationState.ESCALATED
            )

            return response

        except Exception as e:
            logger.error(f"Error processing citizen message: {e}")
            return ConversationResponse(
                message="I apologize, but I'm having trouble processing your request. Please try again or contact support.",
                actions=[],
                next_steps=["Contact human support"],
                requires_human=True,
                confidence=0.0,
                trace_id="",
            )

    async def handle_voice_input(
        self, audio_data: bytes, session_id: str, language: str = "en"
    ) -> ConversationResponse:
        """
        Handle voice input from citizens

        Args:
            audio_data: Raw audio data
            session_id: Session identifier
            language: Language of the audio

        Returns:
            ConversationResponse
        """
        try:
            # In a real implementation, this would use speech-to-text
            # For now, we'll simulate it
            transcribed_text = await self._transcribe_audio(audio_data, language)

            # Process as regular message
            return await self.process_citizen_message(
                transcribed_text,
                session_id,
                ConversationChannel.VOICE,
                language=language,
            )

        except Exception as e:
            logger.error(f"Error handling voice input: {e}")
            return ConversationResponse(
                message="I couldn't understand your voice message. Please try again or use text.",
                actions=[],
                next_steps=["Try text input", "Contact support"],
                requires_human=False,
                confidence=0.0,
            )

    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the conversation

        Args:
            session_id: Session identifier

        Returns:
            Conversation summary
        """
        context = self.active_conversations.get(session_id)
        if not context:
            return {"error": "Conversation not found"}

        return {
            "session_id": session_id,
            "citizen_id": context.citizen_id,
            "channel": context.channel.value,
            "language": context.language,
            "state": context.state.value,
            "message_count": len(context.conversation_history),
            "current_intent": context.current_intent,
            "pending_actions": len(context.pending_actions),
            "started_at": (
                context.conversation_history[0]["timestamp"]
                if context.conversation_history
                else None
            ),
            "last_activity": (
                context.conversation_history[-1]["timestamp"]
                if context.conversation_history
                else None
            ),
        }

    async def _get_conversation_context(
        self,
        session_id: str,
        citizen_id: Optional[str],
        channel: ConversationChannel,
        language: str,
    ) -> ConversationContext:
        """Get or create conversation context"""
        if session_id not in self.active_conversations:
            self.active_conversations[session_id] = ConversationContext(
                session_id=session_id,
                citizen_id=citizen_id,
                channel=channel,
                language=language,
            )

        return self.active_conversations[session_id]

    async def _analyze_citizen_intent(
        self, message: str, context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze citizen intent using LLM"""

        prompt = f"""
        Analyze this citizen message and determine the intent and required actions.

        Message: "{message}"
        Language: {context.language}
        Channel: {context.channel.value}
        Citizen ID: {context.citizen_id or "Not provided"}

        Previous conversation context:
        {json.dumps(context.conversation_history[-3:], indent=2) if context.conversation_history else "No previous context"}

        Determine:
        1. Primary intent (e.g., "apply_for_benefits", "check_status", "ask_question", "file_complaint")
        2. Required services or functions
        3. Information needed from citizen
        4. Next steps
        5. Whether human assistance is needed
        6. Confidence level (0.0-1.0)

        Return JSON response with:
        {{
            "intent": "<primary_intent>",
            "services_needed": ["<service1>", "<service2>"],
            "information_needed": ["<info1>", "<info2>"],
            "next_steps": ["<step1>", "<step2>"],
            "requires_human": <true/false>,
            "confidence": <0.0-1.0>,
            "suggested_response": "<suggested_response_message>"
        }}
        """

        try:
            response = await self.llm_integration._call_llm(
                prompt, ReasoningMode.ASSISTED
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                "intent": "unknown",
                "services_needed": [],
                "information_needed": [],
                "next_steps": ["Contact human support"],
                "requires_human": True,
                "confidence": 0.0,
                "suggested_response": "I need to connect you with a human representative.",
            }

    async def _process_intent(
        self, intent_analysis: Dict[str, Any], context: ConversationContext
    ) -> ConversationResponse:
        """Process the analyzed intent"""

        intent = intent_analysis.get("intent", "unknown")
        confidence = intent_analysis.get("confidence", 0.0)
        requires_human = intent_analysis.get("requires_human", False)

        if requires_human or confidence < 0.5:
            return ConversationResponse(
                message=intent_analysis.get(
                    "suggested_response",
                    "Let me connect you with a human representative.",
                ),
                actions=[
                    {
                        "type": "escalate_to_human",
                        "reason": "Low confidence or complex request",
                    }
                ],
                next_steps=intent_analysis.get(
                    "next_steps", ["Wait for human representative"]
                ),
                requires_human=True,
                confidence=confidence,
            )

        # Process based on intent
        if intent == "apply_for_benefits":
            return await self._handle_benefits_application(intent_analysis, context)
        elif intent == "check_status":
            return await self._handle_status_check(intent_analysis, context)
        elif intent == "ask_question":
            return await self._handle_question(intent_analysis, context)
        elif intent == "file_complaint":
            return await self._handle_complaint(intent_analysis, context)
        else:
            return ConversationResponse(
                message="I understand you need help, but I'm not sure exactly what you're looking for. Could you provide more details?",
                actions=[],
                next_steps=["Provide more specific information"],
                requires_human=False,
                confidence=0.3,
            )

    async def _handle_benefits_application(
        self, intent_analysis: Dict[str, Any], context: ConversationContext
    ) -> ConversationResponse:
        """Handle benefits application intent"""

        # Check if we have enough information
        information_needed = intent_analysis.get("information_needed", [])
        if information_needed:
            return ConversationResponse(
                message=f"To help you apply for benefits, I need some information: {', '.join(information_needed)}. Could you provide these details?",
                actions=[{"type": "collect_information", "fields": information_needed}],
                next_steps=["Provide required information"],
                requires_human=False,
                confidence=0.8,
            )

        # If we have enough information, process the application
        try:
            # Create agentic context
            agentic_context = AgenticContext(
                citizen_id=context.citizen_id,
                service_type="benefits_application",
                urgency_level="normal",
            )

            # This would call your existing decision functions
            # For now, return a mock response
            return ConversationResponse(
                message="I've started your benefits application. You'll receive a confirmation number and next steps shortly.",
                actions=[{"type": "start_application", "service": "benefits"}],
                next_steps=[
                    "Check email for confirmation",
                    "Gather required documents",
                ],
                requires_human=False,
                confidence=0.9,
                trace_id=f"benefits_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )

        except Exception as e:
            logger.error(f"Error handling benefits application: {e}")
            return ConversationResponse(
                message="I encountered an error processing your benefits application. Let me connect you with a specialist.",
                actions=[
                    {
                        "type": "escalate_to_human",
                        "reason": "Application processing error",
                    }
                ],
                next_steps=["Wait for human representative"],
                requires_human=True,
                confidence=0.0,
            )

    async def _handle_status_check(
        self, intent_analysis: Dict[str, Any], context: ConversationContext
    ) -> ConversationResponse:
        """Handle status check intent"""

        # This would integrate with your existing systems
        return ConversationResponse(
            message="I can help you check the status of your applications or requests. What specific status are you looking for?",
            actions=[{"type": "status_check_options"}],
            next_steps=["Specify what status to check"],
            requires_human=False,
            confidence=0.7,
        )

    async def _handle_question(
        self, intent_analysis: Dict[str, Any], context: ConversationContext
    ) -> ConversationResponse:
        """Handle general question intent"""

        # Use LLM to answer the question
        try:
            prompt = f"""
            Answer this citizen's question about government services in a helpful, accurate way.

            Question: {context.conversation_history[-1]['message']}
            Language: {context.language}

            Provide a clear, helpful answer that:
            1. Directly addresses the question
            2. Provides relevant information
            3. Suggests next steps if applicable
            4. Is written in a friendly, professional tone

            If you're not sure about something, say so and suggest contacting a human representative.
            """

            response = await self.llm_integration._call_llm(
                prompt, ReasoningMode.EXPLANATORY
            )

            return ConversationResponse(
                message=response.strip(),
                actions=[],
                next_steps=["Ask follow-up questions if needed"],
                requires_human=False,
                confidence=0.8,
            )

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return ConversationResponse(
                message="I'm having trouble answering your question. Let me connect you with someone who can help.",
                actions=[
                    {"type": "escalate_to_human", "reason": "Question too complex"}
                ],
                next_steps=["Wait for human representative"],
                requires_human=True,
                confidence=0.0,
            )

    async def _handle_complaint(
        self, intent_analysis: Dict[str, Any], context: ConversationContext
    ) -> ConversationResponse:
        """Handle complaint filing intent"""

        return ConversationResponse(
            message="I can help you file a complaint. Please describe the issue you're experiencing, and I'll guide you through the process.",
            actions=[{"type": "start_complaint_process"}],
            next_steps=["Describe the issue", "Provide supporting information"],
            requires_human=False,
            confidence=0.8,
        )

    async def _transcribe_audio(self, audio_data: bytes, language: str) -> str:
        """Transcribe audio to text (mock implementation)"""
        # In a real implementation, this would use speech-to-text services
        await asyncio.sleep(0.5)  # Simulate processing time
        return "Mock transcription of voice input"


def create_conversational_interface(
    decision_engine: DecisionEngine, llm_integration: LLMIntegration
) -> ConversationalInterface:
    """Factory function to create conversational interface"""
    return ConversationalInterface(decision_engine, llm_integration)
