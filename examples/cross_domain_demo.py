"""
Cross-Domain Communication Demo

This example demonstrates how the Decision Layer enables seamless communication
between humans, LLMs, ontologies, and knowledge graphs through a unified interface.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict

from decision_layer.core import DecisionEngine
from decision_layer.knowledge_graph_integration import (
    KnowledgeGraphIntegration,
    create_knowledge_graph_provider,
)
from decision_layer.llm_integration import LLMIntegration, create_llm_provider
from decision_layer.natural_language_interface import UnifiedNaturalLanguageInterface
from decision_layer.ontology_integration import (
    OntologyIntegration,
    create_ontology_provider,
)
from decision_layer.registry import FunctionRegistry, FunctionStatus
from decision_layer.schemas import DecisionSchema, FieldType, SchemaField


async def demonstrate_cross_domain_communication():
    """Demonstrate cross-domain communication capabilities"""

    print("=== Decision Layer Cross-Domain Communication Demo ===\n")

    # 1. Initialize all components
    print("1. Initializing Cross-Domain Components...")

    # Core components
    registry = FunctionRegistry("./cross_domain_demo")
    engine = DecisionEngine()

    # Integration components
    llm_provider = create_llm_provider("mock", {})
    llm_integration = LLMIntegration(registry, llm_provider)

    ontology_provider = create_ontology_provider("mock", {})
    ontology_integration = OntologyIntegration(ontology_provider)

    kg_provider = create_knowledge_graph_provider("mock", {})
    kg_integration = KnowledgeGraphIntegration(kg_provider, registry)

    # Unified interface
    unified_interface = UnifiedNaturalLanguageInterface(
        registry=registry,
        engine=engine,
        llm_integration=llm_integration,
        ontology_integration=ontology_integration,
        knowledge_graph_integration=kg_integration,
    )

    print("   ✓ All components initialized")

    # 2. Create sample decision functions using different approaches
    print("\n2. Creating Decision Functions via Different Approaches...")

    # 2a. LLM-generated function
    print("   a) LLM-Generated Function...")
    llm_artifact = await llm_integration.generate_decision_function(
        policy_description="Approve loan applications for users with credit score above 700 and income above $50,000",
        function_id="loan_approval_llm",
        version="1.0",
        metadata={
            "title": "LLM-Generated Loan Approval",
            "description": "Loan approval logic generated from natural language policy",
            "author": "llm-system",
            "tags": ["loan", "approval", "llm-generated"],
        },
    )
    print(f"      ✓ Created {llm_artifact.function_id} v{llm_artifact.version}")

    # 2b. Ontology-driven function
    print("   b) Ontology-Driven Function...")
    patient_schema = ontology_integration.create_schema_from_ontology("Patient")
    patient_function_code = ontology_integration.create_ontology_validation_function(
        "Patient"
    )

    patient_artifact = registry.register_function(
        function_id="patient_validation",
        version="1.0",
        logic_code=patient_function_code,
        schema=patient_schema,
        metadata={
            "title": "Patient Validation",
            "description": "Patient data validation using healthcare ontology",
            "author": "ontology-system",
            "tags": ["healthcare", "patient", "validation", "ontology-driven"],
        },
        status=FunctionStatus.DRAFT,
    )
    print(f"      ✓ Created {patient_artifact.function_id} v{patient_artifact.version}")

    # 2c. Knowledge graph enhanced function
    print("   c) Knowledge Graph Enhanced Function...")
    risk_schema = DecisionSchema(
        input_schema={
            "user_id": SchemaField(
                name="user_id", type=FieldType.STRING, required=True
            ),
            "transaction_amount": SchemaField(
                name="transaction_amount", type=FieldType.FLOAT, required=True
            ),
        },
        output_schema={
            "risk_score": SchemaField(
                name="risk_score", type=FieldType.FLOAT, required=True
            ),
            "risk_level": SchemaField(
                name="risk_level", type=FieldType.STRING, required=True
            ),
            "recommendation": SchemaField(
                name="recommendation", type=FieldType.STRING, required=True
            ),
        },
        version="1.0",
        function_id="risk_assessment_kg",
    )

    risk_function_code = '''
def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Risk assessment using knowledge graph context"""

    user_id = input_data.get('user_id', '')
    transaction_amount = input_data.get('transaction_amount', 0.0)

    # Mock risk calculation using KG context
    base_risk = 0.1
    if transaction_amount > 1000:
        base_risk += 0.3
    if transaction_amount > 5000:
        base_risk += 0.4

    # Risk level classification
    if base_risk < 0.3:
        risk_level = "low"
        recommendation = "approve"
    elif base_risk < 0.7:
        risk_level = "medium"
        recommendation = "review"
    else:
        risk_level = "high"
        recommendation = "deny"

    return {
        "risk_score": base_risk,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "user_id": user_id,
        "kg_context_used": True
    }
'''

    risk_artifact = registry.register_function(
        function_id="risk_assessment_kg",
        version="1.0",
        logic_code=risk_function_code,
        schema=risk_schema,
        metadata={
            "title": "Knowledge Graph Risk Assessment",
            "description": "Risk assessment enhanced with knowledge graph context",
            "author": "kg-system",
            "tags": ["risk", "assessment", "knowledge-graph"],
        },
        status=FunctionStatus.DRAFT,
    )
    print(f"      ✓ Created {risk_artifact.function_id} v{risk_artifact.version}")

    # 3. Demonstrate natural language queries
    print("\n3. Natural Language Query Processing...")

    queries = [
        "What decision functions are available for loan approval?",
        "Explain the patient validation function in simple terms",
        "What decisions were made for user 123 today?",
        "Show me the risk assessment for transaction amount $2000",
    ]

    for i, query in enumerate(queries, 1):
        print(f"   Query {i}: {query}")

        response = await unified_interface.process_query(
            query=query,
            context={"user_id": "123", "time_range": "today"},
            format="natural",
            include_cross_domain=True,
        )

        print(f"      Intent: {response.intent.intent_type}")
        print(f"      Entities: {response.intent.entities}")
        print(f"      Response: {response.primary_response.get('type', 'processed')}")

        if response.llm_explanation:
            print(
                f"      Cross-domain explanation: {response.llm_explanation[:100]}..."
            )

        print()

    # 4. Demonstrate cross-domain explanations
    print("4. Cross-Domain Decision Explanations...")

    explanations = [
        ("loan_approval_llm", "user", "natural"),
        ("patient_validation", "business", "structured"),
        ("risk_assessment_kg", "technical", "code"),
    ]

    for function_id, audience, format in explanations:
        print(
            f"   Explaining {function_id} for {audience} audience in {format} format:"
        )

        explanation = await unified_interface.explain_decision(
            decision_id=function_id,
            audience=audience,
            format=format,
            include_context=True,
        )

        print(f"      Function: {explanation['function_id']}")
        print(f"      Audience: {explanation['audience']}")
        print(f"      Format: {explanation['format']}")

        if "ontology_context" in explanation:
            print(f"      Ontology context: Available")

        if "knowledge_graph_context" in explanation:
            print(f"      Knowledge graph context: Available")

        print()

    # 5. Demonstrate ontology integration
    print("5. Ontology Integration Features...")

    # Create schema from ontology
    doctor_schema = ontology_integration.create_schema_from_ontology("Doctor")
    print(
        f"   ✓ Created schema from Doctor ontology: {len(doctor_schema.input_schema)} input fields"
    )

    # Validate data against ontology
    patient_data = {
        "patient_id": "P123",
        "age": 35,
        "gender": "female",
        "diagnosis": "diabetes",
    }

    validation_result = ontology_integration.validate_with_ontology(
        patient_data, "Patient"
    )
    print(f"   ✓ Patient data validation: {validation_result['valid']}")

    # Enrich data with ontology
    enriched_data = ontology_integration.enrich_with_ontology(
        patient_data, "Patient", include_relationships=True
    )
    print(
        f"   ✓ Enriched data with ontology context: {len(enriched_data.get('_relationships', {}))} relationships"
    )

    # 6. Demonstrate knowledge graph integration
    print("\n6. Knowledge Graph Integration Features...")

    # Enrich decision context
    kg_context = await kg_integration.enrich_decision_context("user_123", "User")
    print(
        f"   ✓ Enriched KG context: {len(kg_context.relationships)} relationships, {len(kg_context.risk_factors)} risk factors"
    )

    # Analyze entity risk
    risk_analysis = await kg_integration.analyze_entity_risk("user_123", "User")
    print(
        f"   ✓ Risk analysis: Score {risk_analysis['risk_score']:.2f}, {len(risk_analysis['risk_factors'])} factors"
    )

    # Store decision trace in KG
    trace_data = {
        "trace_id": "trace_001",
        "function_id": "risk_assessment_kg",
        "version": "1.0",
        "input_hash": "abc123",
        "output_hash": "def456",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
        "execution_time_ms": 45,
    }

    kg_trace = await kg_integration.store_decision_trace(trace_data, ["user_123"])
    print(
        f"   ✓ Stored trace in KG: {len(kg_trace.relationships_created)} relationships created"
    )

    # 7. Demonstrate comprehensive reporting
    print("\n7. Comprehensive Cross-Domain Reporting...")

    report_criteria = {
        "time_range": {"start": "2025-01-20T00:00:00Z", "end": "2025-01-27T23:59:59Z"},
        "function_ids": [
            "loan_approval_llm",
            "patient_validation",
            "risk_assessment_kg",
        ],
        "entity_ids": ["user_123", "user_456"],
        "type": "comprehensive",
    }

    report = await unified_interface.generate_report(
        criteria=report_criteria, format="markdown"
    )

    print("   ✓ Generated comprehensive report:")
    print(f"      Length: {len(report)} characters")
    print(f"      Sections: {report.count('##')} main sections")
    print(f"      Cross-domain insights: {report.count('Cross-Domain Insights') > 0}")

    # 8. Demonstrate complex query processing
    print("\n8. Complex Query Processing...")

    complex_queries = [
        "What are the risk factors for user 123 and how do they relate to our loan approval decisions?",
        "Show me all healthcare-related decisions made this week and their compliance with our ontology",
        "Analyze the relationship between transaction patterns and risk assessment outcomes",
    ]

    for i, query in enumerate(complex_queries, 1):
        print(f"   Complex Query {i}: {query}")

        answer = await unified_interface.answer_complex_query(
            query=query, context={"time_range": "this_week"}
        )

        print(f"      Components: {len(answer['components'])}")
        print(f"      Confidence: {answer['confidence']:.2f}")
        print(f"      Answer: {answer['comprehensive_answer'][:100]}...")
        print()

    # 9. Demonstrate LLM integration features
    print("9. LLM Integration Features...")

    # Generate policy documentation
    policy_doc = await llm_integration.generate_policy_documentation(
        "loan_approval_llm"
    )
    print(f"   ✓ Generated policy documentation: {len(policy_doc)} characters")

    # Answer natural language query
    nl_query = "What functions do we have for healthcare decisions?"
    nl_answer = await llm_integration.answer_natural_language_query(nl_query)
    print(f"   ✓ Natural language query answered: {nl_answer.get('type', 'processed')}")

    # 10. Summary and capabilities
    print("\n=== Cross-Domain Communication Capabilities Summary ===")

    capabilities = [
        "✅ LLM-Generated Decision Functions",
        "✅ Ontology-Driven Schema Generation",
        "✅ Knowledge Graph Context Enrichment",
        "✅ Natural Language Query Processing",
        "✅ Cross-Domain Decision Explanations",
        "✅ Comprehensive Reporting",
        "✅ Complex Query Processing",
        "✅ Policy Documentation Generation",
        "✅ Risk Analysis with KG Context",
        "✅ Ontology-Based Validation",
        "✅ Unified Interface for All Stakeholders",
    ]

    for capability in capabilities:
        print(f"   {capability}")

    print("\n=== Integration Patterns Demonstrated ===")

    patterns = [
        "🤖 LLM ↔ Decision Functions: Natural language to code generation",
        "🏗️ Ontology ↔ Schemas: Semantic validation and enrichment",
        "🕸️ Knowledge Graph ↔ Context: Entity relationships and risk analysis",
        "🗣️ Natural Language ↔ All: Unified query interface",
        "📊 Cross-Domain ↔ Reporting: Comprehensive insights generation",
    ]

    for pattern in patterns:
        print(f"   {pattern}")

    print("\nThe Decision Layer now provides a complete cross-domain communication")
    print("platform that enables seamless interaction between humans, LLMs,")
    print("ontologies, and knowledge graphs!")


if __name__ == "__main__":
    asyncio.run(demonstrate_cross_domain_communication())
