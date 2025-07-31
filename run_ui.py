#!/usr/bin/env python3
"""
Run the Decision Layer Streamlit UI
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run the Streamlit application"""
    # Starting Decision Layer Web UI

    # Check if streamlit is installed
    try:
        import streamlit

        # Streamlit is available
    except ImportError:
        # Streamlit not found, installing...
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])

    # Check if the app file exists
    app_file = Path("streamlit_app.py")
    if not app_file.exists():
        # streamlit_app.py not found
        return

    # Set environment variables for better UX
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    # Starting Streamlit server
    # Web UI will be available at: http://localhost:8501
    # Press Ctrl+C to stop the server

    try:
        # Run streamlit
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "streamlit_app.py",
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
            ]
        )
    except KeyboardInterrupt:
        # Server stopped by user
        print("Server stopped by user")
    except Exception as e:
        # Error running Streamlit
        print(f"Error running Streamlit: {e}")
        raise


if __name__ == "__main__":
    main()
