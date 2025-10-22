"""
Intent-Based Data Discovery

This module implements intent-based data discovery that automatically finds
relevant data products based on agent intent, solving context overflow and
information dilution problems.

Key Features:
- Natural language intent analysis
- Semantic relevance scoring
- Domain-specific intent understanding
- Automatic data product matching
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Types of agent intents"""

    ELIGIBILITY_CHECK = "eligibility_check"
    CALCULATION = "calculation"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_VERIFICATION = "compliance_verification"
    DOCUMENT_PROCESSING = "document_processing"
    DECISION_MAKING = "decision_making"
    INFORMATION_RETRIEVAL = "information_retrieval"


class UrgencyLevel(str, Enum):
    """Urgency levels for intent processing"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class IntentAnalysis:
    """Analysis of agent intent"""

    intent_type: IntentType
    domain: str
    semantic_tags: List[str] = field(default_factory=list)
    data_types_needed: List[str] = field(default_factory=list)
    context_depth: str = "standard"  # shallow, standard, deep
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    confidence: float = 0.0
    reasoning: str = ""
    suggested_data_products: List[str] = field(default_factory=list)


class IntentBasedDiscovery:
    """
    Discovers relevant data based on agent intent

    This solves the core problem of context overflow by ensuring agents
    only get data that's actually relevant to their specific intent.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.intent_patterns = self._load_intent_patterns()
        self.semantic_mappings = self._load_semantic_mappings()
        self.data_type_mappings = self._load_data_type_mappings()

    async def analyze_intent(self, intent: str) -> IntentAnalysis:
        """
        Analyze intent to understand what data is needed

        This is where the magic happens - we parse natural language intent
        and determine exactly what data products are relevant.
        """
        logger.info(f"Analyzing intent: {intent}")

        # Step 1: Classify intent type
        intent_type = await self._classify_intent_type(intent)

        # Step 2: Extract semantic tags
        semantic_tags = await self._extract_semantic_tags(intent)

        # Step 3: Determine data types needed
        data_types_needed = await self._determine_data_types(intent_type, semantic_tags)

        # Step 4: Assess context depth needed
        context_depth = await self._assess_context_depth(intent_type, semantic_tags)

        # Step 5: Determine urgency level
        urgency_level = await self._assess_urgency(intent)

        # Step 6: Calculate confidence score
        confidence = await self._calculate_confidence(intent_type, semantic_tags)

        # Step 7: Generate reasoning
        reasoning = await self._generate_reasoning(
            intent_type, semantic_tags, data_types_needed
        )

        # Step 8: Suggest relevant data products
        suggested_products = await self._suggest_data_products(
            intent_type, semantic_tags, data_types_needed
        )

        analysis = IntentAnalysis(
            intent_type=intent_type,
            domain=self.domain,
            semantic_tags=semantic_tags,
            data_types_needed=data_types_needed,
            context_depth=context_depth,
            urgency_level=urgency_level,
            confidence=confidence,
            reasoning=reasoning,
            suggested_data_products=suggested_products,
        )

        logger.info(
            f"Intent analysis complete: {intent_type} with {confidence:.2f} confidence"
        )
        return analysis

    async def _classify_intent_type(self, intent: str) -> IntentType:
        """Classify the type of intent"""
        intent_lower = intent.lower()

        # Pattern matching for intent classification
        if any(
            word in intent_lower
            for word in ["eligible", "qualify", "meet requirements"]
        ):
            return IntentType.ELIGIBILITY_CHECK
        elif any(
            word in intent_lower
            for word in ["calculate", "compute", "determine amount"]
        ):
            return IntentType.CALCULATION
        elif any(word in intent_lower for word in ["risk", "assess", "evaluate"]):
            return IntentType.RISK_ASSESSMENT
        elif any(
            word in intent_lower for word in ["comply", "verify", "check compliance"]
        ):
            return IntentType.COMPLIANCE_VERIFICATION
        elif any(
            word in intent_lower for word in ["process", "review", "analyze document"]
        ):
            return IntentType.DOCUMENT_PROCESSING
        elif any(
            word in intent_lower for word in ["decide", "determine", "make decision"]
        ):
            return IntentType.DECISION_MAKING
        elif any(
            word in intent_lower for word in ["find", "get", "retrieve", "lookup"]
        ):
            return IntentType.INFORMATION_RETRIEVAL
        else:
            return IntentType.DECISION_MAKING  # Default fallback

    async def _extract_semantic_tags(self, intent: str) -> List[str]:
        """Extract semantic tags from intent"""
        intent_lower = intent.lower()
        tags = []

        # Domain-specific semantic extraction
        domain_patterns = {
            "healthcare": [
                "patient",
                "medical",
                "health",
                "treatment",
                "procedure",
                "insurance",
                "doctor",
                "hospital",
            ],
            "taxation": [
                "income",
                "tax",
                "deduction",
                "credit",
                "filing",
                "bracket",
                "rate",
                "calculation",
            ],
            "immigration": [
                "visa",
                "passport",
                "immigration",
                "citizen",
                "resident",
                "application",
                "status",
                "document",
            ],
            "social_benefits": [
                "benefit",
                "welfare",
                "support",
                "assistance",
                "unemployment",
                "housing",
                "childcare",
            ],
        }

        patterns = domain_patterns.get(self.domain, [])
        for pattern in patterns:
            if pattern in intent_lower:
                tags.append(pattern)

        # Add general semantic tags
        general_tags = {
            "urgent": ["urgent", "emergency", "asap", "immediately"],
            "personal": ["my", "personal", "individual", "citizen"],
            "financial": ["money", "cost", "payment", "fee", "amount"],
            "legal": ["legal", "law", "regulation", "compliance", "requirement"],
            "document": ["document", "paperwork", "form", "application", "certificate"],
        }

        for tag_type, keywords in general_tags.items():
            if any(keyword in intent_lower for keyword in keywords):
                tags.append(tag_type)

        return list(set(tags))  # Remove duplicates

    async def _determine_data_types(
        self, intent_type: IntentType, semantic_tags: List[str]
    ) -> List[str]:
        """Determine what types of data are needed"""
        data_types = []

        # Base data types by intent type
        base_mappings = {
            IntentType.ELIGIBILITY_CHECK: [
                "eligibility_rules",
                "criteria",
                "requirements",
            ],
            IntentType.CALCULATION: [
                "calculation_rules",
                "formulas",
                "rates",
                "brackets",
            ],
            IntentType.RISK_ASSESSMENT: [
                "risk_factors",
                "assessment_criteria",
                "scoring",
            ],
            IntentType.COMPLIANCE_VERIFICATION: [
                "compliance_rules",
                "regulations",
                "standards",
            ],
            IntentType.DOCUMENT_PROCESSING: [
                "document_schemas",
                "validation_rules",
                "templates",
            ],
            IntentType.DECISION_MAKING: ["decision_trees", "policies", "guidelines"],
            IntentType.INFORMATION_RETRIEVAL: [
                "reference_data",
                "lookup_tables",
                "databases",
            ],
        }

        data_types.extend(base_mappings.get(intent_type, []))

        # Add domain-specific data types
        domain_mappings = {
            "healthcare": [
                "patient_data",
                "medical_records",
                "insurance_data",
                "clinical_guidelines",
            ],
            "taxation": [
                "income_data",
                "tax_codes",
                "deduction_rules",
                "filing_requirements",
            ],
            "immigration": [
                "passport_data",
                "visa_types",
                "security_checks",
                "document_requirements",
            ],
            "social_benefits": [
                "benefit_rules",
                "income_thresholds",
                "family_data",
                "eligibility_criteria",
            ],
        }

        domain_types = domain_mappings.get(self.domain, [])
        data_types.extend(domain_types)

        # Filter based on semantic tags
        filtered_types = []
        for data_type in data_types:
            if any(tag in data_type.lower() for tag in semantic_tags):
                filtered_types.append(data_type)

        return (
            filtered_types if filtered_types else data_types[:3]
        )  # Fallback to first 3

    async def _assess_context_depth(
        self, intent_type: IntentType, semantic_tags: List[str]
    ) -> str:
        """Assess how much context depth is needed"""
        # Complex intents need deeper context
        deep_intents = [
            IntentType.RISK_ASSESSMENT,
            IntentType.DECISION_MAKING,
            IntentType.COMPLIANCE_VERIFICATION,
        ]

        if intent_type in deep_intents:
            return "deep"

        # Urgent intents might need more context
        if "urgent" in semantic_tags:
            return "deep"

        # Simple intents can use shallow context
        shallow_intents = [
            IntentType.INFORMATION_RETRIEVAL,
            IntentType.DOCUMENT_PROCESSING,
        ]

        if intent_type in shallow_intents:
            return "shallow"

        return "standard"

    async def _assess_urgency(self, intent: str) -> UrgencyLevel:
        """Assess urgency level of the intent"""
        intent_lower = intent.lower()

        if any(
            word in intent_lower for word in ["emergency", "urgent", "critical", "asap"]
        ):
            return UrgencyLevel.CRITICAL
        elif any(word in intent_lower for word in ["priority", "important", "soon"]):
            return UrgencyLevel.HIGH
        elif any(word in intent_lower for word in ["routine", "normal", "standard"]):
            return UrgencyLevel.NORMAL
        else:
            return UrgencyLevel.NORMAL  # Default

    async def _calculate_confidence(
        self, intent_type: IntentType, semantic_tags: List[str]
    ) -> float:
        """Calculate confidence in the intent analysis"""
        confidence = 0.5  # Base confidence

        # Higher confidence for clear intent types
        clear_intents = [
            IntentType.ELIGIBILITY_CHECK,
            IntentType.CALCULATION,
            IntentType.INFORMATION_RETRIEVAL,
        ]

        if intent_type in clear_intents:
            confidence += 0.2

        # Higher confidence for more semantic tags
        if len(semantic_tags) >= 3:
            confidence += 0.1
        elif len(semantic_tags) >= 1:
            confidence += 0.05

        # Domain-specific confidence boost
        domain_tags = {
            "healthcare": ["patient", "medical", "health"],
            "taxation": ["income", "tax", "calculation"],
            "immigration": ["visa", "passport", "immigration"],
            "social_benefits": ["benefit", "welfare", "support"],
        }

        domain_keywords = domain_tags.get(self.domain, [])
        if any(tag in semantic_tags for tag in domain_keywords):
            confidence += 0.1

        return min(confidence, 1.0)

    async def _generate_reasoning(
        self, intent_type: IntentType, semantic_tags: List[str], data_types: List[str]
    ) -> str:
        """Generate human-readable reasoning for the analysis"""
        reasoning_parts = []

        reasoning_parts.append(f"Intent classified as: {intent_type.value}")

        if semantic_tags:
            reasoning_parts.append(
                f"Key concepts identified: {', '.join(semantic_tags)}"
            )

        if data_types:
            reasoning_parts.append(f"Required data types: {', '.join(data_types[:3])}")

        reasoning_parts.append(f"Domain context: {self.domain}")

        return ". ".join(reasoning_parts) + "."

    async def _suggest_data_products(
        self, intent_type: IntentType, semantic_tags: List[str], data_types: List[str]
    ) -> List[str]:
        """Suggest relevant data products based on analysis"""
        suggestions = []

        # Map intent types to data products
        intent_product_mapping = {
            IntentType.ELIGIBILITY_CHECK: ["eligibility_context", "criteria_mapping"],
            IntentType.CALCULATION: ["calculation_rules", "formula_mapping"],
            IntentType.RISK_ASSESSMENT: ["risk_factors", "assessment_criteria"],
            IntentType.COMPLIANCE_VERIFICATION: [
                "compliance_rules",
                "regulation_mapping",
            ],
            IntentType.DOCUMENT_PROCESSING: ["document_schemas", "validation_rules"],
            IntentType.DECISION_MAKING: ["decision_trees", "policy_guidelines"],
            IntentType.INFORMATION_RETRIEVAL: ["reference_data", "lookup_tables"],
        }

        base_suggestions = intent_product_mapping.get(intent_type, [])
        suggestions.extend(base_suggestions)

        # Add domain-specific suggestions
        domain_suggestions = {
            "healthcare": [
                "patient_eligibility_context",
                "medical_procedure_semantics",
            ],
            "taxation": ["income_verification_context", "tax_bracket_semantics"],
            "immigration": ["visa_eligibility_context", "security_check_semantics"],
            "social_benefits": [
                "benefit_eligibility_context",
                "income_threshold_mapping",
            ],
        }

        domain_products = domain_suggestions.get(self.domain, [])
        suggestions.extend(domain_products)

        # Remove duplicates and limit
        suggestions = list(set(suggestions))
        return suggestions[:5]  # Max 5 suggestions

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent patterns for classification"""
        return {
            "eligibility": ["eligible", "qualify", "meet requirements", "criteria"],
            "calculation": ["calculate", "compute", "determine amount", "figure out"],
            "risk": ["risk", "assess", "evaluate", "danger"],
            "compliance": ["comply", "verify", "check compliance", "follow rules"],
            "document": ["process", "review", "analyze document", "handle"],
            "decision": ["decide", "determine", "make decision", "choose"],
            "information": ["find", "get", "retrieve", "lookup", "search"],
        }

    def _load_semantic_mappings(self) -> Dict[str, List[str]]:
        """Load semantic mappings for tag extraction"""
        return {
            "healthcare": [
                "patient",
                "medical",
                "health",
                "treatment",
                "procedure",
                "insurance",
            ],
            "taxation": ["income", "tax", "deduction", "credit", "filing", "bracket"],
            "immigration": ["visa", "passport", "immigration", "citizen", "resident"],
            "social_benefits": [
                "benefit",
                "welfare",
                "support",
                "assistance",
                "unemployment",
            ],
        }

    def _load_data_type_mappings(self) -> Dict[str, List[str]]:
        """Load data type mappings"""
        return {
            "eligibility_check": ["eligibility_rules", "criteria", "requirements"],
            "calculation": ["calculation_rules", "formulas", "rates"],
            "risk_assessment": ["risk_factors", "assessment_criteria"],
            "compliance_verification": ["compliance_rules", "regulations"],
            "document_processing": ["document_schemas", "validation_rules"],
            "decision_making": ["decision_trees", "policies"],
            "information_retrieval": ["reference_data", "lookup_tables"],
        }
