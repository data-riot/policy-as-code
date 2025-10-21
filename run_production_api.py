#!/usr/bin/env python3
"""
Production-grade Decision Layer API runner
Integrates all governance features: ledger, legal refs, signatures, explanations, audit
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decision_layer.core import DecisionEngine
from decision_layer.api import create_api
from decision_layer.ledger_postgres import create_postgresql_ledger
from decision_layer.release import create_release_manager
from decision_layer.audit_service import create_audit_service


async def setup_governance_services():
    """Setup all governance services"""

    # Database connection string
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/decision_layer"
    )

    # Initialize trace ledger
    print("Initializing trace ledger...")
    trace_ledger = create_postgresql_ledger(db_url)
    await trace_ledger.writer.initialize()
    await trace_ledger.reader.initialize()

    # Initialize release manager
    print("Initializing release manager...")
    release_manager = create_release_manager()

    # Initialize audit service
    print("Initializing audit service...")
    audit_service = create_audit_service(trace_ledger, release_manager)

    return trace_ledger, release_manager, audit_service


async def main():
    """Main application entry point"""

    print("Starting Decision Layer API with governance features...")

    # Setup governance services
    trace_ledger, release_manager, audit_service = await setup_governance_services()

    # Initialize decision engine
    print("Initializing decision engine...")
    engine = DecisionEngine(
        storage_backend="file",
        config={
            "security": {
                "enable_rate_limiting": True,
                "enable_input_sanitization": True,
                "enable_trace_sanitization": True,
            },
            "plugins": {
                "validation": {"enabled": True},
                "tracing": {"enabled": True, "path": "./traces"},
                "caching": {"enabled": True},
            },
        },
    )

    # Create API with governance features
    print("Creating API with governance features...")
    api = create_api(
        engine=engine,
        trace_ledger=trace_ledger,
        release_manager=release_manager,
        host="0.0.0.0",
        port=8000,
    )

    # Start audit service in background
    print("Starting audit service...")
    audit_task = asyncio.create_task(
        audit_service.start_periodic_audits(interval_hours=24)
    )

    try:
        print("Starting API server...")
        print("API Documentation: http://localhost:8000/docs")
        print("Health Check: http://localhost:8000/health")
        print("Governance Features:")
        print("  - Immutable trace ledger with hash chaining")
        print("  - Legal reference validation (Finlex/EUR-Lex)")
        print("  - Digital signatures and release management")
        print("  - Citizen-facing explanation API")
        print("  - Independent audit service")
        print("  - Deterministic function constraints")

        # Run the API server
        api.run()

    except KeyboardInterrupt:
        print("\nShutting down...")
        audit_task.cancel()

        # Close database connections
        await trace_ledger.writer.close()
        await trace_ledger.reader.close()

        print("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
