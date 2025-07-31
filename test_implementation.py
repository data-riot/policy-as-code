#!/usr/bin/env python3
"""
Test script to verify the Decision Layer implementation
"""

import asyncio
import json
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from decision_layer import DecisionEngine
        print("✅ DecisionEngine imported")
        
        from decision_layer import DecisionLayerConfig, load_config
        print("✅ Config modules imported")
        
        from decision_layer import PostgreSQLStorage, FileStorage
        print("✅ Storage modules imported")
        
        from decision_layer import APIKeyAuth
        print("✅ Auth modules imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        from decision_layer.config import DecisionLayerConfig
        
        # Test default config
        config = DecisionLayerConfig()
        print("✅ Default config created")
        
        # Test file config
        if Path("config.yaml").exists():
            config = DecisionLayerConfig.from_file("config.yaml")
            print("✅ Config loaded from file")
        
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

async def test_storage():
    """Test storage backends"""
    print("\n🔍 Testing storage...")
    
    try:
        from decision_layer.storage import FileStorage
        
        # Test file storage
        storage = FileStorage("./test_functions")
        
        # Test save/load
        test_code = '''
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    return {"result": "test"}
'''
        
        await storage.save_function("test_policy", "v1.0", test_code)
        print("✅ Function saved")
        
        code = await storage.load_function("test_policy", "v1.0")
        print("✅ Function loaded")
        
        functions = await storage.list_functions()
        print(f"✅ Functions listed: {functions}")
        
        versions = await storage.list_versions("test_policy")
        print(f"✅ Versions listed: {versions}")
        
        return True
    except Exception as e:
        print(f"❌ Storage error: {e}")
        return False

async def test_engine():
    """Test decision engine"""
    print("\n🔍 Testing decision engine...")
    
    try:
        from decision_layer import DecisionEngine
        
        # Create engine with file storage
        config = {
            "storage": {"backend": "file", "path": "./test_functions"},
            "plugins": {
                "validation": {"enabled": False},
                "tracing": {"enabled": True, "path": "./test_traces"},
                "caching": {"enabled": True}
            }
        }
        
        engine = DecisionEngine(config=config)
        print("✅ Engine created")
        
        # Test function deployment
        test_code = '''
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    amount = input_data.get('amount', 0)
    if amount > 1000:
        return {"approved": False, "reason": "Amount too high"}
    else:
        return {"approved": True, "reason": "Amount within limits"}
'''
        
        await engine.deploy_function("test_policy", "v1.0", test_code)
        print("✅ Function deployed")
        
        # Test execution
        result = await engine.execute("test_policy", {"amount": 500})
        print(f"✅ Function executed: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Engine error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing Decision Layer Implementation\n")
    
    # Test imports
    if not test_imports():
        return
    
    # Test config
    if not test_config():
        return
    
    # Test storage
    if not await test_storage():
        return
    
    # Test engine
    if not await test_engine():
        return
    
    print("\n🎉 All tests passed! Decision Layer is ready to use.")

if __name__ == "__main__":
    asyncio.run(main()) 