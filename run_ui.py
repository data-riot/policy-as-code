#!/usr/bin/env python3
"""
Run the Decision Layer Streamlit UI
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the Streamlit application"""
    print("🚀 Starting Decision Layer Web UI...")
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit is available")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # Check if the app file exists
    app_file = Path("streamlit_app.py")
    if not app_file.exists():
        print("❌ streamlit_app.py not found")
        return
    
    # Set environment variables for better UX
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    print("🌐 Starting Streamlit server...")
    print("📱 Web UI will be available at: http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")

if __name__ == "__main__":
    main() 