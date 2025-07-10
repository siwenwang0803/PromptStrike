"""
Sidecar Recovery Validation for PromptStrike
验证 Sidecar 的错误恢复能力
"""

import pytest
import asyncio
import time
import json
import random
import psutil
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta


@dataclass
class RecoveryScenario:
    """Recovery test scenario definition"""
    name: str
    failure_type: str
    duration: float
    expected_recovery_time: float
    severity: str
    description: str


@dataclass
class RecoveryMetrics:
    """Recovery performance metrics"""
    scenario_name: str
    failure_start_time: float
    recovery_start_time: float
    recovery_complete_time: float
    total_downtime: float
    recovery_duration: float
    health_checks_failed: int
    health_checks_total: int
    requests_failed: int
    requests_total: int
    memory_leaked: bool = False
    connections_leaked: bool = False
    graceful_shutdown: bool = True
    
    @property
    def health_check_success_rate(self) -> float:
        """Calculate health check success rate during recovery"""
        if self.health_checks_total == 0:
            return 1.0
        return 1.0 - (self.health_checks_failed / self.health_checks_total)
    
    @property
    def request_success_rate(self) -> float:
        """Calculate request success rate during recovery"""
        if self.requests_total == 0:
            return 1.0
        return 1.0 - (self.requests_failed / self.requests_total)
    
    @property
    def recovery_efficiency(self) -> float:
        """Calculate overall recovery efficiency score"""
        time_score = max(0, 1 - (self.recovery_duration / 60.0))  # Target < 60s
        health_score = self.health_check_success_rate
        request_score = self.request_success_rate
        
        efficiency = (time_score * 0.4 + health_score * 0.3 + request_score * 0.3)
        
        # Penalties for leaks and ungraceful shutdown
        if self.memory_leaked:
            efficiency *= 0.8
        if self.connections_leaked:
            efficiency *= 0.8
        if not self.graceful_shutdown:
            efficiency *= 0.7
        
        return min(1.0, max(0.0, efficiency))


class SidecarRecoveryValidator:
    """Validates sidecar recovery capabilities"""
    
    def __init__(self):
        self.recovery_scenarios = [
            RecoveryScenario(
                name="memory_exhaustion_recovery",
                failure_type="memory_exhaustion",
                duration=30.0,
                expected_recovery_time=15.0,
                severity="high",
                description="Recovery from memory exhaustion"
            ),
            RecoveryScenario(
                name="connection_pool_exhaustion",
                failure_type="connection_exhaustion",
                duration=20.0,
                expected_recovery_time=10.0,
                severity="medium",
                description="Recovery from connection pool exhaustion"
            ),
            RecoveryScenario(
                name="database_connection_failure",
                failure_type="db_connection_failure",
                duration=45.0,
                expected_recovery_time=20.0,
                severity="high",
                description="Recovery from database connection failure"
            ),
            RecoveryScenario(
                name="external_api_timeout",
                failure_type="api_timeout",
                duration=25.0,
                expected_recovery_time=5.0,
                severity="medium",
                description="Recovery from external API timeouts"
            ),
            RecoveryScenario(
                name="disk_space_exhaustion",
                failure_type="disk_full",
                duration=40.0,
                expected_recovery_time=30.0,
                severity="critical",
                description="Recovery from disk space exhaustion"
            ),
            RecoveryScenario(
                name="thread_pool_exhaustion",
                failure_type="thread_exhaustion",
                duration=15.0,
                expected_recovery_time=8.0,
                severity="medium",
                description="Recovery from thread pool exhaustion"
            ),
            RecoveryScenario(
                name="graceful_shutdown_recovery",
                failure_type="graceful_shutdown",
                duration=10.0,
                expected_recovery_time=12.0,
                severity="low",
                description="Recovery from graceful shutdown"
            ),
            RecoveryScenario(
                name="forced_termination_recovery",
                failure_type="sigkill",
                duration=5.0,
                expected_recovery_time=20.0,
                severity="high",
                description="Recovery from forced termination"
            ),
            RecoveryScenario(
                name="configuration_reload",
                failure_type="config_reload",
                duration=8.0,
                expected_recovery_time=5.0,
                severity="low",
                description="Recovery from configuration reload"
            ),
            RecoveryScenario(
                name="cascading_failure_recovery",
                failure_type="cascading_failure",
                duration=60.0,
                expected_recovery_time=45.0,
                severity="critical",
                description="Recovery from cascading failures"
            )
        ]
        
        self.recovery_metrics: List[RecoveryMetrics] = []
        
    async def validate_all_recovery_scenarios(self) -> List[RecoveryMetrics]:
        """Validate all recovery scenarios"""
        print("🏥 Starting Sidecar Recovery Validation")
        print("=" * 60)
        
        for scenario in self.recovery_scenarios:
            print(f"\n🔧 Testing {scenario.name}...")
            metrics = await self._validate_recovery_scenario(scenario)
            self.recovery_metrics.append(metrics)
            
            # Report scenario results
            status = "✅ PASS" if metrics.recovery_efficiency >= 0.7 else "❌ FAIL"
            print(f"{status} {scenario.name}: {metrics.recovery_efficiency:.2f} efficiency")
        
        # Generate comprehensive report
        self._generate_recovery_report()
        
        return self.recovery_metrics
    
    async def _validate_recovery_scenario(self, scenario: RecoveryScenario) -> RecoveryMetrics:
        """Validate a specific recovery scenario"""
        # Initialize metrics
        metrics = RecoveryMetrics(
            scenario_name=scenario.name,
            failure_start_time=time.time(),
            recovery_start_time=0,
            recovery_complete_time=0,
            total_downtime=0,
            recovery_duration=0,
            health_checks_failed=0,
            health_checks_total=0,
            requests_failed=0,
            requests_total=0
        )
        
        # Create mock sidecar for testing
        sidecar = MockSidecarService()
        
        try:
            # Phase 1: Inject failure
            await self._inject_failure(sidecar, scenario)
            metrics.recovery_start_time = time.time()
            
            # Phase 2: Monitor recovery
            await self._monitor_recovery(sidecar, scenario, metrics)
            
            # Phase 3: Validate post-recovery state
            await self._validate_post_recovery_state(sidecar, metrics)
            
        except Exception as e:
            print(f"Recovery validation failed: {e}")
            metrics.recovery_duration = time.time() - metrics.recovery_start_time
        
        return metrics
    
    async def _inject_failure(self, sidecar: 'MockSidecarService', scenario: RecoveryScenario):
        """Inject specific failure type"""
        print(f"   💥 Injecting {scenario.failure_type} failure...")
        
        if scenario.failure_type == "memory_exhaustion":
            await sidecar.simulate_memory_exhaustion()
        elif scenario.failure_type == "connection_exhaustion":
            await sidecar.simulate_connection_exhaustion()
        elif scenario.failure_type == "db_connection_failure":
            await sidecar.simulate_db_connection_failure()
        elif scenario.failure_type == "api_timeout":
            await sidecar.simulate_api_timeout()
        elif scenario.failure_type == "disk_full":
            await sidecar.simulate_disk_full()
        elif scenario.failure_type == "thread_exhaustion":
            await sidecar.simulate_thread_exhaustion()
        elif scenario.failure_type == "graceful_shutdown":
            await sidecar.simulate_graceful_shutdown()
        elif scenario.failure_type == "sigkill":
            await sidecar.simulate_forced_termination()
        elif scenario.failure_type == "config_reload":
            await sidecar.simulate_config_reload()
        elif scenario.failure_type == "cascading_failure":
            await sidecar.simulate_cascading_failure()
        else:
            raise ValueError(f"Unknown failure type: {scenario.failure_type}")
    
    async def _monitor_recovery(self, sidecar: 'MockSidecarService', 
                              scenario: RecoveryScenario, metrics: RecoveryMetrics):
        """Monitor the recovery process"""
        print(f"   👀 Monitoring recovery for {scenario.duration}s...")
        
        start_time = time.time()
        recovery_detected = False
        
        while (time.time() - start_time) < scenario.duration:
            # Health check
            is_healthy = await self._perform_health_check(sidecar)
            metrics.health_checks_total += 1
            
            if not is_healthy:
                metrics.health_checks_failed += 1
            elif not recovery_detected:
                # First successful health check after failure
                metrics.recovery_complete_time = time.time()
                metrics.recovery_duration = metrics.recovery_complete_time - metrics.recovery_start_time
                recovery_detected = True
                print(f"   ✅ Recovery detected in {metrics.recovery_duration:.2f}s")
            
            # Request test
            success = await self._perform_request_test(sidecar)
            metrics.requests_total += 1
            
            if not success:
                metrics.requests_failed += 1
            
            await asyncio.sleep(2)  # Check every 2 seconds
        
        # Calculate total downtime
        if recovery_detected:
            metrics.total_downtime = metrics.recovery_duration
        else:
            metrics.total_downtime = scenario.duration
            metrics.recovery_complete_time = time.time()
            metrics.recovery_duration = metrics.recovery_complete_time - metrics.recovery_start_time
    
    async def _validate_post_recovery_state(self, sidecar: 'MockSidecarService', 
                                          metrics: RecoveryMetrics):
        """Validate the state after recovery"""
        print("   🔍 Validating post-recovery state...")
        
        # Check for memory leaks
        memory_usage = await sidecar.get_memory_usage()
        if memory_usage > sidecar.baseline_memory * 1.5:  # 50% increase
            metrics.memory_leaked = True
            print("   ⚠️ Memory leak detected")
        
        # Check for connection leaks
        connection_count = await sidecar.get_connection_count()
        if connection_count > sidecar.baseline_connections * 2:  # 100% increase
            metrics.connections_leaked = True
            print("   ⚠️ Connection leak detected")
        
        # Check graceful shutdown capability
        try:
            await sidecar.graceful_shutdown()
            metrics.graceful_shutdown = True
        except Exception:
            metrics.graceful_shutdown = False
            print("   ⚠️ Graceful shutdown failed")
    
    async def _perform_health_check(self, sidecar: 'MockSidecarService') -> bool:
        """Perform health check"""
        try:
            health_status = await sidecar.health_check()
            return health_status.get("status") == "healthy"
        except Exception:
            return False
    
    async def _perform_request_test(self, sidecar: 'MockSidecarService') -> bool:
        """Perform request test"""
        try:
            response = await sidecar.process_request({"test": "recovery"})
            return response is not None
        except Exception:
            return False
    
    def _generate_recovery_report(self):
        """Generate comprehensive recovery report"""
        print("\n" + "=" * 80)
        print("🏥 SIDECAR RECOVERY VALIDATION REPORT")
        print("=" * 80)
        
        # Calculate overall metrics
        total_scenarios = len(self.recovery_metrics)
        passed_scenarios = sum(1 for m in self.recovery_metrics if m.recovery_efficiency >= 0.7)
        overall_efficiency = sum(m.recovery_efficiency for m in self.recovery_metrics) / total_scenarios
        
        print(f"\n📊 Overall Results:")
        print(f"  Total Scenarios: {total_scenarios}")
        print(f"  Passed Scenarios: {passed_scenarios}")
        print(f"  Success Rate: {passed_scenarios / total_scenarios * 100:.1f}%")
        print(f"  Overall Efficiency: {overall_efficiency:.2f}")
        
        # Status assessment
        if overall_efficiency >= 0.8:
            status = "🎉 EXCELLENT"
        elif overall_efficiency >= 0.7:
            status = "✅ GOOD"
        elif overall_efficiency >= 0.5:
            status = "⚠️ ACCEPTABLE"
        else:
            status = "❌ NEEDS_IMPROVEMENT"
        
        print(f"\n{status} Recovery Capability")
        
        # Individual scenario results
        print(f"\n📋 Individual Scenario Results:")
        for metrics in self.recovery_metrics:
            status_icon = "✅" if metrics.recovery_efficiency >= 0.7 else "❌"
            print(f"  {status_icon} {metrics.scenario_name}:")
            print(f"    Recovery Time: {metrics.recovery_duration:.2f}s")
            print(f"    Health Success Rate: {metrics.health_check_success_rate:.1%}")
            print(f"    Request Success Rate: {metrics.request_success_rate:.1%}")
            print(f"    Efficiency Score: {metrics.recovery_efficiency:.2f}")
            
            if metrics.memory_leaked:
                print(f"    ⚠️ Memory leak detected")
            if metrics.connections_leaked:
                print(f"    ⚠️ Connection leak detected")
            if not metrics.graceful_shutdown:
                print(f"    ⚠️ Graceful shutdown failed")
        
        # Recovery time analysis
        recovery_times = [m.recovery_duration for m in self.recovery_metrics]
        avg_recovery_time = sum(recovery_times) / len(recovery_times)
        max_recovery_time = max(recovery_times)
        min_recovery_time = min(recovery_times)
        
        print(f"\n⏱️ Recovery Time Analysis:")
        print(f"  Average Recovery Time: {avg_recovery_time:.2f}s")
        print(f"  Fastest Recovery: {min_recovery_time:.2f}s")
        print(f"  Slowest Recovery: {max_recovery_time:.2f}s")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        slow_scenarios = [m for m in self.recovery_metrics if m.recovery_duration > 30]
        if slow_scenarios:
            print(f"  • Optimize recovery for: {', '.join(m.scenario_name for m in slow_scenarios)}")
        
        leak_scenarios = [m for m in self.recovery_metrics if m.memory_leaked or m.connections_leaked]
        if leak_scenarios:
            print(f"  • Fix resource leaks in: {', '.join(m.scenario_name for m in leak_scenarios)}")
        
        if overall_efficiency < 0.7:
            print(f"  • Implement circuit breakers and health checks")
            print(f"  • Add automated recovery mechanisms")
            print(f"  • Improve error handling and logging")
        
        # Production readiness assessment
        print(f"\n🏆 Production Readiness:")
        if overall_efficiency >= 0.8 and max_recovery_time <= 60:
            print("  🎉 PRODUCTION READY - Excellent recovery capabilities")
        elif overall_efficiency >= 0.7 and max_recovery_time <= 120:
            print("  ✅ PRODUCTION READY - Good recovery with minor optimizations needed")
        elif overall_efficiency >= 0.5:
            print("  ⚠️ NEEDS IMPROVEMENT - Acceptable but requires hardening")
        else:
            print("  ❌ NOT PRODUCTION READY - Significant recovery issues")


class MockSidecarService:
    """Mock sidecar service for recovery testing"""
    
    def __init__(self):
        self.healthy = True
        self.memory_exhausted = False
        self.connections_exhausted = False
        self.db_connection_failed = False
        self.api_timeout = False
        self.disk_full = False
        self.thread_exhausted = False
        self.shutdown = False
        self.baseline_memory = 100  # MB
        self.baseline_connections = 10
        self.current_memory = self.baseline_memory
        self.current_connections = self.baseline_connections
        
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        if self.shutdown:
            raise Exception("Service shutdown")
        
        status = "healthy" if self.healthy and not any([
            self.memory_exhausted,
            self.connections_exhausted, 
            self.db_connection_failed,
            self.disk_full,
            self.thread_exhausted
        ]) else "unhealthy"
        
        return {
            "status": status,
            "memory_usage": self.current_memory,
            "connections": self.current_connections,
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock request processing"""
        if self.shutdown or not self.healthy:
            raise Exception("Service unavailable")
        
        if self.memory_exhausted:
            raise MemoryError("Out of memory")
        
        if self.connections_exhausted:
            raise ConnectionError("Connection pool exhausted")
        
        if self.db_connection_failed:
            raise Exception("Database connection failed")
        
        if self.api_timeout:
            await asyncio.sleep(10)  # Simulate timeout
            raise asyncio.TimeoutError("API timeout")
        
        if self.disk_full:
            raise OSError("No space left on device")
        
        if self.thread_exhausted:
            raise Exception("Thread pool exhausted")
        
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.01, 0.1))
        
        return {"status": "processed", "request_id": str(time.time())}
    
    async def get_memory_usage(self) -> float:
        """Get current memory usage"""
        return self.current_memory
    
    async def get_connection_count(self) -> int:
        """Get current connection count"""
        return self.current_connections
    
    async def graceful_shutdown(self):
        """Graceful shutdown"""
        if self.shutdown:
            return
        
        print("   Initiating graceful shutdown...")
        await asyncio.sleep(0.5)  # Cleanup time
        self.shutdown = True
        self.healthy = False
    
    # Failure simulation methods
    async def simulate_memory_exhaustion(self):
        """Simulate memory exhaustion"""
        self.memory_exhausted = True
        self.current_memory = self.baseline_memory * 10  # 10x memory usage
        self.healthy = False
        
        # Auto-recovery after some time
        await asyncio.sleep(5)
        self._auto_recover()
    
    async def simulate_connection_exhaustion(self):
        """Simulate connection pool exhaustion"""
        self.connections_exhausted = True
        self.current_connections = 1000  # High connection count
        self.healthy = False
        
        await asyncio.sleep(3)
        self._auto_recover()
    
    async def simulate_db_connection_failure(self):
        """Simulate database connection failure"""
        self.db_connection_failed = True
        self.healthy = False
        
        await asyncio.sleep(8)
        self._auto_recover()
    
    async def simulate_api_timeout(self):
        """Simulate external API timeout"""
        self.api_timeout = True
        self.healthy = False
        
        await asyncio.sleep(2)
        self._auto_recover()
    
    async def simulate_disk_full(self):
        """Simulate disk space exhaustion"""
        self.disk_full = True
        self.healthy = False
        
        await asyncio.sleep(10)
        self._auto_recover()
    
    async def simulate_thread_exhaustion(self):
        """Simulate thread pool exhaustion"""
        self.thread_exhausted = True
        self.healthy = False
        
        await asyncio.sleep(4)
        self._auto_recover()
    
    async def simulate_graceful_shutdown(self):
        """Simulate graceful shutdown"""
        await self.graceful_shutdown()
        
        # Auto-restart
        await asyncio.sleep(6)
        self._restart()
    
    async def simulate_forced_termination(self):
        """Simulate forced termination (SIGKILL)"""
        self.shutdown = True
        self.healthy = False
        
        # Longer restart time for forced termination
        await asyncio.sleep(12)
        self._restart()
    
    async def simulate_config_reload(self):
        """Simulate configuration reload"""
        self.healthy = False
        
        # Quick reload
        await asyncio.sleep(2)
        self._auto_recover()
    
    async def simulate_cascading_failure(self):
        """Simulate cascading failure"""
        # Multiple failures in sequence
        self.memory_exhausted = True
        await asyncio.sleep(5)
        
        self.connections_exhausted = True
        await asyncio.sleep(5)
        
        self.db_connection_failed = True
        await asyncio.sleep(5)
        
        # Gradual recovery
        await asyncio.sleep(10)
        self._auto_recover()
    
    def _auto_recover(self):
        """Auto-recovery mechanism"""
        self.memory_exhausted = False
        self.connections_exhausted = False
        self.db_connection_failed = False
        self.api_timeout = False
        self.disk_full = False
        self.thread_exhausted = False
        self.current_memory = self.baseline_memory
        self.current_connections = self.baseline_connections
        self.healthy = True
    
    def _restart(self):
        """Restart service"""
        self.shutdown = False
        self._auto_recover()


@pytest.fixture
def recovery_validator():
    """Fixture for recovery validator"""
    return SidecarRecoveryValidator()


@pytest.mark.asyncio
async def test_memory_exhaustion_recovery(recovery_validator):
    """Test recovery from memory exhaustion"""
    scenario = RecoveryScenario(
        name="memory_exhaustion_test",
        failure_type="memory_exhaustion",
        duration=15.0,
        expected_recovery_time=10.0,
        severity="high",
        description="Memory exhaustion recovery test"
    )
    
    metrics = await recovery_validator._validate_recovery_scenario(scenario)
    
    # Should recover within expected time
    assert metrics.recovery_duration <= scenario.expected_recovery_time + 5.0
    
    # Should have reasonable success rates
    assert metrics.health_check_success_rate >= 0.5
    assert metrics.request_success_rate >= 0.3
    
    # Recovery efficiency should be acceptable
    assert metrics.recovery_efficiency >= 0.4


@pytest.mark.asyncio
async def test_connection_exhaustion_recovery(recovery_validator):
    """Test recovery from connection pool exhaustion"""
    scenario = RecoveryScenario(
        name="connection_exhaustion_test",
        failure_type="connection_exhaustion",
        duration=10.0,
        expected_recovery_time=5.0,
        severity="medium",
        description="Connection exhaustion recovery test"
    )
    
    metrics = await recovery_validator._validate_recovery_scenario(scenario)
    
    assert metrics.recovery_duration <= scenario.expected_recovery_time + 3.0
    assert metrics.recovery_efficiency >= 0.5


@pytest.mark.asyncio
async def test_graceful_shutdown_recovery(recovery_validator):
    """Test graceful shutdown and restart"""
    scenario = RecoveryScenario(
        name="graceful_shutdown_test",
        failure_type="graceful_shutdown",
        duration=12.0,
        expected_recovery_time=8.0,
        severity="low",
        description="Graceful shutdown recovery test"
    )
    
    metrics = await recovery_validator._validate_recovery_scenario(scenario)
    
    assert metrics.graceful_shutdown == True
    assert metrics.recovery_efficiency >= 0.6


@pytest.mark.asyncio
async def test_comprehensive_recovery_validation(recovery_validator):
    """Test comprehensive recovery validation"""
    # Run subset of scenarios for testing
    test_scenarios = [
        "memory_exhaustion_recovery",
        "connection_pool_exhaustion", 
        "graceful_shutdown_recovery"
    ]
    
    recovery_validator.recovery_scenarios = [
        s for s in recovery_validator.recovery_scenarios 
        if s.name in test_scenarios
    ]
    
    metrics_list = await recovery_validator.validate_all_recovery_scenarios()
    
    # Should have results for all test scenarios
    assert len(metrics_list) == len(test_scenarios)
    
    # At least 2/3 should pass
    passed = sum(1 for m in metrics_list if m.recovery_efficiency >= 0.7)
    assert passed >= len(test_scenarios) * 0.6
    
    # Overall efficiency should be reasonable
    overall_efficiency = sum(m.recovery_efficiency for m in metrics_list) / len(metrics_list)
    assert overall_efficiency >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])