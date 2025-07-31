"""
Unified Natural Language Interface for Decision Layer

Provides a single interface for cross-domain communication between
humans, LLMs, ontologies, and knowledge graphs.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .core import DecisionEngine
from .knowledge_graph_integration import KnowledgeGraphIntegration
from .llm_integration import LLMIntegration
from .ontology_integration import OntologyIntegration
from .registry import FunctionRegistry


@dataclass
class QueryIntent:
    """Parsed intent of a natural language query"""

    intent_type: str  # function_search, decision_explanation, trace_query, etc.
    entities: List[str]
    time_range: Optional[Dict[str, str]]
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class CrossDomainResponse:
    """Response from cross-domain query processing"""

    query: str
    intent: QueryIntent
    primary_response: Dict[str, Any]
    ontology_context: Optional[Dict[str, Any]]
    knowledge_graph_context: Optional[Dict[str, Any]]
    llm_explanation: Optional[str]
    format: str  # natural, structured, technical


class UnifiedNaturalLanguageInterface:
    """
    Unified interface for cross-domain communication

    Provides a single point of interaction for:
    - Natural language queries about decisions
    - Cross-domain context enrichment
    - Multi-format explanations
    - Integration between all knowledge sources
    """

    def __init__(
        self,
        registry: FunctionRegistry,
        engine: DecisionEngine,
        llm_integration: LLMIntegration,
        ontology_integration: OntologyIntegration,
        knowledge_graph_integration: KnowledgeGraphIntegration,
    ):
        self.registry = registry
        self.engine = engine
        self.llm = llm_integration
        self.ontology = ontology_integration
        self.kg = knowledge_graph_integration

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        format: str = "natural",
        include_cross_domain: bool = True,
    ) -> CrossDomainResponse:
        """
        Process a natural language query with cross-domain enrichment

        Args:
            query: Natural language query
            context: Additional context (user_id, time_range, etc.)
            format: Output format ("natural", "structured", "technical")
            include_cross_domain: Whether to include ontology and KG context

        Returns:
            CrossDomainResponse with comprehensive answer
        """

        # Parse query intent
        intent = await self._parse_query_intent(query)

        # Get primary response based on intent
        primary_response = await self._handle_query_intent(query, intent, context)

        # Initialize cross-domain context
        ontology_context = None
        knowledge_graph_context = None
        llm_explanation = None

        # Enrich with cross-domain information if requested
        if include_cross_domain:
            ontology_context = await self._get_ontology_context(query, intent, context)
            knowledge_graph_context = await self._get_knowledge_graph_context(
                query, intent, context
            )
            llm_explanation = await self._generate_cross_domain_explanation(
                query, primary_response, ontology_context, knowledge_graph_context
            )

        return CrossDomainResponse(
            query=query,
            intent=intent,
            primary_response=primary_response,
            ontology_context=ontology_context,
            knowledge_graph_context=knowledge_graph_context,
            llm_explanation=llm_explanation,
            format=format,
        )

    async def explain_decision(
        self,
        decision_id: str,
        audience: str = "user",
        format: str = "natural",
        include_context: bool = True,
    ) -> Dict[str, Any]:
        """
        Explain a decision with cross-domain context

        Args:
            decision_id: Decision to explain (function_id or trace_id)
            audience: Target audience ("user", "business", "technical")
            format: Output format ("natural", "structured", "technical")
            include_context: Whether to include cross-domain context

        Returns:
            Comprehensive explanation with context
        """

        # Determine if this is a function ID or trace ID
        if "trace_" in decision_id:
            return await self._explain_trace(
                decision_id, audience, format, include_context
            )
        else:
            return await self._explain_function(
                decision_id, audience, format, include_context
            )

    async def generate_report(
        self, criteria: Dict[str, Any], format: str = "markdown"
    ) -> str:
        """
        Generate a comprehensive report based on criteria

        Args:
            criteria: Report criteria (time_range, functions, entities, etc.)
            format: Output format ("markdown", "json", "html")

        Returns:
            Generated report
        """

        # Extract criteria
        time_range = criteria.get("time_range")
        function_ids = criteria.get("function_ids", [])
        entity_ids = criteria.get("entity_ids", [])
        report_type = criteria.get("type", "summary")

        # Collect data based on criteria
        report_data = {
            "time_range": time_range,
            "functions": [],
            "entities": [],
            "decisions": [],
            "cross_domain_insights": {},
        }

        # Get function information
        for function_id in function_ids:
            try:
                artifact = self.registry.get_function(function_id, "latest")
                report_data["functions"].append(
                    {
                        "function_id": artifact.function_id,
                        "version": artifact.version,
                        "title": artifact.metadata.title,
                        "description": artifact.metadata.description,
                        "tags": artifact.metadata.tags,
                    }
                )
            except Exception:
                continue

        # Get entity information
        for entity_id in entity_ids:
            try:
                kg_context = await self.kg.analyze_entity_risk(entity_id, "User")
                report_data["entities"].append(kg_context)
            except Exception:
                continue

        # Get decision history
        if entity_ids and time_range:
            for entity_id in entity_ids:
                try:
                    history = await self.kg.query_decision_history(
                        entity_id, time_range=time_range
                    )
                    report_data["decisions"].extend(history)
                except Exception:
                    continue

        # Generate cross-domain insights
        report_data["cross_domain_insights"] = (
            await self._generate_cross_domain_insights(report_data)
        )

        # Generate report in requested format
        if format == "markdown":
            return self._generate_markdown_report(report_data, report_type)
        elif format == "json":
            return json.dumps(report_data, indent=2)
        else:
            return str(report_data)

    async def answer_complex_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Answer complex queries that require multiple knowledge sources

        Args:
            query: Complex natural language query
            context: Additional context

        Returns:
            Comprehensive answer using all available knowledge sources
        """

        # Parse complex query
        query_components = await self._parse_complex_query(query)

        # Process each component
        component_responses = {}
        for component in query_components:
            component_response = await self._process_query_component(component, context)
            component_responses[component["type"]] = component_response

        # Synthesize comprehensive answer
        comprehensive_answer = await self._synthesize_comprehensive_answer(
            query, query_components, component_responses
        )

        return {
            "query": query,
            "components": query_components,
            "component_responses": component_responses,
            "comprehensive_answer": comprehensive_answer,
            "confidence": self._calculate_comprehensive_confidence(component_responses),
        }

    async def _parse_query_intent(self, query: str) -> QueryIntent:
        """Parse the intent of a natural language query"""

        # Use LLM to parse intent
        intent_analysis = await self.llm.answer_natural_language_query(query)

        # Extract entities and time references
        entities = await self._extract_entities(query)
        time_range = await self._extract_time_range(query)

        return QueryIntent(
            intent_type=intent_analysis.get("type", "unknown"),
            entities=entities,
            time_range=time_range,
            confidence=intent_analysis.get("confidence", 0.5),
            metadata=intent_analysis.get("metadata", {}),
        )

    async def _handle_query_intent(
        self, query: str, intent: QueryIntent, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle query based on parsed intent"""

        if intent.intent_type == "function_search":
            return await self._handle_function_search(query, intent, context)
        elif intent.intent_type == "decision_explanation":
            return await self._handle_decision_explanation(query, intent, context)
        elif intent.intent_type == "trace_query":
            return await self._handle_trace_query(query, intent, context)
        elif intent.intent_type == "risk_analysis":
            return await self._handle_risk_analysis(query, intent, context)
        else:
            return {"type": "unknown", "message": "I don't understand that query"}

    async def _handle_function_search(
        self, query: str, intent: QueryIntent, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle function search queries"""
        # Mock implementation - would use actual search
        return {
            "type": "function_search",
            "query": query,
            "results": [
                {
                    "function_id": "loan_approval",
                    "title": "Loan Approval",
                    "description": "Loan approval logic",
                }
            ],
        }

    async def _handle_decision_explanation(
        self, query: str, intent: QueryIntent, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle decision explanation queries"""
        # Mock implementation - would extract function reference and explain
        return {
            "type": "decision_explanation",
            "query": query,
            "explanation": "This decision function evaluates loan applications based on credit score and income.",
        }

    async def _handle_trace_query(
        self, query: str, intent: QueryIntent, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle trace query requests"""
        # Mock implementation - would query actual traces
        return {
            "type": "trace_query",
            "query": query,
            "results": [
                {
                    "trace_id": "trace_001",
                    "timestamp": "2025-01-27T10:00:00Z",
                    "status": "success",
                }
            ],
        }

    async def _handle_risk_analysis(
        self, query: str, intent: QueryIntent, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle risk analysis queries"""
        # Mock implementation - would perform actual risk analysis
        return {
            "type": "risk_analysis",
            "query": query,
            "risk_score": 0.3,
            "risk_factors": ["new_account", "high_transaction_volume"],
        }

    async def _get_ontology_context(
        self, query: str, intent: QueryIntent, context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get ontology context for the query"""

        try:
            # Extract ontology-relevant entities
            ontology_entities = await self._extract_ontology_entities(query)

            ontology_context = {}
            for entity in ontology_entities:
                # Get ontology class for entity
                ontology_class = await self._map_entity_to_ontology_class(entity)
                if ontology_class:
                    # Get ontology mapping
                    mapping = self.ontology.get_ontology_mapping(ontology_class)
                    ontology_context[entity] = {
                        "ontology_class": ontology_class,
                        "properties": mapping.schema_fields,
                        "relationships": mapping.relationships,
                        "validation_rules": mapping.validation_rules,
                    }

            return ontology_context if ontology_context else None

        except Exception:
            return None

    async def _get_knowledge_graph_context(
        self, query: str, intent: QueryIntent, context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get knowledge graph context for the query"""

        try:
            # Extract KG entities
            kg_entities = await self._extract_kg_entities(query)

            kg_context = {}
            for entity_id in kg_entities:
                # Get KG context for entity
                entity_context = await self.kg.enrich_decision_context(
                    entity_id, "User"
                )
                kg_context[entity_id] = {
                    "properties": entity_context.properties,
                    "relationships": entity_context.relationships,
                    "risk_factors": entity_context.risk_factors,
                    "historical_data": entity_context.historical_data,
                }

            return kg_context if kg_context else None

        except Exception:
            return None

    async def _generate_cross_domain_explanation(
        self,
        query: str,
        primary_response: Dict[str, Any],
        ontology_context: Optional[Dict[str, Any]],
        knowledge_graph_context: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate cross-domain explanation using LLM"""

        try:
            # Prepare context for LLM explanation
            _ = {
                "query": query,
                "primary_response": primary_response,
                "ontology_context": ontology_context,
                "knowledge_graph_context": knowledge_graph_context,
            }

            prompt = f"""
            Generate a comprehensive explanation that integrates information from multiple sources:

            Query: {query}
            Primary Response: {json.dumps(primary_response, indent=2)}
            Ontology Context: {json.dumps(ontology_context, indent=2) if ontology_context else "None"}
            Knowledge Graph Context: {json.dumps(knowledge_graph_context, indent=2) if knowledge_graph_context else "None"}

            Provide an explanation that:
            1. Answers the original query
            2. Incorporates relevant ontology information
            3. Includes knowledge graph insights
            4. Explains how the different sources relate to each other
            """

            return await self.llm.llm.generate_text(prompt)

        except Exception:
            return None

    async def _explain_function(
        self, function_id: str, audience: str, format: str, include_context: bool
    ) -> Dict[str, Any]:
        """Explain a decision function with context"""

        # Get basic explanation
        explanation = await self.llm.explain_decision_function(
            function_id, audience=audience, format=format
        )

        result = {
            "function_id": function_id,
            "explanation": explanation,
            "audience": audience,
            "format": format,
        }

        if include_context:
            # Add ontology context
            try:
                # Get function artifact for ontology mapping
                self.registry.get_function(function_id, "latest")
                ontology_mapping = self.ontology.get_ontology_mapping(
                    "DecisionFunction"
                )
                result["ontology_context"] = {
                    "schema_fields": ontology_mapping.schema_fields,
                    "relationships": ontology_mapping.relationships,
                }
            except Exception:
                pass

            # Add knowledge graph context
            try:
                kg_node_id = await self.kg.represent_function_in_kg(function_id)
                result["knowledge_graph_context"] = {
                    "node_id": kg_node_id,
                    "representation": "function_node_created",
                }
            except Exception:
                pass

        return result

    async def _explain_trace(
        self, trace_id: str, audience: str, format: str, include_context: bool
    ) -> Dict[str, Any]:
        """Explain a decision trace with context"""

        # This would integrate with the tracing system
        # For now, return a placeholder
        return {
            "trace_id": trace_id,
            "explanation": f"Decision trace {trace_id} explanation for {audience} audience",
            "audience": audience,
            "format": format,
            "note": "Trace explanation would integrate with tracing system",
        }

    async def _generate_cross_domain_insights(
        self, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate cross-domain insights from report data"""

        insights = {
            "ontology_insights": [],
            "knowledge_graph_insights": [],
            "integration_insights": [],
        }

        # Generate ontology insights
        for function in report_data["functions"]:
            try:
                mapping = self.ontology.get_ontology_mapping("DecisionFunction")
                insights["ontology_insights"].append(
                    {
                        "function_id": function["function_id"],
                        "schema_compliance": "valid",
                        "relationship_count": len(mapping.relationships),
                    }
                )
            except Exception:
                pass

        # Generate knowledge graph insights
        for entity in report_data["entities"]:
            try:
                risk_analysis = await self.kg.analyze_entity_risk(
                    entity["entity_id"], entity["entity_type"]
                )
                insights["knowledge_graph_insights"].append(
                    {
                        "entity_id": entity["entity_id"],
                        "risk_score": risk_analysis["risk_score"],
                        "risk_factors": risk_analysis["risk_factors"],
                    }
                )
            except Exception:
                pass

        return insights

    def _generate_markdown_report(
        self, report_data: Dict[str, Any], report_type: str
    ) -> str:
        """Generate markdown report"""

        markdown = f"# Decision Layer Report - {report_type.title()}\n\n"

        # Functions section
        if report_data["functions"]:
            markdown += "## Decision Functions\n\n"
            for function in report_data["functions"]:
                markdown += f"### {function['title']}\n"
                markdown += f"- **ID**: {function['function_id']}\n"
                markdown += f"- **Version**: {function['version']}\n"
                markdown += f"- **Description**: {function['description']}\n"
                markdown += f"- **Tags**: {', '.join(function['tags'])}\n\n"

        # Entities section
        if report_data["entities"]:
            markdown += "## Entities\n\n"
            for entity in report_data["entities"]:
                markdown += f"### Entity {entity['entity_id']}\n"
                markdown += f"- **Type**: {entity['entity_type']}\n"
                markdown += f"- **Risk Score**: {entity['risk_score']:.2f}\n"
                markdown += (
                    f"- **Risk Factors**: {', '.join(entity['risk_factors'])}\n\n"
                )

        # Decisions section
        if report_data["decisions"]:
            markdown += "## Recent Decisions\n\n"
            for decision in report_data["decisions"][:10]:  # Show last 10
                markdown += (
                    f"- **{decision['function_id']}** ({decision['timestamp']})\n"
                )

        # Cross-domain insights
        if report_data["cross_domain_insights"]:
            markdown += "## Cross-Domain Insights\n\n"
            insights = report_data["cross_domain_insights"]

            if insights["ontology_insights"]:
                markdown += "### Ontology Insights\n"
                for insight in insights["ontology_insights"]:
                    markdown += f"- {insight['function_id']}: {insight['relationship_count']} relationships\n"
                markdown += "\n"

            if insights["knowledge_graph_insights"]:
                markdown += "### Knowledge Graph Insights\n"
                for insight in insights["knowledge_graph_insights"]:
                    markdown += f"- {insight['entity_id']}: Risk score {insight['risk_score']:.2f}\n"
                markdown += "\n"

        return markdown

    async def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query"""
        # Mock entity extraction - would use NER or LLM
        entities = []
        if "user" in query.lower():
            entities.append("user")
        if "transaction" in query.lower():
            entities.append("transaction")
        if "decision" in query.lower():
            entities.append("decision")
        return entities

    async def _extract_time_range(self, query: str) -> Optional[Dict[str, str]]:
        """Extract time range from query"""
        # Mock time extraction - would use date parsing
        if "today" in query.lower():
            return {"start": "2025-01-27T00:00:00Z", "end": "2025-01-27T23:59:59Z"}
        elif "last week" in query.lower():
            return {"start": "2025-01-20T00:00:00Z", "end": "2025-01-27T23:59:59Z"}
        return None

    async def _extract_ontology_entities(self, query: str) -> List[str]:
        """Extract ontology-relevant entities"""
        # Mock extraction - would use ontology-aware NER
        return ["Patient", "Doctor", "Medication"]

    async def _extract_kg_entities(self, query: str) -> List[str]:
        """Extract knowledge graph entities"""
        # Mock extraction - would use KG-aware entity linking
        return ["user_123", "transaction_456"]

    async def _map_entity_to_ontology_class(self, entity: str) -> Optional[str]:
        """Map entity to ontology class"""
        # Mock mapping - would use ontology lookup
        mapping = {"Patient": "Patient", "Doctor": "Doctor", "Medication": "Medication"}
        return mapping.get(entity)

    async def _parse_complex_query(self, query: str) -> List[Dict[str, Any]]:
        """Parse complex query into components"""
        # Mock parsing - would use LLM to decompose complex queries
        return [
            {"type": "function_search", "query": query},
            {"type": "entity_lookup", "query": query},
        ]

    async def _process_query_component(
        self, component: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process individual query component"""
        # Mock processing - would handle each component type
        return {"component_type": component["type"], "result": "processed"}

    async def _synthesize_comprehensive_answer(
        self, query: str, components: List[Dict[str, Any]], responses: Dict[str, Any]
    ) -> str:
        """Synthesize comprehensive answer from component responses"""
        # Mock synthesis - would use LLM to combine responses
        return f"Comprehensive answer for: {query}"

    def _calculate_comprehensive_confidence(self, responses: Dict[str, Any]) -> float:
        """Calculate confidence for comprehensive answer"""
        # Mock confidence calculation
        return 0.85


# Factory function for creating unified interface
def create_unified_interface(
    registry: FunctionRegistry,
    engine: DecisionEngine,
    llm_integration: LLMIntegration,
    ontology_integration: OntologyIntegration,
    knowledge_graph_integration: KnowledgeGraphIntegration,
) -> UnifiedNaturalLanguageInterface:
    """Create a unified natural language interface"""
    return UnifiedNaturalLanguageInterface(
        registry=registry,
        engine=engine,
        llm_integration=llm_integration,
        ontology_integration=ontology_integration,
        knowledge_graph_integration=knowledge_graph_integration,
    )
