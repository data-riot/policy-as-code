"""
Trace Compression Module

This module provides compression capabilities for trace records,
enabling efficient storage and transmission of large trace data.
"""

import gzip
import json
import zlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict

from policy_as_code.tracing.errors import CompressionError
from policy_as_code.trace_schema import TraceRecord


class TraceCompressor:
    """Compresses and decompresses trace records"""

    def __init__(self):
        self.compression_algorithms = ["gzip", "zlib", "lz4"]
        self.compression_stats: Dict[str, int] = {}

    async def compress_trace(
        self, trace: TraceRecord, algorithm: str = "gzip"
    ) -> bytes:
        """Compress a trace record"""
        try:
            # Serialize trace to JSON
            trace_data = json.dumps(asdict(trace), default=str).encode("utf-8")

            # Apply compression based on algorithm
            if algorithm == "gzip":
                compressed_data = gzip.compress(trace_data)
            elif algorithm == "zlib":
                compressed_data = zlib.compress(trace_data)
            elif algorithm == "lz4":
                # LZ4 would require additional dependency
                compressed_data = gzip.compress(trace_data)  # Fallback to gzip
            else:
                raise CompressionError(
                    f"Unsupported compression algorithm: {algorithm}"
                )

            # Update stats
            self.compression_stats["compressions"] = (
                self.compression_stats.get("compressions", 0) + 1
            )
            self.compression_stats["bytes_compressed"] = self.compression_stats.get(
                "bytes_compressed", 0
            ) + len(trace_data)
            self.compression_stats[
                "bytes_after_compression"
            ] = self.compression_stats.get("bytes_after_compression", 0) + len(
                compressed_data
            )

            return compressed_data

        except Exception as e:
            raise CompressionError(f"Compression failed: {e}")

    async def decompress_trace(
        self, compressed_data: bytes, algorithm: str = "gzip"
    ) -> TraceRecord:
        """Decompress a trace record"""
        try:
            # Decompress based on algorithm
            if algorithm == "gzip":
                decompressed_data = gzip.decompress(compressed_data)
            elif algorithm == "zlib":
                decompressed_data = zlib.decompress(compressed_data)
            elif algorithm == "lz4":
                # LZ4 would require additional dependency
                decompressed_data = gzip.decompress(compressed_data)  # Fallback to gzip
            else:
                raise CompressionError(
                    f"Unsupported compression algorithm: {algorithm}"
                )

            # Deserialize JSON
            trace_dict = json.loads(decompressed_data.decode("utf-8"))

            # Convert back to TraceRecord
            trace = self._dict_to_trace_record(trace_dict)

            # Update stats
            self.compression_stats["decompressions"] = (
                self.compression_stats.get("decompressions", 0) + 1
            )

            return trace

        except Exception as e:
            raise CompressionError(f"Decompression failed: {e}")

    def _dict_to_trace_record(self, trace_dict: Dict[str, Any]) -> TraceRecord:
        """Convert dictionary back to TraceRecord"""
        # This is a simplified conversion - in practice you'd need more robust parsing
        return TraceRecord(
            trace_id=trace_dict.get("trace_id"),
            trace_type=trace_dict.get("trace_type"),
            status=trace_dict.get("status"),
            start_time=(
                datetime.fromisoformat(trace_dict.get("start_time"))
                if trace_dict.get("start_time")
                else None
            ),
            end_time=(
                datetime.fromisoformat(trace_dict.get("end_time"))
                if trace_dict.get("end_time")
                else None
            ),
            duration_ms=trace_dict.get("duration_ms"),
            metadata=trace_dict.get("metadata"),
            events=trace_dict.get("events"),
            input_data=trace_dict.get("input_data"),
            output_data=trace_dict.get("output_data"),
            error_data=trace_dict.get("error_data"),
            performance_metrics=trace_dict.get("performance_metrics"),
        )

    async def compress_traces_batch(
        self, traces: List[TraceRecord], algorithm: str = "gzip"
    ) -> bytes:
        """Compress multiple traces in a batch"""
        try:
            # Serialize all traces
            traces_data = [asdict(trace) for trace in traces]
            batch_data = json.dumps(traces_data, default=str).encode("utf-8")

            # Apply compression
            if algorithm == "gzip":
                compressed_data = gzip.compress(batch_data)
            elif algorithm == "zlib":
                compressed_data = zlib.compress(batch_data)
            else:
                compressed_data = gzip.compress(batch_data)

            # Update stats
            self.compression_stats["batch_compressions"] = (
                self.compression_stats.get("batch_compressions", 0) + 1
            )

            return compressed_data

        except Exception as e:
            raise CompressionError(f"Batch compression failed: {e}")

    async def decompress_traces_batch(
        self, compressed_data: bytes, algorithm: str = "gzip"
    ) -> List[TraceRecord]:
        """Decompress multiple traces from a batch"""
        try:
            # Decompress
            if algorithm == "gzip":
                decompressed_data = gzip.decompress(compressed_data)
            elif algorithm == "zlib":
                decompressed_data = zlib.decompress(compressed_data)
            else:
                decompressed_data = gzip.decompress(compressed_data)

            # Deserialize
            traces_data = json.loads(decompressed_data.decode("utf-8"))

            # Convert to TraceRecord objects
            traces = [
                self._dict_to_trace_record(trace_dict) for trace_dict in traces_data
            ]

            # Update stats
            self.compression_stats["batch_decompressions"] = (
                self.compression_stats.get("batch_decompressions", 0) + 1
            )

            return traces

        except Exception as e:
            raise CompressionError(f"Batch decompression failed: {e}")

    def get_compression_ratio(self) -> float:
        """Get overall compression ratio"""
        bytes_compressed = self.compression_stats.get("bytes_compressed", 0)
        bytes_after = self.compression_stats.get("bytes_after_compression", 0)

        if bytes_compressed == 0:
            return 0.0

        return bytes_after / bytes_compressed

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return {
            "compressions": self.compression_stats.get("compressions", 0),
            "decompressions": self.compression_stats.get("decompressions", 0),
            "batch_compressions": self.compression_stats.get("batch_compressions", 0),
            "batch_decompressions": self.compression_stats.get(
                "batch_decompressions", 0
            ),
            "bytes_compressed": self.compression_stats.get("bytes_compressed", 0),
            "bytes_after_compression": self.compression_stats.get(
                "bytes_after_compression", 0
            ),
            "compression_ratio": self.get_compression_ratio(),
        }


class TraceCompressionOptimizer:
    """Optimizes compression settings for different trace types"""

    def __init__(self):
        self.optimization_rules = {
            "decision": {"algorithm": "gzip", "level": 6},
            "audit": {"algorithm": "zlib", "level": 9},
            "workflow": {"algorithm": "gzip", "level": 5},
            "api_call": {"algorithm": "gzip", "level": 4},
            "system_event": {"algorithm": "zlib", "level": 7},
        }

    def get_optimal_settings(self, trace_type: str) -> Dict[str, Any]:
        """Get optimal compression settings for trace type"""
        return self.optimization_rules.get(
            trace_type, {"algorithm": "gzip", "level": 6}
        )

    def analyze_trace_size(self, trace: TraceRecord) -> Dict[str, Any]:
        """Analyze trace size and recommend compression settings"""
        trace_data = json.dumps(asdict(trace), default=str)
        size_analysis = {
            "original_size_bytes": len(trace_data.encode("utf-8")),
            "estimated_compressed_size": 0,
            "compression_potential": "low",
            "recommended_algorithm": "gzip",
            "recommended_level": 6,
        }

        # Estimate compressed size
        compressed_data = gzip.compress(trace_data.encode("utf-8"))
        size_analysis["estimated_compressed_size"] = len(compressed_data)

        # Determine compression potential
        compression_ratio = len(compressed_data) / len(trace_data.encode("utf-8"))
        if compression_ratio < 0.3:
            size_analysis["compression_potential"] = "high"
        elif compression_ratio < 0.6:
            size_analysis["compression_potential"] = "medium"
        else:
            size_analysis["compression_potential"] = "low"

        return size_analysis


# Export main classes
__all__ = ["TraceCompressor", "TraceCompressionOptimizer"]
