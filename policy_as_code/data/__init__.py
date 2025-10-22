"""
Domain-First Autonomous Data Architecture

This module implements the revolutionary domain-first data architecture that solves:
- Context overflow in GenAI systems
- Information dilution from monolithic data lakes
- Silent drift in domain context
- Token cost explosion from irrelevant data

Key Components:
- Autonomous Data Products: Self-organizing domain-centric data
- Intent-Based Discovery: AI discovers relevant data based on intent
- Domain-Specific Semantic Context: Preserves domain expertise
- Multimodal Data Integration: Text, structured, unstructured data
- Context Compression: Optimal token usage
- Drift Detection: Continuous domain context monitoring
"""

from .autonomous_products import AutonomousDataProduct, DomainContext
from .intent_discovery import IntentBasedDiscovery, IntentAnalysis
from .semantic_context import DomainSemanticContext, SemanticContext
from .multimodal import MultimodalDataStore, MultimodalData
from .domain_agents import DomainAwareAgent, HealthcareAgent, TaxAgent, ImmigrationAgent
from .drift_detection import DomainDriftDetector, DriftReport
from .context_compression import ContextCompression, CompressionStrategy

__all__ = [
    "AutonomousDataProduct",
    "DomainContext",
    "IntentBasedDiscovery",
    "IntentAnalysis",
    "DomainSemanticContext",
    "SemanticContext",
    "MultimodalDataStore",
    "MultimodalData",
    "DomainAwareAgent",
    "HealthcareAgent",
    "TaxAgent",
    "ImmigrationAgent",
    "DomainDriftDetector",
    "DriftReport",
    "ContextCompression",
    "CompressionStrategy",
]
