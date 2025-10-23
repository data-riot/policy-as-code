#!/usr/bin/env python3
"""
Test suite for Graph Resolver
Tests the integration points and budget constraints
"""

import unittest
import tempfile
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from scripts.graph_resolver import GraphResolver  # noqa: E402


class TestGraphResolver(unittest.TestCase):
    """Test cases for GraphResolver"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary TTL files for testing
        self.temp_dir = tempfile.mkdtemp()

        # Create test controls file
        self.controls_path = os.path.join(self.temp_dir, "controls.ttl")
        with open(self.controls_path, "w") as f:
            f.write(
                """
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ctr: <https://example.org/policy-as-code/controls#> .

ctr:gdpr-art6-1b a skos:Concept ;
  skos:notation "GDPR-6-1-b" .
            """
            )

        # Create test catalog file
        self.catalog_path = os.path.join(self.temp_dir, "catalog.ttl")
        with open(self.catalog_path, "w") as f:
            f.write(
                """
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix pa: <https://example.org/policy-as-code/v1#> .
@prefix ds: <https://example.org/dataset/> .

ds:test-dataset a dcat:Dataset ;
  dct:identifier "test-dataset" ;
  dct:title "Test Dataset" ;
  pa:pii_class pa:PII_High ;
  pa:lawful_basis "GDPR-6-1-b" ;
  pa:retention_days "365"^^<http://www.w3.org/2001/XMLSchema#integer> .
            """
            )

        # Initialize resolver
        self.resolver = GraphResolver(self.controls_path, self.catalog_path)

    def test_dataset_meta_lookup(self):
        """Test dataset metadata lookup"""
        result = self.resolver.lookup("dataset_meta", {"id": "test-dataset"})

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "test-dataset")
        self.assertEqual(result["title"], "Test Dataset")
        self.assertEqual(result["pii_class"], "PII_High")
        self.assertEqual(result["lawful_basis"], "GDPR-6-1-b")
        self.assertEqual(result["retention_days"], 365)

    def test_dataset_meta_not_found(self):
        """Test dataset metadata lookup for non-existent dataset"""
        result = self.resolver.lookup("dataset_meta", {"id": "non-existent"})
        self.assertIsNone(result)

    def test_policy_check_compliant(self):
        """Test policy check for compliant dataset"""
        result = self.resolver.lookup(
            "policy_check", {"dataset_id": "test-dataset", "max_retention_days": 1000}
        )

        self.assertIsNotNone(result)
        self.assertTrue(result["compliant"])
        self.assertIn("dataset_meta", result)
        self.assertIn("checks_passed", result)

    def test_policy_check_retention_violation(self):
        """Test policy check for retention violation"""
        result = self.resolver.lookup(
            "policy_check", {"dataset_id": "test-dataset", "max_retention_days": 100}
        )

        self.assertIsNotNone(result)
        self.assertFalse(result["compliant"])
        self.assertIn("retention", result["reason"].lower())

    def test_budget_constraints(self):
        """Test budget constraint enforcement"""
        # Reset budget
        self.resolver.reset_budget()

        # Make multiple calls to test budget
        for i in range(10):
            result = self.resolver.lookup("dataset_meta", {"id": "test-dataset"})
            if result is None:
                # Budget exceeded
                break

        budget_status = self.resolver.get_budget_status()
        self.assertLessEqual(
            budget_status["total_time_ms"], budget_status["total_budget_ms"]
        )

    def test_unknown_query_type(self):
        """Test handling of unknown query type"""
        result = self.resolver.lookup("unknown_type", {})
        self.assertIsNone(result)

    def test_missing_parameters(self):
        """Test handling of missing parameters"""
        result = self.resolver.lookup("dataset_meta", {})
        self.assertIsNone(result)

        result = self.resolver.lookup("policy_check", {})
        self.assertIsNone(result)


def run_tests():
    """Run the test suite"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
