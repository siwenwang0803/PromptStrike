"""
Lightweight Mode for Chaos Testing

Provides resource-optimized chaos testing capabilities for SMEs and
resource-constrained environments. Reduces memory footprint, CPU usage,
and test duration while maintaining effectiveness.
"""

import asyncio
import gc
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
from contextlib import contextmanager

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .config import ChaosConfig, get_chaos_config
from .chaos_replay import ChaosReplayEngine, ChaosScenario
from .mutation_engine import MutationEngine, MutationType


@dataclass
class ResourceProfile:
    """Resource consumption profile for lightweight mode"""
    memory_limit_mb: int = 512  # 512MB for SMEs
    cpu_cores: float = 0.5      # Half a CPU core
    max_concurrent_tests: int = 1  # Sequential execution
    test_duration_seconds: int = 30  # Shorter tests
    sample_rate: float = 0.1     # Sample 10% of operations
    batch_size: int = 10         # Smaller batches
    
    @classmethod
    def ultra_light(cls) -> 'ResourceProfile':
        """Ultra-lightweight profile for very constrained environments"""
        return cls(
            memory_limit_mb=256,
            cpu_cores=0.25,
            max_concurrent_tests=1,
            test_duration_seconds=15,
            sample_rate=0.05,
            batch_size=5
        )
    
    @classmethod
    def standard_light(cls) -> 'ResourceProfile':
        """Standard lightweight profile for typical SMEs"""
        return cls()  # Use defaults
    
    @classmethod
    def balanced(cls) -> 'ResourceProfile':
        """Balanced profile with moderate resources"""
        return cls(
            memory_limit_mb=1024,
            cpu_cores=1.0,
            max_concurrent_tests=2,
            test_duration_seconds=60,
            sample_rate=0.2,
            batch_size=20
        )


@dataclass
class LightweightMetrics:
    """Metrics for lightweight mode execution"""
    start_time: datetime
    end_time: Optional[datetime] = None
    memory_used_mb: float = 0
    peak_memory_mb: float = 0
    cpu_percent: float = 0
    tests_executed: int = 0
    tests_skipped: int = 0
    errors_found: int = 0
    resource_violations: int = 0


class ResourceMonitor:
    """Monitors and enforces resource constraints"""
    
    def __init__(self, profile: ResourceProfile):
        self.profile = profile
        self.violations = 0
        
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()
            self.start_memory = self.get_memory_usage()
        else:
            self.process = None
            self.start_memory = 0
            print("Warning: psutil not available - resource monitoring disabled")
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        if PSUTIL_AVAILABLE and self.process:
            return self.process.memory_info().rss / 1024 / 1024
        else:
            # Return a mock value for testing
            return 100.0
    
    def get_cpu_percent(self) -> float:
        """Get current CPU usage percentage"""
        if PSUTIL_AVAILABLE and self.process:
            return self.process.cpu_percent(interval=0.1)
        else:
            # Return a mock value for testing
            return 25.0
    
    def check_limits(self) -> Tuple[bool, Optional[str]]:
        """Check if resource limits are exceeded"""
        memory_mb = self.get_memory_usage()
        
        if memory_mb > self.profile.memory_limit_mb:
            self.violations += 1
            return False, f"Memory limit exceeded: {memory_mb:.1f}MB > {self.profile.memory_limit_mb}MB"
        
        # CPU check (averaged over time)
        cpu_percent = self.get_cpu_percent()
        cpu_threshold = self.profile.cpu_cores * 100
        
        if cpu_percent > cpu_threshold * 1.5:  # Allow 50% burst
            self.violations += 1
            return False, f"CPU limit exceeded: {cpu_percent:.1f}% > {cpu_threshold:.1f}%"
        
        return True, None
    
    @contextmanager
    def resource_guard(self):
        """Context manager for resource monitoring"""
        try:
            yield self
        finally:
            # Force garbage collection
            gc.collect()
            
            # Check final resource usage
            final_memory = self.get_memory_usage()
            if final_memory > self.start_memory * 1.5:
                # Memory leak detected
                gc.collect(2)  # Full collection


class LightweightChaosEngine:
    """
    Lightweight chaos engine optimized for resource-constrained environments.
    Designed for SMEs with limited infrastructure.
    """
    
    def __init__(self, 
                 profile: Optional[ResourceProfile] = None,
                 config: Optional[ChaosConfig] = None):
        self.profile = profile or ResourceProfile.standard_light()
        self.config = config or get_chaos_config()
        self.monitor = ResourceMonitor(self.profile)
        self.metrics = None
        
        # Optimize components for lightweight mode
        self._configure_lightweight_components()
    
    def _configure_lightweight_components(self):
        """Configure components for minimal resource usage"""
        # Reduce mutation engine memory footprint
        self.mutation_engine = MutationEngine(seed=42)
        
        # Configure lightweight scenarios only
        self.lightweight_scenarios = [
            ChaosScenario.MALFORMED_SPANS,
            ChaosScenario.ENCODING_ERRORS,
            ChaosScenario.SLOW_NETWORK,
            ChaosScenario.TIMEOUT_CHAOS
        ]
        
        # Exclude resource-intensive scenarios
        self.excluded_scenarios = [
            ChaosScenario.MEMORY_PRESSURE,
            ChaosScenario.CPU_SPIKE,
            ChaosScenario.DISK_FULL,
            ChaosScenario.FILE_DESCRIPTOR_EXHAUSTION
        ]
    
    async def run_lightweight_test(self, 
                                 test_name: str,
                                 target_system: Any = None,
                                 custom_scenarios: Optional[List[ChaosScenario]] = None) -> Dict[str, Any]:
        """
        Run chaos test in lightweight mode with resource constraints.
        
        Args:
            test_name: Name of the test
            target_system: System to test (optional)
            custom_scenarios: Custom scenarios to run (optional)
            
        Returns:
            Test results with resource usage metrics
        """
        self.metrics = LightweightMetrics(start_time=datetime.now())
        
        with self.monitor.resource_guard() as monitor:
            try:
                # Select appropriate scenarios
                scenarios = custom_scenarios or self.lightweight_scenarios
                scenarios = [s for s in scenarios if s not in self.excluded_scenarios]
                
                # Run tests with resource constraints
                results = await self._execute_constrained_tests(
                    test_name, 
                    scenarios,
                    target_system
                )
                
                self.metrics.end_time = datetime.now()
                self.metrics.memory_used_mb = monitor.get_memory_usage()
                self.metrics.peak_memory_mb = max(
                    self.metrics.memory_used_mb,
                    self.metrics.peak_memory_mb
                )
                
                return self._compile_results(results)
                
            except Exception as e:
                self.metrics.errors_found += 1
                return {
                    'success': False,
                    'error': str(e),
                    'metrics': self._get_metrics_summary()
                }
    
    async def _execute_constrained_tests(self, 
                                       test_name: str,
                                       scenarios: List[ChaosScenario],
                                       target_system: Any) -> List[Dict[str, Any]]:
        """Execute tests with resource constraints"""
        results = []
        
        # Sequential execution to minimize resource usage
        for scenario in scenarios:
            # Check resource limits before each test
            within_limits, violation_msg = self.monitor.check_limits()
            if not within_limits:
                self.metrics.tests_skipped += 1
                self.metrics.resource_violations += 1
                results.append({
                    'scenario': scenario.value,
                    'status': 'skipped',
                    'reason': violation_msg
                })
                continue
            
            # Run single scenario test
            try:
                result = await self._run_single_scenario(
                    test_name,
                    scenario,
                    target_system
                )
                results.append(result)
                self.metrics.tests_executed += 1
                
                # Small delay to prevent CPU spikes
                await asyncio.sleep(0.1)
                
                # Periodic garbage collection
                if self.metrics.tests_executed % 5 == 0:
                    gc.collect()
                    
            except Exception as e:
                self.metrics.errors_found += 1
                results.append({
                    'scenario': scenario.value,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    async def _run_single_scenario(self, 
                                 test_name: str,
                                 scenario: ChaosScenario,
                                 target_system: Any) -> Dict[str, Any]:
        """Run a single chaos scenario with minimal resources"""
        start_time = time.time()
        
        # Create minimal test data
        test_data = self._generate_minimal_test_data()
        
        # Run with reduced duration and sampling
        chaos_engine = ChaosReplayEngine(
            target_replay_engine=target_system,
            mutation_engine=self.mutation_engine
        )
        
        # Override intensity for lightweight mode
        chaos_engine.chaos_intensity = self.profile.sample_rate
        
        result = await chaos_engine.run_chaos_test(
            test_name=f"{test_name}_{scenario.value}",
            scenarios=[scenario],
            test_duration=self.profile.test_duration_seconds,
            test_data=test_data,
            concurrent_requests=1  # Always sequential in lightweight mode
        )
        
        return {
            'scenario': scenario.value,
            'status': 'completed',
            'duration': time.time() - start_time,
            'success_rate': result.success_rate,
            'errors': result.error_count,
            'resilience_score': result.resilience_score
        }
    
    def _generate_minimal_test_data(self) -> List[Dict[str, Any]]:
        """Generate minimal test data to reduce memory usage"""
        return [
            {
                'trace_id': f'lightweight_trace_{i}',
                'span_id': f'span_{i}',
                'operation': 'test_op',
                'timestamp': time.time_ns()
            }
            for i in range(self.profile.batch_size)
        ]
    
    def _compile_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compile test results with resource metrics"""
        successful_tests = [r for r in results if r.get('status') == 'completed']
        
        return {
            'success': True,
            'test_summary': {
                'total_scenarios': len(results),
                'executed': self.metrics.tests_executed,
                'skipped': self.metrics.tests_skipped,
                'errors': self.metrics.errors_found
            },
            'resource_usage': self._get_metrics_summary(),
            'scenario_results': results,
            'recommendations': self._generate_recommendations(results)
        }
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get resource usage metrics summary"""
        if not self.metrics:
            return {}
        
        duration = (self.metrics.end_time - self.metrics.start_time).total_seconds() \
                  if self.metrics.end_time else 0
        
        return {
            'duration_seconds': duration,
            'memory_used_mb': round(self.metrics.memory_used_mb, 2),
            'peak_memory_mb': round(self.metrics.peak_memory_mb, 2),
            'memory_limit_mb': self.profile.memory_limit_mb,
            'cpu_cores_limit': self.profile.cpu_cores,
            'resource_violations': self.metrics.resource_violations,
            'efficiency_score': self._calculate_efficiency_score()
        }
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate resource efficiency score (0-100)"""
        if not self.metrics or self.metrics.tests_executed == 0:
            return 0.0
        
        # Factors: tests completed, resource usage, violations
        completion_rate = self.metrics.tests_executed / (
            self.metrics.tests_executed + self.metrics.tests_skipped + 1
        )
        
        memory_efficiency = 1.0 - (
            self.metrics.memory_used_mb / self.profile.memory_limit_mb
        )
        
        violation_penalty = max(0, 1.0 - (self.metrics.resource_violations * 0.1))
        
        score = (completion_rate * 0.4 + 
                memory_efficiency * 0.4 + 
                violation_penalty * 0.2) * 100
        
        return round(max(0, min(100, score)), 2)
    
    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on lightweight mode execution"""
        recommendations = []
        
        if self.metrics.resource_violations > 0:
            recommendations.append(
                f"Consider using ultra-light profile - {self.metrics.resource_violations} "
                f"resource violations detected"
            )
        
        if self.metrics.tests_skipped > 0:
            recommendations.append(
                f"Reduce test scope or increase resource limits - "
                f"{self.metrics.tests_skipped} tests were skipped"
            )
        
        efficiency = self._calculate_efficiency_score()
        if efficiency < 70:
            recommendations.append(
                "Low efficiency score - consider optimizing test selection or "
                "increasing resource allocation"
            )
        
        # Profile-specific recommendations
        if self.profile.memory_limit_mb < 512:
            recommendations.append(
                "Ultra-light mode active - some chaos scenarios may not provide "
                "comprehensive coverage"
            )
        
        return recommendations


class LightweightProfileSelector:
    """Automatically selects appropriate lightweight profile based on system resources"""
    
    @staticmethod
    def auto_select() -> ResourceProfile:
        """Automatically select profile based on available resources"""
        if PSUTIL_AVAILABLE:
            # Get system resources
            total_memory_mb = psutil.virtual_memory().total / 1024 / 1024
            cpu_count = psutil.cpu_count()
            
            # Select profile based on available resources
            if total_memory_mb < 1024 or cpu_count <= 1:
                # Very limited resources
                return ResourceProfile.ultra_light()
            elif total_memory_mb < 4096 or cpu_count <= 2:
                # Limited resources (typical SME)
                return ResourceProfile.standard_light()
            else:
                # Moderate resources available
                return ResourceProfile.balanced()
        else:
            # Default to standard lightweight if psutil unavailable
            print("Warning: Cannot detect system resources - using standard profile")
            return ResourceProfile.standard_light()
    
    @staticmethod
    def recommend_profile(workload_type: str = "general") -> ResourceProfile:
        """Recommend profile based on workload type"""
        profiles = {
            "minimal": ResourceProfile.ultra_light(),
            "sme": ResourceProfile.standard_light(),
            "balanced": ResourceProfile.balanced(),
            "ci": ResourceProfile(
                memory_limit_mb=512,
                cpu_cores=0.5,
                max_concurrent_tests=1,
                test_duration_seconds=30,
                sample_rate=0.15,
                batch_size=15
            ),
            "development": ResourceProfile(
                memory_limit_mb=2048,
                cpu_cores=1.5,
                max_concurrent_tests=3,
                test_duration_seconds=60,
                sample_rate=0.3,
                batch_size=30
            )
        }
        
        return profiles.get(workload_type, ResourceProfile.standard_light())


# Convenience functions for quick lightweight testing
async def run_quick_lightweight_test(target_system: Any = None) -> Dict[str, Any]:
    """Run a quick lightweight chaos test with auto-selected profile"""
    profile = LightweightProfileSelector.auto_select()
    engine = LightweightChaosEngine(profile=profile)
    
    return await engine.run_lightweight_test(
        test_name="quick_lightweight_test",
        target_system=target_system
    )


async def run_sme_chaos_test(target_system: Any = None, 
                           duration_minutes: int = 5) -> Dict[str, Any]:
    """Run chaos test optimized for SME environments"""
    profile = ResourceProfile.standard_light()
    profile.test_duration_seconds = duration_minutes * 60
    
    engine = LightweightChaosEngine(profile=profile)
    
    # Use SME-appropriate scenarios
    sme_scenarios = [
        ChaosScenario.MALFORMED_SPANS,
        ChaosScenario.ENCODING_ERRORS,
        ChaosScenario.TIMEOUT_CHAOS
    ]
    
    return await engine.run_lightweight_test(
        test_name="sme_chaos_test",
        target_system=target_system,
        custom_scenarios=sme_scenarios
    )


def get_resource_requirements(profile_name: str = "standard") -> Dict[str, Any]:
    """Get resource requirements for different profiles"""
    profiles = {
        "ultra_light": ResourceProfile.ultra_light(),
        "standard": ResourceProfile.standard_light(),
        "balanced": ResourceProfile.balanced()
    }
    
    profile = profiles.get(profile_name, ResourceProfile.standard_light())
    
    return {
        "profile_name": profile_name,
        "memory_required_mb": profile.memory_limit_mb,
        "cpu_cores_required": profile.cpu_cores,
        "estimated_duration_seconds": profile.test_duration_seconds,
        "max_concurrent_tests": profile.max_concurrent_tests,
        "suitable_for": _get_suitable_environments(profile)
    }


def _get_suitable_environments(profile: ResourceProfile) -> List[str]:
    """Determine suitable environments for a resource profile"""
    if profile.memory_limit_mb <= 512:
        return ["containers", "ci/cd", "edge_devices", "sme_servers"]
    elif profile.memory_limit_mb <= 1024:
        return ["vms", "small_servers", "development_machines"]
    else:
        return ["dedicated_servers", "cloud_instances", "enterprise_infrastructure"]