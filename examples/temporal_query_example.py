"""
Example: Querying for policies active in April 2017

This demonstrates how to use the Decision Layer API to find all decision functions
that were active (deployed and approved) during a specific time period.
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


def query_policies_active_in_april_2017():
    """
    Query for all policies that were active in April 2017
    """

    # Method 1: Using the functions endpoint with date filtering
    print("Querying for policies active in April 2017...")

    # Get all functions with their metadata
    response = requests.get(f"{API_BASE_URL}/functions", headers=headers)
    response.raise_for_status()

    functions = response.json()
    active_policies = []

    # Filter for policies active in April 2017
    target_start = datetime(2017, 4, 1, tzinfo=timezone.utc)
    target_end = datetime(2017, 4, 30, 23, 59, 59, tzinfo=timezone.utc)

    for function in functions:
        function_id = function["function_id"]

        # Get detailed information for each function
        detail_response = requests.get(
            f"{API_BASE_URL}/functions/{function_id}/info", headers=headers
        )
        detail_response.raise_for_status()

        function_details = detail_response.json()

        # Check if any version was active during April 2017
        for version_info in function_details.get("versions", []):
            version = version_info["version"]
            created_at = datetime.fromisoformat(
                version_info["created_at"].replace("Z", "+00:00")
            )
            status = version_info["status"]

            # Check if this version was active during April 2017
            if (
                status == "approved"
                and created_at <= target_end
                and (
                    version_info.get("deprecated_at") is None
                    or datetime.fromisoformat(
                        version_info["deprecated_at"].replace("Z", "+00:00")
                    )
                    >= target_start
                )
            ):

                active_policies.append(
                    {
                        "function_id": function_id,
                        "version": version,
                        "title": version_info.get("title", function_id),
                        "description": version_info.get("description", ""),
                        "created_at": version_info["created_at"],
                        "author": version_info.get("author", "unknown"),
                        "tags": version_info.get("tags", []),
                        "policy_references": version_info.get("policy_references", []),
                        "compliance_requirements": version_info.get(
                            "compliance_requirements", []
                        ),
                    }
                )

    return active_policies


def query_policies_with_temporal_context():
    """
    Advanced query with temporal context using cross-domain features
    """

    print("Advanced temporal query with cross-domain context...")

    # Use the cross-domain query endpoint for more sophisticated temporal queries
    query_data = {
        "query": "Show me all decision functions that were active in April 2017 with their policy references and compliance requirements",
        "context": {
            "time_range": {
                "start": "2017-04-01T00:00:00Z",
                "end": "2017-04-30T23:59:59Z",
            },
            "include_metadata": True,
            "include_traces": False,
        },
        "include_cross_domain": True,
        "format": "structured",
    }

    response = requests.post(
        f"{API_BASE_URL}/cross-domain/query", json=query_data, headers=headers
    )
    response.raise_for_status()

    return response.json()


def get_policy_execution_history(
    function_id: str, version: str, start_date: str, end_date: str
):
    """
    Get execution history for a specific policy during a time period
    """

    print(f"📊 Getting execution history for {function_id} v{version}...")

    # Query traces for the specific function and time period
    response = requests.get(
        f"{API_BASE_URL}/traces/{function_id}",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "version": version,
            "limit": 1000,
        },
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def analyze_policy_performance(active_policies: List[Dict[str, Any]]):
    """
    Analyze performance metrics for active policies
    """

    print("📈 Analyzing policy performance...")

    performance_data = []

    for policy in active_policies:
        function_id = policy["function_id"]
        version = policy["version"]

        # Get performance metrics for April 2017
        response = requests.get(
            f"{API_BASE_URL}/functions/{function_id}/metrics",
            params={
                "version": version,
                "start_date": "2017-04-01",
                "end_date": "2017-04-30",
            },
            headers=headers,
        )
        response.raise_for_status()

        metrics = response.json()

        performance_data.append(
            {
                "function_id": function_id,
                "version": version,
                "total_executions": metrics.get("total_executions", 0),
                "success_rate": metrics.get("success_rate", 0),
                "average_execution_time": metrics.get("average_execution_time", 0),
                "error_count": metrics.get("error_count", 0),
                "policy_references": policy.get("policy_references", []),
                "compliance_requirements": policy.get("compliance_requirements", []),
            }
        )

    return performance_data


def generate_policy_report(
    active_policies: List[Dict[str, Any]], performance_data: List[Dict[str, Any]]
):
    """
    Generate a comprehensive report of active policies
    """

    print("📋 Generating comprehensive policy report...")

    report = {
        "report_period": "April 2017",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_active_policies": len(active_policies),
            "total_executions": sum(p["total_executions"] for p in performance_data),
            "average_success_rate": (
                sum(p["success_rate"] for p in performance_data) / len(performance_data)
                if performance_data
                else 0
            ),
        },
        "policies": [],
    }

    # Combine policy and performance data
    for policy in active_policies:
        performance = next(
            (
                p
                for p in performance_data
                if p["function_id"] == policy["function_id"]
                and p["version"] == policy["version"]
            ),
            None,
        )

        policy_report = {
            "function_id": policy["function_id"],
            "version": policy["version"],
            "title": policy["title"],
            "description": policy["description"],
            "author": policy["author"],
            "tags": policy["tags"],
            "policy_references": policy["policy_references"],
            "compliance_requirements": policy["compliance_requirements"],
            "performance": performance or {},
        }

        report["policies"].append(policy_report)

    return report


async def main():
    """
    Main function demonstrating temporal policy querying
    """

    print("🚀 Decision Layer - Temporal Policy Query Example")
    print("=" * 60)

    try:
        # 1. Basic query for active policies
        print("\n1️⃣ Basic temporal query...")
        active_policies = query_policies_active_in_april_2017()

        print(f"Found {len(active_policies)} active policies in April 2017:")
        for policy in active_policies:
            print(
                f"  • {policy['function_id']} v{policy['version']} - {policy['title']}"
            )

        # 2. Advanced cross-domain query
        print("\n2️⃣ Advanced cross-domain query...")
        cross_domain_result = query_policies_with_temporal_context()
        print(
            f"Cross-domain query result: {cross_domain_result.get('primary_response', 'No response')}"
        )

        # 3. Get execution history for a sample policy
        if active_policies:
            sample_policy = active_policies[0]
            print(f"\n3️⃣ Execution history for {sample_policy['function_id']}...")

            history = get_policy_execution_history(
                sample_policy["function_id"],
                sample_policy["version"],
                "2017-04-01",
                "2017-04-30",
            )

            print(f"Found {len(history.get('traces', []))} executions")

        # 4. Analyze performance
        print("\n4️⃣ Performance analysis...")
        performance_data = analyze_policy_performance(active_policies)

        for perf in performance_data:
            print(
                f"  • {perf['function_id']}: {perf['total_executions']} executions, "
                f"{perf['success_rate']:.1%} success rate"
            )

        # 5. Generate comprehensive report
        print("\n5️⃣ Generating comprehensive report...")
        report = generate_policy_report(active_policies, performance_data)

        # Save report to file
        with open("april_2017_policy_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"✅ Report saved to april_2017_policy_report.json")
        print(
            f"📊 Summary: {report['summary']['total_active_policies']} policies, "
            f"{report['summary']['total_executions']} total executions"
        )

    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        print("Make sure the Decision Layer API is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
