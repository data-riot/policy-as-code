"""
PostgreSQL Trace Store

This module provides PostgreSQL-based storage for trace records,
enabling persistent storage and efficient querying of trace data.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import asdict

import asyncpg
from policy_as_code.tracing.errors import PostgresError, StorageError
from policy_as_code.trace_schema import TraceRecord, TraceQuery, TraceSummary


class PostgreSQLTraceStore:
    """PostgreSQL-based trace storage"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize the database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string, min_size=1, max_size=10
            )
            await self._create_tables()
        except Exception as e:
            raise PostgresError(f"Failed to initialize PostgreSQL store: {e}")

    async def _create_tables(self):
        """Create necessary database tables"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id VARCHAR(255) PRIMARY KEY,
                    trace_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_ms INTEGER,
                    metadata JSONB,
                    events JSONB,
                    input_data JSONB,
                    output_data JSONB,
                    error_data JSONB,
                    performance_metrics JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_traces_function_id
                ON traces ((metadata->>'function_id'))
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_traces_start_time
                ON traces (start_time)
            """
            )

    async def store_trace(self, trace: TraceRecord) -> bool:
        """Store a trace record"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO traces (
                        trace_id, trace_type, status, start_time, end_time,
                        duration_ms, metadata, events, input_data, output_data,
                        error_data, performance_metrics
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (trace_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        end_time = EXCLUDED.end_time,
                        duration_ms = EXCLUDED.duration_ms,
                        events = EXCLUDED.events,
                        output_data = EXCLUDED.output_data,
                        error_data = EXCLUDED.error_data,
                        performance_metrics = EXCLUDED.performance_metrics
                """,
                    trace.trace_id,
                    trace.trace_type.value,
                    trace.status.value,
                    trace.start_time,
                    trace.end_time,
                    trace.duration_ms,
                    json.dumps(asdict(trace.metadata)) if trace.metadata else None,
                    (
                        json.dumps([asdict(event) for event in trace.events])
                        if trace.events
                        else None
                    ),
                    json.dumps(trace.input_data) if trace.input_data else None,
                    json.dumps(trace.output_data) if trace.output_data else None,
                    json.dumps(trace.error_data) if trace.error_data else None,
                    (
                        json.dumps(trace.performance_metrics)
                        if trace.performance_metrics
                        else None
                    ),
                )
                return True
        except Exception as e:
            raise StorageError(f"Failed to store trace: {e}")

    async def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        """Retrieve a trace by ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM traces WHERE trace_id = $1", trace_id
                )
                if row:
                    return self._row_to_trace(row)
                return None
        except Exception as e:
            raise StorageError(f"Failed to get trace: {e}")

    async def query_traces(self, query: TraceQuery) -> List[TraceRecord]:
        """Query traces based on criteria"""
        try:
            async with self.pool.acquire() as conn:
                conditions = []
                params = []
                param_count = 0

                if query.trace_id:
                    param_count += 1
                    conditions.append(f"trace_id = ${param_count}")
                    params.append(query.trace_id)

                if query.function_id:
                    param_count += 1
                    conditions.append(f"metadata->>'function_id' = ${param_count}")
                    params.append(query.function_id)

                if query.start_time:
                    param_count += 1
                    conditions.append(f"start_time >= ${param_count}")
                    params.append(query.start_time)

                if query.end_time:
                    param_count += 1
                    conditions.append(f"start_time <= ${param_count}")
                    params.append(query.end_time)

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                sql = f"""
                    SELECT * FROM traces
                    WHERE {where_clause}
                    ORDER BY start_time DESC
                    LIMIT ${param_count + 1} OFFSET ${param_count + 2}
                """
                params.extend([query.limit, query.offset])

                rows = await conn.fetch(sql, *params)
                return [self._row_to_trace(row) for row in rows]

        except Exception as e:
            raise StorageError(f"Failed to query traces: {e}")

    async def get_trace_summary(self, query: TraceQuery) -> TraceSummary:
        """Get summary statistics for traces"""
        try:
            async with self.pool.acquire() as conn:
                # Build conditions similar to query_traces
                conditions = []
                params = []
                param_count = 0

                if query.function_id:
                    param_count += 1
                    conditions.append(f"metadata->>'function_id' = ${param_count}")
                    params.append(query.function_id)

                if query.start_time:
                    param_count += 1
                    conditions.append(f"start_time >= ${param_count}")
                    params.append(query.start_time)

                if query.end_time:
                    param_count += 1
                    conditions.append(f"start_time <= ${param_count}")
                    params.append(query.end_time)

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                # Get summary statistics
                summary_sql = f"""
                    SELECT
                        COUNT(*) as total_traces,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_traces,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_traces,
                        AVG(duration_ms) as avg_duration_ms,
                        MIN(start_time) as earliest_time,
                        MAX(start_time) as latest_time
                    FROM traces
                    WHERE {where_clause}
                """

                row = await conn.fetchrow(summary_sql, *params)

                total_traces = row["total_traces"] or 0
                completed_traces = row["completed_traces"] or 0
                success_rate = (
                    (completed_traces / total_traces) if total_traces > 0 else 0.0
                )

                return TraceSummary(
                    total_traces=total_traces,
                    completed_traces=completed_traces,
                    failed_traces=row["failed_traces"] or 0,
                    average_duration_ms=float(row["avg_duration_ms"] or 0),
                    success_rate=success_rate,
                    time_range={
                        "start": row["earliest_time"],
                        "end": row["latest_time"],
                    },
                )

        except Exception as e:
            raise StorageError(f"Failed to get trace summary: {e}")

    def _row_to_trace(self, row) -> TraceRecord:
        """Convert database row to TraceRecord"""
        # This is a simplified conversion - in practice you'd need more robust parsing
        return TraceRecord(
            trace_id=row["trace_id"],
            trace_type=row["trace_type"],
            status=row["status"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_ms=row["duration_ms"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            events=json.loads(row["events"]) if row["events"] else None,
            input_data=json.loads(row["input_data"]) if row["input_data"] else None,
            output_data=json.loads(row["output_data"]) if row["output_data"] else None,
            error_data=json.loads(row["error_data"]) if row["error_data"] else None,
            performance_metrics=(
                json.loads(row["performance_metrics"])
                if row["performance_metrics"]
                else None
            ),
        )

    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()


# Export main class
__all__ = ["PostgreSQLTraceStore"]
