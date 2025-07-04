"""
Test suite for lightweight chaos testing mode
"""

import pytest
import asyncio
import psutil
from unittest.mock import Mock, patch, MagicMock
import time

from tests.chaos.lightweight_mode import (
    LightweightChaosEngine,
    ResourceProfile,
    ResourceMonitor,
    LightweightProfileSelector,
    run_quick_lightweight_test,
    run_sme_chaos_test,
    get_resource_requirements
)
from tests.chaos.chaos_replay import ChaosScenario


class TestResourceProfile:
    """Test resource profile configurations"""
    
    def test_ultra_light_profile(self):
        """Test ultra-light profile for very constrained environments"""
        profile = ResourceProfile.ultra_light()
        
        assert profile.memory_limit_mb == 256
        assert profile.cpu_cores == 0.25
        assert profile.max_concurrent_tests == 1
        assert profile.test_duration_seconds == 15
        assert profile.sample_rate == 0.05
    
    def test_standard_light_profile(self):
        """Test standard lightweight profile"""
        profile = ResourceProfile.standard_light()
        
        assert profile.memory_limit_mb == 512
        assert profile.cpu_cores == 0.5
        assert profile.max_concurrent_tests == 1
        assert profile.test_duration_seconds == 30
        assert profile.sample_rate == 0.1
    
    def test_balanced_profile(self):
        """Test balanced profile"""
        profile = ResourceProfile.balanced()
        
        assert profile.memory_limit_mb == 1024
        assert profile.cpu_cores == 1.0
        assert profile.max_concurrent_tests == 2
        assert profile.test_duration_seconds == 60
        assert profile.sample_rate == 0.2


class TestResourceMonitor:
    """Test resource monitoring functionality"""
    
    def test_resource_monitor_initialization(self):
        """Test resource monitor initialization"""
        profile = ResourceProfile.standard_light()
        monitor = ResourceMonitor(profile)
        
        assert monitor.profile == profile
        assert monitor.violations == 0
        assert monitor.start_memory > 0
    
    def test_memory_usage_detection(self):
        """Test memory usage detection"""
        profile = ResourceProfile.standard_light()
        monitor = ResourceMonitor(profile)
        
        memory_mb = monitor.get_memory_usage()
        assert memory_mb > 0
        assert isinstance(memory_mb, float)
    
    def test_cpu_usage_detection(self):
        """Test CPU usage detection"""
        profile = ResourceProfile.standard_light()
        monitor = ResourceMonitor(profile)
        
        cpu_percent = monitor.get_cpu_percent()
        assert cpu_percent >= 0
        assert isinstance(cpu_percent, float)
    
    def test_resource_limit_checking(self):
        """Test resource limit checking"""
        # Create profile with very low limits to trigger violations
        profile = ResourceProfile(memory_limit_mb=1, cpu_cores=0.01)
        monitor = ResourceMonitor(profile)
        
        within_limits, violation_msg = monitor.check_limits()
        
        # Should exceed the 1MB memory limit
        assert within_limits is False
        assert "Memory limit exceeded" in violation_msg
        assert monitor.violations > 0
    
    def test_resource_guard_context_manager(self):
        """Test resource guard context manager"""
        profile = ResourceProfile.standard_light()
        monitor = ResourceMonitor(profile)
        
        with monitor.resource_guard() as guard:
            assert guard == monitor
            # Simulate some work
            data = [i for i in range(1000)]
        
        # Should trigger garbage collection
        # Memory should be managed


class TestLightweightChaosEngine:
    """Test lightweight chaos engine functionality"""
    
    @pytest.fixture
    def mock_target_system(self):
        """Create mock target system"""
        mock = AsyncMock()
        mock.replay_span = AsyncMock(return_value=None)
        return mock
    
    def test_engine_initialization(self):
        """Test engine initialization with lightweight configuration"""
        engine = LightweightChaosEngine()
        
        assert engine.profile is not None
        assert engine.mutation_engine is not None
        assert len(engine.lightweight_scenarios) > 0
        assert len(engine.excluded_scenarios) > 0
        
        # Verify resource-intensive scenarios are excluded
        assert ChaosScenario.MEMORY_PRESSURE in engine.excluded_scenarios
        assert ChaosScenario.CPU_SPIKE in engine.excluded_scenarios
    
    def test_custom_profile_initialization(self):
        """Test engine with custom profile"""
        profile = ResourceProfile.ultra_light()
        engine = LightweightChaosEngine(profile=profile)
        
        assert engine.profile == profile
        assert engine.profile.memory_limit_mb == 256
    
    @pytest.mark.asyncio
    async def test_lightweight_test_execution(self, mock_target_system):
        """Test lightweight chaos test execution"""
        profile = ResourceProfile.ultra_light()
        engine = LightweightChaosEngine(profile=profile)
        
        result = await engine.run_lightweight_test(
            test_name="test_lightweight",
            target_system=mock_target_system,
            custom_scenarios=[ChaosScenario.MALFORMED_SPANS]
        )
        
        assert result['success'] is True
        assert 'test_summary' in result
        assert 'resource_usage' in result
        assert 'scenario_results' in result
        assert result['test_summary']['executed'] >= 0
    
    @pytest.mark.asyncio
    async def test_resource_constrained_execution(self, mock_target_system):
        """Test execution with resource constraints"""
        # Create profile with very tight constraints
        profile = ResourceProfile(
            memory_limit_mb=100,  # Very low limit
            cpu_cores=0.1,
            test_duration_seconds=5
        )
        engine = LightweightChaosEngine(profile=profile)
        
        result = await engine.run_lightweight_test(
            test_name="constrained_test",
            target_system=mock_target_system
        )
        
        # Should handle resource constraints gracefully
        assert 'resource_usage' in result
        assert result['resource_usage']['resource_violations'] >= 0
    
    @pytest.mark.asyncio
    async def test_scenario_filtering(self, mock_target_system):
        """Test that resource-intensive scenarios are filtered out"""
        engine = LightweightChaosEngine()
        
        # Try to run with resource-intensive scenarios
        result = await engine.run_lightweight_test(
            test_name="filtered_test",
            target_system=mock_target_system,
            custom_scenarios=[
                ChaosScenario.MEMORY_PRESSURE,  # Should be filtered
                ChaosScenario.MALFORMED_SPANS    # Should run
            ]
        )
        
        # Only lightweight scenario should run
        executed_scenarios = [
            r['scenario'] for r in result['scenario_results']
            if r.get('status') == 'completed'
        ]
        
        assert ChaosScenario.MEMORY_PRESSURE.value not in executed_scenarios
    
    def test_minimal_test_data_generation(self):
        """Test minimal test data generation"""
        profile = ResourceProfile(batch_size=5)
        engine = LightweightChaosEngine(profile=profile)
        
        test_data = engine._generate_minimal_test_data()
        
        assert len(test_data) == 5
        assert all('trace_id' in item for item in test_data)
        assert all('span_id' in item for item in test_data)
    
    def test_efficiency_score_calculation(self):
        """Test efficiency score calculation"""
        engine = LightweightChaosEngine()
        engine.metrics = MagicMock()
        engine.metrics.tests_executed = 8
        engine.metrics.tests_skipped = 2
        engine.metrics.memory_used_mb = 256
        engine.metrics.resource_violations = 0
        
        score = engine._calculate_efficiency_score()
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_recommendations_generation(self):
        """Test recommendation generation"""
        engine = LightweightChaosEngine()
        engine.metrics = MagicMock()
        engine.metrics.resource_violations = 5
        engine.metrics.tests_skipped = 3
        
        recommendations = engine._generate_recommendations([])
        
        assert len(recommendations) > 0
        assert any('ultra-light' in r for r in recommendations)
        assert any('skipped' in r for r in recommendations)


class TestLightweightProfileSelector:
    """Test profile selection functionality"""
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    def test_auto_select_ultra_light(self, mock_cpu, mock_memory):
        """Test auto-selection of ultra-light profile"""
        # Simulate very limited resources
        mock_memory.return_value = MagicMock(total=512 * 1024 * 1024)  # 512MB
        mock_cpu.return_value = 1
        
        profile = LightweightProfileSelector.auto_select()
        
        assert profile.memory_limit_mb == 256  # Ultra-light
        assert profile.cpu_cores == 0.25
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    def test_auto_select_standard(self, mock_cpu, mock_memory):
        """Test auto-selection of standard profile"""
        # Simulate limited SME resources
        mock_memory.return_value = MagicMock(total=2048 * 1024 * 1024)  # 2GB
        mock_cpu.return_value = 2
        
        profile = LightweightProfileSelector.auto_select()
        
        assert profile.memory_limit_mb == 512  # Standard light
        assert profile.cpu_cores == 0.5
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    def test_auto_select_balanced(self, mock_cpu, mock_memory):
        """Test auto-selection of balanced profile"""
        # Simulate moderate resources
        mock_memory.return_value = MagicMock(total=8192 * 1024 * 1024)  # 8GB
        mock_cpu.return_value = 4
        
        profile = LightweightProfileSelector.auto_select()
        
        assert profile.memory_limit_mb == 1024  # Balanced
        assert profile.cpu_cores == 1.0
    
    def test_workload_based_recommendation(self):
        """Test workload-based profile recommendation"""
        # Test different workload types
        minimal_profile = LightweightProfileSelector.recommend_profile("minimal")
        assert minimal_profile.memory_limit_mb == 256
        
        sme_profile = LightweightProfileSelector.recommend_profile("sme")
        assert sme_profile.memory_limit_mb == 512
        
        ci_profile = LightweightProfileSelector.recommend_profile("ci")
        assert ci_profile.memory_limit_mb == 512
        assert ci_profile.test_duration_seconds == 30
        
        # Test default
        default_profile = LightweightProfileSelector.recommend_profile("unknown")
        assert default_profile.memory_limit_mb == 512


class TestConvenienceFunctions:
    """Test convenience functions for lightweight testing"""
    
    @pytest.mark.asyncio
    @patch('tests.chaos.lightweight_mode.LightweightProfileSelector.auto_select')
    async def test_quick_lightweight_test(self, mock_auto_select):
        """Test quick lightweight test function"""
        mock_auto_select.return_value = ResourceProfile.ultra_light()
        
        with patch('tests.chaos.lightweight_mode.LightweightChaosEngine.run_lightweight_test') as mock_run:
            mock_run.return_value = {'success': True, 'test_summary': {}}
            
            result = await run_quick_lightweight_test()
            
            assert result['success'] is True
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sme_chaos_test(self):
        """Test SME-optimized chaos test"""
        with patch('tests.chaos.lightweight_mode.LightweightChaosEngine.run_lightweight_test') as mock_run:
            mock_run.return_value = {
                'success': True,
                'test_summary': {'executed': 3}
            }
            
            result = await run_sme_chaos_test(duration_minutes=1)
            
            assert result['success'] is True
            # Verify SME-appropriate scenarios were used
            call_args = mock_run.call_args
            assert 'custom_scenarios' in call_args[1]
            scenarios = call_args[1]['custom_scenarios']
            assert ChaosScenario.MALFORMED_SPANS in scenarios
            assert ChaosScenario.MEMORY_PRESSURE not in scenarios
    
    def test_get_resource_requirements(self):
        """Test resource requirements information"""
        # Test standard profile
        requirements = get_resource_requirements("standard")
        
        assert requirements['profile_name'] == "standard"
        assert requirements['memory_required_mb'] == 512
        assert requirements['cpu_cores_required'] == 0.5
        assert 'suitable_for' in requirements
        assert 'sme_servers' in requirements['suitable_for']
        
        # Test ultra-light profile
        ultra_requirements = get_resource_requirements("ultra_light")
        assert ultra_requirements['memory_required_mb'] == 256
        assert 'edge_devices' in ultra_requirements['suitable_for']


class TestResourceEfficiency:
    """Test resource efficiency in lightweight mode"""
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test that memory usage stays within limits"""
        profile = ResourceProfile(memory_limit_mb=1024)
        engine = LightweightChaosEngine(profile=profile)
        
        # Get initial memory
        initial_memory = engine.monitor.get_memory_usage()
        
        # Run lightweight test
        result = await engine.run_lightweight_test(
            test_name="memory_test",
            custom_scenarios=[ChaosScenario.ENCODING_ERRORS]
        )
        
        # Check memory didn't exceed limit significantly
        final_memory = engine.monitor.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Should not increase by more than 50% of limit
        assert memory_increase < profile.memory_limit_mb * 0.5
    
    def test_garbage_collection_triggers(self):
        """Test that garbage collection is triggered appropriately"""
        engine = LightweightChaosEngine()
        
        # Mock gc.collect to verify it's called
        with patch('gc.collect') as mock_gc:
            # Simulate resource guard usage
            with engine.monitor.resource_guard():
                pass
            
            # GC should be called
            mock_gc.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])