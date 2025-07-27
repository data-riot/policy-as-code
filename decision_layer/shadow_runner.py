from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
import hashlib

from .executor import DecisionExecutor, generate_input_hash, generate_output_hash
from .registry import DecisionRegistry

class ShadowResult:
    """Result of a shadow execution"""
    
    def __init__(self, 
                 input_data: Any,
                 current_output: Dict[str, Any],
                 shadow_output: Dict[str, Any],
                 current_version: str,
                 shadow_version: str,
                 execution_time_ms: float):
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
            "removed_fields": []
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
                diff_summary["changed_fields"].append({
                    "field": key,
                    "current_value": self.current_output[key],
                    "shadow_value": self.shadow_output[key]
                })
        
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
            "diff_summary": self.diff_summary
        }

class ShadowRunner:
    """
    Shadow runner for testing decision logic against historical or live inputs
    without affecting production decisions.
    """
    
    def __init__(self, 
                 registry: DecisionRegistry,
                 trace_sink=None,
                 caller: str = "shadow-runner"):
        self.registry = registry
        self.trace_sink = trace_sink
        self.caller = caller
        self.executor = DecisionExecutor(registry, trace_sink, caller)
    
    def run_simulation(self, 
                      function_id: str,
                      current_version: str,
                      shadow_version: str,
                      inputs: List[Any]) -> List[ShadowResult]:
        """
        Run simulation comparing two versions of a decision function.
        
        Args:
            function_id: The decision function ID
            current_version: Current production version
            shadow_version: Version to test
            inputs: List of input data to test against
            
        Returns:
            List of shadow results showing differences
        """
        results = []
        
        for input_data in inputs:
            try:
                # Run current version
                current_output = self.executor.run(
                    function_id, 
                    current_version, 
                    input_data,
                    enable_validation=True
                )
                
                # Run shadow version
                shadow_output = self.executor.run(
                    function_id, 
                    shadow_version, 
                    input_data,
                    enable_validation=True
                )
                
                # Create shadow result
                result = ShadowResult(
                    input_data=input_data,
                    current_output=current_output,
                    shadow_output=shadow_output,
                    current_version=current_version,
                    shadow_version=shadow_version,
                    execution_time_ms=0  # Will be updated from executor
                )
                
                results.append(result)
                
            except Exception as e:
                # Log error but continue with other inputs
                error_result = ShadowResult(
                    input_data=input_data,
                    current_output={},
                    shadow_output={},
                    current_version=current_version,
                    shadow_version=shadow_version,
                    execution_time_ms=0
                )
                error_result.has_differences = True
                error_result.diff_summary = {
                    "status": "error",
                    "error": str(e)
                }
                results.append(error_result)
        
        return results
    
    def run_mirror(self, 
                   function_id: str,
                   current_version: str,
                   shadow_version: str,
                   input_data: Any) -> ShadowResult:
        """
        Run mirror execution on live traffic.
        This runs both versions in parallel and logs differences.
        """
        try:
            # Run current version (this is the production decision)
            current_output = self.executor.run(
                function_id, 
                current_version, 
                input_data,
                enable_validation=True
            )
            
            # Run shadow version (this is just for comparison)
            shadow_output = self.executor.run(
                function_id, 
                shadow_version, 
                input_data,
                enable_validation=True
            )
            
            # Create shadow result
            result = ShadowResult(
                input_data=input_data,
                current_output=current_output,
                shadow_output=shadow_output,
                current_version=current_version,
                shadow_version=shadow_version,
                execution_time_ms=0
            )
            
            # Log shadow trace if differences found
            if result.has_differences and self.trace_sink:
                shadow_trace = {
                    "type": "shadow_mirror",
                    "function_id": function_id,
                    "current_version": current_version,
                    "shadow_version": shadow_version,
                    "input_hash": generate_input_hash(input_data),
                    "timestamp": datetime.utcnow().isoformat(),
                    "diff_summary": result.diff_summary
                }
                self.trace_sink.emit(shadow_trace)
            
            return result
            
        except Exception as e:
            # Create error result
            result = ShadowResult(
                input_data=input_data,
                current_output={},
                shadow_output={},
                current_version=current_version,
                shadow_version=shadow_version,
                execution_time_ms=0
            )
            result.has_differences = True
            result.diff_summary = {
                "status": "error",
                "error": str(e)
            }
            return result
    
    def analyze_regression(self, 
                          function_id: str,
                          current_version: str,
                          shadow_version: str,
                          inputs: List[Any]) -> Dict[str, Any]:
        """
        Analyze potential regressions by running simulation and categorizing differences.
        """
        results = self.run_simulation(function_id, current_version, shadow_version, inputs)
        
        analysis = {
            "function_id": function_id,
            "current_version": current_version,
            "shadow_version": shadow_version,
            "total_inputs": len(inputs),
            "successful_runs": 0,
            "failed_runs": 0,
            "identical_outputs": 0,
            "different_outputs": 0,
            "regression_categories": {
                "critical": [],
                "warning": [],
                "improvement": []
            },
            "common_differences": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for result in results:
            if result.diff_summary.get("status") == "error":
                analysis["failed_runs"] += 1
                continue
            
            analysis["successful_runs"] += 1
            
            if result.has_differences:
                analysis["different_outputs"] += 1
                
                # Categorize the difference
                category = self._categorize_difference(result)
                analysis["regression_categories"][category].append({
                    "input_hash": generate_input_hash(result.input_data),
                    "diff_summary": result.diff_summary
                })
                
                # Track common differences
                for change in result.diff_summary.get("changed_fields", []):
                    field = change["field"]
                    if field not in analysis["common_differences"]:
                        analysis["common_differences"][field] = 0
                    analysis["common_differences"][field] += 1
            else:
                analysis["identical_outputs"] += 1
        
        return analysis
    
    def _categorize_difference(self, result: ShadowResult) -> str:
        """
        Categorize a difference as critical, warning, or improvement.
        This is a simple heuristic - in practice you'd want more sophisticated logic.
        """
        # This is a placeholder implementation
        # In a real system, you'd have business rules for categorizing changes
        
        # Example: if refund amount changed, it's critical
        if "refund" in result.current_output and "refund" in result.shadow_output:
            current_refund = result.current_output["refund"]
            shadow_refund = result.shadow_output["refund"]
            if abs(current_refund - shadow_refund) > 10:
                return "critical"
        
        # Example: if reason changed but amount didn't, it's a warning
        if "reason" in result.diff_summary.get("changed_fields", []):
            return "warning"
        
        # Default to warning for unknown changes
        return "warning"
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a human-readable report from shadow analysis.
        """
        report = f"""
Shadow Analysis Report
=====================

Function: {analysis['function_id']}
Current Version: {analysis['current_version']}
Shadow Version: {analysis['shadow_version']}
Analysis Time: {analysis['timestamp']}

Summary:
- Total Inputs: {analysis['total_inputs']}
- Successful Runs: {analysis['successful_runs']}
- Failed Runs: {analysis['failed_runs']}
- Identical Outputs: {analysis['identical_outputs']}
- Different Outputs: {analysis['different_outputs']}

Regression Categories:
- Critical: {len(analysis['regression_categories']['critical'])}
- Warning: {len(analysis['regression_categories']['warning'])}
- Improvement: {len(analysis['regression_categories']['improvement'])}

Common Differences:
"""
        
        for field, count in analysis['common_differences'].items():
            report += f"- {field}: {count} changes\n"
        
        if analysis['regression_categories']['critical']:
            report += "\nCritical Changes:\n"
            for change in analysis['regression_categories']['critical'][:5]:  # Show first 5
                report += f"- Input {change['input_hash']}: {change['diff_summary']}\n"
        
        return report 