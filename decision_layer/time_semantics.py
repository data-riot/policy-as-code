"""
Deterministic Time Semantics
Production-grade time handling with UTC normalization, clock skew, and replay consistency
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import pytz

from .errors import DecisionLayerError


class TimeSource(str, Enum):
    """Sources of time for deterministic execution"""

    SYSTEM_CLOCK = "system_clock"  # System clock (non-deterministic)
    FIXED_TIME = "fixed_time"  # Fixed time for testing
    FEATURE_STORE = "feature_store"  # Time from feature store
    EXTERNAL_API = "external_api"  # Time from external API
    NORMALIZED_UTC = "normalized_utc"  # UTC with skew correction


class ClockSkewStrategy(str, Enum):
    """Strategies for handling clock skew"""

    IGNORE = "ignore"  # Ignore skew (testing only)
    CORRECT = "correct"  # Correct skew by offset
    REJECT = "reject"  # Reject if skew exceeds threshold
    WARN = "warn"  # Warn but continue


@dataclass(frozen=True)
class TimeConfiguration:
    """Configuration for deterministic time handling"""

    # Time source configuration
    primary_source: TimeSource = TimeSource.NORMALIZED_UTC
    fallback_sources: Optional[List[TimeSource]] = None

    # Clock skew handling
    max_skew_ms: int = 5000  # 5 seconds max skew
    skew_strategy: ClockSkewStrategy = ClockSkewStrategy.CORRECT
    skew_correction_window_ms: int = 300000  # 5 minutes

    # Timezone handling
    default_timezone: str = "UTC"
    allowed_timezones: Optional[List[str]] = None

    # Replay configuration
    enable_replay_mode: bool = False
    replay_time_offset_ms: int = 0

    def __post_init__(self):
        if self.fallback_sources is None:
            object.__setattr__(self, "fallback_sources", [TimeSource.SYSTEM_CLOCK])

        if self.allowed_timezones is None:
            object.__setattr__(
                self,
                "allowed_timezones",
                ["UTC", "Europe/Helsinki", "America/New_York"],
            )


@dataclass(frozen=True)
class DeterministicTimestamp:
    """Deterministic timestamp with full metadata"""

    # Core timestamp
    timestamp: datetime

    # Source and metadata
    source: TimeSource
    timezone: str
    normalized_utc: datetime

    # Clock skew information
    clock_skew_ms: Optional[int] = None
    skew_corrected: bool = False

    # Replay information
    is_replay: bool = False
    original_timestamp: Optional[datetime] = None

    # Validation
    is_valid: bool = True
    validation_errors: Optional[List[str]] = None

    def __post_init__(self):
        if self.validation_errors is None:
            object.__setattr__(self, "validation_errors", [])

        # Ensure normalized_utc is always UTC
        if self.normalized_utc.tzinfo != timezone.utc:
            normalized = self.normalized_utc.astimezone(timezone.utc)
            object.__setattr__(self, "normalized_utc", normalized)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "timezone": self.timezone,
            "normalized_utc": self.normalized_utc.isoformat(),
            "clock_skew_ms": self.clock_skew_ms,
            "skew_corrected": self.skew_corrected,
            "is_replay": self.is_replay,
            "original_timestamp": (
                self.original_timestamp.isoformat() if self.original_timestamp else None
            ),
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


class DeterministicTimeManager:
    """Manages deterministic time for decision functions"""

    def __init__(self, config: TimeConfiguration):
        self.config = config
        self.clock_skew_history: List[Dict[str, Any]] = []
        self.replay_mode = False
        self.replay_offset_ms = 0

    def get_current_time(
        self, source: Optional[TimeSource] = None
    ) -> DeterministicTimestamp:
        """Get current deterministic time"""
        source = source or self.config.primary_source

        if self.replay_mode:
            return self._get_replay_time(source)

        if source == TimeSource.FIXED_TIME:
            return self._get_fixed_time()
        elif source == TimeSource.SYSTEM_CLOCK:
            return self._get_system_time()
        elif source == TimeSource.NORMALIZED_UTC:
            return self._get_normalized_utc_time()
        elif source == TimeSource.FEATURE_STORE:
            return self._get_feature_store_time()
        elif source == TimeSource.EXTERNAL_API:
            return self._get_external_api_time()
        else:
            raise DecisionLayerError(
                "invalid_time_source", f"Unknown time source: {source}"
            )

    def _get_fixed_time(self) -> DeterministicTimestamp:
        """Get fixed time for testing"""
        fixed_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        return DeterministicTimestamp(
            timestamp=fixed_time,
            source=TimeSource.FIXED_TIME,
            timezone="UTC",
            normalized_utc=fixed_time,
            is_replay=False,
            is_valid=True,
        )

    def _get_system_time(self) -> DeterministicTimestamp:
        """Get system clock time"""
        now = datetime.now(timezone.utc)
        return DeterministicTimestamp(
            timestamp=now,
            source=TimeSource.SYSTEM_CLOCK,
            timezone="UTC",
            normalized_utc=now,
            is_replay=False,
            is_valid=True,
        )

    def _get_normalized_utc_time(self) -> DeterministicTimestamp:
        """Get normalized UTC time with skew correction"""
        system_time = datetime.now(timezone.utc)

        # Calculate clock skew if we have reference time
        clock_skew_ms = self._calculate_clock_skew(system_time)

        # Apply skew correction if needed
        if clock_skew_ms and abs(clock_skew_ms) > 0:
            if self.config.skew_strategy == ClockSkewStrategy.CORRECT:
                corrected_time = system_time + timedelta(milliseconds=-clock_skew_ms)
                skew_corrected = True
            elif (
                self.config.skew_strategy == ClockSkewStrategy.REJECT
                and abs(clock_skew_ms) > self.config.max_skew_ms
            ):
                raise DecisionLayerError(
                    "clock_skew_exceeded",
                    f"Clock skew {clock_skew_ms}ms exceeds threshold {self.config.max_skew_ms}ms",
                )
            else:
                corrected_time = system_time
                skew_corrected = False
        else:
            corrected_time = system_time
            skew_corrected = False

        return DeterministicTimestamp(
            timestamp=system_time,
            source=TimeSource.NORMALIZED_UTC,
            timezone="UTC",
            normalized_utc=corrected_time,
            clock_skew_ms=clock_skew_ms,
            skew_corrected=skew_corrected,
            is_replay=False,
            is_valid=True,
        )

    def _get_feature_store_time(self) -> DeterministicTimestamp:
        """Get time from feature store"""
        # In production, this would query the feature store for the current time
        # For now, return system time with feature store source
        now = datetime.now(timezone.utc)
        return DeterministicTimestamp(
            timestamp=now,
            source=TimeSource.FEATURE_STORE,
            timezone="UTC",
            normalized_utc=now,
            is_replay=False,
            is_valid=True,
        )

    def _get_external_api_time(self) -> DeterministicTimestamp:
        """Get time from external API"""
        # In production, this would call an external time API
        # For now, return system time with external API source
        now = datetime.now(timezone.utc)
        return DeterministicTimestamp(
            timestamp=now,
            source=TimeSource.EXTERNAL_API,
            timezone="UTC",
            normalized_utc=now,
            is_replay=False,
            is_valid=True,
        )

    def _get_replay_time(self, source: TimeSource) -> DeterministicTimestamp:
        """Get time for replay mode"""
        # In replay mode, return the original timestamp plus offset
        original_time = datetime.now(timezone.utc)  # Would be from trace

        if self.replay_offset_ms != 0:
            replay_time = original_time + timedelta(milliseconds=self.replay_offset_ms)
        else:
            replay_time = original_time

        return DeterministicTimestamp(
            timestamp=replay_time,
            source=source,
            timezone="UTC",
            normalized_utc=replay_time,
            is_replay=True,
            original_timestamp=original_time,
            is_valid=True,
        )

    def _calculate_clock_skew(self, current_time: datetime) -> Optional[int]:
        """Calculate clock skew against reference time"""
        # In production, this would compare against NTP servers or reference clocks
        # For now, return None (no skew detected)
        return None

    def enable_replay_mode(self, offset_ms: int = 0) -> None:
        """Enable replay mode with optional time offset"""
        self.replay_mode = True
        self.replay_offset_ms = offset_ms

    def disable_replay_mode(self) -> None:
        """Disable replay mode"""
        self.replay_mode = False
        self.replay_offset_ms = 0

    def normalize_timezone(
        self, timestamp: datetime, target_timezone: str = "UTC"
    ) -> datetime:
        """Normalize timestamp to target timezone"""
        if timestamp.tzinfo is None:
            # Assume UTC if no timezone info
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        if target_timezone == "UTC":
            return timestamp.astimezone(timezone.utc)
        else:
            target_tz = pytz.timezone(target_timezone)
            return timestamp.astimezone(target_tz)

    def validate_timezone(self, timezone_str: str) -> bool:
        """Validate timezone string"""
        try:
            pytz.timezone(timezone_str)
            return (
                self.config.allowed_timezones is None
                or timezone_str in self.config.allowed_timezones
            )
        except pytz.exceptions.UnknownTimeZoneError:
            return False

    def get_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[DeterministicTimestamp]:
        """Get deterministic timestamps for a time range"""
        timestamps = []
        current = start_time

        while current <= end_time:
            # Create deterministic timestamp for each point
            dt_timestamp = DeterministicTimestamp(
                timestamp=current,
                source=self.config.primary_source,
                timezone="UTC",
                normalized_utc=current,
                is_replay=self.replay_mode,
                is_valid=True,
            )
            timestamps.append(dt_timestamp)
            current += timedelta(seconds=1)  # 1-second intervals

        return timestamps


class TimeNormalizer:
    """Utility for normalizing timestamps across different sources"""

    @staticmethod
    def normalize_to_utc(
        timestamp: Union[datetime, str], source_timezone: Optional[str] = None
    ) -> datetime:
        """Normalize any timestamp to UTC"""
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                raise DecisionLayerError(
                    "invalid_timestamp_format", f"Cannot parse timestamp: {timestamp}"
                )

        # At this point, timestamp is guaranteed to be datetime
        assert isinstance(timestamp, datetime)

        if timestamp.tzinfo is None:
            if source_timezone:
                # Apply source timezone
                source_tz = pytz.timezone(source_timezone)
                timestamp = source_tz.localize(timestamp)
            else:
                # Assume UTC
                timestamp = timestamp.replace(tzinfo=timezone.utc)

        return timestamp.astimezone(timezone.utc)

    @staticmethod
    def calculate_time_difference(start: datetime, end: datetime) -> timedelta:
        """Calculate time difference between two timestamps"""
        # Ensure both timestamps are timezone-aware
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        return end - start

    @staticmethod
    def is_within_tolerance(
        actual: datetime, expected: datetime, tolerance_ms: int = 1000
    ) -> bool:
        """Check if actual time is within tolerance of expected time"""
        diff = abs(TimeNormalizer.calculate_time_difference(actual, expected))
        return diff.total_seconds() * 1000 <= tolerance_ms


# Production time configuration
PRODUCTION_TIME_CONFIG = TimeConfiguration(
    primary_source=TimeSource.NORMALIZED_UTC,
    fallback_sources=[TimeSource.SYSTEM_CLOCK, TimeSource.FEATURE_STORE],
    max_skew_ms=5000,
    skew_strategy=ClockSkewStrategy.CORRECT,
    default_timezone="UTC",
    allowed_timezones=["UTC", "Europe/Helsinki", "America/New_York"],
    enable_replay_mode=False,
)

# Testing time configuration
TESTING_TIME_CONFIG = TimeConfiguration(
    primary_source=TimeSource.FIXED_TIME,
    fallback_sources=[TimeSource.SYSTEM_CLOCK],
    max_skew_ms=0,
    skew_strategy=ClockSkewStrategy.IGNORE,
    default_timezone="UTC",
    allowed_timezones=["UTC"],
    enable_replay_mode=True,
)


def create_time_manager(
    config: TimeConfiguration = PRODUCTION_TIME_CONFIG,
) -> DeterministicTimeManager:
    """Create a deterministic time manager"""
    return DeterministicTimeManager(config)


def create_testing_time_manager() -> DeterministicTimeManager:
    """Create a testing time manager with fixed time"""
    return DeterministicTimeManager(TESTING_TIME_CONFIG)
