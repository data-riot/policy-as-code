#!/usr/bin/env python3
"""
SHACL validation service for Policy as Code
Validates JSON-LD policies against SHACL schemas
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import requests
from rdflib import Graph
from pyshacl import validate


class SHACLValidator:
    """SHACL validation service"""

    def __init__(self, schema_path: str, fuseki_url: str = None):
        self.schema_path = schema_path
        self.fuseki_url = fuseki_url
        self.schema_graph = self._load_schema()

    def _load_schema(self) -> Graph:
        """Load SHACL schema from file"""
        graph = Graph()
        graph.parse(self.schema_path, format="turtle")
        return graph

    def validate_jsonld(self, jsonld_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON-LD data against SHACL schema"""

        # Convert JSON-LD to RDF
        data_graph = Graph()

        # Create JSON-LD string
        jsonld_str = json.dumps(jsonld_data)

        # Parse JSON-LD into RDF graph
        data_graph.parse(data=jsonld_str, format="json-ld")

        # Validate against SHACL schema
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=self.schema_graph,
            ont_graph=None,
            inference="rdfs",
            abort_on_first=False,
            allow_warnings=False,
            meta_shacl=False,
            debug=False,
        )

        # Parse validation results
        violations = []
        if not conforms:
            for s, p, o in results_graph.triples((None, None, None)):
                if "sh:Violation" in str(p):
                    violations.append(
                        {"severity": str(p), "message": str(o), "subject": str(s)}
                    )

        return {
            "conforms": conforms,
            "violations": violations,
            "results_text": results_text,
        }

    def validate_yaml_file(self, yaml_path: str, context_path: str) -> Dict[str, Any]:
        """Validate YAML policy file"""

        # Convert YAML to JSON-LD
        import yaml

        with open(yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        # Load context
        with open(context_path, "r") as f:
            context = json.load(f)

        # Convert to JSON-LD format
        jsonld_data = {
            "@context": context["@context"],
            "@type": "Policy",
            "@id": f"https://policy-as-code.org/policy/{yaml_data['id']}",
            "id": yaml_data["id"],
            "version": yaml_data["version"],
            "owner": yaml_data["owner"],
            "entrypoint": yaml_data["entrypoint"],
            "status": yaml_data.get("status", "draft"),
        }

        # Add legal references if present
        if "legal_references" in yaml_data:
            jsonld_data["legalReference"] = []
            for ref in yaml_data["legal_references"]:
                jsonld_data["legalReference"].append(
                    {
                        "@id": ref["uri"],
                        "title": ref.get("title", ""),
                        "section": ref.get("section", ""),
                    }
                )

        # Validate
        return self.validate_jsonld(jsonld_data)


def main():
    """Main validation function"""
    if len(sys.argv) < 2:
        print("Usage: validate_shacl.py <jsonld_file_or_yaml_file> [context_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    context_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Get schema path from environment or use default
    schema_path = os.getenv("SHACL_SCHEMA_PATH", "schemas/policy_shape.ttl")

    if not os.path.exists(schema_path):
        print(f"SHACL schema not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    validator = SHACLValidator(schema_path)

    try:
        if input_file.endswith(".yaml") or input_file.endswith(".yml"):
            if not context_file:
                print("Context file required for YAML validation", file=sys.stderr)
                sys.exit(1)
            result = validator.validate_yaml_file(input_file, context_file)
        else:
            # Assume JSON-LD file
            with open(input_file, "r") as f:
                jsonld_data = json.load(f)
            result = validator.validate_jsonld(jsonld_data)

        # Output results
        print(json.dumps(result, indent=2))

        # Exit with error code if validation failed
        if not result["conforms"]:
            sys.exit(1)

    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
