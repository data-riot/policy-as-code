"""
Storage backends for Decision Layer
"""

import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

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

    async def save_function(self, function_id: str, version: str, code: str) -> None:
        """Save function to PostgreSQL"""
        if not self.pool:
            await self.connect()

        try:
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

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()


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
