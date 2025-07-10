"""
Chaos Replay Engine

Implements chaos engineering for the RedForge replay engine,
focusing on resilience testing under adverse conditions.
"""

import asyncio
import random
import time
import json
import traceback
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from .mutation_engine import MutationEngine, MutationType, MutationResult
from .fault_injector import FaultInjector, FaultType

class ChaosScenario(Enum):
    """Types of chaos scenarios to test"""
    # Network chaos
    NETWORK_PARTITION = "network_partition"
    SLOW_NETWORK = "slow_network"
    PACKET_LOSS = "packet_loss"
    CONNECTION_RESET = "connection_reset"
    
    # Resource chaos
    MEMORY_PRESSURE = "memory_pressure"
    CPU_SPIKE = "cpu_spike"
    DISK_FULL = "disk_full"
    FILE_DESCRIPTOR_EXHAUSTION = "fd_exhaustion"
    
    # Timing chaos
    CLOCK_SKEW = "clock_skew"
    TIMEOUT_CHAOS = "timeout_chaos"
    RACE_CONDITIONS = "race_conditions"
    
    # Data chaos
    MALFORMED_SPANS = "malformed_spans"
    CORRUPTED_PAYLOADS = "corrupted_payloads"
    GORK_DATA = "gork_data"
    ENCODING_ERRORS = "encoding_errors"
    
    # Service chaos
    DEPENDENCY_FAILURE = "dependency_failure"
    PARTIAL_FAILURE = "partial_failure"
    CASCADING_FAILURE = "cascading_failure"

@dataclass
class ChaosEvent:
    """Represents a chaos event during testing"""
    scenario: ChaosScenario
    timestamp: datetime
    duration: float
    target: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    impact_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChaosTestResult:
    """Result of a chaos test execution"""
    test_name: str
    scenarios_executed: List[ChaosEvent]
    total_duration: float
    success_rate: float
    error_count: int
    recovery_time: float
    resilience_score: float
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)

class ChaosReplayEngine:
    """
    Chaos engineering implementation for the replay engine.
    Tests resilience under various failure conditions.
    """
    
    def __init__(self, 
                 target_replay_engine: Any,
                 mutation_engine: Optional[MutationEngine] = None,
                 fault_injector: Optional[FaultInjector] = None):
        self.target_engine = target_replay_engine
        self.mutation_engine = mutation_engine or MutationEngine()
        self.fault_injector = fault_injector or FaultInjector()
        
        self.chaos_events: List[ChaosEvent] = []
        self.metrics_collector = ChaosMetricsCollector()
        
        # Chaos configuration
        self.chaos_intensity = 0.3  # 30% chaos injection rate
        self.recovery_timeout = 30.0  # 30 seconds recovery timeout
        self.max_concurrent_chaos = 3  # Max simultaneous chaos events
        
        # Scenario handlers
        self.scenario_handlers = {
            ChaosScenario.MALFORMED_SPANS: self._malformed_spans_chaos,
            ChaosScenario.CORRUPTED_PAYLOADS: self._corrupted_payloads_chaos,
            ChaosScenario.GORK_DATA: self._gork_data_chaos,
            ChaosScenario.ENCODING_ERRORS: self._encoding_errors_chaos,
            ChaosScenario.NETWORK_PARTITION: self._network_partition_chaos,
            ChaosScenario.SLOW_NETWORK: self._slow_network_chaos,
            ChaosScenario.MEMORY_PRESSURE: self._memory_pressure_chaos,
            ChaosScenario.TIMEOUT_CHAOS: self._timeout_chaos_chaos,
            ChaosScenario.RACE_CONDITIONS: self._race_conditions_chaos,
            ChaosScenario.DEPENDENCY_FAILURE: self._dependency_failure_chaos,
        }
    
    async def run_chaos_test(self, 
                           test_name: str,
                           scenarios: List[ChaosScenario],
                           test_duration: float = 60.0,
                           test_data: Optional[List[Dict[str, Any]]] = None,
                           concurrent_requests: int = 1) -> ChaosTestResult:
        """
        Execute a comprehensive chaos test.
        
        Args:
            test_name: Name of the test
            scenarios: Chaos scenarios to execute
            test_duration: Duration of the test in seconds
            test_data: Test data to replay during chaos
            concurrent_requests: Number of concurrent requests to simulate
            
        Returns:
            ChaosTestResult with detailed metrics
        """
        start_time = time.time()
        self.chaos_events.clear()
        self.metrics_collector.reset()
        
        # Prepare test data
        if test_data is None:
            test_data = self._generate_test_spans()
        
        try:
            # Start metrics collection
            self.metrics_collector.start_collection()
            
            # Execute chaos scenarios concurrently with high load support
            chaos_tasks = []
            
            # Create multiple replay tasks for concurrency testing
            replay_tasks = []
            for i in range(concurrent_requests):
                replay_task = asyncio.create_task(
                    self._replay_with_chaos(test_data, test_duration, worker_id=i)
                )
                replay_tasks.append(replay_task)
            
            # Schedule chaos events
            for scenario in scenarios:
                chaos_task = asyncio.create_task(
                    self._schedule_chaos_scenario(scenario, test_duration)
                )
                chaos_tasks.append(chaos_task)
            
            # Wait for all tasks to complete
            all_tasks = replay_tasks + chaos_tasks
            await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Stop metrics collection
            self.metrics_collector.stop_collection()
            
        except Exception as e:
            print(f"Chaos test failed: {e}")
            traceback.print_exc()
        
        # Calculate results
        total_duration = time.time() - start_time
        success_rate = self._calculate_success_rate()
        error_count = len([e for e in self.chaos_events if not e.success])
        recovery_time = self._calculate_recovery_time()
        resilience_score = self._calculate_resilience_score()
        
        return ChaosTestResult(
            test_name=test_name,
            scenarios_executed=self.chaos_events,
            total_duration=total_duration,
            success_rate=success_rate,
            error_count=error_count,
            recovery_time=recovery_time,
            resilience_score=resilience_score,
            detailed_metrics=self.metrics_collector.get_metrics()
        )
    
    async def _replay_with_chaos(self, test_data: List[Dict[str, Any]], duration: float, worker_id: int = 0):
        """Execute replay with ongoing chaos injection"""
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            for span_data in test_data:
                try:
                    # Randomly inject chaos into span data
                    if random.random() < self.chaos_intensity:
                        chaos_span = self._inject_span_chaos(span_data)
                        await self._safe_replay_span(chaos_span)
                    else:
                        await self._safe_replay_span(span_data)
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    self.metrics_collector.record_error(str(e))
                    continue
    
    async def _safe_replay_span(self, span_data: Dict[str, Any]):
        """Safely replay a span with error handling"""
        try:
            # Record attempt
            self.metrics_collector.record_replay_attempt()
            
            # Simulate replay operation (replace with actual replay logic)
            if hasattr(self.target_engine, 'replay_span'):
                await self.target_engine.replay_span(span_data)
            else:
                # Mock replay for testing
                await asyncio.sleep(0.001)
                if 'error' in span_data:
                    raise Exception(f"Simulated replay error: {span_data['error']}")
            
            self.metrics_collector.record_replay_success()
            
        except Exception as e:
            self.metrics_collector.record_replay_error(str(e))
            raise
    
    def _inject_span_chaos(self, span_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inject chaos into span data"""
        # Apply mutation
        mutation_result = self.mutation_engine.mutate(
            span_data, 
            mutation_rate=0.5,
            mutation_types=[
                MutationType.FIELD_DELETION,
                MutationType.FIELD_TYPE_CHANGE,
                MutationType.NULL_INJECTION,
                MutationType.UNICODE_CORRUPTION,
                MutationType.BOUNDARY_VALUES
            ]
        )
        
        return mutation_result.mutated_data
    
    async def _schedule_chaos_scenario(self, scenario: ChaosScenario, test_duration: float):
        """Schedule and execute a chaos scenario"""
        # Random delay before starting chaos
        delay = random.uniform(0, test_duration * 0.3)
        await asyncio.sleep(delay)
        
        # Execute scenario
        if scenario in self.scenario_handlers:
            await self.scenario_handlers[scenario]()
    
    async def _malformed_spans_chaos(self):
        """Inject malformed spans into the replay stream"""
        event = ChaosEvent(
            scenario=ChaosScenario.MALFORMED_SPANS,
            timestamp=datetime.now(),
            duration=0,
            target="replay_engine"
        )
        
        start_time = time.time()
        
        try:
            # Generate various malformed spans
            malformed_spans = [
                # Missing required fields
                {"invalid": "span", "missing": "trace_id"},
                
                # Invalid field types
                {"trace_id": 12345, "span_id": True, "timestamp": "invalid"},
                
                # Circular references
                self._create_circular_span(),
                
                # Extremely large spans
                {"trace_id": "large", "data": "X" * 1000000},
                
                # Invalid JSON structure (if serialized)
                '{"invalid": json, "missing": quote}',
                
                # Binary data in text fields
                {"trace_id": b"\\x00\\x01\\x02\\x03", "span_id": "binary_data"},
                
                # SQL injection attempts
                {"trace_id": "'; DROP TABLE spans; --", "operation": "chaos"},
                
                # XSS attempts
                {"trace_id": "<script>alert('chaos')</script>", "user_input": "xss"},
                
                # Unicode normalization attacks
                {"trace_id": "A\\u0300\\u0301\\u0302", "normalized": "chaos"},
                
                # Deeply nested structures
                self._create_deeply_nested_span(depth=1000),
            ]
            
            # Inject malformed spans
            for span in malformed_spans:
                try:
                    await self._safe_replay_span(span)
                except Exception as e:
                    # Expected to fail, record the type of failure
                    event.parameters[f"failure_{len(event.parameters)}"] = str(e)
                
                await asyncio.sleep(0.1)
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _corrupted_payloads_chaos(self):
        """Inject corrupted payloads"""
        event = ChaosEvent(
            scenario=ChaosScenario.CORRUPTED_PAYLOADS,
            timestamp=datetime.now(),
            duration=0,
            target="payload_processing"
        )
        
        start_time = time.time()
        
        try:
            # Generate corrupted payloads
            base_span = {"trace_id": "test", "span_id": "span1", "operation": "test"}
            
            for _ in range(10):
                # Apply multiple corruptions
                corrupted = base_span.copy()
                
                # Bit flip corruption
                mutation_result = self.mutation_engine.mutate(
                    corrupted, 
                    mutation_types=[MutationType.BIT_FLIP, MutationType.BYTE_CORRUPTION],
                    mutation_rate=0.8
                )
                
                try:
                    await self._safe_replay_span(mutation_result.mutated_data)
                except Exception:
                    pass  # Expected failures
                
                await asyncio.sleep(0.05)
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _gork_data_chaos(self):
        """Inject 'gork' (garbled/corrupted) data"""
        event = ChaosEvent(
            scenario=ChaosScenario.GORK_DATA,
            timestamp=datetime.now(),
            duration=0,
            target="data_processing"
        )
        
        start_time = time.time()
        
        try:
            # Generate various gork patterns
            gork_patterns = [
                # Random binary data
                {"data": b"\\x00\\x01\\x02\\x03\\xff\\xfe\\xfd"},
                
                # Invalid UTF-8 sequences
                {"data": "\\xff\\xfe\\x00\\x00"},
                
                # Mixed encoding chaos
                {"data": "UTF-8: \\xc3\\xa9, Latin-1: \\xe9, Binary: \\x00"},
                
                # Compression artifacts
                {"data": "\\x1f\\x8b\\x08\\x00\\x00\\x00\\x00\\x00"},  # GZIP header
                
                # Protocol buffer corruption
                {"data": "\\x08\\x96\\x01\\x12\\x04\\x08\\xac\\x02"},
                
                # JSON with binary injection
                {"data": '{"key": "\\x00\\x01\\x02", "value": "\\xff\\xfe"}'},
                
                # Base64 corruption
                {"data": "SGVsbG8gV29ybGQ=\\x00\\x01"},
                
                # URL encoding corruption
                {"data": "%GG%HH%II%00%01%02"},
                
                # Unicode normalization chaos
                {"data": "\\u0041\\u0300\\u0301\\u0302\\u0303"},
                
                # Control character injection
                {"data": "\\x01\\x02\\x03\\x07\\x08\\x0c\\x0e\\x0f"},
            ]
            
            for gork_data in gork_patterns:
                try:
                    # Create span with gork data
                    gork_span = {
                        "trace_id": "gork_test",
                        "span_id": f"gork_{len(event.parameters)}",
                        "operation": "gork_chaos",
                        "gork_payload": gork_data["data"]
                    }
                    
                    await self._safe_replay_span(gork_span)
                    
                except Exception as e:
                    event.parameters[f"gork_error_{len(event.parameters)}"] = str(e)
                
                await asyncio.sleep(0.1)
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _encoding_errors_chaos(self):
        """Inject encoding errors"""
        event = ChaosEvent(
            scenario=ChaosScenario.ENCODING_ERRORS,
            timestamp=datetime.now(),
            duration=0,
            target="encoding_handling"
        )
        
        start_time = time.time()
        
        try:
            encoding_attacks = [
                # UTF-8 BOM injection
                "\\ufeff" + "normal_data",
                
                # Invalid UTF-8 sequences
                "\\xc0\\x80",  # Overlong encoding
                "\\xed\\xa0\\x80",  # High surrogate
                "\\xed\\xb0\\x80",  # Low surrogate
                
                # Mixed encodings
                "UTF-8: résumé, Latin-1: \\xe9",
                
                # Null byte injection
                "data\\x00injection",
                
                # Control characters
                "\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08",
                
                # Unicode direction overrides
                "\\u202e\\u202d\\u202c",
                
                # Zero-width characters
                "\\u200b\\u200c\\u200d\\ufeff",
                
                # Emoji normalization
                "👨‍👩‍👧‍👦",  # Family emoji (multiple codepoints)
                
                # RTL/LTR marks
                "\\u200e\\u200f\\u061c",
            ]
            
            for encoding_data in encoding_attacks:
                try:
                    encoding_span = {
                        "trace_id": "encoding_test",
                        "span_id": "encoding_chaos",
                        "data": encoding_data,
                        "user_input": encoding_data
                    }
                    
                    await self._safe_replay_span(encoding_span)
                    
                except Exception as e:
                    event.parameters[f"encoding_error_{len(event.parameters)}"] = str(e)
                
                await asyncio.sleep(0.1)
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _network_partition_chaos(self):
        """Simulate network partition"""
        event = ChaosEvent(
            scenario=ChaosScenario.NETWORK_PARTITION,
            timestamp=datetime.now(),
            duration=0,
            target="network_layer"
        )
        
        start_time = time.time()
        
        try:
            # Simulate network partition by introducing delays and failures
            original_delay = getattr(self.target_engine, '_network_delay', 0)
            
            # Inject severe network delays
            if hasattr(self.target_engine, '_network_delay'):
                self.target_engine._network_delay = 5.0  # 5 second delay
            
            await asyncio.sleep(2.0)  # Partition duration
            
            # Restore network
            if hasattr(self.target_engine, '_network_delay'):
                self.target_engine._network_delay = original_delay
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _slow_network_chaos(self):
        """Simulate slow network conditions"""
        event = ChaosEvent(
            scenario=ChaosScenario.SLOW_NETWORK,
            timestamp=datetime.now(),
            duration=0,
            target="network_layer"
        )
        
        start_time = time.time()
        
        try:
            # Introduce network latency
            latency_duration = random.uniform(2.0, 5.0)
            
            # Simulate by adding delays to operations
            for _ in range(10):
                await asyncio.sleep(latency_duration / 10)
                
                # Try to process a span during slow network
                slow_span = {
                    "trace_id": "slow_network_test",
                    "span_id": f"slow_{time.time()}",
                    "operation": "network_chaos"
                }
                
                try:
                    await asyncio.wait_for(
                        self._safe_replay_span(slow_span), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    event.parameters["timeout_count"] = event.parameters.get("timeout_count", 0) + 1
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _memory_pressure_chaos(self):
        """Simulate memory pressure"""
        event = ChaosEvent(
            scenario=ChaosScenario.MEMORY_PRESSURE,
            timestamp=datetime.now(),
            duration=0,
            target="memory_system"
        )
        
        start_time = time.time()
        
        try:
            # Create memory pressure by allocating large objects
            memory_hogs = []
            
            for i in range(5):
                # Allocate large span data
                large_span = {
                    "trace_id": f"memory_pressure_{i}",
                    "span_id": f"large_span_{i}",
                    "large_data": "X" * (1024 * 1024),  # 1MB per span
                    "operation": "memory_chaos"
                }
                
                memory_hogs.append(large_span)
                
                try:
                    await self._safe_replay_span(large_span)
                except Exception as e:
                    event.parameters[f"memory_error_{i}"] = str(e)
                
                await asyncio.sleep(0.2)
            
            # Hold memory for a bit
            await asyncio.sleep(1.0)
            
            # Clean up
            memory_hogs.clear()
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _timeout_chaos_chaos(self):
        """Inject timeout scenarios"""
        event = ChaosEvent(
            scenario=ChaosScenario.TIMEOUT_CHAOS,
            timestamp=datetime.now(),
            duration=0,
            target="timeout_handling"
        )
        
        start_time = time.time()
        
        try:
            # Create spans that should trigger timeouts
            timeout_spans = [
                {
                    "trace_id": "timeout_test",
                    "span_id": "slow_operation",
                    "operation": "deliberate_delay",
                    "delay": 10.0  # 10 second delay
                },
                {
                    "trace_id": "timeout_test",
                    "span_id": "infinite_loop",
                    "operation": "infinite_operation"
                }
            ]
            
            for span in timeout_spans:
                try:
                    # Set aggressive timeout
                    await asyncio.wait_for(
                        self._safe_replay_span(span),
                        timeout=0.5  # 500ms timeout
                    )
                except asyncio.TimeoutError:
                    event.parameters["timeout_triggered"] = True
                except Exception as e:
                    event.parameters["other_error"] = str(e)
                
                await asyncio.sleep(0.1)
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _race_conditions_chaos(self):
        """Create race condition scenarios"""
        event = ChaosEvent(
            scenario=ChaosScenario.RACE_CONDITIONS,
            timestamp=datetime.now(),
            duration=0,
            target="concurrency_control"
        )
        
        start_time = time.time()
        
        try:
            # Create concurrent operations on same trace
            trace_id = "race_condition_trace"
            
            # Launch multiple concurrent operations
            tasks = []
            for i in range(10):
                span = {
                    "trace_id": trace_id,
                    "span_id": f"concurrent_span_{i}",
                    "operation": f"concurrent_op_{i}",
                    "sequence": i
                }
                
                task = asyncio.create_task(self._safe_replay_span(span))
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count exceptions
            exceptions = [r for r in results if isinstance(r, Exception)]
            event.parameters["concurrent_exceptions"] = len(exceptions)
            event.parameters["successful_operations"] = len(results) - len(exceptions)
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    async def _dependency_failure_chaos(self):
        """Simulate dependency failures"""
        event = ChaosEvent(
            scenario=ChaosScenario.DEPENDENCY_FAILURE,
            timestamp=datetime.now(),
            duration=0,
            target="dependencies"
        )
        
        start_time = time.time()
        
        try:
            # Simulate various dependency failures
            failure_spans = [
                {
                    "trace_id": "dependency_test",
                    "span_id": "db_failure",
                    "operation": "database_query",
                    "simulate_failure": "connection_refused"
                },
                {
                    "trace_id": "dependency_test", 
                    "span_id": "api_failure",
                    "operation": "external_api_call",
                    "simulate_failure": "timeout"
                },
                {
                    "trace_id": "dependency_test",
                    "span_id": "cache_failure",
                    "operation": "cache_lookup",
                    "simulate_failure": "service_unavailable"
                }
            ]
            
            for span in failure_spans:
                try:
                    await self._safe_replay_span(span)
                except Exception as e:
                    event.parameters[f"failure_{span['span_id']}"] = str(e)
                
                await asyncio.sleep(0.2)
            
            event.success = True
            
        except Exception as e:
            event.error = str(e)
            event.success = False
        
        event.duration = time.time() - start_time
        self.chaos_events.append(event)
    
    def _create_circular_span(self) -> Dict[str, Any]:
        """Create a span with circular references"""
        span = {
            "trace_id": "circular_test",
            "span_id": "circular_span",
            "operation": "circular_reference"
        }
        # Create circular reference
        span["self_reference"] = span
        return span
    
    def _create_deeply_nested_span(self, depth: int) -> Dict[str, Any]:
        """Create deeply nested span structure"""
        if depth <= 0:
            return {"leaf": True}
        
        return {
            "trace_id": "deep_nesting_test",
            "span_id": f"nested_span_{depth}",
            "operation": "deep_nesting",
            "nested": self._create_deeply_nested_span(depth - 1)
        }
    
    def _generate_test_spans(self) -> List[Dict[str, Any]]:
        """Generate basic test spans for chaos testing"""
        spans = []
        
        for i in range(20):
            span = {
                "trace_id": f"test_trace_{i // 5}",
                "span_id": f"test_span_{i}",
                "operation": f"test_operation_{i}",
                "timestamp": (datetime.now() - timedelta(seconds=i)).isoformat(),
                "duration": random.uniform(0.001, 0.1),
                "tags": {
                    "service": "test_service",
                    "version": "1.0.0",
                    "environment": "chaos_test"
                }
            }
            spans.append(span)
        
        return spans
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of chaos events"""
        if not self.chaos_events:
            return 1.0
        
        successful = len([e for e in self.chaos_events if e.success])
        return successful / len(self.chaos_events)
    
    def _calculate_recovery_time(self) -> float:
        """Calculate average recovery time"""
        recovery_times = []
        
        for event in self.chaos_events:
            if not event.success:
                # Use duration as recovery time for failed events
                recovery_times.append(event.duration)
        
        return sum(recovery_times) / len(recovery_times) if recovery_times else 0.0
    
    def _calculate_resilience_score(self) -> float:
        """Calculate overall resilience score (0-1)"""
        success_rate = self._calculate_success_rate()
        recovery_time = self._calculate_recovery_time()
        error_count = len([e for e in self.chaos_events if not e.success])
        
        # Weighted score calculation
        success_weight = 0.5
        recovery_weight = 0.3
        error_weight = 0.2
        
        # Normalize recovery time (lower is better)
        recovery_score = max(0, 1 - (recovery_time / 10.0))
        
        # Normalize error count
        error_score = max(0, 1 - (error_count / len(self.chaos_events)))
        
        resilience_score = (
            success_rate * success_weight +
            recovery_score * recovery_weight +
            error_score * error_weight
        )
        
        return min(1.0, max(0.0, resilience_score))

class ChaosMetricsCollector:
    """Collect metrics during chaos testing"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics"""
        self.metrics = {
            "replay_attempts": 0,
            "replay_successes": 0,
            "replay_errors": 0,
            "error_types": {},
            "start_time": None,
            "end_time": None,
            "collection_active": False
        }
    
    def start_collection(self):
        """Start metrics collection"""
        self.metrics["start_time"] = time.time()
        self.metrics["collection_active"] = True
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.metrics["end_time"] = time.time()
        self.metrics["collection_active"] = False
    
    def record_replay_attempt(self):
        """Record a replay attempt"""
        if self.metrics["collection_active"]:
            self.metrics["replay_attempts"] += 1
    
    def record_replay_success(self):
        """Record a successful replay"""
        if self.metrics["collection_active"]:
            self.metrics["replay_successes"] += 1
    
    def record_replay_error(self, error: str):
        """Record a replay error"""
        if self.metrics["collection_active"]:
            self.metrics["replay_errors"] += 1
            
            # Categorize error type
            error_type = type(error).__name__ if hasattr(error, '__name__') else "unknown"
            self.metrics["error_types"][error_type] = self.metrics["error_types"].get(error_type, 0) + 1
    
    def record_error(self, error: str):
        """Record a general error"""
        if self.metrics["collection_active"]:
            error_type = "general_error"
            self.metrics["error_types"][error_type] = self.metrics["error_types"].get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        metrics = self.metrics.copy()
        
        # Calculate derived metrics
        if metrics["replay_attempts"] > 0:
            metrics["success_rate"] = metrics["replay_successes"] / metrics["replay_attempts"]
            metrics["error_rate"] = metrics["replay_errors"] / metrics["replay_attempts"]
        else:
            metrics["success_rate"] = 0.0
            metrics["error_rate"] = 0.0
        
        if metrics["start_time"] and metrics["end_time"]:
            metrics["total_duration"] = metrics["end_time"] - metrics["start_time"]
            
            if metrics["total_duration"] > 0:
                metrics["attempts_per_second"] = metrics["replay_attempts"] / metrics["total_duration"]
            else:
                metrics["attempts_per_second"] = 0.0
        
        return metrics