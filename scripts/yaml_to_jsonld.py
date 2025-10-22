#!/usr/bin/env python3
"""
YAML to JSON-LD converter for Policy as Code
Converts YAML policies to JSON-LD format for SHACL validation
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any


def yaml_to_jsonld(yaml_content: str, context_path: str) -> Dict[str, Any]:
    """Convert YAML policy to JSON-LD format"""

    # Load the context
    with open(context_path, "r") as f:
        context = json.load(f)

    # Parse YAML
    policy_data = yaml.safe_load(yaml_content)

    # Convert to JSON-LD
    jsonld = {
        "@context": context["@context"],
        "@type": "Policy",
        "@id": f"https://policy-as-code.org/policy/{policy_data['id']}",
        "id": policy_data["id"],
        "version": policy_data["version"],
        "owner": policy_data["owner"],
        "entrypoint": policy_data["entrypoint"],
        "status": policy_data.get("status", "draft"),
    }

    # Add legal references if present
    if "legal_references" in policy_data:
        jsonld["legalReference"] = []
        for ref in policy_data["legal_references"]:
            jsonld["legalReference"].append(
                {
                    "@id": ref["uri"],
                    "title": ref.get("title", ""),
                    "section": ref.get("section", ""),
                }
            )

    return jsonld


def main():
    """Main conversion function"""
    if len(sys.argv) != 3:
        print("Usage: yaml_to_jsonld.py <yaml_file> <context_file>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    context_file = sys.argv[2]

    try:
        # Read YAML file
        with open(yaml_file, "r") as f:
            yaml_content = f.read()

        # Convert to JSON-LD
        jsonld = yaml_to_jsonld(yaml_content, context_file)

        # Output JSON-LD
        print(json.dumps(jsonld, indent=2))

    except Exception as e:
        print(f"Error converting YAML to JSON-LD: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
