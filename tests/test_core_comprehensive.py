"""
Comprehensive test suite for policy as code core components
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

from policy_as_code.core.engine import DecisionEngine, DecisionContext, DecisionResult
from policy_as_code.core.registry import FunctionRegistry
from policy_as_code.core.storage import StorageBackend
from policy_as_code.core.errors import DecisionLayerError, ValidationError


class TestDecisionContext:
    """Test DecisionContext functionality"""

    def test_decision_context_creation(self):
        """Test creating a decision context"""
        context = DecisionContext(
            function_id="test_function",
            version="1.0.0",
            input_hash="abc123",
            timestamp=datetime.utcnow(),
            trace_id="trace_123",
        )

        assert context.function_id == "test_function"
        assert context.version == "1.0.0"
        assert context.input_hash == "abc123"
        assert context.trace_id == "trace_123"

    def test_decision_context_immutability(self):
        """Test that DecisionContext is immutable"""
        context = DecisionContext(
            function_id="test_function",
            version="1.0.0",
            input_hash="abc123",
            timestamp=datetime.utcnow(),
            trace_id="trace_123",
        )

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            context.function_id = "new_function"


class TestDecisionResult:
    """Test DecisionResult functionality"""

    def test_decision_result_creation(self):
        """Test creating a decision result"""
        result = DecisionResult(
            decision="approved",
            confidence=0.95,
            reasoning="All criteria met",
            metadata={"processing_time": "100ms"},
        )

        assert result.decision == "approved"
        assert result.confidence == 0.95
        assert result.reasoning == "All criteria met"
        assert result.metadata["processing_time"] == "100ms"

    def test_decision_result_validation(self):
        """Test decision result validation"""
        # Valid result
        result = DecisionResult(
            decision="approved",
            confidence=0.95,
            reasoning="Valid reasoning",
            metadata={},
        )
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

        # Invalid confidence
        with pytest.raises(ValueError):
            DecisionResult(
                decision="approved",
                confidence=1.5,  # Invalid confidence
                reasoning="Test",
                metadata={},
            )


class TestDecisionEngine:
    """Test DecisionEngine functionality"""

    @pytest.fixture
    def engine(self):
        """Create a test decision engine"""
        return DecisionEngine()

    @pytest.fixture
    def mock_function(self):
        """Create a mock decision function"""

        async def test_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> DecisionResult:
            return DecisionResult(
                decision="approved",
                confidence=0.9,
                reasoning="Test decision",
                metadata={},
            )

        return test_function

    @pytest.mark.asyncio
    async def test_execute_decision_function(self, engine, mock_function):
        """Test executing a decision function"""
        # Register function
        await engine.register_function("test_func", "1.0.0", mock_function)

        # Execute function
        result = await engine.execute(
            function_id="test_func", input_data={"amount": 1000}, version="1.0.0"
        )

        assert result.decision == "approved"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_execute_nonexistent_function(self, engine):
        """Test executing a non-existent function"""
        with pytest.raises(DecisionLayerError):
            await engine.execute(
                function_id="nonexistent", input_data={}, version="1.0.0"
            )

    @pytest.mark.asyncio
    async def test_execute_with_validation_error(self, engine):
        """Test execution with validation error"""

        async def error_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> DecisionResult:
            raise ValidationError("Invalid input data")

        await engine.register_function("error_func", "1.0.0", error_function)

        with pytest.raises(ValidationError):
            await engine.execute(
                function_id="error_func", input_data={}, version="1.0.0"
            )


class TestFunctionRegistry:
    """Test FunctionRegistry functionality"""

    @pytest.fixture
    def registry(self):
        """Create a test function registry"""
        return FunctionRegistry()

    @pytest.mark.asyncio
    async def test_register_function(self, registry):
        """Test registering a function"""

        async def test_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> DecisionResult:
            return DecisionResult(
                decision="approved", confidence=0.9, reasoning="Test", metadata={}
            )

        result = await registry.register_function(
            function_id="test_func",
            version="1.0.0",
            function_code=test_function,
            metadata={"author": "test_user"},
        )

        assert result.function_id == "test_func"
        assert result.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_function(self, registry):
        """Test getting a registered function"""

        async def test_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> DecisionResult:
            return DecisionResult(
                decision="approved", confidence=0.9, reasoning="Test", metadata={}
            )

        await registry.register_function(
            function_id="test_func", version="1.0.0", function_code=test_function
        )

        function = await registry.get_function("test_func", "1.0.0")
        assert function is not None

    @pytest.mark.asyncio
    async def test_list_functions(self, registry):
        """Test listing registered functions"""

        async def test_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> DecisionResult:
            return DecisionResult(
                decision="approved", confidence=0.9, reasoning="Test", metadata={}
            )

        await registry.register_function(
            function_id="test_func", version="1.0.0", function_code=test_function
        )

        functions = await registry.list_functions()
        assert len(functions) == 1
        assert functions[0].function_id == "test_func"


class TestStorageBackend:
    """Test StorageBackend functionality"""

    @pytest.fixture
    def storage(self):
        """Create a test storage backend"""
        return StorageBackend()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, storage):
        """Test storing and retrieving data"""
        test_data = {"key": "value", "number": 42}

        await storage.store("test_key", test_data)
        retrieved_data = await storage.retrieve("test_key")

        assert retrieved_data == test_data

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_key(self, storage):
        """Test retrieving non-existent key"""
        result = await storage.retrieve("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, storage):
        """Test deleting a key"""
        test_data = {"key": "value"}

        await storage.store("test_key", test_data)
        await storage.delete("test_key")

        result = await storage.retrieve("test_key")
        assert result is None


class TestErrorHandling:
    """Test error handling functionality"""

    def test_policy_as_code_error(self):
        """Test DecisionLayerError creation"""
        error = DecisionLayerError("Test error message")
        assert str(error) == "Test error message"

    def test_validation_error(self):
        """Test ValidationError creation"""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, DecisionLayerError)


class TestIntegrationScenarios:
    """Test integration scenarios"""

    @pytest.fixture
    def engine_with_registry(self):
        """Create engine with registry"""
        engine = DecisionEngine()
        return engine

    @pytest.mark.asyncio
    async def test_complete_workflow(self, engine_with_registry):
        """Test complete decision workflow"""

        # Define a loan approval function
        async def loan_approval(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> DecisionResult:
            amount = input_data.get("amount", 0)
            credit_score = input_data.get("credit_score", 0)

            if amount <= 10000 and credit_score >= 700:
                return DecisionResult(
                    decision="approved",
                    confidence=0.95,
                    reasoning="Loan approved based on credit score and amount",
                    metadata={"criteria_met": True},
                )
            else:
                return DecisionResult(
                    decision="rejected",
                    confidence=0.9,
                    reasoning="Loan rejected due to insufficient credit score or high amount",
                    metadata={"criteria_met": False},
                )

        # Register function
        await engine_with_registry.register_function(
            function_id="loan_approval", version="1.0.0", function_code=loan_approval
        )

        # Test approved case
        result = await engine_with_registry.execute(
            function_id="loan_approval",
            input_data={"amount": 5000, "credit_score": 750},
            version="1.0.0",
        )

        assert result.decision == "approved"
        assert result.confidence == 0.95

        # Test rejected case
        result = await engine_with_registry.execute(
            function_id="loan_approval",
            input_data={"amount": 15000, "credit_score": 650},
            version="1.0.0",
        )

        assert result.decision == "rejected"
        assert result.confidence == 0.9
