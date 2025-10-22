"""
Storage backends for Decision Layer
"""

import importlib.util
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg

from .errors import StorageError


class StorageBackend(ABC):
    """Abstract storage backend interface"""

    @abstractmethod
    async def save_function(self, function_id: str, version: str, code: str) -> None:
        """Save a function version"""
        pass

    @abstractmethod
    async def load_function(self, function_id: str, version: str) -> str:
        """Load a function version code"""
        pass

    @abstractmethod
    async def load_function_object(self, function_id: str, version: str):
        """Load a function as callable object"""
        pass

    @abstractmethod
    async def list_functions(self) -> List[str]:
        """List all function IDs"""
        pass

    @abstractmethod
    async def list_versions(self, function_id: str) -> List[str]:
        """List all versions for a function"""
        pass

    @abstractmethod
    async def store_decision(self, context, result_data: Dict[str, Any]) -> str:
        """Store decision result"""
        pass

    @abstractmethod
    async def retrieve_decision(self, trace_id: str) -> Dict[str, Any]:
        """Retrieve decision result by trace ID"""
        pass

    @abstractmethod
    async def get_decision_history(
        self, function_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get decision history for a function"""
        pass

    @abstractmethod
    async def get_decisions_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get decisions within a date range"""
        pass

    @abstractmethod
    async def cleanup_old_decisions(self, retention_days: int) -> int:
        """Clean up decisions older than retention_days"""
        pass

    @abstractmethod
    async def get_decision_stats(self, function_id: str) -> Dict[str, Any]:
        """Get decision statistics for a function"""
        pass

    @abstractmethod
    async def store_release(self, release_data: Dict[str, Any]) -> None:
        """Store a release record"""
        pass

    @abstractmethod
    async def get_release(self, release_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific release record"""
        pass

    @abstractmethod
    async def get_releases(
        self, df_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get releases with optional filtering"""
        pass

    @abstractmethod
    async def update_release(
        self, release_id: str, release_data: Dict[str, Any]
    ) -> None:
        """Update a release record"""
        pass

    @abstractmethod
    async def store_function_spec(
        self, df_id: str, version: str, spec: Dict[str, Any]
    ) -> None:
        """Store decision function specification"""
        pass

    @abstractmethod
    async def retrieve_function_spec(
        self, df_id: str, version: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve decision function specification"""
        pass


class FileStorage(StorageBackend):
    """File-based storage backend"""

    def __init__(self, base_path: str = "./functions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    async def save_function(self, function_id: str, version: str, code: str) -> None:
        """Save function to file"""
        function_dir = self.base_path / function_id
        function_dir.mkdir(exist_ok=True)

        file_path = function_dir / f"{version}.py"
        try:
            with open(file_path, "w") as f:
                f.write(code)
        except Exception as e:
            raise StorageError("write", f"Failed to save function: {e}")

    async def load_function(self, function_id: str, version: str) -> str:
        """Load function from file"""
        file_path = self.base_path / function_id / f"{version}.py"

        try:
            with open(file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise StorageError(
                "read", f"Function {function_id} version {version} not found"
            )
        except Exception as e:
            raise StorageError("read", f"Failed to load function: {e}")

    async def load_function_object(self, function_id: str, version: str):
        """Load function as callable object"""
        code = await self.load_function(function_id, version)

        # Create module and execute
        spec = importlib.util.spec_from_loader("temp_module", loader=None)
        if spec is None:
            raise StorageError(
                "read", f"Failed to create module spec for {function_id} v{version}"
            )
        module = importlib.util.module_from_spec(spec)
        exec(code, module.__dict__)

        if not hasattr(module, "decision_function"):
            raise StorageError(
                "read", f"No decision_function found in {function_id} v{version}"
            )

        return module.decision_function

    async def list_functions(self) -> List[str]:
        """List all function IDs"""
        try:
            if not self.base_path.exists():
                return []

            return [
                d.name
                for d in self.base_path.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]
        except Exception as e:
            raise StorageError("list", f"Failed to list functions: {e}")

    async def list_versions(self, function_id: str) -> List[str]:
        """List all versions for a function"""
        function_dir = self.base_path / function_id

        try:
            if not function_dir.exists():
                return []

            versions = [
                f.stem
                for f in function_dir.glob("*.py")
                if f.is_file() and not f.name.startswith(".")
            ]
            return sorted(versions)
        except Exception as e:
            raise StorageError("list", f"Failed to list versions: {e}")

    async def store_decision(self, context, result_data: Dict[str, Any]) -> str:
        """Store decision result to file"""
        decisions_dir = self.base_path / "decisions"
        decisions_dir.mkdir(exist_ok=True)

        file_path = decisions_dir / f"{context.trace_id}.json"
        try:
            import json

            with open(file_path, "w") as f:
                json.dump(
                    {
                        "trace_id": context.trace_id,
                        "function_id": context.function_id,
                        "version": context.version,
                        "timestamp": context.timestamp.isoformat(),
                        "result": result_data,
                    },
                    f,
                )
            return context.trace_id
        except Exception as e:
            raise StorageError("write", f"Failed to store decision: {e}")

    async def retrieve_decision(self, trace_id: str) -> Dict[str, Any]:
        """Retrieve decision result from file"""
        file_path = self.base_path / "decisions" / f"{trace_id}.json"
        try:
            import json

            with open(file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise StorageError("read", f"Decision {trace_id} not found")
        except Exception as e:
            raise StorageError("read", f"Failed to retrieve decision: {e}")

    async def get_decision_history(
        self, function_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get decision history for a function from files"""
        decisions_dir = self.base_path / "decisions"
        if not decisions_dir.exists():
            return []

        try:
            decisions = []
            for file_path in decisions_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    decision = json.load(f)
                    if decision.get("function_id") == function_id:
                        decisions.append(decision)

            # Sort by timestamp descending
            decisions.sort(key=lambda x: x["timestamp"], reverse=True)

            # Apply pagination
            return decisions[offset : offset + limit]
        except Exception as e:
            raise StorageError("read", f"Failed to get decision history: {e}")

    async def get_decisions_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get decisions within a date range from files"""
        decisions_dir = self.base_path / "decisions"
        if not decisions_dir.exists():
            return []

        try:
            decisions = []
            for file_path in decisions_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    decision = json.load(f)
                    decision_time = datetime.fromisoformat(decision["timestamp"])
                    if start_date <= decision_time <= end_date:
                        decisions.append(decision)

            # Sort by timestamp descending
            decisions.sort(key=lambda x: x["timestamp"], reverse=True)

            return decisions[:limit]
        except Exception as e:
            raise StorageError("read", f"Failed to get decisions by date range: {e}")

    async def cleanup_old_decisions(self, retention_days: int) -> int:
        """Clean up decisions older than retention_days from files"""
        decisions_dir = self.base_path / "decisions"
        if not decisions_dir.exists():
            return 0

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0

        try:
            for file_path in decisions_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    decision = json.load(f)
                    decision_time = datetime.fromisoformat(decision["timestamp"])

                    if decision_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1

            return deleted_count
        except Exception as e:
            raise StorageError("delete", f"Failed to cleanup old decisions: {e}")

    async def get_decision_stats(self, function_id: str) -> Dict[str, Any]:
        """Get decision statistics for a function from files"""
        decisions_dir = self.base_path / "decisions"
        if not decisions_dir.exists():
            return {
                "total_decisions": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
            }

        try:
            decisions = []
            for file_path in decisions_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    decision = json.load(f)
                    if decision.get("function_id") == function_id:
                        decisions.append(decision)

            if not decisions:
                return {
                    "total_decisions": 0,
                    "success_rate": 0.0,
                    "avg_execution_time": 0.0,
                }

            total_decisions = len(decisions)
            successful_decisions = sum(
                1 for d in decisions if d.get("result", {}).get("success", False)
            )
            success_rate = (
                successful_decisions / total_decisions if total_decisions > 0 else 0.0
            )

            # Calculate average execution time if available
            execution_times = [
                d.get("result", {}).get("execution_time_ms", 0)
                for d in decisions
                if d.get("result", {}).get("execution_time_ms")
            ]
            avg_execution_time = (
                sum(execution_times) / len(execution_times) if execution_times else 0.0
            )

            return {
                "total_decisions": total_decisions,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "first_decision": min(decisions, key=lambda x: x["timestamp"])[
                    "timestamp"
                ],
                "last_decision": max(decisions, key=lambda x: x["timestamp"])[
                    "timestamp"
                ],
            }
        except Exception as e:
            raise StorageError("read", f"Failed to get decision stats: {e}")

    async def store_release(self, release_data: Dict[str, Any]) -> None:
        """Store a release record to file"""
        releases_dir = self.base_path / "releases"
        releases_dir.mkdir(exist_ok=True)

        release_file = releases_dir / f"{release_data['release_id']}.json"
        try:
            with open(release_file, "w") as f:
                json.dump(release_data, f, indent=2, default=str)
        except Exception as e:
            raise StorageError("write", f"Failed to store release: {e}")

    async def get_release(self, release_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific release record from file"""
        releases_dir = self.base_path / "releases"
        release_file = releases_dir / f"{release_id}.json"

        if not release_file.exists():
            return None

        try:
            with open(release_file, "r") as f:
                return json.load(f)
        except Exception as e:
            raise StorageError("read", f"Failed to get release: {e}")

    async def get_releases(
        self, df_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get releases with optional filtering from files"""
        releases_dir = self.base_path / "releases"
        if not releases_dir.exists():
            return []

        releases = []
        try:
            for file_path in releases_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    release = json.load(f)

                    # Apply filters
                    if df_id and release.get("df_id") != df_id:
                        continue
                    if status and release.get("status") != status:
                        continue

                    releases.append(release)

            # Sort by created_at descending
            releases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return releases
        except Exception as e:
            raise StorageError("read", f"Failed to get releases: {e}")

    async def update_release(
        self, release_id: str, release_data: Dict[str, Any]
    ) -> None:
        """Update a release record in file"""
        releases_dir = self.base_path / "releases"
        release_file = releases_dir / f"{release_id}.json"

        if not release_file.exists():
            raise StorageError("not_found", f"Release {release_id} not found")

        try:
            with open(release_file, "w") as f:
                json.dump(release_data, f, indent=2, default=str)
        except Exception as e:
            raise StorageError("write", f"Failed to update release: {e}")

    async def store_function_spec(
        self, df_id: str, version: str, spec: Dict[str, Any]
    ) -> None:
        """Store decision function specification to file"""
        spec_dir = self.base_path / "specs"
        spec_dir.mkdir(parents=True, exist_ok=True)

        spec_file = spec_dir / f"{df_id}_{version}.json"
        try:
            with open(spec_file, "w") as f:
                json.dump(spec, f, indent=2, default=str)
        except Exception as e:
            raise StorageError("write", f"Failed to store function spec: {e}")

    async def retrieve_function_spec(
        self, df_id: str, version: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve decision function specification from file"""
        spec_dir = self.base_path / "specs"
        spec_file = spec_dir / f"{df_id}_{version}.json"

        if not spec_file.exists():
            return None

        try:
            with open(spec_file, "r") as f:
                return json.load(f)
        except Exception as e:
            raise StorageError("read", f"Failed to retrieve function spec: {e}")


class PostgreSQLStorage(StorageBackend):
    """PostgreSQL-based storage backend"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None

    async def connect(self):
        """Initialize connection pool and create tables"""
        try:
            self.pool = await asyncpg.create_pool(self.connection_string)
            await self._create_tables()
        except Exception as e:
            raise StorageError("connect", f"Failed to connect to PostgreSQL: {e}")

    async def _create_tables(self):
        """Create necessary tables if they don't exist"""
        if self.pool is None:
            raise StorageError("connect", "Database pool not initialized")
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS functions (
                    id SERIAL PRIMARY KEY,
                    function_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    code TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(function_id, version)
                )
            """
            )

            # Create index for faster lookups
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_functions_id_version
                ON functions(function_id, version)
            """
            )

            # Create decisions table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    trace_id TEXT PRIMARY KEY,
                    function_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    result_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """
            )

            # Create releases table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS releases (
                    id SERIAL PRIMARY KEY,
                    release_id TEXT UNIQUE NOT NULL,
                    df_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    effective_from TIMESTAMP NOT NULL,
                    sunset_date TIMESTAMP,
                    change_summary TEXT NOT NULL,
                    signatures JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    created_by TEXT,
                    activated_at TIMESTAMP,
                    activated_by TEXT,
                    sunset_at TIMESTAMP,
                    sunset_by TEXT,
                    updated_at TIMESTAMP,
                    updated_by TEXT
                )
            """
            )

            # Create function_specs table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS function_specs (
                    id SERIAL PRIMARY KEY,
                    df_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    spec_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(df_id, version)
                )
            """
            )

            # Create index for decisions
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_decisions_function_id
                ON decisions(function_id, timestamp)
            """
            )

    async def save_function(self, function_id: str, version: str, code: str) -> None:
        """Save function to PostgreSQL"""
        if not self.pool:
            await self.connect()

        if self.pool is None:
            raise StorageError("save", "Database pool not initialized")

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO functions (function_id, version, code)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (function_id, version)
                    DO UPDATE SET code = $3, created_at = NOW()
                """,
                    function_id,
                    version,
                    code,
                )
        except Exception as e:
            raise StorageError("write", f"Failed to save function: {e}")

    async def load_function(self, function_id: str, version: str) -> str:
        """Load function from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT code FROM functions
                    WHERE function_id = $1 AND version = $2
                """,
                    function_id,
                    version,
                )

                if not row:
                    raise StorageError(
                        "read", f"Function {function_id} version {version} not found"
                    )

                return row["code"]
        except StorageError:
            raise
        except Exception as e:
            raise StorageError("read", f"Failed to load function: {e}")

    async def load_function_object(self, function_id: str, version: str):
        """Load function as callable object"""
        code = await self.load_function(function_id, version)

        # Create module and execute
        import importlib.util

        spec = importlib.util.spec_from_loader("temp_module", loader=None)
        if spec is None:
            raise StorageError(
                "read", f"Failed to create module spec for {function_id} v{version}"
            )
        module = importlib.util.module_from_spec(spec)
        exec(code, module.__dict__)

        if not hasattr(module, "decision_function"):
            raise StorageError(
                "read", f"No decision_function found in {function_id} v{version}"
            )

        return module.decision_function

    async def list_functions(self) -> List[str]:
        """List all function IDs"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT function_id FROM functions
                    ORDER BY function_id
                """
                )
                return [row["function_id"] for row in rows]
        except Exception as e:
            raise StorageError("list", f"Failed to list functions: {e}")

    async def list_versions(self, function_id: str) -> List[str]:
        """List all versions for a function"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT version FROM functions
                    WHERE function_id = $1
                    ORDER BY version
                """,
                    function_id,
                )
                return [row["version"] for row in rows]
        except Exception as e:
            raise StorageError("list", f"Failed to list versions: {e}")

    async def store_decision(self, context, result_data: Dict[str, Any]) -> str:
        """Store decision result to PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO decisions (trace_id, function_id, version, timestamp, result_data)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (trace_id)
                    DO UPDATE SET result_data = $5, timestamp = $4
                """,
                    context.trace_id,
                    context.function_id,
                    context.version,
                    context.timestamp,
                    json.dumps(result_data),
                )
            return context.trace_id
        except Exception as e:
            raise StorageError("write", f"Failed to store decision: {e}")

    async def retrieve_decision(self, trace_id: str) -> Dict[str, Any]:
        """Retrieve decision result from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT trace_id, function_id, version, timestamp, result_data
                    FROM decisions WHERE trace_id = $1
                """,
                    trace_id,
                )

                if not row:
                    raise StorageError("read", f"Decision {trace_id} not found")

                return {
                    "trace_id": row["trace_id"],
                    "function_id": row["function_id"],
                    "version": row["version"],
                    "timestamp": row["timestamp"].isoformat(),
                    "result": json.loads(row["result_data"]),
                }
        except StorageError:
            raise
        except Exception as e:
            raise StorageError("read", f"Failed to retrieve decision: {e}")

    async def get_decision_history(
        self, function_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get decision history for a function from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT trace_id, function_id, version, timestamp, result_data
                    FROM decisions
                    WHERE function_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2 OFFSET $3
                """,
                    function_id,
                    limit,
                    offset,
                )

                return [
                    {
                        "trace_id": row["trace_id"],
                        "function_id": row["function_id"],
                        "version": row["version"],
                        "timestamp": row["timestamp"].isoformat(),
                        "result": json.loads(row["result_data"]),
                    }
                    for row in rows
                ]
        except Exception as e:
            raise StorageError("read", f"Failed to get decision history: {e}")

    async def get_decisions_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get decisions within a date range from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT trace_id, function_id, version, timestamp, result_data
                    FROM decisions
                    WHERE timestamp BETWEEN $1 AND $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                """,
                    start_date,
                    end_date,
                    limit,
                )

                return [
                    {
                        "trace_id": row["trace_id"],
                        "function_id": row["function_id"],
                        "version": row["version"],
                        "timestamp": row["timestamp"].isoformat(),
                        "result": json.loads(row["result_data"]),
                    }
                    for row in rows
                ]
        except Exception as e:
            raise StorageError("read", f"Failed to get decisions by date range: {e}")

    async def cleanup_old_decisions(self, retention_days: int) -> int:
        """Clean up decisions older than retention_days from PostgreSQL"""
        if not self.pool:
            await self.connect()

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM decisions
                    WHERE timestamp < $1
                """,
                    cutoff_date,
                )
                # Extract number of deleted rows from result
                deleted_count = (
                    int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                )
                return deleted_count
        except Exception as e:
            raise StorageError("delete", f"Failed to cleanup old decisions: {e}")

    async def get_decision_stats(self, function_id: str) -> Dict[str, Any]:
        """Get decision statistics for a function from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                # Get basic stats
                stats_row = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_decisions,
                        COUNT(CASE WHEN result_data->>'success' = 'true' THEN 1 END) as successful_decisions,
                        AVG((result_data->>'execution_time_ms')::numeric) as avg_execution_time,
                        MIN(timestamp) as first_decision,
                        MAX(timestamp) as last_decision
                    FROM decisions
                    WHERE function_id = $1
                """,
                    function_id,
                )

                if not stats_row or stats_row["total_decisions"] == 0:
                    return {
                        "total_decisions": 0,
                        "success_rate": 0.0,
                        "avg_execution_time": 0.0,
                        "first_decision": None,
                        "last_decision": None,
                    }

                success_rate = (
                    stats_row["successful_decisions"] / stats_row["total_decisions"]
                    if stats_row["total_decisions"] > 0
                    else 0.0
                )

                return {
                    "total_decisions": stats_row["total_decisions"],
                    "success_rate": success_rate,
                    "avg_execution_time": float(stats_row["avg_execution_time"] or 0),
                    "first_decision": (
                        stats_row["first_decision"].isoformat()
                        if stats_row["first_decision"]
                        else None
                    ),
                    "last_decision": (
                        stats_row["last_decision"].isoformat()
                        if stats_row["last_decision"]
                        else None
                    ),
                }
        except Exception as e:
            raise StorageError("read", f"Failed to get decision stats: {e}")

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()

    async def store_release(self, release_data: Dict[str, Any]) -> None:
        """Store a release record to PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO releases (
                        release_id, df_id, version, status, effective_from,
                        sunset_date, change_summary, signatures, created_at, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    release_data["release_id"],
                    release_data["df_id"],
                    release_data["version"],
                    release_data["status"],
                    release_data["effective_from"],
                    release_data["sunset_date"],
                    release_data["change_summary"],
                    json.dumps(release_data["signatures"]),
                    release_data["created_at"],
                    release_data["created_by"],
                )
        except Exception as e:
            raise StorageError("write", f"Failed to store release: {e}")

    async def get_release(self, release_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific release record from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM releases WHERE release_id = $1", release_id
                )
                if not row:
                    return None

                release_data = dict(row)
                release_data["signatures"] = json.loads(release_data["signatures"])
                return release_data
        except Exception as e:
            raise StorageError("read", f"Failed to get release: {e}")

    async def get_releases(
        self, df_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get releases with optional filtering from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                query = "SELECT * FROM releases WHERE 1=1"
                params = []

                if df_id:
                    query += " AND df_id = $" + str(len(params) + 1)
                    params.append(df_id)

                if status:
                    query += " AND status = $" + str(len(params) + 1)
                    params.append(status)

                query += " ORDER BY created_at DESC"

                rows = await conn.fetch(query, *params)
                releases = []
                for row in rows:
                    release_data = dict(row)
                    release_data["signatures"] = json.loads(release_data["signatures"])
                    releases.append(release_data)

                return releases
        except Exception as e:
            raise StorageError("read", f"Failed to get releases: {e}")

    async def update_release(
        self, release_id: str, release_data: Dict[str, Any]
    ) -> None:
        """Update a release record in PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE releases SET
                        status = $2,
                        effective_from = $3,
                        sunset_date = $4,
                        change_summary = $5,
                        signatures = $6,
                        updated_at = $7,
                        updated_by = $8
                    WHERE release_id = $1
                    """,
                    release_id,
                    release_data["status"],
                    release_data.get("effective_from"),
                    release_data.get("sunset_date"),
                    release_data.get("change_summary"),
                    json.dumps(release_data.get("signatures", [])),
                    datetime.utcnow(),
                    release_data.get("updated_by", "unknown"),
                )
        except Exception as e:
            raise StorageError("write", f"Failed to update release: {e}")

    async def store_function_spec(
        self, df_id: str, version: str, spec: Dict[str, Any]
    ) -> None:
        """Store decision function specification to PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO function_specs (df_id, version, spec_data, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (df_id, version) DO UPDATE SET
                        spec_data = $3,
                        updated_at = $5
                    """,
                    df_id,
                    version,
                    json.dumps(spec),
                    datetime.utcnow(),
                    datetime.utcnow(),
                )
        except Exception as e:
            raise StorageError("write", f"Failed to store function spec: {e}")

    async def retrieve_function_spec(
        self, df_id: str, version: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve decision function specification from PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
            if self.pool is None:
                raise StorageError("operation", "Database pool not initialized")
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT spec_data FROM function_specs WHERE df_id = $1 AND version = $2",
                    df_id,
                    version,
                )
                if not row:
                    return None

                return json.loads(row["spec_data"])
        except Exception as e:
            raise StorageError("read", f"Failed to retrieve function spec: {e}")


def create_storage_backend(backend_type: str, config: Dict[str, Any]) -> StorageBackend:
    """Factory function to create storage backend"""
    if backend_type == "file":
        path = config.get("path", "./functions")
        return FileStorage(path)
    elif backend_type == "postgresql":
        connection_string = config.get("connection_string")
        if not connection_string:
            raise ValueError("PostgreSQL connection_string is required")
        return PostgreSQLStorage(connection_string)
    else:
        raise ValueError(f"Unsupported storage backend: {backend_type}")
