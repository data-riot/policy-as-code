"""
Example: Natural Language Temporal Policy Queries

This demonstrates how to use the Decision Layer's natural language interface
to query for policies active in April 2017 using conversational language.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key"  # Set your API key

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def natural_language_query(
    query: str, context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Send a natural language query to the Decision Layer
    """

    payload = {"query": query, "include_cross_domain": True, "format": "natural"}

    if context:
        payload["context"] = context

    response = requests.post(
        f"{API_BASE_URL}/cross-domain/query", json=payload, headers=headers
    )
    response.raise_for_status()

    return response.json()


def explain_decision_function(
    function_id: str, version: str, audience: str = "user"
) -> Dict[str, Any]:
    """
    Get a natural language explanation of a decision function
    """

    payload = {
        "function_id": function_id,
        "version": version,
        "audience": audience,
        "format": "natural",
        "include_context": True,
    }

    response = requests.post(
        f"{API_BASE_URL}/cross-domain/explain", json=payload, headers=headers
    )
    response.raise_for_status()

    return response.json()


async def main():
    """
    Main function demonstrating natural language temporal queries
    """

    print("🚀 Decision Layer - Natural Language Temporal Queries")
    print("=" * 60)

    # Set temporal context for April 2017
    temporal_context = {
        "time_range": {"start": "2017-04-01T00:00:00Z", "end": "2017-04-30T23:59:59Z"},
        "include_metadata": True,
        "include_traces": False,
    }

    try:
        # 1. Basic temporal query
        print("\n1️⃣ Basic temporal query...")
        query1 = "What decision functions were active in April 2017?"
        result1 = natural_language_query(query1, temporal_context)

        print(f"Query: {query1}")
        print(f"Response: {result1.get('primary_response', 'No response')}")
        if result1.get("llm_explanation"):
            print(f"LLM Explanation: {result1['llm_explanation']}")

        # 2. Query with specific criteria
        print("\n2️⃣ Query with specific criteria...")
        query2 = "Show me all loan approval policies that were active in April 2017 and had high success rates"
        result2 = natural_language_query(query2, temporal_context)

        print(f"Query: {query2}")
        print(f"Response: {result2.get('primary_response', 'No response')}")

        # 3. Query with compliance focus
        print("\n3️⃣ Compliance-focused query...")
        query3 = "Which policies active in April 2017 were compliant with SOX and GDPR regulations?"
        result3 = natural_language_query(query3, temporal_context)

        print(f"Query: {query3}")
        print(f"Response: {result3.get('primary_response', 'No response')}")

        # 4. Query with performance analysis
        print("\n4️⃣ Performance analysis query...")
        query4 = "Analyze the performance of all risk assessment policies that were active in April 2017"
        result4 = natural_language_query(query4, temporal_context)

        print(f"Query: {query4}")
        print(f"Response: {result4.get('primary_response', 'No response')}")

        # 5. Query with policy references
        print("\n5️⃣ Policy reference query...")
        query5 = "What were the policy references and compliance requirements for all active policies in April 2017?"
        result5 = natural_language_query(query5, temporal_context)

        print(f"Query: {query5}")
        print(f"Response: {result5.get('primary_response', 'No response')}")

        # 6. Query with author information
        print("\n6️⃣ Author-focused query...")
        query6 = "Who authored the policies that were active in April 2017 and what were their approval workflows?"
        result6 = natural_language_query(query6, temporal_context)

        print(f"Query: {query6}")
        print(f"Response: {result6.get('primary_response', 'No response')}")

        # 7. Query with change analysis
        print("\n7️⃣ Change analysis query...")
        query7 = "What changes were made to policies between March and April 2017, and what was the impact on decision outcomes?"
        result7 = natural_language_query(query7, temporal_context)

        print(f"Query: {query7}")
        print(f"Response: {result7.get('primary_response', 'No response')}")

        # 8. Query with business impact
        print("\n8️⃣ Business impact query...")
        query8 = "What was the business impact of the policies active in April 2017? Show me approval rates, processing times, and any compliance issues."
        result8 = natural_language_query(query8, temporal_context)

        print(f"Query: {query8}")
        print(f"Response: {result8.get('primary_response', 'No response')}")

        # 9. Query with cross-domain context
        print("\n9️⃣ Cross-domain context query...")
        query9 = "How did the policies active in April 2017 interact with our knowledge graph and ontology systems? What insights can we derive?"
        result9 = natural_language_query(query9, temporal_context)

        print(f"Query: {query9}")
        print(f"Response: {result9.get('primary_response', 'No response')}")
        if result9.get("ontology_context"):
            print(f"Ontology Context: {result9['ontology_context']}")
        if result9.get("knowledge_graph_context"):
            print(f"Knowledge Graph Context: {result9['knowledge_graph_context']}")

        # 10. Query with recommendations
        print("\n🔟 Recommendations query...")
        query10 = "Based on the performance of policies active in April 2017, what recommendations do you have for improving our decision management system?"
        result10 = natural_language_query(query10, temporal_context)

        print(f"Query: {query10}")
        print(f"Response: {result10.get('primary_response', 'No response')}")

        # 11. Generate comprehensive report using natural language
        print("\n📋 Generating comprehensive report...")
        report_query = """
        Generate a comprehensive report for April 2017 that includes:
        1. All active decision functions with their versions and authors
        2. Performance metrics including success rates and execution times
        3. Compliance status and policy references
        4. Business impact analysis
        5. Recommendations for improvement
        6. Cross-domain insights from ontology and knowledge graph integration
        """

        report_result = natural_language_query(report_query, temporal_context)

        print("Comprehensive Report:")
        print(
            f"Primary Response: {report_result.get('primary_response', 'No response')}"
        )

        if report_result.get("llm_explanation"):
            print(f"\nDetailed Analysis: {report_result['llm_explanation']}")

        # Save the comprehensive report
        report_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "query": report_query,
            "temporal_context": temporal_context,
            "response": report_result,
        }

        with open("april_2017_natural_language_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        print(
            f"\n✅ Comprehensive report saved to april_2017_natural_language_report.json"
        )

        # 12. Example of explaining a specific function
        print("\n📖 Function explanation example...")
        # This would work if you have a specific function to explain
        try:
            explanation = explain_decision_function(
                "loan_approval", "2.0", "business_analyst"
            )
            print(
                f"Function Explanation: {explanation.get('explanation', 'No explanation available')}"
            )
        except requests.exceptions.RequestException:
            print("No specific function to explain (this is expected in the example)")

    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        print("Make sure the Decision Layer API is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


def demonstrate_conversational_queries():
    """
    Demonstrate a conversational flow of queries
    """

    print("\n💬 Conversational Query Flow")
    print("=" * 40)

    # Simulate a conversation
    conversation_queries = [
        "What policies were active in April 2017?",
        "Which of those had the highest error rates?",
        "What were the main causes of those errors?",
        "How did the policies perform compared to March 2017?",
        "What recommendations do you have for improving these policies?",
        "Can you show me the approval workflow for the loan approval policy?",
        "What compliance issues were identified during this period?",
        "How did the knowledge graph integration help with decision accuracy?",
    ]

    temporal_context = {
        "time_range": {"start": "2017-04-01T00:00:00Z", "end": "2017-04-30T23:59:59Z"},
        "include_metadata": True,
        "include_traces": True,
    }

    print("Simulating a conversational query flow...")

    for i, query in enumerate(conversation_queries, 1):
        print(f"\nQ{i}: {query}")

        try:
            result = natural_language_query(query, temporal_context)
            response = result.get("primary_response", "No response available")
            print(f"A{i}: {response[:200]}{'...' if len(response) > 200 else ''}")

        except Exception as e:
            print(f"A{i}: Error processing query: {e}")


if __name__ == "__main__":
    asyncio.run(main())
    demonstrate_conversational_queries()
