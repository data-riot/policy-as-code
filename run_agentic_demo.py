#!/usr/bin/env python3
"""
Run Agentic AI Demo

This script runs the complete agentic AI demonstration showing all the new
capabilities added to the policy-as-code platform.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from examples.agentic_demo import main

if __name__ == "__main__":
    print("🚀 Starting Agentic AI Demo...")
    print("This demo showcases the new agentic capabilities added to policy-as-code")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        sys.exit(1)
