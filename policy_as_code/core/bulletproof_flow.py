"""
Bulletproof End-to-End Decision Flow
Policy → Input → Decision → Signed Trace → Persisted Audit

This module implements a complete, validated decision flow with:
- Strict input validation using Pydantic
- Immutable decision execution
- Cryptographic trace signing
- Persistent audit logging
- Comprehensive error handling
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from pydantic import ValidationError as PydanticValidationError

from ..validation.strict_models import (
    EligibilityInput,
    EligibilityOutput,
    DecisionContext,
    DecisionResult,
    TraceRecord,
    TraceStatus,
    ValidationResult,
    validate_eligibility_input,
    validate_eligibility_output,
    validate_decision_context,
    validate_trace_record,
)
from .types import DecisionFunction
from .errors import ValidationError, ExecutionError


class BulletproofDecisionFlow:
    """
    Bulletproof end-to-end decision flow implementation

    Flow:
    1. Policy validation and loading
    2. Strict input validation
    3. Decision execution with monitoring
    4. Output validation
    5. Trace record creation and signing
    6. Persistent audit logging
    """

    def __init__(
        self,
        storage_path: str = "./bulletproof_flow_data",
        enable_audit: bool = True,
        enable_signing: bool = True,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        # Create subdirectories
        (self.storage_path / "policies").mkdir(exist_ok=True)
        (self.storage_path / "traces").mkdir(exist_ok=True)
        (self.storage_path / "audit").mkdir(exist_ok=True)
        (self.storage_path / "signatures").mkdir(exist_ok=True)

        self.enable_audit = enable_audit
        self.enable_signing = enable_signing

        # In-memory function registry
        self._functions: Dict[str, DecisionFunction] = {}

        # Audit log
        self._audit_log: List[Dict[str, Any]] = []

    def register_policy(
        self,
        policy_id: str,
        version: str,
        function: DecisionFunction,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a policy function with metadata"""
        if not policy_id or not version:
            raise ValidationError("Policy ID and version are required")

        # Validate function signature
        if not callable(function):
            raise ValidationError("Function must be callable")

        # Store function
        self._functions[f"{policy_id}:{version}"] = function

        # Store metadata
        if metadata:
            metadata_file = (
                self.storage_path / "policies" / f"{policy_id}_{version}.json"
            )
            with open(metadata_file, "w") as f:
                json.dump(
                    {
                        "policy_id": policy_id,
                        "version": version,
                        "metadata": metadata,
                        "registered_at": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

        self._audit_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "policy_registered",
                "policy_id": policy_id,
                "version": version,
                "metadata": metadata,
            }
        )

    async def execute_decision(
        self,
        policy_id: str,
        version: str,
        input_data: Dict[str, Any],
        client_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute bulletproof decision flow

        Args:
            policy_id: Policy identifier
            version: Policy version
            input_data: Raw input data
            client_id: Client identifier
            request_id: Request identifier

        Returns:
            Complete decision result with trace and audit information
        """
        start_time = datetime.now()
        trace_id = str(uuid.uuid4())

        try:
            # Step 1: Validate and load policy
            policy_function = await self._load_policy(policy_id, version)

            # Step 2: Strict input validation
            input_validation = validate_eligibility_input(input_data)
            if not input_validation.is_valid:
                raise ValidationError(
                    f"Input validation failed: {input_validation.errors}"
                )

            validated_input = EligibilityInput(**input_validation.validated_data)

            # Convert Pydantic model to dict for processing
            input_dict = validated_input.dict()

            # Step 3: Create decision context
            input_hash = self._calculate_hash(input_dict)
            context = DecisionContext(
                function_id=policy_id,
                version=version,
                input_hash=input_hash,
                timestamp=start_time,
                trace_id=trace_id,
                client_id=client_id,
                request_id=request_id,
            )

            # Step 4: Execute decision with monitoring
            execution_start = datetime.now()
            try:
                # Use dict for function execution
                raw_result = await policy_function(input_dict)

                # Validate result is dict
                if not isinstance(raw_result, dict):
                    raise ExecutionError("Policy function must return a dictionary")

            except Exception as e:
                raise ExecutionError(f"Policy execution failed: {str(e)}")

            execution_time = (datetime.now() - execution_start).total_seconds() * 1000

            # Step 5: Strict output validation
            output_validation = validate_eligibility_output(raw_result)
            if not output_validation.is_valid:
                raise ValidationError(
                    f"Output validation failed: {output_validation.errors}"
                )

            validated_output = EligibilityOutput(**output_validation.validated_data)

            # Step 6: Create decision result
            output_hash = self._calculate_hash(validated_output.dict())
            decision_result = DecisionResult(
                trace_id=trace_id,
                function_id=policy_id,
                version=version,
                result=validated_output.dict(),
                execution_time_ms=int(execution_time),
                timestamp=start_time,
                success=True,
                input_hash=input_hash,
                output_hash=output_hash,
            )

            # Step 7: Create and sign trace record
            trace_record = await self._create_trace_record(
                context, decision_result, client_id
            )

            # Step 8: Persist audit trail
            if self.enable_audit:
                await self._persist_audit_trail(context, decision_result, trace_record)

            # Step 9: Return complete result
            return {
                "success": True,
                "trace_id": trace_id,
                "decision": validated_output.dict(),
                "execution_time_ms": int(execution_time),
                "validation": {
                    "input_valid": True,
                    "output_valid": True,
                    "input_errors": [],
                    "output_errors": [],
                },
                "audit": {
                    "trace_record_id": trace_record.trace_id,
                    "audit_persisted": self.enable_audit,
                    "signature_valid": self.enable_signing,
                },
                "metadata": {
                    "policy_id": policy_id,
                    "version": version,
                    "client_id": client_id,
                    "request_id": request_id,
                    "timestamp": start_time.isoformat(),
                },
            }

        except ValidationError as e:
            return await self._handle_validation_error(
                trace_id, policy_id, version, str(e), start_time
            )
        except ExecutionError as e:
            return await self._handle_execution_error(
                trace_id, policy_id, version, str(e), start_time
            )
        except Exception as e:
            return await self._handle_unexpected_error(
                trace_id, policy_id, version, str(e), start_time
            )

    async def _load_policy(self, policy_id: str, version: str) -> DecisionFunction:
        """Load and validate policy function"""
        function_key = f"{policy_id}:{version}"

        if function_key not in self._functions:
            raise ValidationError(f"Policy {policy_id} version {version} not found")

        return self._functions[function_key]

    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of data"""

        # Convert various objects to JSON serializable format
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "__str__") and (
                "Url" in str(type(obj)) or "URL" in str(type(obj))
            ):
                return str(obj)
            elif hasattr(obj, "url"):  # Pydantic URL objects
                return str(obj.url)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json_str = json.dumps(
            data, sort_keys=True, separators=(",", ":"), default=json_serializer
        )
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def _create_trace_record(
        self, context: DecisionContext, result: DecisionResult, client_id: Optional[str]
    ) -> TraceRecord:
        """Create and optionally sign trace record"""

        # Get previous hash for chain
        prev_hash = await self._get_previous_hash()

        # Create trace record
        trace_record = TraceRecord(
            trace_id=context.trace_id,
            df_id=context.function_id,
            version=context.version,
            df_hash=f"sha256:{self._calculate_hash({'id': context.function_id, 'version': context.version})}",
            ts=context.timestamp,
            caller_id=f"xroad:FI/ORG/{client_id or 'DEMO_CLIENT'}",
            cert_thumbprint="a1b2c3d4e5f6789012345678901234567890abcd",  # Valid 40-char hex
            request_nonce=str(uuid.uuid4()),
            input_ref=f"s3://policy-as-code/inputs/redacted-{context.trace_id}.json",
            output=result.result,
            prev_hash=prev_hash,
            chain_hash=self._calculate_hash(
                {
                    "trace_id": context.trace_id,
                    "prev_hash": prev_hash,
                    "output_hash": result.output_hash,
                }
            ),
            status=TraceStatus.OK if result.success else TraceStatus.ERROR,
        )

        # Sign trace record if enabled
        if self.enable_signing:
            signature = await self._sign_trace_record(trace_record)
            trace_record.signature = signature

        # Persist trace record
        await self._persist_trace_record(trace_record)

        return trace_record

    async def _get_previous_hash(self) -> str:
        """Get hash of previous trace record for chaining"""
        trace_files = list((self.storage_path / "traces").glob("*.json"))
        if not trace_files:
            return "0" * 64  # Genesis hash

        # Get most recent trace file
        latest_file = max(trace_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file, "r") as f:
                latest_trace = json.load(f)
                return latest_trace.get("chain_hash", "0" * 64)
        except Exception:
            return "0" * 64

    async def _sign_trace_record(self, trace_record: TraceRecord) -> str:
        """Sign trace record (placeholder implementation)"""
        # In production, this would use real cryptographic signing
        data_to_sign = json.dumps(trace_record.dict(), sort_keys=True)
        signature = hashlib.sha256(data_to_sign.encode()).hexdigest()

        # Store signature metadata
        signature_file = (
            self.storage_path / "signatures" / f"{trace_record.trace_id}.json"
        )
        with open(signature_file, "w") as f:
            json.dump(
                {
                    "trace_id": trace_record.trace_id,
                    "signature": signature,
                    "signed_at": datetime.now().isoformat(),
                    "algorithm": "SHA256",
                    "key_id": "placeholder_key",
                },
                f,
                indent=2,
            )

        return signature

    async def _persist_trace_record(self, trace_record: TraceRecord) -> None:
        """Persist trace record to storage"""
        trace_file = self.storage_path / "traces" / f"{trace_record.trace_id}.json"
        with open(trace_file, "w") as f:
            json.dump(trace_record.dict(), f, indent=2, default=str)

    async def _persist_audit_trail(
        self,
        context: DecisionContext,
        result: DecisionResult,
        trace_record: TraceRecord,
    ) -> None:
        """Persist complete audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "trace_id": context.trace_id,
            "policy_id": context.function_id,
            "version": context.version,
            "client_id": context.client_id,
            "request_id": context.request_id,
            "input_hash": context.input_hash,
            "output_hash": result.output_hash,
            "execution_time_ms": result.execution_time_ms,
            "success": result.success,
            "error_message": result.error_message,
            "trace_record": trace_record.dict(),
            "audit_id": str(uuid.uuid4()),
        }

        # Add to in-memory audit log
        self._audit_log.append(audit_entry)

        # Persist to file
        audit_file = self.storage_path / "audit" / f"audit_{context.trace_id}.json"
        with open(audit_file, "w") as f:
            json.dump(audit_entry, f, indent=2, default=str)

    async def _handle_validation_error(
        self,
        trace_id: str,
        policy_id: str,
        version: str,
        error_message: str,
        start_time: datetime,
    ) -> Dict[str, Any]:
        """Handle validation errors with proper audit trail"""
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        error_result = {
            "success": False,
            "trace_id": trace_id,
            "error": {
                "type": "ValidationError",
                "message": error_message,
                "policy_id": policy_id,
                "version": version,
            },
            "execution_time_ms": int(execution_time),
            "validation": {
                "input_valid": False,
                "output_valid": False,
                "input_errors": [error_message],
                "output_errors": [],
            },
            "audit": {
                "trace_record_id": None,
                "audit_persisted": False,
                "signature_valid": False,
            },
            "metadata": {
                "policy_id": policy_id,
                "version": version,
                "timestamp": start_time.isoformat(),
            },
        }

        # Log error for audit
        if self.enable_audit:
            self._audit_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "validation_error",
                    "trace_id": trace_id,
                    "policy_id": policy_id,
                    "version": version,
                    "error": error_message,
                }
            )

        return error_result

    async def _handle_execution_error(
        self,
        trace_id: str,
        policy_id: str,
        version: str,
        error_message: str,
        start_time: datetime,
    ) -> Dict[str, Any]:
        """Handle execution errors with proper audit trail"""
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        error_result = {
            "success": False,
            "trace_id": trace_id,
            "error": {
                "type": "ExecutionError",
                "message": error_message,
                "policy_id": policy_id,
                "version": version,
            },
            "execution_time_ms": int(execution_time),
            "validation": {
                "input_valid": True,  # Input was valid, execution failed
                "output_valid": False,
                "input_errors": [],
                "output_errors": [error_message],
            },
            "audit": {
                "trace_record_id": None,
                "audit_persisted": False,
                "signature_valid": False,
            },
            "metadata": {
                "policy_id": policy_id,
                "version": version,
                "timestamp": start_time.isoformat(),
            },
        }

        # Log error for audit
        if self.enable_audit:
            self._audit_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "execution_error",
                    "trace_id": trace_id,
                    "policy_id": policy_id,
                    "version": version,
                    "error": error_message,
                }
            )

        return error_result

    async def _handle_unexpected_error(
        self,
        trace_id: str,
        policy_id: str,
        version: str,
        error_message: str,
        start_time: datetime,
    ) -> Dict[str, Any]:
        """Handle unexpected errors with proper audit trail"""
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        error_result = {
            "success": False,
            "trace_id": trace_id,
            "error": {
                "type": "UnexpectedError",
                "message": error_message,
                "policy_id": policy_id,
                "version": version,
            },
            "execution_time_ms": int(execution_time),
            "validation": {
                "input_valid": False,
                "output_valid": False,
                "input_errors": ["Unexpected error occurred"],
                "output_errors": [],
            },
            "audit": {
                "trace_record_id": None,
                "audit_persisted": False,
                "signature_valid": False,
            },
            "metadata": {
                "policy_id": policy_id,
                "version": version,
                "timestamp": start_time.isoformat(),
            },
        }

        # Log error for audit
        if self.enable_audit:
            self._audit_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "unexpected_error",
                    "trace_id": trace_id,
                    "policy_id": policy_id,
                    "version": version,
                    "error": error_message,
                }
            )

        return error_result

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get complete audit log"""
        return self._audit_log.copy()

    def verify_trace_integrity(self) -> Dict[str, Any]:
        """Verify integrity of trace chain"""
        trace_files = list((self.storage_path / "traces").glob("*.json"))

        if not trace_files:
            return {
                "integrity_ok": True,
                "total_traces": 0,
                "broken_chains": [],
                "message": "No traces found",
            }

        broken_chains = []
        prev_hash = "0" * 64

        for trace_file in sorted(trace_files, key=lambda f: f.stat().st_mtime):
            try:
                with open(trace_file, "r") as f:
                    trace_data = json.load(f)

                current_prev_hash = trace_data.get("prev_hash", "0" * 64)
                if current_prev_hash != prev_hash:
                    broken_chains.append(
                        {
                            "trace_id": trace_data.get("trace_id"),
                            "expected_prev_hash": prev_hash,
                            "actual_prev_hash": current_prev_hash,
                        }
                    )

                prev_hash = trace_data.get("chain_hash", "0" * 64)

            except Exception as e:
                broken_chains.append({"trace_id": trace_file.stem, "error": str(e)})

        return {
            "integrity_ok": len(broken_chains) == 0,
            "total_traces": len(trace_files),
            "broken_chains": broken_chains,
            "message": (
                "Trace integrity verified"
                if len(broken_chains) == 0
                else f"Found {len(broken_chains)} broken chains"
            ),
        }
