import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open
from decision_layer.cli import parse_order, main
from decision_layer.entities import Customer, Order
from datetime import datetime

def test_parse_order():
    """Test parsing order from JSON data"""
    data = {
        "id": "A1",
        "customer": {
            "id": "123",
            "signup_date": "2023-01-01T00:00:00",
            "status": "gold"
        },
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "issue": "late"
    }
    
    order = parse_order(data)
    
    assert isinstance(order, Order)
    assert order.id == "A1"
    assert order.issue == "late"
    assert isinstance(order.customer, Customer)
    assert order.customer.id == "123"
    assert order.customer.status == "gold"
    assert order.customer.signup_date == datetime(2023, 1, 1)
    assert order.order_date == datetime(2024, 6, 1)
    assert order.delivery_date == datetime(2024, 6, 5)

@patch('decision_layer.cli.load_yaml_policy')
@patch('decision_layer.cli.DecisionRegistry')
@patch('decision_layer.cli.FileSink')
@patch('decision_layer.cli.DecisionExecutor')
@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
@patch('json.dumps')
def test_main_success(mock_dumps, mock_json_load, mock_open, mock_executor, mock_sink, mock_registry, mock_load_policy):
    """Test successful CLI execution"""
    # Setup mocks
    mock_policy_fn = lambda x: {"result": "success"}
    mock_load_policy.return_value = mock_policy_fn
    
    mock_registry_instance = mock_registry.return_value
    mock_sink_instance = mock_sink.return_value
    mock_executor_instance = mock_executor.return_value
    mock_executor_instance.run.return_value = {"refund": 100, "reason": "Late delivery"}
    
    mock_json_load.return_value = {
        "id": "A1",
        "customer": {
            "id": "123",
            "signup_date": "2023-01-01T00:00:00",
            "status": "gold"
        },
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "issue": "late"
    }
    
    mock_dumps.return_value = '{"refund": 100, "reason": "Late delivery"}'
    
    # Test with trace file
    with patch('sys.argv', ['cli.py', '--policy', 'test.yaml', '--input', 'test.json', '--trace', 'trace.jsonl']):
        main()
    
    # Verify calls
    mock_load_policy.assert_called_once_with('test.yaml')
    mock_registry_instance.register.assert_called_once_with("refund_policy", "v3.2", mock_policy_fn)
    mock_sink.assert_called_once_with('trace.jsonl')
    mock_executor_instance.run.assert_called_once()
    mock_dumps.assert_called_once()

@patch('decision_layer.cli.load_yaml_policy')
@patch('decision_layer.cli.DecisionRegistry')
@patch('decision_layer.cli.FileSink')
@patch('decision_layer.cli.DecisionExecutor')
@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
@patch('json.dumps')
def test_main_without_trace(mock_dumps, mock_json_load, mock_open, mock_executor, mock_sink, mock_registry, mock_load_policy):
    """Test CLI execution without trace file"""
    # Setup mocks
    mock_policy_fn = lambda x: {"result": "success"}
    mock_load_policy.return_value = mock_policy_fn
    
    mock_registry_instance = mock_registry.return_value
    mock_executor_instance = mock_executor.return_value
    mock_executor_instance.run.return_value = {"refund": 50, "reason": "Damaged item"}
    
    mock_json_load.return_value = {
        "id": "A1",
        "customer": {
            "id": "123",
            "signup_date": "2023-01-01T00:00:00",
            "status": "gold"
        },
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "issue": "damaged"
    }
    
    mock_dumps.return_value = '{"refund": 50, "reason": "Damaged item"}'
    
    # Test without trace file
    with patch('sys.argv', ['cli.py', '--policy', 'test.yaml', '--input', 'test.json']):
        main()
    
    # Verify calls
    mock_load_policy.assert_called_once_with('test.yaml')
    mock_registry_instance.register.assert_called_once_with("refund_policy", "v3.2", mock_policy_fn)
    mock_sink.assert_not_called()  # Should not be called when no trace file
    mock_executor_instance.run.assert_called_once()
    mock_dumps.assert_called_once()

@patch('decision_layer.cli.load_yaml_policy')
@patch('decision_layer.cli.DecisionRegistry')
@patch('decision_layer.cli.FileSink')
@patch('decision_layer.cli.DecisionExecutor')
@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
@patch('json.dumps')
def test_main_custom_version(mock_dumps, mock_json_load, mock_open, mock_executor, mock_sink, mock_registry, mock_load_policy):
    """Test CLI execution with custom version"""
    # Setup mocks
    mock_policy_fn = lambda x: {"result": "success"}
    mock_load_policy.return_value = mock_policy_fn
    
    mock_registry_instance = mock_registry.return_value
    mock_executor_instance = mock_executor.return_value
    mock_executor_instance.run.return_value = {"refund": 0, "reason": "Not eligible"}
    
    mock_json_load.return_value = {
        "id": "A1",
        "customer": {
            "id": "123",
            "signup_date": "2023-01-01T00:00:00",
            "status": "gold"
        },
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "issue": "none"
    }
    
    mock_dumps.return_value = '{"refund": 0, "reason": "Not eligible"}'
    
    # Test with custom version
    with patch('sys.argv', ['cli.py', '--policy', 'test.yaml', '--input', 'test.json', '--version', 'v2.0']):
        main()
    
    # Verify calls
    mock_load_policy.assert_called_once_with('test.yaml')
    mock_registry_instance.register.assert_called_once_with("refund_policy", "v2.0", mock_policy_fn)
    mock_executor_instance.run.assert_called_once()
    assert mock_executor_instance.run.call_args[0][0] == "refund_policy"
    assert mock_executor_instance.run.call_args[0][1] == "v2.0"
    mock_dumps.assert_called_once()

def test_cli_integration():
    """Integration test for CLI with actual files"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_file:
        json.dump({
            "id": "A1",
            "customer": {
                "id": "123",
                "signup_date": "2023-01-01T00:00:00",
                "status": "gold"
            },
            "order_date": "2024-06-01T00:00:00",
            "delivery_date": "2024-06-05T00:00:00",
            "issue": "late"
        }, input_file)
        input_path = input_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as trace_file:
        trace_path = trace_file.name
    
    try:
        # Run CLI
        with patch('sys.argv', ['cli.py', '--policy', 'policies/refund_policy.yaml', '--input', input_path, '--trace', trace_path]):
            main()
        
        # Check trace file was created
        assert os.path.exists(trace_path)
        with open(trace_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            trace = json.loads(lines[0])
            assert trace["decision_id"] == "refund_policy"
            assert trace["version"] == "v3.2"
            assert trace["caller"] == "cli"
            assert trace["status"] == "success"
            assert trace["output"]["refund"] == 100
            assert trace["output"]["reason"] == "Late delivery"
    
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(trace_path):
            os.unlink(trace_path) 