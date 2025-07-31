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
    # Starting Decision Layer API Server

    # Load configuration
    try:
        config = load_config()
        # Configuration loaded and validated
    except Exception as e:
        # Configuration error
        print(f"Configuration error: {e}")
        raise

    # Create engine
    try:
        engine = DecisionEngine(config=config.to_dict())
        # Decision engine initialized
    except Exception as e:
        # Engine initialization error
        print(f"Engine initialization error: {e}")
        raise

    # Create API
    api_config = config.api
    host = api_config.host
    port = api_config.port

    api = create_api(engine, host=host, port=port)
    # API created on {host}:{port}

    # Start server
    # API server starting on http://{host}:{port}
    # API documentation available at http://{host}:{port}/docs
    # Health check available at http://{host}:{port}/health
    # Press Ctrl+C to stop the server

    try:
        api.run(host=host, port=port)
    except KeyboardInterrupt:
        # Server stopped by user
        print("Server stopped by user")
    except Exception as e:
        # Server error
        print(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
