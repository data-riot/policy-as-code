"""
Domain-Specific Semantic Context System

This module implements domain-specific semantic context building that preserves
domain expertise and prevents information dilution in AI systems.

Key Features:
- Domain-centric semantic relationships
- Context compression and optimization
- Semantic rule application
- Token efficiency optimization
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SemanticRelationType(str, Enum):
    """Types of semantic relationships"""

    IS_A = "is_a"
    PART_OF = "part_of"
    CAUSES = "causes"
    REQUIRES = "requires"
    EXCLUDES = "excludes"
    SIMILAR_TO = "similar_to"
    DEPENDS_ON = "depends_on"
    VALIDATES = "validates"


class ContextCompressionLevel(str, Enum):
    """Levels of context compression"""

    MINIMAL = "minimal"  # Keep only essential information
    STANDARD = "standard"  # Balance between detail and efficiency
    DETAILED = "detailed"  # Keep most information
    FULL = "full"  # Keep all information


@dataclass
class SemanticRelationship:
    """A semantic relationship between concepts"""

    source: str
    target: str
    relation_type: SemanticRelationType
    confidence: float
    domain_context: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticRule:
    """A semantic rule for domain-specific logic"""

    rule_id: str
    domain: str
    condition: str
    action: str
    priority: int
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticContext:
    """Complete semantic context for a domain"""

    domain: str
    relationships: List[SemanticRelationship]
    semantic_rules: List[SemanticRule]
    content: str
    token_count: int
    compression_level: ContextCompressionLevel
    confidence_score: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class DomainSemanticContext:
    """
    Domain-specific semantic context builder

    This preserves domain expertise by building semantic relationships
    and applying domain-specific rules to create focused, relevant context.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.ontology = self._load_domain_ontology()
        self.semantic_rules = self._load_semantic_rules()
        self.compression_strategies = self._load_compression_strategies()

    async def build_context(
        self, data_products: List[Any], intent_analysis: Any
    ) -> SemanticContext:
        """
        Build domain-specific semantic context

        This is where domain expertise is preserved and context is optimized
        for maximum relevance and token efficiency.
        """
        logger.info(f"Building semantic context for domain: {self.domain}")

        # Step 1: Extract semantic relationships from data products
        relationships = await self._extract_semantic_relationships(data_products)

        # Step 2: Apply domain-specific semantic rules
        applied_rules = await self._apply_semantic_rules(relationships, intent_analysis)

        # Step 3: Build contextual content
        content = await self._build_contextual_content(
            relationships, applied_rules, intent_analysis
        )

        # Step 4: Compress context based on intent requirements
        compressed_content = await self._compress_context(content, intent_analysis)

        # Step 5: Calculate confidence score
        confidence = await self._calculate_context_confidence(
            relationships, applied_rules
        )

        # Step 6: Create final semantic context
        context = SemanticContext(
            domain=self.domain,
            relationships=relationships,
            semantic_rules=applied_rules,
            content=compressed_content,
            token_count=len(compressed_content.split()),
            compression_level=self._determine_compression_level(intent_analysis),
            confidence_score=confidence,
        )

        logger.info(
            f"Semantic context built: {context.token_count} tokens, {confidence:.2f} confidence"
        )
        return context

    async def _extract_semantic_relationships(
        self, data_products: List[Any]
    ) -> List[SemanticRelationship]:
        """Extract semantic relationships from data products"""
        relationships = []

        for product in data_products:
            # Extract relationships from product metadata
            product_relationships = await self._extract_product_relationships(product)
            relationships.extend(product_relationships)

        # Add domain-specific relationships from ontology
        ontology_relationships = await self._extract_ontology_relationships()
        relationships.extend(ontology_relationships)

        # Remove duplicates and sort by confidence
        unique_relationships = self._deduplicate_relationships(relationships)
        unique_relationships.sort(key=lambda r: r.confidence, reverse=True)

        return unique_relationships[:20]  # Limit to top 20 relationships

    async def _extract_product_relationships(
        self, product: Any
    ) -> List[SemanticRelationship]:
        """Extract relationships from a single data product"""
        relationships = []

        # Extract relationships from semantic tags
        if hasattr(product, "semantic_tags"):
            for i, tag in enumerate(product.semantic_tags):
                for j, other_tag in enumerate(product.semantic_tags[i + 1 :], i + 1):
                    # Create similarity relationship
                    relationship = SemanticRelationship(
                        source=tag,
                        target=other_tag,
                        relation_type=SemanticRelationType.SIMILAR_TO,
                        confidence=0.7,
                        domain_context=self.domain,
                        metadata={
                            "source": "semantic_tags",
                            "product_id": getattr(product, "product_id", "unknown"),
                        },
                    )
                    relationships.append(relationship)

        # Extract relationships from product type
        if hasattr(product, "product_type"):
            product_type = product.product_type
            if hasattr(product, "semantic_tags"):
                for tag in product.semantic_tags:
                    relationship = SemanticRelationship(
                        source=tag,
                        target=product_type,
                        relation_type=SemanticRelationType.IS_A,
                        confidence=0.8,
                        domain_context=self.domain,
                        metadata={
                            "source": "product_type",
                            "product_id": getattr(product, "product_id", "unknown"),
                        },
                    )
                    relationships.append(relationship)

        return relationships

    async def _extract_ontology_relationships(self) -> List[SemanticRelationship]:
        """Extract relationships from domain ontology"""
        relationships = []

        if not self.ontology:
            return relationships

        # Extract relationships from ontology structure
        for concept, properties in self.ontology.items():
            if isinstance(properties, dict):
                # Extract "is_a" relationships
                if "is_a" in properties:
                    relationship = SemanticRelationship(
                        source=concept,
                        target=properties["is_a"],
                        relation_type=SemanticRelationType.IS_A,
                        confidence=0.9,
                        domain_context=self.domain,
                        metadata={"source": "ontology"},
                    )
                    relationships.append(relationship)

                # Extract "part_of" relationships
                if "part_of" in properties:
                    relationship = SemanticRelationship(
                        source=concept,
                        target=properties["part_of"],
                        relation_type=SemanticRelationType.PART_OF,
                        confidence=0.8,
                        domain_context=self.domain,
                        metadata={"source": "ontology"},
                    )
                    relationships.append(relationship)

                # Extract "requires" relationships
                if "requires" in properties:
                    requirements = properties["requires"]
                    if isinstance(requirements, list):
                        for req in requirements:
                            relationship = SemanticRelationship(
                                source=concept,
                                target=req,
                                relation_type=SemanticRelationType.REQUIRES,
                                confidence=0.7,
                                domain_context=self.domain,
                                metadata={"source": "ontology"},
                            )
                            relationships.append(relationship)

        return relationships

    async def _apply_semantic_rules(
        self, relationships: List[SemanticRelationship], intent_analysis: Any
    ) -> List[SemanticRule]:
        """Apply domain-specific semantic rules"""
        applied_rules = []

        for rule in self.semantic_rules:
            # Check if rule applies to current context
            if await self._rule_applies(rule, relationships, intent_analysis):
                applied_rules.append(rule)

        # Sort by priority
        applied_rules.sort(key=lambda r: r.priority, reverse=True)

        return applied_rules[:10]  # Limit to top 10 rules

    async def _rule_applies(
        self,
        rule: SemanticRule,
        relationships: List[SemanticRelationship],
        intent_analysis: Any,
    ) -> bool:
        """Check if a semantic rule applies to current context"""
        # Simple pattern matching for now
        # In production, this would use more sophisticated rule evaluation

        condition_lower = rule.condition.lower()

        # Check if rule condition matches intent
        if hasattr(intent_analysis, "intent_type"):
            if intent_analysis.intent_type.value.lower() in condition_lower:
                return True

        # Check if rule condition matches semantic tags
        if hasattr(intent_analysis, "semantic_tags"):
            for tag in intent_analysis.semantic_tags:
                if tag.lower() in condition_lower:
                    return True

        # Check if rule condition matches relationships
        for relationship in relationships:
            if (
                relationship.source.lower() in condition_lower
                or relationship.target.lower() in condition_lower
            ):
                return True

        return False

    async def _build_contextual_content(
        self,
        relationships: List[SemanticRelationship],
        rules: List[SemanticRule],
        intent_analysis: Any,
    ) -> str:
        """Build human-readable contextual content"""
        content_parts = []

        # Add domain context header
        content_parts.append(f"Domain: {self.domain}")
        content_parts.append(
            f"Intent: {getattr(intent_analysis, 'intent_type', 'unknown')}"
        )

        # Add key relationships
        if relationships:
            content_parts.append("\nKey Relationships:")
            for rel in relationships[:5]:  # Top 5 relationships
                content_parts.append(
                    f"- {rel.source} {rel.relation_type.value} {rel.target} (confidence: {rel.confidence:.2f})"
                )

        # Add applicable rules
        if rules:
            content_parts.append("\nApplicable Rules:")
            for rule in rules[:3]:  # Top 3 rules
                content_parts.append(f"- {rule.rule_id}: {rule.action}")

        # Add semantic tags context
        if hasattr(intent_analysis, "semantic_tags") and intent_analysis.semantic_tags:
            content_parts.append(
                f"\nKey Concepts: {', '.join(intent_analysis.semantic_tags)}"
            )

        # Add data types context
        if (
            hasattr(intent_analysis, "data_types_needed")
            and intent_analysis.data_types_needed
        ):
            content_parts.append(
                f"\nRequired Data Types: {', '.join(intent_analysis.data_types_needed[:3])}"
            )

        return "\n".join(content_parts)

    async def _compress_context(self, content: str, intent_analysis: Any) -> str:
        """Compress context based on intent requirements"""
        # Determine compression level based on intent
        compression_level = self._determine_compression_level(intent_analysis)

        if compression_level == ContextCompressionLevel.MINIMAL:
            # Keep only essential information
            lines = content.split("\n")
            essential_lines = [
                line
                for line in lines
                if any(
                    keyword in line.lower()
                    for keyword in ["domain:", "intent:", "key concepts:"]
                )
            ]
            return "\n".join(essential_lines)

        elif compression_level == ContextCompressionLevel.STANDARD:
            # Keep most important information
            lines = content.split("\n")
            important_lines = [
                line
                for line in lines
                if not line.startswith("- ")
                or "confidence: 0.8" in line
                or "confidence: 0.9" in line
            ]
            return "\n".join(important_lines)

        elif compression_level == ContextCompressionLevel.DETAILED:
            # Keep most information but remove low-confidence items
            lines = content.split("\n")
            detailed_lines = [
                line
                for line in lines
                if not ("confidence: 0.5" in line or "confidence: 0.6" in line)
            ]
            return "\n".join(detailed_lines)

        else:  # FULL
            return content

    def _determine_compression_level(
        self, intent_analysis: Any
    ) -> ContextCompressionLevel:
        """Determine appropriate compression level based on intent"""
        if not intent_analysis:
            return ContextCompressionLevel.STANDARD

        # Urgent intents need minimal context for speed
        if hasattr(intent_analysis, "urgency_level"):
            if intent_analysis.urgency_level.value == "critical":
                return ContextCompressionLevel.MINIMAL

        # Complex intents need detailed context
        if hasattr(intent_analysis, "context_depth"):
            if intent_analysis.context_depth == "deep":
                return ContextCompressionLevel.DETAILED
            elif intent_analysis.context_depth == "shallow":
                return ContextCompressionLevel.MINIMAL

        return ContextCompressionLevel.STANDARD

    async def _calculate_context_confidence(
        self, relationships: List[SemanticRelationship], rules: List[SemanticRule]
    ) -> float:
        """Calculate confidence in the semantic context"""
        if not relationships and not rules:
            return 0.0

        # Calculate average relationship confidence
        rel_confidence = 0.0
        if relationships:
            rel_confidence = sum(r.confidence for r in relationships) / len(
                relationships
            )

        # Calculate average rule confidence
        rule_confidence = 0.0
        if rules:
            rule_confidence = sum(r.confidence for r in rules) / len(rules)

        # Weighted average
        if relationships and rules:
            return (rel_confidence * 0.6) + (rule_confidence * 0.4)
        elif relationships:
            return rel_confidence
        elif rules:
            return rule_confidence
        else:
            return 0.0

    def _deduplicate_relationships(
        self, relationships: List[SemanticRelationship]
    ) -> List[SemanticRelationship]:
        """Remove duplicate relationships"""
        seen = set()
        unique = []

        for rel in relationships:
            key = (rel.source, rel.target, rel.relation_type)
            if key not in seen:
                seen.add(key)
                unique.append(rel)

        return unique

    def _load_domain_ontology(self) -> Dict[str, Any]:
        """Load domain-specific ontology"""
        ontology_files = {
            "healthcare": {
                "patient": {
                    "is_a": "person",
                    "requires": ["medical_record", "insurance"],
                },
                "medical_procedure": {
                    "is_a": "treatment",
                    "requires": ["doctor", "facility"],
                },
                "insurance": {"is_a": "coverage", "part_of": "healthcare_system"},
                "eligibility": {
                    "requires": ["criteria", "verification"],
                    "validates": "patient",
                },
            },
            "taxation": {
                "income": {
                    "is_a": "financial_data",
                    "requires": ["verification", "calculation"],
                },
                "tax_bracket": {"is_a": "rate_structure", "part_of": "tax_system"},
                "deduction": {
                    "is_a": "tax_reduction",
                    "requires": ["eligibility", "documentation"],
                },
                "calculation": {
                    "requires": ["income", "rates"],
                    "validates": "tax_amount",
                },
            },
            "immigration": {
                "visa": {
                    "is_a": "travel_document",
                    "requires": ["application", "verification"],
                },
                "passport": {"is_a": "identity_document", "validates": "citizenship"},
                "security_check": {
                    "is_a": "verification",
                    "requires": ["background", "database"],
                },
                "eligibility": {
                    "requires": ["criteria", "documentation"],
                    "validates": "application",
                },
            },
        }

        return ontology_files.get(self.domain, {})

    def _load_semantic_rules(self) -> List[SemanticRule]:
        """Load domain-specific semantic rules"""
        rules_by_domain = {
            "healthcare": [
                SemanticRule(
                    rule_id="healthcare_eligibility_rule",
                    domain="healthcare",
                    condition="eligibility_check",
                    action="require_medical_history_and_insurance",
                    priority=10,
                    confidence=0.9,
                ),
                SemanticRule(
                    rule_id="healthcare_procedure_rule",
                    domain="healthcare",
                    condition="medical_procedure",
                    action="verify_doctor_credentials_and_facility",
                    priority=9,
                    confidence=0.8,
                ),
            ],
            "taxation": [
                SemanticRule(
                    rule_id="tax_calculation_rule",
                    domain="taxation",
                    condition="calculation",
                    action="apply_tax_brackets_and_deductions",
                    priority=10,
                    confidence=0.9,
                ),
                SemanticRule(
                    rule_id="tax_verification_rule",
                    domain="taxation",
                    condition="income_verification",
                    action="cross_reference_with_employer_data",
                    priority=8,
                    confidence=0.8,
                ),
            ],
            "immigration": [
                SemanticRule(
                    rule_id="immigration_security_rule",
                    domain="immigration",
                    condition="security_check",
                    action="verify_against_security_databases",
                    priority=10,
                    confidence=0.9,
                ),
                SemanticRule(
                    rule_id="immigration_document_rule",
                    domain="immigration",
                    condition="document_verification",
                    action="validate_passport_and_supporting_documents",
                    priority=9,
                    confidence=0.8,
                ),
            ],
        }

        return rules_by_domain.get(self.domain, [])

    def _load_compression_strategies(self) -> Dict[str, Any]:
        """Load context compression strategies"""
        return {
            "minimal": {
                "max_tokens": 500,
                "keep_essential_only": True,
                "remove_low_confidence": True,
            },
            "standard": {
                "max_tokens": 2000,
                "keep_essential_only": False,
                "remove_low_confidence": False,
            },
            "detailed": {
                "max_tokens": 4000,
                "keep_essential_only": False,
                "remove_low_confidence": False,
            },
            "full": {
                "max_tokens": 8000,
                "keep_essential_only": False,
                "remove_low_confidence": False,
            },
        }
