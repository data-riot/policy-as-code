"""
Shadow Runner for Decision Layer

Provides safe testing capabilities for decision functions by running
new versions against historical or live inputs without affecting production.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

from .core import DecisionEngine
from .errors import ShadowExecutionError
from .registry import FunctionRegistry


def generate_input_hash(input_data: Any) -> str:
    """Generate hash of input data"""
    json_str = json.dumps(input_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


class ShadowResult:
    """Result of a shadow execution"""

    def __init__(
        self,
        input_data: Any,
        current_output: Dict[str, Any],
        shadow_output: Dict[str, Any],
        current_version: str,
        shadow_version: str,
        execution_time_ms: float,
    ):
        self.input_data = input_data
        self.current_output = current_output
        self.shadow_output = shadow_output
        self.current_version = current_version
        self.shadow_version = shadow_version
        self.execution_time_ms = execution_time_ms
        self.timestamp = datetime.utcnow()

        # Calculate differences
        self.has_differences = self._calculate_differences()
        self.diff_summary = self._generate_diff_summary()

    def _calculate_differences(self) -> bool:
        """Check if outputs are different"""
        return self.current_output != self.shadow_output

    def _generate_diff_summary(self) -> Dict[str, Any]:
        """Generate a summary of differences between outputs"""
        if not self.has_differences:
            return {"status": "identical"}

        diff_summary = {
            "status": "different",
            "changed_fields": [],
            "added_fields": [],
            "removed_fields": [],
        }

        current_keys = set(self.current_output.keys())
        shadow_keys = set(self.shadow_output.keys())

        # Find added and removed fields
        added = shadow_keys - current_keys
        removed = current_keys - shadow_keys
        common = current_keys & shadow_keys

        if added:
            diff_summary["added_fields"] = list(added)
        if removed:
            diff_summary["removed_fields"] = list(removed)

        # Find changed values
        for key in common:
            if self.current_output[key] != self.shadow_output[key]:
                diff_summary["changed_fields"].append(
                    {
                        "field": key,
                        "current_value": self.current_output[key],
                        "shadow_value": self.shadow_output[key],
                    }
                )

        return diff_summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "input_hash": generate_input_hash(self.input_data),
            "current_output": self.current_output,
            "shadow_output": self.shadow_output,
            "current_version": self.current_version,
            "shadow_version": self.shadow_version,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "has_differences": self.has_differences,
            "diff_summary": self.diff_summary,
        }


class ShadowRunner:
    """
    Shadow runner for testing decision logic against historical or live inputs
    without affecting production decisions.
    """

    def __init__(
        self, registry: FunctionRegistry, trace_sink=None, caller: str = "shadow-runner"
    ):
        self.registry = registry
        self.trace_sink = trace_sink
        self.caller = caller
        self.engine = DecisionEngine()

    async def run_simulation(
        self,
        function_id: str,
        current_version: str,
        shadow_version: str,
        inputs: List[Any],
    ) -> List[ShadowResult]:
        """
        Run simulation mode: test new version against historical inputs

        Args:
            function_id: Function to test
            current_version: Current production version
            shadow_version: New version to test
            inputs: List of historical input data

        Returns:
            List of ShadowResult objects with comparison data
        """
        results = []

        for input_data in inputs:
            try:
                # Execute current version
                current_start = datetime.utcnow()
                current_result = await self.engine.execute(
                    function_id, input_data, current_version
                )
                current_time = (
                    datetime.utcnow() - current_start
                ).total_seconds() * 1000

                # Execute shadow version
                shadow_start = datetime.utcnow()
                shadow_result = await self.engine.execute(
                    function_id, input_data, shadow_version
                )
                shadow_time = (datetime.utcnow() - shadow_start).total_seconds() * 1000

                # Create shadow result
                result = ShadowResult(
                    input_data=input_data,
                    current_output=current_result,
                    shadow_output=shadow_result,
                    current_version=current_version,
                    shadow_version=shadow_version,
                    execution_time_ms=max(current_time, shadow_time),
                )

                results.append(result)

                # Log to trace sink if available
                if self.trace_sink:
                    await self._log_shadow_result(result)

            except Exception as e:
                # Create error result
                error_result = ShadowResult(
                    input_data=input_data,
                    current_output={"error": str(e)},
                    shadow_output={"error": str(e)},
                    current_version=current_version,
                    shadow_version=shadow_version,
                    execution_time_ms=0,
                )
                results.append(error_result)

        return results

    async def run_mirror(
        self,
        function_id: str,
        current_version: str,
        shadow_version: str,
        input_data: Any,
    ) -> ShadowResult:
        """
        Run mirror mode: test new version against live input

        Args:
            function_id: Function to test
            current_version: Current production version
            shadow_version: New version to test
            input_data: Live input data

        Returns:
            ShadowResult with comparison data
        """
        try:
            # Execute current version (production)
            current_start = datetime.utcnow()
            current_result = await self.engine.execute(
                function_id, input_data, current_version
            )
            current_time = (datetime.utcnow() - current_start).total_seconds() * 1000

            # Execute shadow version (non-production)
            shadow_start = datetime.utcnow()
            shadow_result = await self.engine.execute(
                function_id, input_data, shadow_version
            )
            shadow_time = (datetime.utcnow() - shadow_start).total_seconds() * 1000

            # Create shadow result
            result = ShadowResult(
                input_data=input_data,
                current_output=current_result,
                shadow_output=shadow_result,
                current_version=current_version,
                shadow_version=shadow_version,
                execution_time_ms=max(current_time, shadow_time),
            )

            # Log to trace sink if available
            if self.trace_sink:
                await self._log_shadow_result(result)

            return result

        except Exception as e:
            raise ShadowExecutionError(f"Mirror execution failed: {str(e)}")

    async def analyze_regression(
        self,
        function_id: str,
        current_version: str,
        shadow_version: str,
        inputs: List[Any],
    ) -> Dict[str, Any]:
        """
        Analyze potential regressions between versions

        Args:
            function_id: Function to analyze
            current_version: Current production version
            shadow_version: New version to analyze
            inputs: Test inputs

        Returns:
            Analysis results with regression information
        """
        results = await self.run_simulation(
            function_id, current_version, shadow_version, inputs
        )

        analysis = {
            "function_id": function_id,
            "current_version": current_version,
            "shadow_version": shadow_version,
            "total_tests": len(results),
            "identical_results": 0,
            "different_results": 0,
            "errors": 0,
            "regressions": [],
            "improvements": [],
            "changes": [],
        }

        for result in results:
            if "error" in result.current_output or "error" in result.shadow_output:
                analysis["errors"] += 1
            elif result.has_differences:
                analysis["different_results"] += 1

                # Categorize the difference
                category = self._categorize_difference(result)
                if category == "regression":
                    analysis["regressions"].append(
                        {
                            "input_hash": generate_input_hash(result.input_data),
                            "diff_summary": result.diff_summary,
                        }
                    )
                elif category == "improvement":
                    analysis["improvements"].append(
                        {
                            "input_hash": generate_input_hash(result.input_data),
                            "diff_summary": result.diff_summary,
                        }
                    )
                else:
                    analysis["changes"].append(
                        {
                            "input_hash": generate_input_hash(result.input_data),
                            "diff_summary": result.diff_summary,
                        }
                    )
            else:
                analysis["identical_results"] += 1

        # Calculate confidence scores
        analysis["confidence"] = {
            "identical_ratio": analysis["identical_results"] / analysis["total_tests"],
            "regression_ratio": len(analysis["regressions"]) / analysis["total_tests"],
            "improvement_ratio": len(analysis["improvements"])
            / analysis["total_tests"],
        }

        return analysis

    def _categorize_difference(self, result: ShadowResult) -> str:
        """
        Categorize the type of difference between versions

        Args:
            result: ShadowResult to categorize

        Returns:
            Category: "regression", "improvement", or "change"
        """
        # Simple categorization logic - can be enhanced
        current_output = result.current_output
        shadow_output = result.shadow_output

        # Check for common decision fields
        decision_fields = ["approved", "allowed", "valid", "success", "status"]

        for field in decision_fields:
            if field in current_output and field in shadow_output:
                current_value = current_output[field]
                shadow_value = shadow_output[field]

                # Boolean decision logic
                if isinstance(current_value, bool) and isinstance(shadow_value, bool):
                    if current_value and not shadow_value:
                        return "regression"  # Was approved, now denied
                    elif not current_value and shadow_value:
                        return "improvement"  # Was denied, now approved

                # String status logic
                elif isinstance(current_value, str) and isinstance(shadow_value, str):
                    if current_value.lower() in [
                        "approved",
                        "allowed",
                        "valid",
                        "success",
                    ] and shadow_value.lower() not in [
                        "approved",
                        "allowed",
                        "valid",
                        "success",
                    ]:
                        return "regression"
                    elif current_value.lower() not in [
                        "approved",
                        "allowed",
                        "valid",
                        "success",
                    ] and shadow_value.lower() in [
                        "approved",
                        "allowed",
                        "valid",
                        "success",
                    ]:
                        return "improvement"

        return "change"  # Default to neutral change

    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a human-readable report from analysis results

        Args:
            analysis: Analysis results from analyze_regression

        Returns:
            Formatted report string
        """
        report = f"""
Shadow Testing Report
====================

Function: {analysis['function_id']}
Current Version: {analysis['current_version']}
Shadow Version: {analysis['shadow_version']}

Test Results:
- Total Tests: {analysis['total_tests']}
- Identical Results: {analysis['identical_results']} ({analysis['confidence']['identical_ratio']:.1%})
- Different Results: {analysis['different_results']}
- Errors: {analysis['errors']}

Change Analysis:
- Regressions: {len(analysis['regressions'])} ({analysis['confidence']['regression_ratio']:.1%})
- Improvements: {len(analysis['improvements'])} ({analysis['confidence']['improvement_ratio']:.1%})
- Neutral Changes: {len(analysis['changes'])}

Recommendation: {'SAFE TO DEPLOY' if analysis['confidence']['regression_ratio'] < 0.05 else 'REVIEW REQUIRED'}
"""
        return report

    async def _log_shadow_result(self, result: ShadowResult):
        """Log shadow result to trace sink"""
        if self.trace_sink:
            try:
                log_entry = {
                    "type": "shadow_result",
                    "timestamp": result.timestamp.isoformat(),
                    "caller": self.caller,
                    "result": result.to_dict(),
                }
                await self.trace_sink.log(log_entry)
            except Exception as e:
                # Don't fail shadow execution due to logging errors
                print(f"Warning: Failed to log shadow result: {e}")
