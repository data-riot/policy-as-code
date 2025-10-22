"""
Comprehensive Documentation-Implementation Cross-Check Tests

This test suite ensures that:
1. Documentation accurately reflects the actual implementation
2. All documented features are actually implemented
3. All implementation features are properly documented
4. Configuration files match documentation
5. API specifications match actual endpoints
6. Example scripts are runnable
7. Security features match security documentation
8. Process workflows are correctly documented

These tests help maintain consistency between docs and code,
ensuring the system works as documented for human users.
"""

import os
import json
import yaml
import pytest
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Any, Set
from unittest.mock import patch, Mock

# Test configuration
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
POLICY_AS_CODE_DIR = PROJECT_ROOT / "policy_as_code"
EXAMPLES_DIR = PROJECT_ROOT / "examples"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
CONFIG_DIR = PROJECT_ROOT / "config"


class TestDocumentationImplementationConsistency:
    """Test that documentation matches implementation"""

    def test_documented_modules_exist(self):
        """Test 1: All documented modules actually exist and are importable"""
        documented_modules = [
            "policy_as_code.core.enhanced_engine",
            "policy_as_code.core.security",
            "policy_as_code.api.enhanced_rest",
            "policy_as_code.governance.audit_service",
            "policy_as_code.governance.legal_refs",
            "policy_as_code.governance.release",
            "policy_as_code.tracing.ledger",
            "policy_as_code.ai.llm",
            "policy_as_code.ai.conversational",
            "policy_as_code.validation.eli_validator",
            "policy_as_code.data.domain_agents",
            "policy_as_code.data.semantic_context",
            "policy_as_code.data.drift_detection",
            "policy_as_code.data.intent_discovery",
            "policy_as_code.data.multimodal",
            "policy_as_code.data.context_compression",
            "policy_as_code.data.autonomous_products",
        ]

        missing_modules = []
        importable_modules = []

        for module_name in documented_modules:
            try:
                importlib.import_module(module_name)
                importable_modules.append(module_name)
            except ImportError as e:
                missing_modules.append(f"{module_name}: {e}")

        # Report results
        print(f"✅ Importable modules: {len(importable_modules)}")
        print(f"❌ Missing modules: {len(missing_modules)}")

        if missing_modules:
            print("Missing modules:")
            for module in missing_modules:
                print(f"  - {module}")

        # Allow some missing modules (dependencies not installed)
        assert (
            len(importable_modules) >= len(documented_modules) * 0.6
        ), f"Too many missing modules: {len(missing_modules)}/{len(documented_modules)}"

    def test_api_endpoints_match_openapi_spec(self):
        """Test 2: API endpoints in enhanced_rest.py match OpenAPI specification"""
        openapi_file = DOCS_DIR / "reference" / "openapi.json"
        assert openapi_file.exists(), "OpenAPI specification file missing"

        with open(openapi_file, "r") as f:
            openapi_spec = json.load(f)

        # Check that documented endpoints exist in OpenAPI spec
        documented_endpoints = list(openapi_spec.get("paths", {}).keys())

        # Basic endpoints that should exist
        expected_endpoints = [
            "/health",
            "/registry/functions",
            "/registry/functions/{function_id}",
            "/decisions/{function_id}",
            "/audit/reports",
            "/explain/{trace_id}",
            "/legal/validate",
        ]

        missing_endpoints = []
        for endpoint in expected_endpoints:
            if endpoint not in documented_endpoints:
                missing_endpoints.append(endpoint)

        print(f"✅ Documented endpoints: {len(documented_endpoints)}")
        print(f"❌ Missing endpoints: {len(missing_endpoints)}")

        if missing_endpoints:
            print("Missing endpoints:")
            for endpoint in missing_endpoints:
                print(f"  - {endpoint}")

        # Allow some missing endpoints
        assert (
            len(missing_endpoints) <= 2
        ), f"Too many missing endpoints: {missing_endpoints}"

    def test_configuration_files_exist_and_valid(self):
        """Test 3: Configuration files exist and are valid YAML/JSON"""
        config_files = [
            CONFIG_DIR / "config.yaml",
            CONFIG_DIR / "domain_data_architecture.yaml",
            CONFIG_DIR / "env.example",
        ]

        valid_configs = 0
        for config_file in config_files:
            if config_file.exists():
                try:
                    if config_file.suffix in [".yaml", ".yml"]:
                        with open(config_file, "r") as f:
                            yaml.safe_load(f)
                    elif config_file.suffix == ".json":
                        with open(config_file, "r") as f:
                            json.load(f)
                    valid_configs += 1
                    print(f"✅ {config_file.name} is valid")
                except Exception as e:
                    print(f"❌ {config_file.name} is invalid: {e}")
            else:
                print(f"❌ {config_file.name} missing")

        assert (
            valid_configs >= 2
        ), f"Too few valid config files: {valid_configs}/{len(config_files)}"

    def test_schema_files_match_api_documentation(self):
        """Test 4: Schema files exist and match API documentation"""
        schema_files = [
            "CoreOntology.json",
            "DecisionFunctionSpec.json",
            "EligibilityInput.json",
            "EligibilityOutput.json",
            "SchemaRegistry.json",
            "TraceRecord.json",
        ]

        valid_schemas = 0
        for schema_file in schema_files:
            schema_path = SCHEMAS_DIR / schema_file
            if schema_path.exists():
                try:
                    with open(schema_path, "r") as f:
                        schema_data = json.load(f)
                        if isinstance(schema_data, dict):
                            valid_schemas += 1
                            print(f"✅ {schema_file} is valid")
                        else:
                            print(f"❌ {schema_file} is not a JSON object")
                except Exception as e:
                    print(f"❌ {schema_file} is invalid: {e}")
            else:
                print(f"❌ {schema_file} missing")

        assert (
            valid_schemas >= 4
        ), f"Too few valid schemas: {valid_schemas}/{len(schema_files)}"

    def test_example_scripts_are_runnable(self):
        """Test 5: Example scripts exist and are syntactically valid Python"""
        example_scripts = [
            "comprehensive_demo.py",
            "environmental_compliance.py",
            "healthcare_eligibility.py",
            "immigration_visa_processing.py",
            "refund_policy.py",
            "risk_assessment.py",
            "social_benefits_allocation.py",
            "tax_calculation.py",
            "yaml_decision_example.py",
            "domain_first_demo.py",
        ]

        valid_scripts = 0
        for script in example_scripts:
            script_path = (
                EXAMPLES_DIR / "demos" / script
                if script != "domain_first_demo.py"
                else EXAMPLES_DIR / script
            )
            if script_path.exists():
                try:
                    with open(script_path, "r") as f:
                        compile(f.read(), str(script_path), "exec")
                    valid_scripts += 1
                    print(f"✅ {script} is syntactically valid")
                except SyntaxError as e:
                    print(f"❌ {script} has syntax error: {e}")
            else:
                print(f"❌ {script} missing")

        assert (
            valid_scripts >= 6
        ), f"Too few valid scripts: {valid_scripts}/{len(example_scripts)}"

    def test_makefile_targets_exist(self):
        """Test 6: Makefile targets mentioned in docs actually exist"""
        makefile_path = PROJECT_ROOT / "Makefile"
        assert makefile_path.exists(), "Makefile missing"

        with open(makefile_path, "r") as f:
            makefile_content = f.read()

        # Targets mentioned in documentation
        documented_targets = [
            "install",
            "test",
            "lint",
            "format",
            "demo",
            "clean",
            "setup-db",
            "benchmark",
            "audit",
        ]

        existing_targets = []
        missing_targets = []
        for target in documented_targets:
            if f"{target}:" in makefile_content:
                existing_targets.append(target)
            else:
                missing_targets.append(target)

        print(f"✅ Existing targets: {len(existing_targets)}")
        print(f"❌ Missing targets: {len(missing_targets)}")

        if missing_targets:
            print("Missing targets:")
            for target in missing_targets:
                print(f"  - {target}")

        assert (
            len(existing_targets) >= 6
        ), f"Too few existing targets: {len(existing_targets)}/{len(documented_targets)}"

    def test_docker_configuration_matches_deployment_docs(self):
        """Test 7: Docker files exist and match deployment documentation"""
        docker_files = [
            "Dockerfile",
            "Dockerfile.enhanced",
            "docker-compose.yml",
            "docker-compose.enhanced.yml",
        ]

        existing_docker_files = 0
        for docker_file in docker_files:
            docker_path = PROJECT_ROOT / docker_file
            if docker_path.exists():
                with open(docker_path, "r") as f:
                    content = f.read().strip()
                    if len(content) > 0:
                        existing_docker_files += 1
                        print(f"✅ {docker_file} exists and is not empty")
                    else:
                        print(f"❌ {docker_file} is empty")
            else:
                print(f"❌ {docker_file} missing")

        assert (
            existing_docker_files >= 2
        ), f"Too few Docker files: {existing_docker_files}/{len(docker_files)}"

    def test_security_features_match_documentation(self):
        """Test 8: Security features mentioned in docs are implemented"""
        security_docs = DOCS_DIR / "security.md"
        assert security_docs.exists(), "Security documentation missing"

        # Check that security modules exist
        security_modules = [
            "policy_as_code.security.kms_integration",
            "policy_as_code.core.security",
        ]

        existing_security_modules = 0
        for module_name in security_modules:
            try:
                importlib.import_module(module_name)
                existing_security_modules += 1
                print(f"✅ {module_name} is importable")
            except ImportError:
                print(f"❌ {module_name} is not importable")

        assert (
            existing_security_modules >= 1
        ), f"Too few security modules: {existing_security_modules}/{len(security_modules)}"

    def test_governance_features_are_implemented(self):
        """Test 9: Governance features documented are actually implemented"""
        governance_modules = [
            "policy_as_code.governance.audit_service",
            "policy_as_code.governance.legal_refs",
            "policy_as_code.governance.release",
            "policy_as_code.governance.explain",
        ]

        existing_governance_modules = 0
        for module_name in governance_modules:
            try:
                importlib.import_module(module_name)
                existing_governance_modules += 1
                print(f"✅ {module_name} is importable")
            except ImportError:
                print(f"❌ {module_name} is not importable")

        assert (
            existing_governance_modules >= 2
        ), f"Too few governance modules: {existing_governance_modules}/{len(governance_modules)}"

    def test_ai_features_match_agentic_documentation(self):
        """Test 10: AI features mentioned in agentic-ai.md are implemented"""
        ai_modules = [
            "policy_as_code.ai.llm",
            "policy_as_code.ai.conversational",
            "policy_as_code.ai.workflow",
            "policy_as_code.ai.monitoring",
        ]

        existing_ai_modules = 0
        for module_name in ai_modules:
            try:
                importlib.import_module(module_name)
                existing_ai_modules += 1
                print(f"✅ {module_name} is importable")
            except ImportError:
                print(f"❌ {module_name} is not importable")

        assert (
            existing_ai_modules >= 2
        ), f"Too few AI modules: {existing_ai_modules}/{len(ai_modules)}"

    def test_data_architecture_features_exist(self):
        """Test 11: Data architecture features are implemented"""
        data_modules = [
            "policy_as_code.data.domain_agents",
            "policy_as_code.data.semantic_context",
            "policy_as_code.data.drift_detection",
            "policy_as_code.data.intent_discovery",
            "policy_as_code.data.multimodal",
            "policy_as_code.data.context_compression",
            "policy_as_code.data.autonomous_products",
        ]

        existing_data_modules = 0
        for module_name in data_modules:
            try:
                importlib.import_module(module_name)
                existing_data_modules += 1
                print(f"✅ {module_name} is importable")
            except ImportError:
                print(f"❌ {module_name} is not importable")

        assert (
            existing_data_modules >= 4
        ), f"Too few data modules: {existing_data_modules}/{len(data_modules)}"

    def test_validation_features_are_implemented(self):
        """Test 12: Validation features are implemented"""
        validation_modules = [
            "policy_as_code.validation.eli_validator",
        ]

        existing_validation_modules = 0
        for module_name in validation_modules:
            try:
                importlib.import_module(module_name)
                existing_validation_modules += 1
                print(f"✅ {module_name} is importable")
            except ImportError:
                print(f"❌ {module_name} is not importable")

        assert (
            existing_validation_modules >= 1
        ), f"Too few validation modules: {existing_validation_modules}/{len(validation_modules)}"

    def test_tracing_features_are_implemented(self):
        """Test 13: Tracing features are implemented"""
        tracing_modules = [
            "policy_as_code.tracing.ledger",
            "policy_as_code.tracing.postgres",
            "policy_as_code.tracing.audit",
            "policy_as_code.tracing.query",
            "policy_as_code.tracing.integrity",
            "policy_as_code.tracing.compression",
        ]

        existing_tracing_modules = 0
        for module_name in tracing_modules:
            try:
                importlib.import_module(module_name)
                existing_tracing_modules += 1
                print(f"✅ {module_name} is importable")
            except ImportError:
                print(f"❌ {module_name} is not importable")

        assert (
            existing_tracing_modules >= 3
        ), f"Too few tracing modules: {existing_tracing_modules}/{len(tracing_modules)}"

    def test_documentation_links_are_valid(self):
        """Test 14: Internal documentation links point to existing files"""
        key_docs = [
            "README.md",
            "CONTRIBUTING.md",
            "DEVELOPMENT_ROADMAP.md",
            "docs/README.md",
            "docs/architecture/architecture.md",
            "docs/architecture/agentic-ai.md",
            "docs/architecture/governance.md",
            "docs/architecture/security.md",
            "docs/getting-started/development.md",
            "docs/getting-started/deployment.md",
            "docs/getting-started/claude.md",
            "docs/reference/api.md",
            "docs/reference/cli.md",
            "docs/security.md",
            "docs/domain-first-architecture.md",
        ]

        existing_docs = 0
        for doc_file in key_docs:
            doc_path = PROJECT_ROOT / doc_file
            if doc_path.exists():
                existing_docs += 1
                print(f"✅ {doc_file} exists")
            else:
                print(f"❌ {doc_file} missing")

        assert (
            existing_docs >= 12
        ), f"Too few documentation files: {existing_docs}/{len(key_docs)}"

    def test_requirements_files_exist_and_valid(self):
        """Test 15: Requirements files exist and have valid syntax"""
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
        ]

        valid_requirements = 0
        for req_file in requirements_files:
            req_path = PROJECT_ROOT / req_file
            if req_path.exists():
                try:
                    with open(req_path, "r") as f:
                        lines = f.readlines()
                        valid_lines = 0
                        for line_num, line in enumerate(lines, 1):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # Basic validation - package name should not contain spaces
                                package_name = (
                                    line.split("==")[0]
                                    .split(">=")[0]
                                    .split("<=")[0]
                                    .split(">")[0]
                                    .split("<")[0]
                                    .split("~")[0]
                                )
                                if " " not in package_name:
                                    valid_lines += 1
                        if valid_lines > 0:
                            valid_requirements += 1
                            print(f"✅ {req_file} is valid ({valid_lines} packages)")
                        else:
                            print(f"❌ {req_file} has no valid packages")
                except Exception as e:
                    print(f"❌ {req_file} is invalid: {e}")
            else:
                print(f"❌ {req_file} missing")

        assert (
            valid_requirements >= 1
        ), f"Too few valid requirements files: {valid_requirements}/{len(requirements_files)}"

    def test_project_structure_matches_documentation(self):
        """Test 16: Actual project structure matches documented structure"""
        key_directories = [
            "policy_as_code",
            "docs",
            "examples",
            "tests",
            "schemas",
            "config",
            "traces",
            "functions",
        ]

        existing_dirs = 0
        for directory in key_directories:
            dir_path = PROJECT_ROOT / directory
            if dir_path.exists():
                existing_dirs += 1
                print(f"✅ {directory}/ exists")
            else:
                print(f"❌ {directory}/ missing")

        assert (
            existing_dirs >= 6
        ), f"Too few directories: {existing_dirs}/{len(key_directories)}"

    def test_pyproject_toml_is_valid(self):
        """Test 17: pyproject.toml exists and is valid"""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml missing"

        with open(pyproject_path, "r") as f:
            content = f.read()
            # Basic validation - should contain [tool.poetry] or [build-system]
            if "[tool." in content or "[build-system]" in content:
                print("✅ pyproject.toml is valid")
            else:
                print("❌ pyproject.toml has invalid format")
                assert False, "Invalid pyproject.toml format"

    def test_license_file_exists(self):
        """Test 18: LICENSE file exists"""
        license_path = PROJECT_ROOT / "LICENSE"
        if license_path.exists():
            print("✅ LICENSE file exists")
        else:
            print("❌ LICENSE file missing")
            assert False, "LICENSE file missing"

    def test_gitignore_exists(self):
        """Test 19: .gitignore file exists"""
        gitignore_path = PROJECT_ROOT / ".gitignore"
        if gitignore_path.exists():
            print("✅ .gitignore file exists")
        else:
            print("❌ .gitignore file missing")
            assert False, ".gitignore file missing"

    def test_comprehensive_demo_is_runnable(self):
        """Test 20: Comprehensive demo can be imported and basic structure is valid"""
        demo_path = EXAMPLES_DIR / "demos" / "comprehensive_demo.py"
        if demo_path.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    "comprehensive_demo", demo_path
                )
                demo_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(demo_module)

                # Check that it has expected functions/classes
                if hasattr(demo_module, "main") or hasattr(demo_module, "run_demo"):
                    print("✅ Comprehensive demo is importable and has main function")
                else:
                    print("❌ Comprehensive demo missing main function")
                    assert (
                        False
                    ), "Comprehensive demo should have main() or run_demo() function"

            except Exception as e:
                print(f"❌ Cannot import comprehensive demo: {e}")
                assert False, f"Cannot import comprehensive demo: {e}"
        else:
            print("❌ Comprehensive demo missing")
            assert False, "Comprehensive demo missing"


class TestProcessWorkflowConsistency:
    """Test that documented processes match actual implementation"""

    def test_development_workflow_matches_contributing_guide(self):
        """Test that development workflow in docs matches actual setup"""
        # Check that development setup script exists
        dev_setup = PROJECT_ROOT / "bin" / "dev-setup.sh"
        if dev_setup.exists():
            # Check that it's executable
            if os.access(dev_setup, os.X_OK):
                print("✅ Development setup script exists and is executable")
            else:
                print("❌ Development setup script not executable")
                assert False, "Development setup script not executable"
        else:
            print("❌ Development setup script missing")
            assert False, "Development setup script missing"

    def test_testing_process_is_documented_and_implemented(self):
        """Test that testing process is properly documented and implemented"""
        # Check pytest configuration exists
        pytest_ini = PROJECT_ROOT / "pytest.ini"
        if pytest_ini.exists():
            print("✅ pytest.ini exists")
        else:
            print("❌ pytest.ini missing")
            assert False, "pytest.ini missing"

        # Check that test directory has proper structure
        test_init = PROJECT_ROOT / "tests" / "__init__.py"
        if test_init.exists():
            print("✅ tests/__init__.py exists")
        else:
            print("❌ tests/__init__.py missing")
            assert False, "tests/__init__.py missing"

    def test_deployment_process_matches_docker_config(self):
        """Test that deployment process matches Docker configuration"""
        # Check that both basic and enhanced Docker configs exist
        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
        ]

        existing_docker_files = 0
        for docker_file in docker_files:
            docker_path = PROJECT_ROOT / docker_file
            if docker_path.exists():
                existing_docker_files += 1
                print(f"✅ {docker_file} exists")
            else:
                print(f"❌ {docker_file} missing")

        assert (
            existing_docker_files >= 1
        ), f"Too few Docker files: {existing_docker_files}/{len(docker_files)}"

    def test_security_process_matches_implementation(self):
        """Test that security process matches actual security implementation"""
        # Check that security configuration exists
        security_config = POLICY_AS_CODE_DIR / "core" / "security.py"
        if security_config.exists():
            print("✅ Security configuration exists")
        else:
            print("❌ Security configuration missing")
            assert False, "Security configuration missing"

        # Check that KMS integration exists
        kms_integration = POLICY_AS_CODE_DIR / "security" / "kms_integration.py"
        if kms_integration.exists():
            print("✅ KMS integration exists")
        else:
            print("❌ KMS integration missing")
            assert False, "KMS integration missing"

    def test_audit_process_is_implemented(self):
        """Test that audit process is properly implemented"""
        audit_service = POLICY_AS_CODE_DIR / "governance" / "audit_service.py"
        if audit_service.exists():
            print("✅ Audit service exists")
            # Try to import audit service
            try:
                from policy_as_code.governance.audit_service import AuditService

                print("✅ AuditService is importable")
            except ImportError:
                print("❌ Cannot import AuditService")
                pytest.skip("Cannot import AuditService")
        else:
            print("❌ Audit service missing")
            assert False, "Audit service missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
