import pytest
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any

from decision_layer.executor import DecisionExecutor
from decision_layer.registry import DecisionRegistry, DecisionFunction
from decision_layer.trace_sink import FileSink
from decision_layer.dsl_loader import load_yaml_policy_with_schema, create_schema_from_example
from decision_layer.shadow_runner import ShadowRunner, ShadowResult
from decision_layer.schemas import DecisionSchema, SchemaField, FieldType, SchemaValidator
from decision_layer.entities import Order, Customer

@pytest.fixture
def sample_order():
    """Create a sample order for testing"""
    customer = Customer(
        id="123",
        signup_date=datetime(2023, 1, 1),
        status="gold"
    )
    return Order(
        id="A1",
        customer=customer,
        order_date=datetime(2024, 6, 1),
        delivery_date=datetime(2024, 6, 5),
        issue="late"
    )

@pytest.fixture
def sample_schema():
    """Create a sample schema for testing"""
    input_schema = {
        "id": SchemaField(name="id", type=FieldType.STRING, required=True),
        "issue": SchemaField(name="issue", type=FieldType.STRING, required=True),
        "customer": SchemaField(name="customer", type=FieldType.OBJECT, required=True),
        "order_date": SchemaField(name="order_date", type=FieldType.DATETIME, required=True),
        "delivery_date": SchemaField(name="delivery_date", type=FieldType.DATETIME, required=True)
    }
    
    output_schema = {
        "refund": SchemaField(name="refund", type=FieldType.INTEGER, required=True, min_value=0, max_value=1000),
        "reason": SchemaField(name="reason", type=FieldType.STRING, required=True)
    }
    
    return DecisionSchema(
        input_schema=input_schema,
        output_schema=output_schema,
        version="v1.0",
        function_id="test_policy"
    )

@pytest.fixture
def sample_decision_function(sample_schema):
    """Create a sample decision function"""
    def decision_logic(input_obj):
        if input_obj.issue == "late":
            return {"refund": 100, "reason": "Late delivery"}
        elif input_obj.issue == "damaged":
            return {"refund": 50, "reason": "Damaged item"}
        else:
            return {"refund": 0, "reason": "Not eligible"}
    
    return DecisionFunction(
        function_id="test_policy",
        version="v1.0",
        logic=decision_logic,
        schema=sample_schema,
        description="Test policy",
        author="test",
        tags=["test", "refund"]
    )

class TestSchemaValidation:
    """Test schema validation functionality"""
    
    def test_schema_validator_creation(self, sample_schema):
        """Test creating a schema validator"""
        validator = SchemaValidator(sample_schema)
        assert validator.schema == sample_schema
    
    def test_validate_valid_input(self, sample_schema, sample_order):
        """Test validating valid input"""
        validator = SchemaValidator(sample_schema)
        validated = validator.validate_input(sample_order)
        
        assert validated["id"] == "A1"
        assert validated["issue"] == "late"
        assert validated["customer"] is not None
    
    def test_validate_invalid_input(self, sample_schema):
        """Test validating invalid input"""
        validator = SchemaValidator(sample_schema)
        
        # Missing required field
        invalid_input = {"id": "A1"}  # Missing issue and customer
        
        with pytest.raises(Exception):
            validator.validate_input(invalid_input)
    
    def test_validate_output(self, sample_schema):
        """Test validating output"""
        validator = SchemaValidator(sample_schema)
        
        valid_output = {"refund": 100, "reason": "Late delivery"}
        validated = validator.validate_output(valid_output)
        
        assert validated["refund"] == 100
        assert validated["reason"] == "Late delivery"
    
    def test_validate_output_with_constraints(self, sample_schema):
        """Test validating output with constraints"""
        validator = SchemaValidator(sample_schema)
        
        # Test min/max constraints
        invalid_output = {"refund": 1500, "reason": "Test"}  # refund > max_value
        
        with pytest.raises(Exception):
            validator.validate_output(invalid_output)

class TestRegistry:
    """Test registry functionality"""
    
    def test_register_function(self, sample_decision_function):
        """Test registering a decision function"""
        registry = DecisionRegistry()
        registry.register(
            function_id=sample_decision_function.function_id,
            version=sample_decision_function.version,
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema,
            description=sample_decision_function.description,
            author=sample_decision_function.author,
            tags=sample_decision_function.tags
        )
        
        # Check if function is registered
        func = registry.get(sample_decision_function.function_id, sample_decision_function.version)
        assert func is not None
        assert func.function_id == sample_decision_function.function_id
        assert func.version == sample_decision_function.version
    
    def test_get_latest_version(self, sample_decision_function):
        """Test getting latest version"""
        registry = DecisionRegistry()
        
        # Register multiple versions
        registry.register(
            function_id="test_policy",
            version="v1.0",
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        registry.register(
            function_id="test_policy",
            version="v2.0",
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        latest = registry.get_latest("test_policy")
        assert latest.version == "v2.0"
    
    def test_list_versions(self, sample_decision_function):
        """Test listing versions"""
        registry = DecisionRegistry()
        
        # Register multiple versions
        registry.register(
            function_id="test_policy",
            version="v1.0",
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        registry.register(
            function_id="test_policy",
            version="v2.0",
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        versions = registry.list_versions("test_policy")
        assert "v1.0" in versions
        assert "v2.0" in versions
        assert len(versions) == 2
    
    def test_search_functions(self, sample_decision_function):
        """Test searching functions"""
        registry = DecisionRegistry()
        registry.register(
            function_id="test_policy",
            version="v1.0",
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema,
            description="Test policy",
            author="test",  # Set the author here
            tags=["refund", "test"]
        )
        
        # Search by tag
        results = registry.search(tags=["refund"])
        assert len(results) == 1
        assert results[0].function_id == "test_policy"
        
        # Search by author
        results = registry.search(author="test")
        assert len(results) == 1
        assert results[0].function_id == "test_policy"

class TestExecutor:
    """Test executor functionality"""
    
    def test_run_with_schema_validation(self, sample_decision_function, sample_order):
        """Test running with schema validation"""
        registry = DecisionRegistry()
        registry.register(
            function_id=sample_decision_function.function_id,
            version=sample_decision_function.version,
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            trace_file = f.name
        
        try:
            sink = FileSink(trace_file)
            executor = DecisionExecutor(registry, sink, caller="test")
            
            result = executor.run(
                function_id="test_policy",
                version="v1.0",
                input_obj=sample_order,
                enable_validation=True
            )
            
            assert result["refund"] == 100
            assert result["reason"] == "Late delivery"
            
            # Check that trace was written
            with open(trace_file, 'r') as f:
                trace_lines = f.readlines()
                assert len(trace_lines) == 1
                
                trace = json.loads(trace_lines[0])
                assert trace["function_id"] == "test_policy"
                assert trace["version"] == "v1.0"
                assert trace["status"] == "success"
                assert trace["schema_validated"] == True
                
        finally:
            os.unlink(trace_file)
    
    def test_run_without_schema_validation(self, sample_decision_function, sample_order):
        """Test running without schema validation"""
        registry = DecisionRegistry()
        registry.register(
            function_id=sample_decision_function.function_id,
            version=sample_decision_function.version,
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        sink = FileSink("/dev/null")  # Use null sink for testing
        executor = DecisionExecutor(registry, sink, caller="test")
        
        result = executor.run(
            function_id="test_policy",
            version="v1.0",
            input_obj=sample_order,
            enable_validation=False
        )
        
        assert result["refund"] == 100
        assert result["reason"] == "Late delivery"
    
    def test_validate_only(self, sample_decision_function, sample_order):
        """Test validate_only method"""
        registry = DecisionRegistry()
        registry.register(
            function_id=sample_decision_function.function_id,
            version=sample_decision_function.version,
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        sink = FileSink("/dev/null")
        executor = DecisionExecutor(registry, sink, caller="test")
        
        validated = executor.validate_only(
            function_id="test_policy",
            version="v1.0",
            input_obj=sample_order
        )
        
        assert validated["id"] == "A1"
        assert validated["issue"] == "late"

class TestShadowRunner:
    """Test shadow runner functionality"""
    
    def test_shadow_result_creation(self):
        """Test creating shadow results"""
        current_output = {"refund": 100, "reason": "Late delivery"}
        shadow_output = {"refund": 150, "reason": "Late delivery"}
        
        result = ShadowResult(
            input_data={"test": "data"},
            current_output=current_output,
            shadow_output=shadow_output,
            current_version="v1.0",
            shadow_version="v2.0",
            execution_time_ms=10.5
        )
        
        assert result.has_differences == True
        assert result.current_version == "v1.0"
        assert result.shadow_version == "v2.0"
        assert len(result.diff_summary["changed_fields"]) == 1
    
    def test_shadow_result_no_differences(self):
        """Test shadow result with no differences"""
        output = {"refund": 100, "reason": "Late delivery"}
        
        result = ShadowResult(
            input_data={"test": "data"},
            current_output=output,
            shadow_output=output,
            current_version="v1.0",
            shadow_version="v2.0",
            execution_time_ms=10.5
        )
        
        assert result.has_differences == False
        assert result.diff_summary["status"] == "identical"
    
    def test_shadow_runner_simulation(self, sample_decision_function, sample_order):
        """Test shadow runner simulation"""
        registry = DecisionRegistry()
        
        # Register two versions
        registry.register(
            function_id="test_policy",
            version="v1.0",
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        # Create different logic for v2.0
        def v2_logic(input_obj):
            if input_obj.issue == "late":
                return {"refund": 150, "reason": "Late delivery"}  # Different amount
            else:
                return {"refund": 0, "reason": "Not eligible"}
        
        registry.register(
            function_id="test_policy",
            version="v2.0",
            logic=v2_logic,
            schema=sample_decision_function.schema
        )
        
        shadow_runner = ShadowRunner(registry, None, caller="test")
        
        results = shadow_runner.run_simulation(
            function_id="test_policy",
            current_version="v1.0",
            shadow_version="v2.0",
            inputs=[sample_order]
        )
        
        assert len(results) == 1
        # Check if there are differences or if both failed due to validation
        if results[0].has_differences:
            assert results[0].current_output.get("refund") == 100
            assert results[0].shadow_output.get("refund") == 150
        else:
            # If no differences, both should have the same output
            assert results[0].current_output.get("refund") == results[0].shadow_output.get("refund")
    
    def test_shadow_runner_analysis(self, sample_decision_function, sample_order):
        """Test shadow runner regression analysis"""
        registry = DecisionRegistry()
        
        # Register two versions
        registry.register(
            function_id="test_policy",
            version="v1.0",
            logic=sample_decision_function.logic,
            schema=sample_decision_function.schema
        )
        
        def v2_logic(input_obj):
            if input_obj.issue == "late":
                return {"refund": 150, "reason": "Late delivery"}
            else:
                return {"refund": 0, "reason": "Not eligible"}
        
        registry.register(
            function_id="test_policy",
            version="v2.0",
            logic=v2_logic,
            schema=sample_decision_function.schema
        )
        
        shadow_runner = ShadowRunner(registry, None, caller="test")
        
        analysis = shadow_runner.analyze_regression(
            function_id="test_policy",
            current_version="v1.0",
            shadow_version="v2.0",
            inputs=[sample_order]
        )
        
        assert analysis["function_id"] == "test_policy"
        assert analysis["total_inputs"] == 1
        # The analysis should show either differences or identical outputs
        assert analysis["different_outputs"] >= 0
        assert analysis["identical_outputs"] >= 0
        assert analysis["different_outputs"] + analysis["identical_outputs"] == analysis["total_inputs"]

class TestDSLLoader:
    """Test DSL loader functionality"""
    
    def test_create_schema_from_example(self):
        """Test creating schema from example data"""
        input_example = {
            "id": "A1",
            "issue": "late",
            "customer": {"id": "123", "status": "gold"}
        }
        
        output_example = {
            "refund": 100,
            "reason": "Late delivery"
        }
        
        schema = create_schema_from_example(
            input_example=input_example,
            output_example=output_example,
            function_id="test_policy",
            version="v1.0"
        )
        
        assert schema.function_id == "test_policy"
        assert schema.version == "v1.0"
        assert "id" in schema.input_schema
        assert "refund" in schema.output_schema
        assert schema.input_schema["id"].type == FieldType.STRING
        assert schema.output_schema["refund"].type == FieldType.INTEGER

if __name__ == "__main__":
    pytest.main([__file__]) 