"""
Autonomous Data Products - Domain-Centric Self-Organizing Data

This module implements autonomous data products that automatically discover,
organize, and serve domain-specific context to AI agents based on intent.

Key Features:
- Intent-based data discovery
- Domain-centric semantic context
- Automatic data organization
- Token efficiency optimization
- Multimodal data integration
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from .intent_discovery import IntentBasedDiscovery, IntentAnalysis
from .semantic_context import DomainSemanticContext, SemanticContext
from .multimodal import MultimodalDataStore, MultimodalData
from .context_compression import ContextCompression, CompressionStrategy

logger = logging.getLogger(__name__)


class DomainType(str, Enum):
    """Supported government domains"""

    HEALTHCARE = "healthcare"
    TAXATION = "taxation"
    IMMIGRATION = "immigration"
    SOCIAL_BENEFITS = "social_benefits"
    ENVIRONMENTAL = "environmental"
    EDUCATION = "education"
    TRANSPORTATION = "transportation"
    HOUSING = "housing"


class DataProductType(str, Enum):
    """Types of autonomous data products"""

    ELIGIBILITY_CONTEXT = "eligibility_context"
    SEMANTIC_MAPPING = "semantic_mapping"
    LEGAL_ONTOLOGY = "legal_ontology"
    PROCEDURE_GUIDELINES = "procedure_guidelines"
    COMPLIANCE_RULES = "compliance_rules"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class DataProduct:
    """Individual data product within a domain"""

    product_id: str
    product_type: DataProductType
    domain: DomainType
    data_source: str
    semantic_tags: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    token_efficiency: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainContext:
    """Complete domain context for an agent"""

    domain: DomainType
    intent: str
    semantic_context: SemanticContext
    multimodal_data: MultimodalData
    data_products: List[DataProduct]
    token_efficiency: float
    confidence_score: float
    context_size_tokens: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class AutonomousDataProduct:
    """
    Domain-centric data product with self-organizing capabilities

    This is the core innovation that solves GenAI data problems:
    - No context overflow: Only relevant data is loaded
    - No information dilution: Domain expertise is preserved
    - No silent drift: Continuous monitoring and adaptation
    - Scalable by design: Domain boundaries enable independent scaling
    """

    def __init__(
        self,
        domain: DomainType,
        product_id: str,
        max_context_tokens: int = 4000,
        relevance_threshold: float = 0.7,
    ):
        self.domain = domain
        self.product_id = product_id
        self.max_context_tokens = max_context_tokens
        self.relevance_threshold = relevance_threshold

        # Core components
        self.intent_discovery = IntentBasedDiscovery(domain)
        self.semantic_context = DomainSemanticContext(domain)
        self.multimodal_data = MultimodalDataStore(domain)
        self.context_compression = ContextCompression(domain)

        # Domain-specific data products
        self.data_products: Dict[str, DataProduct] = {}
        self.domain_ontologies: Dict[str, Any] = {}
        self.semantic_rules: Dict[str, Any] = {}

        # Performance tracking
        self.token_usage_history: List[int] = []
        self.relevance_scores: List[float] = []
        self.drift_indicators: List[float] = []

    async def initialize(self) -> None:
        """Initialize the autonomous data product"""
        logger.info(f"Initializing autonomous data product for domain: {self.domain}")

        # Load domain-specific ontologies
        await self._load_domain_ontologies()

        # Load semantic rules
        await self._load_semantic_rules()

        # Initialize data products
        await self._initialize_data_products()

        logger.info(f"Autonomous data product initialized: {self.product_id}")

    async def discover_and_organize(self, intent: str) -> DomainContext:
        """
        Automatically discover and organize relevant data based on intent

        This is the core method that solves context overflow and information dilution
        """
        logger.info(f"Discovering data for intent: {intent}")

        # Step 1: Analyze intent to understand what data is needed
        intent_analysis = await self.intent_discovery.analyze_intent(intent)

        # Step 2: Find relevant data products based on intent
        relevant_products = await self._find_relevant_data_products(intent_analysis)

        # Step 3: Build domain-specific semantic context
        semantic_context = await self.semantic_context.build_context(
            relevant_products, intent_analysis
        )

        # Step 4: Integrate multimodal data
        multimodal_data = await self.multimodal_data.integrate(
            semantic_context, relevant_products
        )

        # Step 5: Compress context to optimal size
        compressed_context = await self.context_compression.compress(
            semantic_context,
            max_tokens=self.max_context_tokens,
            strategy=CompressionStrategy.SEMANTIC_PRESERVATION,
        )

        # Step 6: Calculate token efficiency
        token_efficiency = self._calculate_token_efficiency(
            compressed_context, relevant_products
        )

        # Step 7: Build final domain context
        domain_context = DomainContext(
            domain=self.domain,
            intent=intent,
            semantic_context=compressed_context,
            multimodal_data=multimodal_data,
            data_products=relevant_products,
            token_efficiency=token_efficiency,
            confidence_score=intent_analysis.confidence,
            context_size_tokens=len(compressed_context.content.split()),
        )

        # Step 8: Track performance metrics
        await self._track_performance_metrics(domain_context)

        logger.info(f"Domain context created: {token_efficiency:.2f} token efficiency")
        return domain_context

    async def _find_relevant_data_products(
        self, intent_analysis: IntentAnalysis
    ) -> List[DataProduct]:
        """Find only data products relevant to the specific intent"""
        relevant_products = []

        for product_id, product in self.data_products.items():
            # Calculate relevance score based on intent
            relevance_score = await self._calculate_product_relevance(
                product, intent_analysis
            )

            if relevance_score >= self.relevance_threshold:
                product.relevance_score = relevance_score
                relevant_products.append(product)

        # Sort by relevance score (highest first)
        relevant_products.sort(key=lambda p: p.relevance_score, reverse=True)

        # Limit to prevent context overflow
        max_products = min(len(relevant_products), 5)  # Max 5 products per intent

        logger.info(
            f"Found {len(relevant_products)} relevant products, using top {max_products}"
        )
        return relevant_products[:max_products]

    async def _calculate_product_relevance(
        self, product: DataProduct, intent_analysis: IntentAnalysis
    ) -> float:
        """Calculate how relevant a data product is to the intent"""
        # Base relevance from semantic tags
        semantic_match = self._calculate_semantic_match(
            product.semantic_tags, intent_analysis.semantic_tags
        )

        # Domain-specific relevance
        domain_match = 1.0 if product.domain == intent_analysis.domain else 0.0

        # Recency factor (newer data is more relevant)
        recency_factor = self._calculate_recency_factor(product.last_updated)

        # Combined relevance score
        relevance = semantic_match * 0.5 + domain_match * 0.3 + recency_factor * 0.2

        return min(relevance, 1.0)

    def _calculate_semantic_match(
        self, product_tags: List[str], intent_tags: List[str]
    ) -> float:
        """Calculate semantic match between product and intent tags"""
        if not product_tags or not intent_tags:
            return 0.0

        matches = len(set(product_tags) & set(intent_tags))
        total_tags = len(set(product_tags) | set(intent_tags))

        return matches / total_tags if total_tags > 0 else 0.0

    def _calculate_recency_factor(self, last_updated: datetime) -> float:
        """Calculate recency factor for data product"""
        days_old = (datetime.now(timezone.utc) - last_updated).days

        # Exponential decay: newer data is more relevant
        if days_old == 0:
            return 1.0
        elif days_old <= 7:
            return 0.9
        elif days_old <= 30:
            return 0.7
        elif days_old <= 90:
            return 0.5
        else:
            return 0.3

    def _calculate_token_efficiency(
        self, context: SemanticContext, products: List[DataProduct]
    ) -> float:
        """Calculate token efficiency of the domain context"""
        if not products:
            return 0.0

        # Calculate information density
        total_tokens = context.token_count
        relevant_information = sum(p.relevance_score for p in products)

        # Token efficiency = relevant information per token
        efficiency = relevant_information / total_tokens if total_tokens > 0 else 0.0

        return min(efficiency, 1.0)

    async def _track_performance_metrics(self, context: DomainContext) -> None:
        """Track performance metrics for continuous improvement"""
        self.token_usage_history.append(context.context_size_tokens)
        self.relevance_scores.append(context.token_efficiency)

        # Keep only last 100 measurements
        if len(self.token_usage_history) > 100:
            self.token_usage_history = self.token_usage_history[-100:]
            self.relevance_scores = self.relevance_scores[-100:]

    async def _load_domain_ontologies(self) -> None:
        """Load domain-specific ontologies"""
        ontology_files = {
            DomainType.HEALTHCARE: "ontologies/healthcare_ontology.json",
            DomainType.TAXATION: "ontologies/taxation_ontology.json",
            DomainType.IMMIGRATION: "ontologies/immigration_ontology.json",
            DomainType.SOCIAL_BENEFITS: "ontologies/social_benefits_ontology.json",
        }

        ontology_file = ontology_files.get(self.domain)
        if ontology_file:
            try:
                with open(ontology_file, "r") as f:
                    self.domain_ontologies[self.domain] = json.load(f)
                logger.info(f"Loaded ontology for domain: {self.domain}")
            except FileNotFoundError:
                logger.warning(f"Ontology file not found: {ontology_file}")

    async def _load_semantic_rules(self) -> None:
        """Load domain-specific semantic rules"""
        rules_files = {
            DomainType.HEALTHCARE: "rules/healthcare_semantic_rules.json",
            DomainType.TAXATION: "rules/taxation_semantic_rules.json",
            DomainType.IMMIGRATION: "rules/immigration_semantic_rules.json",
            DomainType.SOCIAL_BENEFITS: "rules/social_benefits_semantic_rules.json",
        }

        rules_file = rules_files.get(self.domain)
        if rules_file:
            try:
                with open(rules_file, "r") as f:
                    self.semantic_rules[self.domain] = json.load(f)
                logger.info(f"Loaded semantic rules for domain: {self.domain}")
            except FileNotFoundError:
                logger.warning(f"Semantic rules file not found: {rules_file}")

    async def _initialize_data_products(self) -> None:
        """Initialize domain-specific data products"""
        # This would typically load from a database or configuration
        # For now, we'll create some example products

        base_products = {
            DomainType.HEALTHCARE: [
                DataProduct(
                    product_id="patient_eligibility_context",
                    product_type=DataProductType.ELIGIBILITY_CONTEXT,
                    domain=self.domain,
                    data_source="healthcare_apis",
                    semantic_tags=["patient", "eligibility", "medical", "insurance"],
                ),
                DataProduct(
                    product_id="medical_procedure_semantics",
                    product_type=DataProductType.SEMANTIC_MAPPING,
                    domain=self.domain,
                    data_source="clinical_guidelines",
                    semantic_tags=["procedure", "medical", "clinical", "guidelines"],
                ),
                DataProduct(
                    product_id="insurance_coverage_mapping",
                    product_type=DataProductType.COMPLIANCE_RULES,
                    domain=self.domain,
                    data_source="insurance_providers",
                    semantic_tags=["insurance", "coverage", "network", "provider"],
                ),
            ],
            DomainType.TAXATION: [
                DataProduct(
                    product_id="income_verification_context",
                    product_type=DataProductType.ELIGIBILITY_CONTEXT,
                    domain=self.domain,
                    data_source="tax_authority_apis",
                    semantic_tags=["income", "verification", "tax", "calculation"],
                ),
                DataProduct(
                    product_id="tax_bracket_semantics",
                    product_type=DataProductType.SEMANTIC_MAPPING,
                    domain=self.domain,
                    data_source="tax_law_database",
                    semantic_tags=["tax", "bracket", "rate", "calculation"],
                ),
                DataProduct(
                    product_id="deduction_eligibility_mapping",
                    product_type=DataProductType.COMPLIANCE_RULES,
                    domain=self.domain,
                    data_source="tax_regulations",
                    semantic_tags=["deduction", "eligibility", "tax", "compliance"],
                ),
            ],
            DomainType.IMMIGRATION: [
                DataProduct(
                    product_id="visa_eligibility_context",
                    product_type=DataProductType.ELIGIBILITY_CONTEXT,
                    domain=self.domain,
                    data_source="immigration_database",
                    semantic_tags=["visa", "eligibility", "immigration", "application"],
                ),
                DataProduct(
                    product_id="security_check_semantics",
                    product_type=DataProductType.RISK_ASSESSMENT,
                    domain=self.domain,
                    data_source="security_databases",
                    semantic_tags=["security", "background", "check", "risk"],
                ),
                DataProduct(
                    product_id="document_verification_mapping",
                    product_type=DataProductType.COMPLIANCE_RULES,
                    domain=self.domain,
                    data_source="document_verification_apis",
                    semantic_tags=["document", "verification", "passport", "identity"],
                ),
            ],
        }

        products = base_products.get(self.domain, [])
        for product in products:
            self.data_products[product.product_id] = product

        logger.info(
            f"Initialized {len(products)} data products for domain: {self.domain}"
        )

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        if not self.token_usage_history:
            return {"status": "no_data"}

        avg_tokens = sum(self.token_usage_history) / len(self.token_usage_history)
        avg_efficiency = sum(self.relevance_scores) / len(self.relevance_scores)

        return {
            "domain": self.domain,
            "product_id": self.product_id,
            "avg_tokens_per_context": avg_tokens,
            "avg_token_efficiency": avg_efficiency,
            "total_contexts_served": len(self.token_usage_history),
            "data_products_count": len(self.data_products),
            "relevance_threshold": self.relevance_threshold,
            "max_context_tokens": self.max_context_tokens,
        }

    async def update_data_product(
        self, product_id: str, updates: Dict[str, Any]
    ) -> None:
        """Update a data product with new information"""
        if product_id not in self.data_products:
            logger.warning(f"Data product not found: {product_id}")
            return

        product = self.data_products[product_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)

        product.last_updated = datetime.now(timezone.utc)

        logger.info(f"Updated data product: {product_id}")

    async def add_data_product(self, product: DataProduct) -> None:
        """Add a new data product to the domain"""
        self.data_products[product.product_id] = product
        logger.info(f"Added data product: {product.product_id}")

    async def remove_data_product(self, product_id: str) -> None:
        """Remove a data product from the domain"""
        if product_id in self.data_products:
            del self.data_products[product_id]
            logger.info(f"Removed data product: {product_id}")
        else:
            logger.warning(f"Data product not found: {product_id}")
