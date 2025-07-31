import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from decision_layer import DecisionContext, DecisionEngine
from decision_layer.errors import ExecutionError, FunctionNotFoundError


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def engine(temp_data_dir):
    """Create a test engine with temporary storage"""
    config = {
        "storage": {"path": temp_data_dir},
        "plugins": {
            "validation": {"enabled": False},  # Disable for simpler tests
            "tracing": {"enabled": True, "path": f"{temp_data_dir}/traces"},
            "caching": {"enabled": True},
        },
    }
    return DecisionEngine(config=config)


@pytest.fixture
def sample_function():
    """Create a sample decision function"""

    def decision_function(
        input_data: Dict[str, Any], context: DecisionContext
    ) -> Dict[str, Any]:
        amount = input_data.get("amount", 0)
        if amount > 1000:
            return {"approved": False, "reason": "Amount too high"}
        else:
            return {"approved": True, "reason": "Amount within limits"}

    return decision_function


class TestDecisionEngine:
    """Test the core decision engine functionality"""

    @pytest.mark.asyncio
    async def test_engine_creation(self, engine):
        """Test that engine can be created"""
        assert engine is not None
        assert engine.storage is not None
        assert len(engine.plugins["pre_execute"]) >= 0
        assert len(engine.plugins["post_execute"]) >= 0

    @pytest.mark.asyncio
    async def test_deploy_function(self, engine, sample_function):
        """Test deploying a function"""
        function_code = """
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    amount = input_data.get('amount', 0)
    if amount > 1000:
        return {"approved": False, "reason": "Amount too high"}
    else:
        return {"approved": True, "reason": "Amount within limits"}
"""

        await engine.deploy_function("test_policy", "v1.0", function_code)

        # Verify function was deployed
        functions = await engine.list_functions()
        assert "test_policy" in functions

        versions = await engine.list_versions("test_policy")
        assert "v1.0" in versions

    @pytest.mark.asyncio
    async def test_execute_function(self, engine, sample_function):
        """Test executing a function"""
        # Deploy function first
        function_code = """
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    amount = input_data.get('amount', 0)
    if amount > 1000:
        return {"approved": False, "reason": "Amount too high"}
    else:
        return {"approved": True, "reason": "Amount within limits"}
"""
        await engine.deploy_function("test_policy", "v1.0", function_code)

        # Test with low amount
        result = await engine.execute("test_policy", {"amount": 500})
        assert result["approved"] is True
        assert "within limits" in result["reason"]

        # Test with high amount
        result = await engine.execute("test_policy", {"amount": 1500})
        assert result["approved"] is False
        assert "too high" in result["reason"]

    @pytest.mark.asyncio
    async def test_version_management(self, engine):
        """Test version management"""
        # Deploy multiple versions
        v1_code = """
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    return {"version": "v1.0", "result": "old"}
"""

        v2_code = """
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    return {"version": "v2.0", "result": "new"}
"""

        await engine.deploy_function("test_policy", "v1.0", v1_code)
        await engine.deploy_function("test_policy", "v2.0", v2_code)

        # List versions
        versions = await engine.list_versions("test_policy")
        assert "v1.0" in versions
        assert "v2.0" in versions
        assert len(versions) == 2

        # Test specific version execution
        result = await engine.execute("test_policy", {}, version="v1.0")
        assert result["version"] == "v1.0"

        result = await engine.execute("test_policy", {}, version="v2.0")
        assert result["version"] == "v2.0"

        # Test latest version (should be v2.0)
        result = await engine.execute("test_policy", {})
        assert result["version"] == "v2.0"

    @pytest.mark.asyncio
    async def test_error_handling(self, engine):
        """Test error handling"""
        # Deploy function with error
        error_code = """
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    raise ValueError("Test error")
"""

        await engine.deploy_function("error_policy", "v1.0", error_code)

        # Test that error is properly handled
        with pytest.raises(ExecutionError) as exc_info:
            await engine.execute("error_policy", {})

        assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_function_not_found(self, engine):
        """Test handling of non-existent functions"""
        with pytest.raises(FunctionNotFoundError) as exc_info:
            await engine.execute("non_existent", {})

        assert "not found" in str(exc_info.value)


class TestPlugins:
    """Test plugin functionality"""

    @pytest.mark.asyncio
    async def test_tracing_plugin(self, temp_data_dir):
        """Test that tracing plugin works"""
        config = {
            "storage": {"path": temp_data_dir},
            "plugins": {
                "tracing": {"enabled": True, "path": f"{temp_data_dir}/traces"}
            },
        }
        engine = DecisionEngine(config=config)

        # Deploy and execute function
        function_code = """
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    return {"result": "success"}
"""

        await engine.deploy_function("test_policy", "v1.0", function_code)
        await engine.execute("test_policy", {"test": "data"})

        # Check that trace file was created
        trace_dir = Path(f"{temp_data_dir}/traces")
        assert trace_dir.exists()

        trace_files = list(trace_dir.glob("*.jsonl"))
        assert len(trace_files) > 0

    @pytest.mark.asyncio
    async def test_caching_plugin(self, temp_data_dir):
        """Test that caching plugin works"""
        config = {
            "storage": {"path": temp_data_dir},
            "plugins": {"caching": {"enabled": True}},
        }
        engine = DecisionEngine(config=config)

        # Deploy function
        function_code = """
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    return {"result": "success", "timestamp": "now"}
"""

        await engine.deploy_function("test_policy", "v1.0", function_code)

        # Execute twice with same input
        result1 = await engine.execute("test_policy", {"test": "data"})
        result2 = await engine.execute("test_policy", {"test": "data"})

        # Results should be identical (cached)
        assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__])
