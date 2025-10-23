#!/usr/bin/env python3
"""
Simple API Server Runner
Easy way to start the Policy as Code API server
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from policy_as_code.simple_api import main
except ImportError as e:
    print(f"❌ Failed to import API server: {e}")
    print("   Make sure you're in the project root directory")
    print("   Install dependencies with: pip install -e .[production]")
    sys.exit(1)

if __name__ == "__main__":
    main()
