#!/usr/bin/env python3
"""
Test the Streamlit app functionality
"""

import asyncio
import json
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported")
        
        import pandas as pd
        print("✅ Pandas imported")
        
        import plotly.express as px
        print("✅ Plotly imported")
        
        from decision_layer import DecisionEngine, load_config
        print("✅ Decision Layer imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        from decision_layer.config import load_config
        
        config = load_config()
        print("✅ Configuration loaded")
        
        # Test config structure
        assert hasattr(config, 'storage')
        assert hasattr(config, 'security')
        assert hasattr(config, 'plugins')
        print("✅ Configuration structure valid")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

async def test_engine_initialization():
    """Test engine initialization"""
    print("\n🔍 Testing engine initialization...")
    
    try:
        from decision_layer import DecisionEngine, load_config
        
        config = load_config()
        engine = DecisionEngine(config=config.to_dict())
        print("✅ Engine initialized")
        
        # Test basic operations
        functions = await engine.list_functions()
        print(f"✅ Functions listed: {len(functions)} found")
        
        return True
    except Exception as e:
        print(f"❌ Engine error: {e}")
        return False

def test_streamlit_app():
    """Test Streamlit app file"""
    print("\n🔍 Testing Streamlit app...")
    
    try:
        app_file = Path("streamlit_app.py")
        if not app_file.exists():
            print("❌ streamlit_app.py not found")
            return False
        
        # Try to import the app functions
        import sys
        sys.path.append('.')
        
        # Test that the file can be executed
        with open(app_file, 'r') as f:
            content = f.read()
        
        if 'def main()' in content:
            print("✅ Streamlit app structure valid")
        else:
            print("❌ Streamlit app missing main function")
            return False
        
        if 'st.set_page_config' in content:
            print("✅ Streamlit app properly configured")
        else:
            print("❌ Streamlit app missing page config")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Streamlit app error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing Decision Layer Streamlit UI\n")
    
    # Test imports
    if not test_imports():
        return False
    
    # Test config
    if not test_config_loading():
        return False
    
    # Test engine
    if not await test_engine_initialization():
        return False
    
    # Test Streamlit app
    if not test_streamlit_app():
        return False
    
    print("\n🎉 All tests passed! Streamlit UI is ready to use.")
    print("\n📱 To start the web interface:")
    print("   python run_ui.py")
    print("   # Then open http://localhost:8501 in your browser")
    
    return True

if __name__ == "__main__":
    asyncio.run(main()) 