import pytest
import json
import subprocess
import tempfile
import os
from pathlib import Path

def test_cli_basic_functionality():
    """Test basic CLI functionality with valid inputs"""
    result = subprocess.run([
        "python3", "-m", "decision_layer.cli",
        "--policy", "policies/refund_policy.yaml",
        "--input", "tests/data/sample_order.json"
    ], capture_output=True, text=True, cwd="/workspace")
    
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["refund"] == 100
    assert output["reason"] == "Late delivery"
    assert output["rule_id"] == "late"

def test_cli_with_trace_output(tmp_path):
    """Test CLI functionality with trace output"""
    trace_file = tmp_path / "test_trace.jsonl"
    
    result = subprocess.run([
        "python3", "-m", "decision_layer.cli",
        "--policy", "policies/refund_policy.yaml",
        "--input", "tests/data/sample_order.json",
        "--trace", str(trace_file)
    ], capture_output=True, text=True, cwd="/workspace")
    
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["refund"] == 100
    
    # Verify trace file was created
    assert trace_file.exists()
    with open(trace_file) as f:
        trace_data = json.loads(f.read().strip())
        assert trace_data["output"]["refund"] == 100
        assert trace_data["version"] == "v3.2"
        assert trace_data["caller"] == "cli"

def test_cli_with_custom_version(tmp_path):
    """Test CLI functionality with custom version"""
    result = subprocess.run([
        "python3", "-m", "decision_layer.cli",
        "--policy", "policies/refund_policy.yaml",
        "--input", "tests/data/sample_order.json",
        "--version", "custom-v1"
    ], capture_output=True, text=True, cwd="/workspace")
    
    assert result.returncode == 0

def test_cli_missing_policy_file():
    """Test CLI with missing policy file"""
    result = subprocess.run([
        "python3", "-m", "decision_layer.cli",
        "--policy", "nonexistent.yaml",
        "--input", "tests/data/sample_order.json"
    ], capture_output=True, text=True, cwd="/workspace")
    
    assert result.returncode != 0
    assert "No such file or directory" in result.stderr or "FileNotFoundError" in result.stderr

def test_cli_missing_input_file():
    """Test CLI with missing input file"""
    result = subprocess.run([
        "python3", "-m", "decision_layer.cli",
        "--policy", "policies/refund_policy.yaml",
        "--input", "nonexistent.json"
    ], capture_output=True, text=True, cwd="/workspace")
    
    assert result.returncode != 0
    assert "No such file or directory" in result.stderr or "FileNotFoundError" in result.stderr

def test_cli_help():
    """Test CLI help functionality"""
    result = subprocess.run([
        "python3", "-m", "decision_layer.cli",
        "--help"
    ], capture_output=True, text=True, cwd="/workspace")
    
    assert result.returncode == 0
    assert "Run a decision policy" in result.stdout
    assert "--policy" in result.stdout
    assert "--input" in result.stdout

def test_cli_with_different_order_data(tmp_path):
    """Test CLI with different order data (damaged case)"""
    # Create a test input file for damaged order
    damaged_order = {
        "id": "B1",
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "issue": "damaged",
        "customer": {
            "id": "456",
            "signup_date": "2023-01-01T00:00:00",
            "status": "silver"
        }
    }
    
    input_file = tmp_path / "damaged_order.json"
    with open(input_file, 'w') as f:
        json.dump(damaged_order, f)
    
    result = subprocess.run([
        "python3", "-m", "decision_layer.cli",
        "--policy", "policies/refund_policy.yaml",
        "--input", str(input_file)
    ], capture_output=True, text=True, cwd="/workspace")
    
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["refund"] == 50
    assert output["reason"] == "Damaged item"
    assert output["rule_id"] == "damaged"