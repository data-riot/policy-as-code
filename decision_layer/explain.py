"""
Citizen-facing Explanation API
Human-readable justification with legal references and decision paths
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .errors import DecisionLayerError
from .legal_refs import LawReference
from .release import Release, ReleaseManager
from .trace_ledger import TraceRecord, TraceLedger


@dataclass
class DecisionExplanation:
    """Human-readable decision explanation"""

    trace_id: str
    function_id: str
    version: str
    timestamp: datetime
    decision: str
    legal_basis: List[LawReference]
    decision_path: List[str]
    input_summary: Dict[str, Any]
    output_summary: Dict[str, Any]
    confidence_score: Optional[float] = None
    redacted_fields: List[str] = None

    def __post_init__(self):
        if self.redacted_fields is None:
            self.redacted_fields = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "trace_id": self.trace_id,
            "function_id": self.function_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "decision": self.decision,
            "legal_basis": [ref.to_dict() for ref in self.legal_basis],
            "decision_path": self.decision_path,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "confidence_score": self.confidence_score,
            "redacted_fields": self.redacted_fields,
        }


class ExplanationError(DecisionLayerError):
    """Explanation generation errors"""

    def __init__(self, error_type: str, message: str):
        super().__init__(f"Explanation error ({error_type}): {message}")
        self.error_type = error_type


class ExplanationRenderer:
    """Renders human-readable explanations"""

    def __init__(self, release_manager: ReleaseManager, trace_ledger: TraceLedger):
        self.release_manager = release_manager
        self.trace_ledger = trace_ledger

    async def explain_decision(
        self, trace_id: str, redact_sensitive: bool = True
    ) -> DecisionExplanation:
        """Generate explanation for a decision trace"""
        # Get trace record
        trace_record = await self.trace_ledger.get_trace(trace_id)
        if not trace_record:
            raise ExplanationError("trace_not_found", f"Trace {trace_id} not found")

        # Get release information
        release = self.release_manager.get_release(
            trace_record.df_id, trace_record.version
        )
        if not release:
            raise ExplanationError(
                "release_not_found",
                f"Release for {trace_record.df_id} v{trace_record.version} not found",
            )

        # Generate explanation
        explanation = await self._generate_explanation(
            trace_record, release, redact_sensitive
        )
        return explanation

    async def _generate_explanation(
        self, trace_record: TraceRecord, release: Release, redact_sensitive: bool
    ) -> DecisionExplanation:
        """Generate detailed explanation"""

        # Determine decision outcome
        decision = self._determine_decision_outcome(trace_record)

        # Extract legal basis
        legal_basis = release.legal_references

        # Generate decision path
        decision_path = self._generate_decision_path(trace_record)

        # Summarize input/output
        input_summary = self._summarize_input(trace_record.input_json, redact_sensitive)
        output_summary = self._summarize_output(
            trace_record.output_json, redact_sensitive
        )

        # Determine redacted fields
        redacted_fields = self._get_redacted_fields(
            trace_record.input_json, redact_sensitive
        )

        # Calculate confidence score (simplified)
        confidence_score = self._calculate_confidence_score(trace_record)

        return DecisionExplanation(
            trace_id=trace_record.trace_id,
            function_id=trace_record.df_id,
            version=trace_record.version,
            timestamp=trace_record.timestamp,
            decision=decision,
            legal_basis=legal_basis,
            decision_path=decision_path,
            input_summary=input_summary,
            output_summary=output_summary,
            confidence_score=confidence_score,
            redacted_fields=redacted_fields,
        )

    def _determine_decision_outcome(self, trace_record: TraceRecord) -> str:
        """Determine the decision outcome from trace"""
        if trace_record.status == "error":
            return f"Decision failed: {trace_record.output_json.get('error', 'Unknown error')}"

        # Analyze output to determine decision
        output = trace_record.output_json

        # Common decision patterns
        if "approved" in output:
            return f"Decision: {'Approved' if output['approved'] else 'Rejected'}"
        elif "decision" in output:
            return f"Decision: {output['decision']}"
        elif "result" in output:
            return f"Result: {output['result']}"
        else:
            return "Decision completed successfully"

    def _generate_decision_path(self, trace_record: TraceRecord) -> List[str]:
        """Generate human-readable decision path"""
        path = []

        # Add function information
        path.append(
            f"Applied decision function: {trace_record.df_id} v{trace_record.version}"
        )

        # Add input analysis
        input_data = trace_record.input_json
        if "amount" in input_data:
            path.append(f"Analyzed amount: {input_data['amount']}")
        if "customer_score" in input_data:
            path.append(f"Evaluated customer score: {input_data['customer_score']}")
        if "risk_level" in input_data:
            path.append(f"Assessed risk level: {input_data['risk_level']}")

        # Add processing steps
        path.append("Applied business rules and compliance checks")
        path.append("Generated decision based on legal requirements")

        return path

    def _summarize_input(
        self, input_data: Dict[str, Any], redact_sensitive: bool
    ) -> Dict[str, Any]:
        """Summarize input data for explanation"""
        summary = {}

        # Define sensitive fields that should be redacted
        sensitive_fields = {"ssn", "personal_id", "email", "phone", "address", "name"}

        for key, value in input_data.items():
            if redact_sensitive and key.lower() in sensitive_fields:
                summary[key] = "[REDACTED]"
            elif isinstance(value, (str, int, float, bool)):
                summary[key] = value
            elif isinstance(value, dict):
                summary[key] = f"Object with {len(value)} fields"
            elif isinstance(value, list):
                summary[key] = f"List with {len(value)} items"
            else:
                summary[key] = str(type(value).__name__)

        return summary

    def _summarize_output(
        self, output_data: Dict[str, Any], redact_sensitive: bool
    ) -> Dict[str, Any]:
        """Summarize output data for explanation"""
        summary = {}

        for key, value in output_data.items():
            if redact_sensitive and key.lower() in {
                "internal_notes",
                "debug_info",
                "trace",
            }:
                summary[key] = "[REDACTED]"
            elif isinstance(value, (str, int, float, bool)):
                summary[key] = value
            elif isinstance(value, dict):
                summary[key] = f"Object with {len(value)} fields"
            elif isinstance(value, list):
                summary[key] = f"List with {len(value)} items"
            else:
                summary[key] = str(type(value).__name__)

        return summary

    def _get_redacted_fields(
        self, input_data: Dict[str, Any], redact_sensitive: bool
    ) -> List[str]:
        """Get list of redacted fields"""
        if not redact_sensitive:
            return []

        sensitive_fields = {"ssn", "personal_id", "email", "phone", "address", "name"}
        redacted = []

        for key in input_data.keys():
            if key.lower() in sensitive_fields:
                redacted.append(key)

        return redacted

    def _calculate_confidence_score(self, trace_record: TraceRecord) -> Optional[float]:
        """Calculate confidence score for the decision"""
        if trace_record.status == "error":
            return 0.0

        # Simplified confidence calculation
        # In production, this would be more sophisticated
        output = trace_record.output_json

        if "confidence" in output:
            return float(output["confidence"])
        elif "score" in output:
            return float(output["score"]) / 100.0
        else:
            # Default confidence based on successful execution
            return 0.95


class ExplanationAPI:
    """API for citizen-facing explanations"""

    def __init__(self, renderer: ExplanationRenderer):
        self.renderer = renderer

    async def get_explanation(
        self, trace_id: str, redact_sensitive: bool = True
    ) -> DecisionExplanation:
        """Get explanation for a decision trace"""
        return await self.renderer.explain_decision(trace_id, redact_sensitive)

    async def get_explanations_for_function(
        self,
        function_id: str,
        version: Optional[str] = None,
        limit: int = 10,
        redact_sensitive: bool = True,
    ) -> List[DecisionExplanation]:
        """Get explanations for multiple traces of a function"""
        traces = await self.renderer.trace_ledger.get_traces_by_function(
            function_id, version, limit
        )

        explanations = []
        for trace in traces:
            try:
                explanation = await self.renderer.explain_decision(
                    trace.trace_id, redact_sensitive
                )
                explanations.append(explanation)
            except ExplanationError:
                # Skip traces that can't be explained
                continue

        return explanations

    async def get_explanations_by_timeframe(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
        redact_sensitive: bool = True,
    ) -> List[DecisionExplanation]:
        """Get explanations for traces within a time range"""
        traces = await self.renderer.trace_ledger.get_traces_by_timeframe(
            start_time, end_time, limit
        )

        explanations = []
        for trace in traces:
            try:
                explanation = await self.renderer.explain_decision(
                    trace.trace_id, redact_sensitive
                )
                explanations.append(explanation)
            except ExplanationError:
                # Skip traces that can't be explained
                continue

        return explanations


def create_explanation_api(
    release_manager: ReleaseManager, trace_ledger: TraceLedger
) -> ExplanationAPI:
    """Create an explanation API instance"""
    renderer = ExplanationRenderer(release_manager, trace_ledger)
    return ExplanationAPI(renderer)
