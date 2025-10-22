"""
Context Compression and Optimization

This module implements intelligent context compression that optimizes token usage
while preserving essential semantic information for AI agents.

Key Features:
- Semantic-aware compression
- Token efficiency optimization
- Context overflow prevention
- Domain-specific compression strategies
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CompressionStrategy(str, Enum):
    """Context compression strategies"""

    SEMANTIC_PRESERVATION = "semantic_preservation"  # Preserve semantic relationships
    TOKEN_EFFICIENCY = "token_efficiency"  # Maximize token efficiency
    DOMAIN_FOCUSED = "domain_focused"  # Focus on domain-specific content
    INTENT_BASED = "intent_based"  # Compress based on intent requirements


class CompressionLevel(str, Enum):
    """Levels of compression"""

    MINIMAL = "minimal"  # Light compression, preserve most information
    MODERATE = "moderate"  # Balanced compression
    AGGRESSIVE = "aggressive"  # Heavy compression, keep only essentials
    MAXIMUM = "maximum"  # Maximum compression, minimal information


@dataclass
class CompressionResult:
    """Result of context compression"""

    original_content: str
    compressed_content: str
    compression_ratio: float
    tokens_saved: int
    semantic_preservation_score: float
    strategy_used: CompressionStrategy
    level_used: CompressionLevel
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextCompression:
    """
    Intelligent context compression for optimal token usage

    This solves context overflow by compressing information while preserving
    essential semantic relationships and domain expertise.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.compression_strategies = self._load_compression_strategies()
        self.semantic_preservers = self._load_semantic_preservers()
        self.domain_keywords = self._load_domain_keywords()

    async def compress(
        self,
        semantic_context: Any,
        max_tokens: int = 4000,
        strategy: CompressionStrategy = CompressionStrategy.SEMANTIC_PRESERVATION,
    ) -> Any:
        """
        Compress semantic context to optimal size

        This intelligently reduces token count while preserving essential
        semantic information and domain expertise.
        """
        logger.info(
            f"Compressing context for domain: {self.domain}, max_tokens: {max_tokens}"
        )

        if not hasattr(semantic_context, "content"):
            return semantic_context

        original_content = semantic_context.content
        original_tokens = len(original_content.split())

        # If already under limit, return as-is
        if original_tokens <= max_tokens:
            logger.info("Context already within token limit")
            return semantic_context

        # Determine compression level needed
        compression_level = self._determine_compression_level(
            original_tokens, max_tokens
        )

        # Apply compression strategy
        compressed_content = await self._apply_compression_strategy(
            original_content, strategy, compression_level, max_tokens
        )

        # Calculate compression metrics
        compressed_tokens = len(compressed_content.split())
        compression_ratio = compressed_tokens / original_tokens
        tokens_saved = original_tokens - compressed_tokens

        # Calculate semantic preservation score
        semantic_score = await self._calculate_semantic_preservation(
            original_content, compressed_content
        )

        # Create compression result
        compression_result = CompressionResult(
            original_content=original_content,
            compressed_content=compressed_content,
            compression_ratio=compression_ratio,
            tokens_saved=tokens_saved,
            semantic_preservation_score=semantic_score,
            strategy_used=strategy,
            level_used=compression_level,
            metadata={
                "domain": self.domain,
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
                "compression_efficiency": tokens_saved / original_tokens,
            },
        )

        # Update semantic context with compressed content
        semantic_context.content = compressed_content
        semantic_context.token_count = compressed_tokens

        logger.info(
            f"Compression complete: {compression_ratio:.2f} ratio, {semantic_score:.2f} semantic preservation"
        )
        return semantic_context

    def _determine_compression_level(
        self, original_tokens: int, max_tokens: int
    ) -> CompressionLevel:
        """Determine appropriate compression level"""
        ratio = max_tokens / original_tokens

        if ratio >= 0.8:
            return CompressionLevel.MINIMAL
        elif ratio >= 0.6:
            return CompressionLevel.MODERATE
        elif ratio >= 0.4:
            return CompressionLevel.AGGRESSIVE
        else:
            return CompressionLevel.MAXIMUM

    async def _apply_compression_strategy(
        self,
        content: str,
        strategy: CompressionStrategy,
        level: CompressionLevel,
        max_tokens: int,
    ) -> str:
        """Apply specific compression strategy"""

        if strategy == CompressionStrategy.SEMANTIC_PRESERVATION:
            return await self._semantic_preservation_compression(
                content, level, max_tokens
            )
        elif strategy == CompressionStrategy.TOKEN_EFFICIENCY:
            return await self._token_efficiency_compression(content, level, max_tokens)
        elif strategy == CompressionStrategy.DOMAIN_FOCUSED:
            return await self._domain_focused_compression(content, level, max_tokens)
        elif strategy == CompressionStrategy.INTENT_BASED:
            return await self._intent_based_compression(content, level, max_tokens)
        else:
            return await self._semantic_preservation_compression(
                content, level, max_tokens
            )

    async def _semantic_preservation_compression(
        self, content: str, level: CompressionLevel, max_tokens: int
    ) -> str:
        """Compress while preserving semantic relationships"""
        lines = content.split("\n")
        compressed_lines = []

        # Preserve essential semantic elements
        essential_patterns = [
            "Domain:",
            "Intent:",
            "Key Relationships:",
            "Applicable Rules:",
            "Key Concepts:",
        ]

        for line in lines:
            # Always keep essential patterns
            if any(pattern in line for pattern in essential_patterns):
                compressed_lines.append(line)
            # Keep high-confidence relationships
            elif "confidence: 0.8" in line or "confidence: 0.9" in line:
                compressed_lines.append(line)
            # Apply level-based filtering
            elif level == CompressionLevel.MINIMAL:
                compressed_lines.append(line)
            elif level == CompressionLevel.MODERATE and "confidence: 0.7" in line:
                compressed_lines.append(line)
            elif level == CompressionLevel.AGGRESSIVE and "confidence: 0.6" in line:
                compressed_lines.append(line)
            # Maximum compression - only essentials
            elif level == CompressionLevel.MAXIMUM:
                if any(pattern in line for pattern in essential_patterns):
                    compressed_lines.append(line)

        compressed_content = "\n".join(compressed_lines)

        # If still too long, apply additional compression
        if len(compressed_content.split()) > max_tokens:
            return await self._apply_additional_compression(
                compressed_content, max_tokens
            )

        return compressed_content

    async def _token_efficiency_compression(
        self, content: str, level: CompressionLevel, max_tokens: int
    ) -> str:
        """Compress for maximum token efficiency"""
        words = content.split()

        if level == CompressionLevel.MINIMAL:
            # Remove redundant words
            filtered_words = self._remove_redundant_words(words)
        elif level == CompressionLevel.MODERATE:
            # Remove redundant words and low-value words
            filtered_words = self._remove_redundant_words(words)
            filtered_words = self._remove_low_value_words(filtered_words)
        elif level == CompressionLevel.AGGRESSIVE:
            # Keep only essential words
            filtered_words = self._keep_essential_words(words)
        else:  # MAXIMUM
            # Keep only domain keywords and essential words
            filtered_words = self._keep_domain_keywords(words)

        compressed_content = " ".join(filtered_words)

        # If still too long, apply additional compression
        if len(compressed_content.split()) > max_tokens:
            return await self._apply_additional_compression(
                compressed_content, max_tokens
            )

        return compressed_content

    async def _domain_focused_compression(
        self, content: str, level: CompressionLevel, max_tokens: int
    ) -> str:
        """Compress focusing on domain-specific content"""
        lines = content.split("\n")
        domain_lines = []

        # Prioritize domain-specific content
        domain_keywords = self.domain_keywords.get(self.domain, [])

        for line in lines:
            # Keep lines with domain keywords
            if any(keyword.lower() in line.lower() for keyword in domain_keywords):
                domain_lines.append(line)
            # Keep essential patterns
            elif any(
                pattern in line for pattern in ["Domain:", "Intent:", "Key Concepts:"]
            ):
                domain_lines.append(line)
            # Apply level-based filtering
            elif level in [CompressionLevel.MINIMAL, CompressionLevel.MODERATE]:
                domain_lines.append(line)

        compressed_content = "\n".join(domain_lines)

        # If still too long, apply additional compression
        if len(compressed_content.split()) > max_tokens:
            return await self._apply_additional_compression(
                compressed_content, max_tokens
            )

        return compressed_content

    async def _intent_based_compression(
        self, content: str, level: CompressionLevel, max_tokens: int
    ) -> str:
        """Compress based on intent requirements"""
        lines = content.split("\n")
        intent_lines = []

        # Extract intent from content
        intent_type = self._extract_intent_type(content)

        # Keep lines relevant to intent
        for line in lines:
            if self._is_relevant_to_intent(line, intent_type):
                intent_lines.append(line)
            # Always keep essential patterns
            elif any(
                pattern in line for pattern in ["Domain:", "Intent:", "Key Concepts:"]
            ):
                intent_lines.append(line)

        compressed_content = "\n".join(intent_lines)

        # If still too long, apply additional compression
        if len(compressed_content.split()) > max_tokens:
            return await self._apply_additional_compression(
                compressed_content, max_tokens
            )

        return compressed_content

    async def _apply_additional_compression(self, content: str, max_tokens: int) -> str:
        """Apply additional compression if still over limit"""
        words = content.split()

        # Remove words until under limit
        while len(words) > max_tokens:
            # Remove least important words
            words = self._remove_least_important_words(words)

        return " ".join(words)

    def _remove_redundant_words(self, words: List[str]) -> List[str]:
        """Remove redundant words"""
        redundant_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
        }

        return [word for word in words if word.lower() not in redundant_words]

    def _remove_low_value_words(self, words: List[str]) -> List[str]:
        """Remove low-value words"""
        low_value_words = {
            "very",
            "really",
            "quite",
            "rather",
            "somewhat",
            "fairly",
            "pretty",
            "kind",
            "sort",
            "type",
            "way",
            "thing",
            "stuff",
        }

        return [word for word in words if word.lower() not in low_value_words]

    def _keep_essential_words(self, words: List[str]) -> List[str]:
        """Keep only essential words"""
        essential_patterns = [
            "domain:",
            "intent:",
            "confidence:",
            "relationship:",
            "rule:",
            "concept:",
            "type:",
            "required:",
            "applicable:",
        ]

        essential_words = []
        for word in words:
            if any(pattern in word.lower() for pattern in essential_patterns):
                essential_words.append(word)
            elif word.lower() in self.domain_keywords.get(self.domain, []):
                essential_words.append(word)

        return essential_words

    def _keep_domain_keywords(self, words: List[str]) -> List[str]:
        """Keep only domain keywords and essential words"""
        domain_keywords = set(self.domain_keywords.get(self.domain, []))
        essential_words = []

        for word in words:
            if word.lower() in domain_keywords:
                essential_words.append(word)
            elif any(pattern in word.lower() for pattern in ["domain:", "intent:"]):
                essential_words.append(word)

        return essential_words

    def _remove_least_important_words(self, words: List[str]) -> List[str]:
        """Remove least important words"""
        # Remove common words first
        common_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "very",
            "really",
            "quite",
            "rather",
            "somewhat",
            "fairly",
        }

        filtered_words = [word for word in words if word.lower() not in common_words]

        # If still too many words, remove more
        if len(filtered_words) > len(words) * 0.8:
            return words[:-1]  # Remove last word

        return filtered_words

    def _extract_intent_type(self, content: str) -> str:
        """Extract intent type from content"""
        content_lower = content.lower()

        if "eligibility" in content_lower:
            return "eligibility_check"
        elif "calculate" in content_lower:
            return "calculation"
        elif "risk" in content_lower:
            return "risk_assessment"
        elif "compliance" in content_lower:
            return "compliance_verification"
        else:
            return "decision_making"

    def _is_relevant_to_intent(self, line: str, intent_type: str) -> bool:
        """Check if line is relevant to intent"""
        line_lower = line.lower()

        intent_keywords = {
            "eligibility_check": ["eligible", "qualify", "criteria", "requirements"],
            "calculation": ["calculate", "compute", "amount", "rate", "formula"],
            "risk_assessment": ["risk", "assess", "evaluate", "danger", "threat"],
            "compliance_verification": ["comply", "verify", "check", "regulation"],
            "decision_making": ["decide", "determine", "choose", "policy"],
        }

        keywords = intent_keywords.get(intent_type, [])
        return any(keyword in line_lower for keyword in keywords)

    async def _calculate_semantic_preservation(
        self, original_content: str, compressed_content: str
    ) -> float:
        """Calculate how well semantic information is preserved"""
        original_words = set(original_content.lower().split())
        compressed_words = set(compressed_content.lower().split())

        # Calculate overlap
        overlap = len(original_words & compressed_words)
        total_original = len(original_words)

        if total_original == 0:
            return 0.0

        # Calculate semantic preservation score
        preservation_score = overlap / total_original

        # Boost score for preserving key semantic elements
        key_elements = ["domain:", "intent:", "relationship:", "rule:", "concept:"]
        preserved_elements = sum(
            1 for element in key_elements if element in compressed_content.lower()
        )
        element_boost = preserved_elements / len(key_elements) * 0.2

        return min(preservation_score + element_boost, 1.0)

    def _load_compression_strategies(self) -> Dict[str, Any]:
        """Load compression strategy configurations"""
        return {
            "semantic_preservation": {
                "preserve_relationships": True,
                "preserve_rules": True,
                "preserve_concepts": True,
            },
            "token_efficiency": {
                "remove_redundant": True,
                "remove_low_value": True,
                "optimize_word_choice": True,
            },
            "domain_focused": {
                "prioritize_domain_keywords": True,
                "preserve_domain_context": True,
                "remove_generic_content": True,
            },
            "intent_based": {
                "filter_by_intent": True,
                "preserve_intent_relevant": True,
                "remove_irrelevant": True,
            },
        }

    def _load_semantic_preservers(self) -> Dict[str, List[str]]:
        """Load semantic preservation patterns"""
        return {
            "healthcare": [
                "patient",
                "medical",
                "procedure",
                "insurance",
                "eligibility",
            ],
            "taxation": ["income", "tax", "deduction", "calculation", "bracket"],
            "immigration": ["visa", "passport", "immigration", "security", "document"],
            "social_benefits": [
                "benefit",
                "welfare",
                "support",
                "eligibility",
                "income",
            ],
        }

    def _load_domain_keywords(self) -> Dict[str, List[str]]:
        """Load domain-specific keywords"""
        return {
            "healthcare": [
                "patient",
                "medical",
                "health",
                "treatment",
                "procedure",
                "insurance",
                "doctor",
                "hospital",
                "clinical",
                "diagnosis",
                "therapy",
                "medication",
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
                "amount",
                "refund",
                "liability",
                "exemption",
                "withholding",
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
                "security",
                "background",
                "check",
                "verification",
            ],
            "social_benefits": [
                "benefit",
                "welfare",
                "support",
                "assistance",
                "unemployment",
                "housing",
                "childcare",
                "disability",
                "income",
                "threshold",
                "eligibility",
                "allocation",
            ],
        }
