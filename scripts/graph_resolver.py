#!/usr/bin/env python3
"""
Graph Resolver for Policy as Code
Provides in-memory resolver for dataset metadata and policy checks
"""

import time
from typing import Dict, Any, Optional, List
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery


class GraphResolver:
    """In-memory graph resolver with budget constraints"""

    def __init__(
        self,
        controls_path: str = "docs/ontology/controls.ttl",
        catalog_path: str = "data/catalog.ttl",
    ):
        self.graph = Graph()
        self.controls_path = controls_path
        self.catalog_path = catalog_path
        self.call_budget_ms = 100  # 100ms per call
        self.total_budget_ms = 500  # 500ms total budget
        self.total_time_ms = 0

        # Load the graph
        self._load_graph()

        # Define namespaces
        self.DCAT = Namespace("http://www.w3.org/ns/dcat#")
        self.DCT = Namespace("http://purl.org/dc/terms/")
        self.PA = Namespace("https://example.org/policy-as-code/v1#")
        self.DS = Namespace("https://example.org/dataset/")

    def _load_graph(self):
        """Load TTL files into the graph"""
        try:
            self.graph.parse(self.controls_path, format="turtle")
            self.graph.parse(self.catalog_path, format="turtle")
            print(f"Loaded graph with {len(self.graph)} triples")
        except Exception as e:
            print(f"Error loading graph: {e}")
            raise

    def _check_budget(self, start_time: float) -> bool:
        """Check if we're within budget constraints"""
        elapsed_ms = (time.time() - start_time) * 1000
        self.total_time_ms += elapsed_ms

        if elapsed_ms > self.call_budget_ms:
            print(
                f"WARNING: Call exceeded {self.call_budget_ms}ms budget: {elapsed_ms:.2f}ms"
            )
            return False

        if self.total_time_ms > self.total_budget_ms:
            print(
                f"ERROR: Total budget exceeded {self.total_budget_ms}ms: {self.total_time_ms:.2f}ms"
            )
            return False

        return True

    def lookup(
        self, query_type: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Main lookup interface with budget constraints

        Args:
            query_type: Type of query (e.g., "dataset_meta")
            params: Query parameters

        Returns:
            Query results or None if budget exceeded
        """
        start_time = time.time()

        try:
            if query_type == "dataset_meta":
                return self._lookup_dataset_meta(params)
            elif query_type == "policy_check":
                return self._lookup_policy_check(params)
            else:
                print(f"Unknown query type: {query_type}")
                return None

        finally:
            if not self._check_budget(start_time):
                return None

    def _lookup_dataset_meta(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Lookup dataset metadata by ID"""
        dataset_id = params.get("id")
        if not dataset_id:
            return None

        # SPARQL query to get dataset metadata
        query = f"""
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX pa: <https://example.org/policy-as-code/v1#>

        SELECT ?title ?pii_class ?lawful_basis ?retention_days
        WHERE {{
            ?ds a dcat:Dataset ;
                dct:identifier "{dataset_id}" ;
                dct:title ?title ;
                pa:pii_class ?pii_class ;
                pa:lawful_basis ?lawful_basis ;
                pa:retention_days ?retention_days .
        }}
        """

        # Prepare and execute query
        prepared_query = prepareQuery(query)
        results = self.graph.query(prepared_query)

        # Convert results to dict
        for row in results:
            return {
                "id": dataset_id,
                "title": str(row.title),
                "pii_class": str(row.pii_class).split("#")[-1],  # Extract concept name
                "lawful_basis": str(row.lawful_basis),
                "retention_days": int(row.retention_days),
            }

        return None

    def _lookup_policy_check(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check policy compliance against dataset metadata"""
        dataset_id = params.get("dataset_id")
        policy_max_retention = params.get("max_retention_days")

        if not dataset_id or policy_max_retention is None:
            return None

        # Get dataset metadata
        dataset_meta = self._lookup_dataset_meta({"id": dataset_id})
        if not dataset_meta:
            return {"compliant": False, "reason": "Dataset not found"}

        # Check PII class and lawful basis
        pii_class = dataset_meta["pii_class"]
        lawful_basis = dataset_meta["lawful_basis"]

        if pii_class == "PII_High":
            if lawful_basis not in ["GDPR-6-1-b", "GDPR-6-1-c"]:
                return {
                    "compliant": False,
                    "reason": f"High PII class requires GDPR-6-1-b or GDPR-6-1-c, got {lawful_basis}",
                }

        # Check retention days
        retention_days = dataset_meta["retention_days"]
        if retention_days > policy_max_retention:
            return {
                "compliant": False,
                "reason": f"Retention days {retention_days} exceeds policy limit {policy_max_retention}",
            }

        return {
            "compliant": True,
            "dataset_meta": dataset_meta,
            "checks_passed": ["pii_class", "lawful_basis", "retention_days"],
        }

    def reset_budget(self):
        """Reset the total budget counter"""
        self.total_time_ms = 0

    def get_budget_status(self) -> Dict[str, float]:
        """Get current budget status"""
        return {
            "total_time_ms": self.total_time_ms,
            "remaining_ms": self.total_budget_ms - self.total_time_ms,
            "call_budget_ms": self.call_budget_ms,
            "total_budget_ms": self.total_budget_ms,
        }


def main():
    """Test the graph resolver"""
    resolver = GraphResolver()

    print("=== Graph Resolver Test ===")

    # Test dataset metadata lookup
    print("\n1. Dataset Metadata Lookup:")
    result = resolver.lookup("dataset_meta", {"id": "loan-apps"})
    print(f"Result: {result}")

    # Test policy check
    print("\n2. Policy Check:")
    result = resolver.lookup(
        "policy_check", {"dataset_id": "loan-apps", "max_retention_days": 1000}
    )
    print(f"Result: {result}")

    # Test budget status
    print("\n3. Budget Status:")
    print(f"Budget: {resolver.get_budget_status()}")

    # Test SPARQL query
    print("\n4. SPARQL Smoke Test:")
    with open("tests/graph/sparql/smoke.rq", "r") as f:
        query = f.read()

    prepared_query = prepareQuery(query)
    results = resolver.graph.query(prepared_query)

    print("Dataset Catalog:")
    for row in results:
        print(f"  ID: {row.id}, Title: {row.title}, PII: {row.pii}")


if __name__ == "__main__":
    main()
