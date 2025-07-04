"""
Fault Injector for Chaos Testing

Provides systematic fault injection capabilities for testing system resilience
under various failure conditions.
"""

import asyncio
import random
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta


class FaultType(Enum):
    """Types of faults that can be injected"""
    # Network faults
    NETWORK_DELAY = "network_delay"
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_PARTITION = "network_partition"
    PACKET_LOSS = "packet_loss"
    CONNECTION_RESET = "connection_reset"
    
    # Resource faults
    MEMORY_EXHAUSTION = "memory_exhaustion"
    CPU_SPIKE = "cpu_spike"
    DISK_FULL = "disk_full"
    FILE_DESCRIPTOR_LIMIT = "fd_limit"
    
    # Service faults
    SERVICE_UNAVAILABLE = "service_unavailable"
    SLOW_RESPONSE = "slow_response"
    PARTIAL_FAILURE = "partial_failure"
    CASCADE_FAILURE = "cascade_failure"
    
    # Data faults
    DATA_CORRUPTION = "data_corruption"
    SERIALIZATION_ERROR = "serialization_error"
    ENCODING_ERROR = "encoding_error"
    
    # Timing faults
    CLOCK_SKEW = "clock_skew"
    RACE_CONDITION = "race_condition"
    DEADLOCK = "deadlock"


@dataclass
class FaultInjectionResult:
    """Result of fault injection"""
    fault_type: FaultType
    target: str
    parameters: Dict[str, Any]
    start_time: datetime
    duration: float
    success: bool
    error: Optional[str] = None
    impact_metrics: Dict[str, Any] = None


class FaultInjector:
    """
    Systematic fault injection for chaos testing.
    Provides controlled failure scenarios to test system resilience.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)
        self.active_faults: List[FaultInjectionResult] = []
        
        # Fault injection strategies
        self.fault_strategies = {
            FaultType.NETWORK_DELAY: self._inject_network_delay,
            FaultType.NETWORK_TIMEOUT: self._inject_network_timeout,
            FaultType.NETWORK_PARTITION: self._inject_network_partition,
            FaultType.PACKET_LOSS: self._inject_packet_loss,
            FaultType.CONNECTION_RESET: self._inject_connection_reset,
            FaultType.MEMORY_EXHAUSTION: self._inject_memory_exhaustion,
            FaultType.CPU_SPIKE: self._inject_cpu_spike,
            FaultType.DISK_FULL: self._inject_disk_full,
            FaultType.SERVICE_UNAVAILABLE: self._inject_service_unavailable,
            FaultType.SLOW_RESPONSE: self._inject_slow_response,
            FaultType.DATA_CORRUPTION: self._inject_data_corruption,
            FaultType.CLOCK_SKEW: self._inject_clock_skew,
            FaultType.RACE_CONDITION: self._inject_race_condition,
        }
        
        # Default fault parameters
        self.default_parameters = {
            FaultType.NETWORK_DELAY: {"delay_ms": 1000, "jitter_ms": 200},
            FaultType.NETWORK_TIMEOUT: {"timeout_ms": 5000},
            FaultType.NETWORK_PARTITION: {"duration_s": 10},
            FaultType.PACKET_LOSS: {"loss_rate": 0.1},
            FaultType.MEMORY_EXHAUSTION: {"memory_mb": 100},
            FaultType.CPU_SPIKE: {"cpu_percent": 90, "duration_s": 5},
            FaultType.SERVICE_UNAVAILABLE: {"error_rate": 1.0},
            FaultType.SLOW_RESPONSE: {"delay_ms": 2000},
        }
    
    async def inject_fault(self, 
                          fault_type: FaultType, 
                          target: str,
                          parameters: Optional[Dict[str, Any]] = None,
                          duration: float = 10.0) -> FaultInjectionResult:
        """
        Inject a specific fault into the target system.
        
        Args:
            fault_type: Type of fault to inject
            target: Target component or system
            parameters: Fault-specific parameters
            duration: Duration to maintain the fault
            
        Returns:
            FaultInjectionResult with injection details
        """
        if parameters is None:
            parameters = self.default_parameters.get(fault_type, {})
        
        start_time = datetime.now()
        
        try:
            if fault_type in self.fault_strategies:
                await self.fault_strategies[fault_type](target, parameters, duration)
                success = True
                error = None
            else:
                success = False
                error = f"Unknown fault type: {fault_type}"
                
        except Exception as e:
            success = False
            error = str(e)
        
        result = FaultInjectionResult(
            fault_type=fault_type,
            target=target,
            parameters=parameters,
            start_time=start_time,
            duration=time.time() - start_time.timestamp(),
            success=success,
            error=error,
            impact_metrics={}
        )
        
        self.active_faults.append(result)
        return result
    
    async def inject_random_fault(self, 
                                 target: str,
                                 fault_types: Optional[List[FaultType]] = None,
                                 duration: float = 10.0) -> FaultInjectionResult:
        """Inject a random fault from the available types"""
        if fault_types is None:
            fault_types = list(FaultType)
        
        fault_type = self.random.choice(fault_types)
        return await self.inject_fault(fault_type, target, duration=duration)
    
    async def inject_fault_sequence(self,
                                   target: str,
                                   fault_sequence: List[FaultType],
                                   interval: float = 5.0) -> List[FaultInjectionResult]:
        """Inject a sequence of faults with intervals"""
        results = []
        
        for fault_type in fault_sequence:
            result = await self.inject_fault(fault_type, target)
            results.append(result)
            await asyncio.sleep(interval)
        
        return results
    
    async def inject_concurrent_faults(self,
                                      targets: List[str],
                                      fault_types: List[FaultType],
                                      duration: float = 10.0) -> List[FaultInjectionResult]:
        """Inject multiple faults concurrently"""
        tasks = []
        
        for target, fault_type in zip(targets, fault_types):
            task = asyncio.create_task(
                self.inject_fault(fault_type, target, duration=duration)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, FaultInjectionResult)]
    
    # Fault injection implementations
    
    async def _inject_network_delay(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject network delay"""
        delay_ms = parameters.get("delay_ms", 1000)
        jitter_ms = parameters.get("jitter_ms", 200)
        
        # Simulate network delay for duration
        end_time = time.time() + duration
        while time.time() < end_time:
            actual_delay = delay_ms + self.random.uniform(-jitter_ms, jitter_ms)
            await asyncio.sleep(actual_delay / 1000.0)
            await asyncio.sleep(0.1)  # Small interval between delays
    
    async def _inject_network_timeout(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject network timeout"""
        timeout_ms = parameters.get("timeout_ms", 5000)
        
        # Simulate timeout by waiting longer than expected
        await asyncio.sleep(timeout_ms / 1000.0)
    
    async def _inject_network_partition(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject network partition"""
        partition_duration = parameters.get("duration_s", duration)
        
        # Simulate network partition by blocking communication
        await asyncio.sleep(partition_duration)
    
    async def _inject_packet_loss(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject packet loss"""
        loss_rate = parameters.get("loss_rate", 0.1)
        
        # Simulate packet loss for duration
        end_time = time.time() + duration
        while time.time() < end_time:
            if self.random.random() < loss_rate:
                # Simulate dropped packet
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.05)
    
    async def _inject_connection_reset(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject connection reset"""
        # Simulate connection reset
        await asyncio.sleep(0.1)
        raise ConnectionResetError(f"Connection reset for {target}")
    
    async def _inject_memory_exhaustion(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject memory exhaustion"""
        memory_mb = parameters.get("memory_mb", 100)
        
        # Allocate large amount of memory
        memory_hog = []
        try:
            for _ in range(memory_mb):
                # Allocate 1MB chunks
                memory_hog.append(b'0' * (1024 * 1024))
            
            await asyncio.sleep(duration)
        finally:
            # Clean up memory
            memory_hog.clear()
    
    async def _inject_cpu_spike(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject CPU spike"""
        cpu_percent = parameters.get("cpu_percent", 90)
        spike_duration = parameters.get("duration_s", duration)
        
        # Simulate CPU spike with busy loop
        end_time = time.time() + spike_duration
        while time.time() < end_time:
            # Busy loop to consume CPU
            for _ in range(10000):
                _ = sum(range(100))
            await asyncio.sleep(0.001)  # Brief yield
    
    async def _inject_disk_full(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject disk full condition"""
        # Simulate disk full error
        await asyncio.sleep(0.1)
        raise OSError("No space left on device")
    
    async def _inject_service_unavailable(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject service unavailable"""
        error_rate = parameters.get("error_rate", 1.0)
        
        # Return service unavailable for duration
        end_time = time.time() + duration
        while time.time() < end_time:
            if self.random.random() < error_rate:
                raise Exception(f"Service {target} unavailable")
            await asyncio.sleep(0.1)
    
    async def _inject_slow_response(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject slow response"""
        delay_ms = parameters.get("delay_ms", 2000)
        
        # Add significant delay to responses
        await asyncio.sleep(delay_ms / 1000.0)
    
    async def _inject_data_corruption(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject data corruption"""
        corruption_rate = parameters.get("corruption_rate", 0.1)
        
        # Simulate data corruption
        if self.random.random() < corruption_rate:
            raise ValueError(f"Data corruption detected in {target}")
    
    async def _inject_clock_skew(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject clock skew"""
        skew_seconds = parameters.get("skew_seconds", 300)  # 5 minutes
        
        # Simulate clock skew by introducing timestamp inconsistencies
        await asyncio.sleep(duration)
    
    async def _inject_race_condition(self, target: str, parameters: Dict[str, Any], duration: float):
        """Inject race condition"""
        # Simulate race condition with random delays
        delay = self.random.uniform(0.001, 0.1)
        await asyncio.sleep(delay)
    
    def get_active_faults(self) -> List[FaultInjectionResult]:
        """Get list of currently active faults"""
        return self.active_faults.copy()
    
    def clear_faults(self):
        """Clear all fault injection history"""
        self.active_faults.clear()
    
    def get_fault_statistics(self) -> Dict[str, Any]:
        """Get statistics about injected faults"""
        if not self.active_faults:
            return {"total_faults": 0}
        
        fault_counts = {}
        success_count = 0
        total_duration = 0
        
        for fault in self.active_faults:
            fault_type = fault.fault_type.value
            fault_counts[fault_type] = fault_counts.get(fault_type, 0) + 1
            if fault.success:
                success_count += 1
            total_duration += fault.duration
        
        return {
            "total_faults": len(self.active_faults),
            "fault_type_distribution": fault_counts,
            "success_rate": success_count / len(self.active_faults),
            "average_duration": total_duration / len(self.active_faults),
            "total_duration": total_duration
        }
    
    def recommend_fault_sequence(self, target_resilience: str) -> List[FaultType]:
        """Recommend fault sequence based on target resilience testing"""
        sequences = {
            "network": [
                FaultType.NETWORK_DELAY,
                FaultType.PACKET_LOSS,
                FaultType.NETWORK_PARTITION,
                FaultType.CONNECTION_RESET
            ],
            "resource": [
                FaultType.MEMORY_EXHAUSTION,
                FaultType.CPU_SPIKE,
                FaultType.DISK_FULL
            ],
            "service": [
                FaultType.SERVICE_UNAVAILABLE,
                FaultType.SLOW_RESPONSE,
                FaultType.PARTIAL_FAILURE
            ],
            "comprehensive": [
                FaultType.NETWORK_DELAY,
                FaultType.MEMORY_EXHAUSTION,
                FaultType.SERVICE_UNAVAILABLE,
                FaultType.DATA_CORRUPTION,
                FaultType.RACE_CONDITION
            ]
        }
        
        return sequences.get(target_resilience, sequences["comprehensive"])


class ChaosMonkey(FaultInjector):
    """
    Extended fault injector that implements chaos monkey patterns
    for continuous fault injection.
    """
    
    def __init__(self, seed: Optional[int] = None):
        super().__init__(seed)
        self.chaos_enabled = False
        self.chaos_task = None
        self.chaos_intensity = 0.1  # 10% chance per interval
        self.chaos_interval = 30.0  # 30 seconds
    
    async def start_chaos_monkey(self, 
                                targets: List[str],
                                fault_types: Optional[List[FaultType]] = None,
                                intensity: float = 0.1,
                                interval: float = 30.0):
        """Start continuous chaos injection"""
        self.chaos_enabled = True
        self.chaos_intensity = intensity
        self.chaos_interval = interval
        
        if fault_types is None:
            fault_types = [
                FaultType.NETWORK_DELAY,
                FaultType.SERVICE_UNAVAILABLE,
                FaultType.SLOW_RESPONSE
            ]
        
        self.chaos_task = asyncio.create_task(
            self._chaos_loop(targets, fault_types)
        )
    
    async def stop_chaos_monkey(self):
        """Stop continuous chaos injection"""
        self.chaos_enabled = False
        if self.chaos_task:
            self.chaos_task.cancel()
            try:
                await self.chaos_task
            except asyncio.CancelledError:
                pass
    
    async def _chaos_loop(self, targets: List[str], fault_types: List[FaultType]):
        """Main chaos monkey loop"""
        while self.chaos_enabled:
            try:
                # Randomly decide whether to inject chaos
                if self.random.random() < self.chaos_intensity:
                    target = self.random.choice(targets)
                    fault_type = self.random.choice(fault_types)
                    
                    # Inject fault with short duration
                    await self.inject_fault(
                        fault_type, 
                        target, 
                        duration=min(self.chaos_interval, 10.0)
                    )
                
                await asyncio.sleep(self.chaos_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Chaos monkey error: {e}")
                await asyncio.sleep(1.0)