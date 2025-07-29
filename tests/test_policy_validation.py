import pytest
import tempfile
import yaml
from decision_layer.dsl_loader import load_yaml_policy
from dataclasses import dataclass

@dataclass 
class PolicyTestObject:
    status: str = "active"
    count: int = 5
    flag: bool = True

def test_load_valid_policy(tmp_path):
    """Test loading a valid YAML policy"""
    policy_file = tmp_path / "valid_policy.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: active_rule
    if: { field: "status", operator: "==", value: "active" }
    then: { action: "approve" }
default:
  action: "deny"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    
    # Test function works
    obj = PolicyTestObject()
    result = policy_fn(obj)
    assert result["action"] == "approve"
    assert result["rule_id"] == "active_rule"

def test_load_policy_missing_file():
    """Test loading policy from non-existent file"""
    with pytest.raises(FileNotFoundError):
        load_yaml_policy("nonexistent_policy.yaml")

def test_load_policy_invalid_yaml(tmp_path):
    """Test loading policy with invalid YAML syntax"""
    policy_file = tmp_path / "invalid.yaml"
    with open(policy_file, 'w') as f:
        f.write("invalid: yaml: content: [unclosed")
    
    with pytest.raises(yaml.YAMLError):
        load_yaml_policy(str(policy_file))

def test_load_policy_missing_rules_key(tmp_path):
    """Test loading policy missing required 'rules' key"""
    policy_file = tmp_path / "no_rules.yaml"
    policy_content = """
function: test_policy
version: v1.0
default:
  action: "deny"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    with pytest.raises(KeyError):
        load_yaml_policy(str(policy_file))

def test_load_policy_missing_default_key(tmp_path):
    """Test loading policy missing required 'default' key"""
    policy_file = tmp_path / "no_default.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: test_rule
    if: { field: "status", operator: "==", value: "active" }
    then: { action: "approve" }
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    with pytest.raises(KeyError):
        load_yaml_policy(str(policy_file))

def test_policy_with_empty_rules(tmp_path):
    """Test policy with empty rules list"""
    policy_file = tmp_path / "empty_rules.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules: []
default:
  action: "deny"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    obj = PolicyTestObject()
    result = policy_fn(obj)
    
    # Should fall back to default
    assert result["action"] == "deny"

def test_policy_with_multiple_matching_rules(tmp_path):
    """Test that first matching rule wins when multiple rules match"""
    policy_file = tmp_path / "multiple_match.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: first
    if: { field: "status", operator: "==", value: "active" }
    then: { action: "first_action", priority: 1 }
  - id: second
    if: { field: "status", operator: "==", value: "active" }
    then: { action: "second_action", priority: 2 }
default:
  action: "deny"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    obj = PolicyTestObject(status="active")
    result = policy_fn(obj)
    
    # Should match first rule
    assert result["action"] == "first_action"
    assert result["priority"] == 1
    assert result["rule_id"] == "first"

def test_policy_with_non_string_values(tmp_path):
    """Test policy with integer and boolean values"""
    policy_file = tmp_path / "non_string.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: count_rule
    if: { field: "count", operator: "==", value: 5 }
    then: { action: "count_match" }
  - id: flag_rule
    if: { field: "flag", operator: "==", value: true }
    then: { action: "flag_match" }
default:
  action: "no_match"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    
    # Test integer matching
    obj1 = PolicyTestObject(count=5, flag=False)
    result1 = policy_fn(obj1)
    assert result1["action"] == "count_match"
    assert result1["rule_id"] == "count_rule"
    
    # Test boolean matching
    obj2 = PolicyTestObject(count=10, flag=True)
    result2 = policy_fn(obj2)
    assert result2["action"] == "flag_match"
    assert result2["rule_id"] == "flag_rule"

def test_policy_field_resolution_error(tmp_path):
    """Test policy with field that doesn't exist on object"""
    policy_file = tmp_path / "bad_field.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: bad_rule
    if: { field: "nonexistent_field", operator: "==", value: "test" }
    then: { action: "should_not_reach" }
default:
  action: "default"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    obj = PolicyTestObject()
    
    # Should raise ValueError when trying to access nonexistent field
    with pytest.raises(ValueError, match="Field 'nonexistent_field' not found"):
        policy_fn(obj)

def test_policy_with_complex_then_values(tmp_path):
    """Test policy with complex 'then' values including nested objects"""
    policy_file = tmp_path / "complex_then.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: complex_rule
    if: { field: "status", operator: "==", value: "active" }
    then: 
      action: "approve"
      metadata:
        reason: "status_check"
        confidence: 0.95
      tags: ["automated", "approved"]
default:
  action: "deny"
  metadata:
    reason: "default"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    obj = PolicyTestObject(status="active")
    result = policy_fn(obj)
    
    assert result["action"] == "approve"
    assert result["rule_id"] == "complex_rule"
    assert result["metadata"]["reason"] == "status_check"
    assert result["metadata"]["confidence"] == 0.95
    assert result["tags"] == ["automated", "approved"]