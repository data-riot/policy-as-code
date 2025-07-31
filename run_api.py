#!/usr/bin/env python3
"""
Run the Decision Layer API server
"""

import asyncio
import os
from pathlib import Path
from decision_layer import DecisionEngine
from decision_layer.api import create_api
from decision_layer.config import load_config


def main():
    """Main function to run the API server"""
    print("🚀 Starting Decision Layer API Server...")
    
    # Load configuration
    try:
        config = load_config()
        print("✅ Configuration loaded and validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Create engine
    try:
        engine = DecisionEngine(config=config.to_dict())
        print("✅ Decision engine initialized")
    except Exception as e:
        print(f"❌ Engine initialization error: {e}")
        return
    
    # Create API
    api_config = config.api
    host = api_config.host
    port = api_config.port
    
    api = create_api(engine, host=host, port=port)
    print(f"✅ API created on {host}:{port}")
    
    # Start server
    print(f"🌐 API server starting on http://{host}:{port}")
    print(f"📚 API documentation available at http://{host}:{port}/docs")
    print(f"🔍 Health check available at http://{host}:{port}/health")
    print("Press Ctrl+C to stop the server")
    
    try:
        api.run(host=host, port=port)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == "__main__":
    main() 