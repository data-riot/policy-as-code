import pytest
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from datetime import datetime
from api.fastapi_app import app

client = TestClient(app)

def test_decide_endpoint_success():
    """Test successful decision via API"""
    input_data = {
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
    
    response = client.post("/decide/refund_policy/v3.2", json=input_data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["refund"] == 100
    assert result["reason"] == "Late delivery"
    assert result["rule_id"] == "late"

def test_decide_endpoint_damaged():
    """Test decision for damaged item via API"""
    input_data = {
        "id": "A2",
        "customer": {
            "id": "456",
            "signup_date": "2023-02-01T00:00:00",
            "status": "silver"
        },
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "issue": "damaged"
    }
    
    response = client.post("/decide/refund_policy/v3.2", json=input_data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["refund"] == 50
    assert result["reason"] == "Damaged item"
    assert result["rule_id"] == "damaged"

def test_decide_endpoint_default():
    """Test decision for default case via API"""
    input_data = {
        "id": "A3",
        "customer": {
            "id": "789",
            "signup_date": "2023-03-01T00:00:00",
            "status": "bronze"
        },
        "order_date": "2024-06-01T00:00:00",
        "delivery_date": "2024-06-05T00:00:00",
        "issue": "none"
    }
    
    response = client.post("/decide/refund_policy/v3.2", json=input_data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["refund"] == 0
    assert result["reason"] == "Not eligible"

def test_decide_endpoint_invalid_policy():
    """Test API with invalid policy name"""
    input_data = {
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
    
    response = client.post("/decide/invalid_policy/v3.2", json=input_data)
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]

def test_decide_endpoint_invalid_version():
    """Test API with invalid version"""
    input_data = {
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
    
    response = client.post("/decide/refund_policy/invalid_version", json=input_data)
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]

def test_api_health_check():
    """Test API health check endpoint"""
    response = client.get("/docs")
    assert response.status_code == 200 