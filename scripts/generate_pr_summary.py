#!/usr/bin/env python3
"""
Pull Request Summary Generator

This script analyzes a pull request and generates a comprehensive summary
including changes, affected files, and impact analysis for the Policy as Code repository.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import yaml


class PRSummaryGenerator:
    """Generates comprehensive pull request summaries."""

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        pr_number: int,
        base_branch: str,
        head_branch: str,
        config_file: str = None,
    ):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.pr_number = pr_number
        self.base_branch = base_branch
        self.head_branch = head_branch

        # Load configuration
        self.config = self.load_config(config_file)
        self.categories = self.config.get("categories", {})
        self.impact_thresholds = self.config.get("impact_thresholds", {})
        self.testing_recommendations = self.config.get("testing_recommendations", {})
        self.policy_considerations = self.config.get("policy_considerations", {})
        self.summary_template = self.config.get("summary_template", {})

    def load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__), "pr_summary_config.yaml"
            )

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(
                f"Warning: Config file {config_file} not found, using defaults",
                file=sys.stderr,
            )
            return self.get_default_config()
        except yaml.YAMLError as e:
            print(
                f"Warning: Error parsing config file: {e}, using defaults",
                file=sys.stderr,
            )
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "categories": {
                "decision_functions": {
                    "patterns": [r"policy_as_code/.*\.py$", r"examples/.*\.py$"],
                    "description": "Decision Functions & Logic",
                    "icon": "⚖️",
                },
                "governance": {
                    "patterns": [
                        r"policy_as_code/(trace_ledger|legal_refs|release|audit_service)\.py$"
                    ],
                    "description": "Governance & Compliance",
                    "icon": "🔒",
                },
                "agentic_ai": {
                    "patterns": [
                        r"policy_as_code/(llm_integration|conversational_interface|workflow_orchestration|agent_performance_monitor)\.py$"
                    ],
                    "description": "Agentic AI Features",
                    "icon": "🤖",
                },
                "api": {
                    "patterns": [r"policy_as_code/(api|agentic_api)\.py$"],
                    "description": "API Endpoints",
                    "icon": "🌐",
                },
                "security": {
                    "patterns": [
                        r"policy_as_code/(security|auth|caller_auth|kms_integration|replay_protection)\.py$"
                    ],
                    "description": "Security & Authentication",
                    "icon": "🛡️",
                },
                "testing": {
                    "patterns": [r"tests/.*", r"policy_as_code/testing_slos\.py$"],
                    "description": "Testing & Quality Assurance",
                    "icon": "🧪",
                },
                "documentation": {
                    "patterns": [r"docs/.*\.md$", r"README\.md$", r"claude\.md$"],
                    "description": "Documentation",
                    "icon": "📚",
                },
                "configuration": {
                    "patterns": [
                        r"config\.yaml$",
                        r"docker-compose\.yml$",
                        r"Dockerfile$",
                        r"Makefile$",
                        r"pyproject\.toml$",
                    ],
                    "description": "Configuration & Deployment",
                    "icon": "⚙️",
                },
                "examples": {
                    "patterns": [r"examples/.*"],
                    "description": "Examples & Demos",
                    "icon": "💡",
                },
            },
            "impact_thresholds": {
                "large_change_lines": 500,
                "complex_change_lines": 100,
                "high_priority_categories": [
                    "governance",
                    "security",
                    "agentic_ai",
                    "api",
                ],
            },
            "testing_recommendations": {},
            "policy_considerations": {},
            "summary_template": {
                "max_commits_display": 10,
                "max_complex_changes_display": 5,
            },
        }

    def get_git_diff(self) -> str:
        """Get the git diff between base and head branches."""
        try:
            result = subprocess.run(
                ["git", "diff", f"{self.base_branch}...{self.head_branch}", "--stat"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error getting git diff: {e}", file=sys.stderr)
            return ""

    def get_commit_messages(self) -> List[str]:
        """Get commit messages between base and head branches."""
        try:
            result = subprocess.run(
                ["git", "log", f"{self.base_branch}..{self.head_branch}", "--oneline"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except subprocess.CalledProcessError as e:
            print(f"Error getting commit messages: {e}", file=sys.stderr)
            return []

    def get_changed_files(self) -> List[str]:
        """Get list of changed files."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    f"{self.base_branch}...{self.head_branch}",
                    "--name-only",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except subprocess.CalledProcessError as e:
            print(f"Error getting changed files: {e}", file=sys.stderr)
            return []

    def categorize_files(self, files: List[str]) -> Dict[str, List[str]]:
        """Categorize files based on Policy as Code patterns."""
        categorized = {category: [] for category in self.categories.keys()}
        categorized["other"] = []

        for file_path in files:
            categorized_flag = False
            for category, config in self.categories.items():
                for pattern in config["patterns"]:
                    if re.match(pattern, file_path):
                        categorized[category].append(file_path)
                        categorized_flag = True
                        break
                if categorized_flag:
                    break

            if not categorized_flag:
                categorized["other"].append(file_path)

        return categorized

    def analyze_code_changes(self, files: List[str]) -> Dict[str, Any]:
        """Analyze code changes for impact assessment."""
        analysis = {
            "lines_added": 0,
            "lines_removed": 0,
            "files_modified": len(files),
            "new_files": 0,
            "deleted_files": 0,
            "complexity_changes": [],
        }

        try:
            # Get detailed diff stats
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    f"{self.base_branch}...{self.head_branch}",
                    "--numstat",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        added = parts[0] if parts[0] != "-" else "0"
                        removed = parts[1] if parts[1] != "-" else "0"
                        filename = parts[2]

                        if added == "0" and removed == "0":
                            analysis["new_files"] += 1
                        elif filename in files:
                            analysis["lines_added"] += int(added)
                            analysis["lines_removed"] += int(removed)

                            # Check for complexity indicators
                            if int(added) > 100 or int(removed) > 100:
                                analysis["complexity_changes"].append(
                                    {
                                        "file": filename,
                                        "added": int(added),
                                        "removed": int(removed),
                                        "type": "large_change",
                                    }
                                )

        except subprocess.CalledProcessError as e:
            print(f"Error analyzing code changes: {e}", file=sys.stderr)

        return analysis

    def generate_impact_assessment(
        self, categorized_files: Dict[str, List[str]], analysis: Dict[str, Any]
    ) -> str:
        """Generate impact assessment based on changes."""
        impact_levels = []

        # Get thresholds from config
        large_change_threshold = self.impact_thresholds.get("large_change_lines", 500)
        high_priority_categories = self.impact_thresholds.get(
            "high_priority_categories", []
        )

        # Check for high-impact changes
        for category in high_priority_categories:
            if categorized_files.get(category):
                config = self.categories.get(category, {})
                icon = config.get("icon", "⚠️")
                description = config.get("description", category.title())
                impact_levels.append(
                    f"{icon} **{description} Impact**: Changes to {description.lower()}"
                )

        if (
            analysis["lines_added"] > large_change_threshold
            or analysis["lines_removed"] > large_change_threshold
        ):
            impact_levels.append("📊 **Large Change**: Significant code modifications")

        if analysis["complexity_changes"]:
            impact_levels.append(
                "⚠️ **Complex Changes**: Files with substantial modifications"
            )

        if not impact_levels:
            impact_levels.append("✅ **Low Impact**: Minor changes with minimal risk")

        return "\n".join(impact_levels)

    def generate_testing_recommendations(
        self, categorized_files: Dict[str, List[str]]
    ) -> str:
        """Generate testing recommendations based on changes."""
        recommendations = []

        # Use configuration-based recommendations
        for category, files in categorized_files.items():
            if files and category in self.testing_recommendations:
                category_recommendations = self.testing_recommendations[category]
                for rec in category_recommendations:
                    recommendations.append(f"- **{category.title()}**: {rec}")

        # Fallback to default recommendations if no config-based ones
        if not recommendations:
            if categorized_files.get("decision_functions"):
                recommendations.append(
                    "- **Decision Function Tests**: Ensure 100% branch coverage for new/modified decision functions"
                )

            if categorized_files.get("governance"):
                recommendations.append(
                    "- **Governance Tests**: Verify trace ledger integrity and legal reference validation"
                )

            if categorized_files.get("security"):
                recommendations.append(
                    "- **Security Tests**: Run security scans and authentication flow tests"
                )

            if categorized_files.get("agentic_ai"):
                recommendations.append(
                    "- **AI Tests**: Test LLM integration and agentic workflow functionality"
                )

            if categorized_files.get("api"):
                recommendations.append(
                    "- **API Tests**: Verify endpoint functionality and schema validation"
                )

            if categorized_files.get("testing"):
                recommendations.append(
                    "- **Test Infrastructure**: Validate testing framework and SLO requirements"
                )

            if not recommendations:
                recommendations.append(
                    "- **General Testing**: Run full test suite to ensure no regressions"
                )

        return "\n".join(recommendations)

    def generate_summary(self) -> str:
        """Generate comprehensive PR summary."""
        changed_files = self.get_changed_files()
        categorized_files = self.categorize_files(changed_files)
        analysis = self.analyze_code_changes(changed_files)
        commit_messages = self.get_commit_messages()

        # Generate summary sections
        summary_parts = [
            f"# 📋 Pull Request Summary #{self.pr_number}",
            "",
            f"**Branch**: `{self.head_branch}` → `{self.base_branch}`",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## 📊 Change Overview",
            "",
            f"- **Files Modified**: {analysis['files_modified']}",
            f"- **Lines Added**: {analysis['lines_added']:,}",
            f"- **Lines Removed**: {analysis['lines_removed']:,}",
            f"- **New Files**: {analysis['new_files']}",
            "",
        ]

        # Add categorized changes
        summary_parts.extend(["## 📁 Changes by Category", ""])

        # Sort categories by priority if available
        sorted_categories = sorted(
            categorized_files.items(),
            key=lambda x: self.categories.get(x[0], {}).get("priority", 999),
        )

        for category, files in sorted_categories:
            if files:
                config = self.categories.get(
                    category, {"description": category.title()}
                )
                icon = config.get("icon", "📁")
                description = config.get("description", category.title())
                summary_parts.extend([f"### {icon} {description}", ""])

                for file_path in files:
                    summary_parts.append(f"- `{file_path}`")

                summary_parts.append("")

        # Add impact assessment
        summary_parts.extend(
            [
                "## 🎯 Impact Assessment",
                "",
                self.generate_impact_assessment(categorized_files, analysis),
                "",
            ]
        )

        # Add commit messages
        if commit_messages:
            max_commits = self.summary_template.get("max_commits_display", 10)
            summary_parts.extend(["## 📝 Commit Messages", ""])

            for commit in commit_messages[:max_commits]:
                summary_parts.append(f"- {commit}")

            if len(commit_messages) > max_commits:
                summary_parts.append(
                    f"- ... and {len(commit_messages) - max_commits} more commits"
                )

            summary_parts.append("")

        # Add testing recommendations
        summary_parts.extend(
            [
                "## 🧪 Testing Recommendations",
                "",
                self.generate_testing_recommendations(categorized_files),
                "",
            ]
        )

        # Add complexity changes
        if analysis["complexity_changes"]:
            max_complex = self.summary_template.get("max_complex_changes_display", 5)
            summary_parts.extend(
                [
                    "## ⚠️ Complex Changes",
                    "",
                    "The following files have substantial modifications:",
                    "",
                ]
            )

            for change in analysis["complexity_changes"][:max_complex]:
                summary_parts.append(
                    f"- `{change['file']}`: +{change['added']} -{change['removed']} lines"
                )

            if len(analysis["complexity_changes"]) > max_complex:
                summary_parts.append(
                    f"- ... and {len(analysis['complexity_changes']) - max_complex} more complex changes"
                )

            summary_parts.append("")

        # Add Policy as Code specific notes
        summary_parts.extend(["## 🔍 Policy as Code Considerations", ""])

        # Use configuration-based policy considerations
        policy_notes = []
        for category, files in categorized_files.items():
            if files and category in self.policy_considerations:
                category_considerations = self.policy_considerations[category]
                for consideration in category_considerations:
                    policy_notes.append(f"- {consideration}")

        # Fallback to default considerations
        if not policy_notes:
            policy_notes = [
                "- **Governance**: Ensure all decision functions maintain legal compliance and audit trails",
                "- **Security**: Verify authentication and authorization changes don't introduce vulnerabilities",
                "- **Testing**: Maintain 100% branch coverage and SLO requirements",
                "- **Documentation**: Update relevant documentation for any API or configuration changes",
            ]

        summary_parts.extend(policy_notes)
        summary_parts.append("")

        return "\n".join(summary_parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate PR summary for Policy as Code repository"
    )
    parser.add_argument(
        "--pr-number", type=int, required=True, help="Pull request number"
    )
    parser.add_argument("--repo-owner", required=True, help="Repository owner")
    parser.add_argument("--repo-name", required=True, help="Repository name")
    parser.add_argument("--base-branch", required=True, help="Base branch")
    parser.add_argument("--head-branch", required=True, help="Head branch")
    parser.add_argument("--config-file", help="Configuration file path")
    parser.add_argument("--output", default="pr_summary.md", help="Output file path")

    args = parser.parse_args()

    generator = PRSummaryGenerator(
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        pr_number=args.pr_number,
        base_branch=args.base_branch,
        head_branch=args.head_branch,
        config_file=args.config_file,
    )

    summary = generator.generate_summary()

    # Write summary to file
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"PR summary generated: {args.output}")
    print(f"Summary length: {len(summary)} characters")


if __name__ == "__main__":
    main()
