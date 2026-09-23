"""
Encryption Performance Metrics Module

Tracks performance metrics for encryption/decryption operations.
Provides insights per PRD Section 8: Security Performance.

Metrics tracked:
- Encryption speed (MB/s)
- Decryption speed (MB/s)
- Average operation time
- Operations per second
- Total operations count

Storage: In-memory (production could use Redis)
"""

import time
import logging
from typing import Optional, Callable
from datetime import datetime, timezone
from collections import deque
from threading import Lock
from functools import wraps
from contextlib import contextmanager
from src.security.config_loader import get_config_int

logger = logging.getLogger(__name__)

# CONFIGURATION

def _get_max_history(db=None):
    return get_config_int("PERFORMANCE_HISTORY_SIZE", db, 1000)

def _get_slow_threshold(db=None):
    return get_config_int("SLOW_OPERATION_THRESHOLD_MS", db, 1000)

# Module-level defaults (overridden by DB)
MAX_HISTORY_SIZE = 1000
SLOW_OPERATION_THRESHOLD_MS = 1000

# Public API
__all__ = [
    'PerformanceTracker',
    'get_performance_metrics',
    'track_encryption',
    'track_decryption',
    'reset_metrics',
]


# PERFORMANCE TRACKER

class PerformanceTracker:
    """
    Thread-safe performance metrics tracker for encryption operations.
    """
    
    def __init__(self):
        self._lock = Lock()
        self._operations = {
            'encryption': deque(maxlen=MAX_HISTORY_SIZE),
            'decryption': deque(maxlen=MAX_HISTORY_SIZE),
            'hashing': deque(maxlen=MAX_HISTORY_SIZE),
            'key_rotation': deque(maxlen=MAX_HISTORY_SIZE),
        }
        self._totals = {
            'encryption_count': 0,
            'decryption_count': 0,
            'hashing_count': 0,
            'key_rotation_count': 0,
            'total_bytes_encrypted': 0,
            'total_bytes_decrypted': 0,
        }
        self._started_at = datetime.now(timezone.utc)
    
    def record_operation(
        self,
        operation_type: str,
        duration_ms: float,
        bytes_processed: int = 0,
        success: bool = True,
    ) -> None:
        """Record a completed operation."""
        with self._lock:
            if operation_type in self._operations:
                self._operations[operation_type].append({
                    'timestamp': time.time(),
                    'duration_ms': duration_ms,
                    'bytes_processed': bytes_processed,
                    'success': success,
                })
                
                # Update totals
                count_key = f"{operation_type}_count"
                if count_key in self._totals:
                    self._totals[count_key] += 1
                
                if operation_type == 'encryption':
                    self._totals['total_bytes_encrypted'] += bytes_processed
                elif operation_type == 'decryption':
                    self._totals['total_bytes_decrypted'] += bytes_processed
                
                # Log slow operations
                if duration_ms > SLOW_OPERATION_THRESHOLD_MS:
                    logger.warning(
                        f"Slow {operation_type}: {duration_ms:.2f}ms "
                        f"for {bytes_processed} bytes"
                    )
    
    def get_metrics(self, operation_type: Optional[str] = None) -> dict:
        """Get performance metrics."""
        with self._lock:
            if operation_type:
                return self._calculate_metrics_for_operation(operation_type)
            
            # Return all metrics
            all_metrics = {}
            for op_type in self._operations.keys():
                all_metrics[op_type] = self._calculate_metrics_for_operation(op_type)
            
            all_metrics['totals'] = self._totals.copy()
            all_metrics['tracker_started_at'] = self._started_at.isoformat()
            all_metrics['uptime_seconds'] = (
                datetime.now(timezone.utc) - self._started_at
            ).total_seconds()
            
            return all_metrics
    
    def _calculate_metrics_for_operation(self, operation_type: str) -> dict:
        """Calculate stats for specific operation type."""
        ops = list(self._operations.get(operation_type, []))
        
        if not ops:
            return {
                'operation': operation_type,
                'count': 0,
                'avg_duration_ms': 0,
                'min_duration_ms': 0,
                'max_duration_ms': 0,
                'p95_duration_ms': 0,
                'p99_duration_ms': 0,
                'total_bytes': 0,
                'avg_bytes_per_op': 0,
                'throughput_mbps': 0,
                'success_rate': 100,
                'recent_ops': [],
            }
        
        # Calculate stats
        durations = [op['duration_ms'] for op in ops]
        durations_sorted = sorted(durations)
        
        total_bytes = sum(op['bytes_processed'] for op in ops)
        total_time_seconds = sum(durations) / 1000
        
        success_count = sum(1 for op in ops if op['success'])
        success_rate = (success_count / len(ops)) * 100
        
        # Calculate throughput (MB/s)
        throughput_mbps = 0
        if total_time_seconds > 0 and total_bytes > 0:
            throughput_mbps = (total_bytes / (1024 * 1024)) / total_time_seconds
        
        # Percentiles
        p95_index = int(len(durations_sorted) * 0.95)
        p99_index = int(len(durations_sorted) * 0.99)
        
        return {
            'operation': operation_type,
            'count': len(ops),
            'avg_duration_ms': round(sum(durations) / len(durations), 2),
            'min_duration_ms': round(min(durations), 2),
            'max_duration_ms': round(max(durations), 2),
            'p95_duration_ms': round(durations_sorted[p95_index] if p95_index < len(durations_sorted) else durations_sorted[-1], 2),
            'p99_duration_ms': round(durations_sorted[p99_index] if p99_index < len(durations_sorted) else durations_sorted[-1], 2),
            'total_bytes': total_bytes,
            'avg_bytes_per_op': int(total_bytes / len(ops)) if ops else 0,
            'throughput_mbps': round(throughput_mbps, 2),
            'success_rate': round(success_rate, 2),
            'recent_ops': ops[-10:],  # Last 10 operations
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            for op_type in self._operations:
                self._operations[op_type].clear()
            for key in self._totals:
                self._totals[key] = 0
            self._started_at = datetime.now(timezone.utc)
            logger.info("Performance metrics reset")


# GLOBAL TRACKER INSTANCE

_tracker = PerformanceTracker()


def get_performance_metrics(operation_type: Optional[str] = None) -> dict:
    """Get current performance metrics."""
    return _tracker.get_metrics(operation_type)


def reset_metrics() -> None:
    """Reset all performance metrics."""
    _tracker.reset()


# DECORATORS (Easy tracking)

def track_encryption(func: Callable) -> Callable:
    """Decorator to track encryption performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        success = True
        result = None
        bytes_processed = 0
        
        try:
            result = func(*args, **kwargs)
            
            # Try to get bytes from args or result
            if args and isinstance(args[0], (bytes, bytearray)):
                bytes_processed = len(args[0])
            elif result and isinstance(result, (bytes, bytearray)):
                bytes_processed = len(result)
            
            return result
            
        except Exception as e:
            success = False
            raise
        
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _tracker.record_operation(
                'encryption',
                duration_ms=duration_ms,
                bytes_processed=bytes_processed,
                success=success,
            )
    
    return wrapper


def track_decryption(func: Callable) -> Callable:
    """Decorator to track decryption performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        success = True
        result = None
        bytes_processed = 0
        
        try:
            result = func(*args, **kwargs)
            
            if args and isinstance(args[0], (bytes, bytearray)):
                bytes_processed = len(args[0])
            elif result and isinstance(result, (bytes, bytearray)):
                bytes_processed = len(result)
            
            return result
            
        except Exception as e:
            success = False
            raise
        
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            _tracker.record_operation(
                'decryption',
                duration_ms=duration_ms,
                bytes_processed=bytes_processed,
                success=success,
            )
    
    return wrapper


@contextmanager
def track_operation(operation_type: str, bytes_processed: int = 0):
    """
    Context manager for tracking custom operations.
    
    Example:
        with track_operation('key_rotation'):
            rotate_file_key(...)
    """
    start_time = time.perf_counter()
    success = True
    
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _tracker.record_operation(
            operation_type,
            duration_ms=duration_ms,
            bytes_processed=bytes_processed,
            success=success,
        )


# CLI HELPER

def print_metrics_summary() -> None:
    """Print performance metrics in human-readable format."""
    metrics = get_performance_metrics()
    
    print("\n" + "=" * 70)
    print("⚡ TRUSTSHARE ENCRYPTION PERFORMANCE METRICS")
    print("=" * 70)
    
    print(f"\n📊 Overall Stats:")
    print(f"   Uptime: {metrics['uptime_seconds']:.0f} seconds")
    print(f"   Started: {metrics['tracker_started_at']}")
    
    print(f"\n📈 Totals:")
    totals = metrics['totals']
    print(f"   Total encryptions: {totals['encryption_count']}")
    print(f"   Total decryptions: {totals['decryption_count']}")
    print(f"   Total bytes encrypted: {totals['total_bytes_encrypted']:,}")
    print(f"   Total bytes decrypted: {totals['total_bytes_decrypted']:,}")
    
    for op_type in ['encryption', 'decryption', 'hashing', 'key_rotation']:
        op_metrics = metrics.get(op_type, {})
        if op_metrics.get('count', 0) > 0:
            print(f"\n⚡ {op_type.upper()}:")
            print(f"   Operations: {op_metrics['count']}")
            print(f"   Avg time: {op_metrics['avg_duration_ms']}ms")
            print(f"   P95 time: {op_metrics['p95_duration_ms']}ms")
            print(f"   P99 time: {op_metrics['p99_duration_ms']}ms")
            print(f"   Throughput: {op_metrics['throughput_mbps']} MB/s")
            print(f"   Success rate: {op_metrics['success_rate']}%")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    print_metrics_summary()