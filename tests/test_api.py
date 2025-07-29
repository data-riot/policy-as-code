import pytest
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from datetime import datetime
from api.fastapi_app import app, load_policies

# Load policies before running tests
load_policies()

client = TestClient(app)

def test_decide_endpoint_success():
    """Test successful decision via API"""
    input_data = {
        "input": {
            "id": "A1",
            "customer": {
                "id": "123",
                "signup_date": "2023-01-01T00:00:00",
                "status": "gold"
            },
            "order_date": "2024-06-01T00:00:00",
            "delivery_date": "2024-06-05T00:00:00",
            "issue": "late"
        },
        "version": "v3.2",
        "enable_validation": True
    }
    
    response = client.post("/decide/refund_policy", json=input_data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["output"]["refund"] == 100
    assert result["output"]["reason"] == "Late delivery"
    assert result["output"]["rule_id"] == "late_delivery"

def test_decide_endpoint_damaged():
    """Test decision for damaged item via API"""
    input_data = {
        "input": {
            "id": "A2",
            "customer": {
                "id": "456",
                "signup_date": "2023-02-01T00:00:00",
                "status": "silver"
            },
            "order_date": "2024-06-01T00:00:00",
            "delivery_date": "2024-06-05T00:00:00",
            "issue": "damaged"
        },
        "version": "v3.2",
        "enable_validation": True
    }
    
    response = client.post("/decide/refund_policy", json=input_data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["output"]["refund"] == 50
    assert result["output"]["reason"] == "Damaged item"
    assert result["output"]["rule_id"] == "damaged_item"

def test_decide_endpoint_default():
    """Test decision for default case via API"""
    input_data = {
        "input": {
            "id": "A3",
            "customer": {
                "id": "789",
                "signup_date": "2023-03-01T00:00:00",
                "status": "bronze"
            },
            "order_date": "2024-06-01T00:00:00",
            "delivery_date": "2024-06-05T00:00:00",
            "issue": "none"
        },
        "version": "v3.2",
        "enable_validation": True
    }
    
    response = client.post("/decide/refund_policy", json=input_data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["output"]["refund"] == 0
    assert result["output"]["reason"] == "Not eligible for refund"

def test_decide_endpoint_invalid_policy():
    """Test API with invalid policy name"""
    input_data = {
        "input": {
            "id": "A1",
            "customer": {
                "id": "123",
                "signup_date": "2023-01-01T00:00:00",
                "status": "gold"
            },
            "order_date": "2024-06-01T00:00:00",
            "delivery_date": "2024-06-05T00:00:00",
            "issue": "late"
        },
        "version": "v3.2",
        "enable_validation": True
    }
    
    response = client.post("/decide/invalid_policy", json=input_data)
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]

def test_decide_endpoint_invalid_version():
    """Test API with invalid version"""
    input_data = {
        "input": {
            "id": "A1",
            "customer": {
                "id": "123",
                "signup_date": "2023-01-01T00:00:00",
                "status": "gold"
            },
            "order_date": "2024-06-01T00:00:00",
            "delivery_date": "2024-06-05T00:00:00",
            "issue": "late"
        },
        "version": "invalid_version",
        "enable_validation": True
    }
    
    response = client.post("/decide/refund_policy", json=input_data)
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]

def test_api_health_check():
    """Test API health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy" 