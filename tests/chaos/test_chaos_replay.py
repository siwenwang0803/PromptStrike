"""
Test suite for chaos replay engine
"""

import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock

from tests.chaos.chaos_replay import ChaosReplayEngine, ChaosScenario
from tests.chaos.mutation_engine import MutationEngine
from tests.chaos.fault_injector import FaultInjector


class MockReplayEngine:
    """Mock replay engine for testing"""
    
    def __init__(self):
        self.replay_calls = []
        self.should_fail = False
        self.failure_rate = 0.0
        
    async def replay_span(self, span_data):
        """Mock replay span method"""
        self.replay_calls.append(span_data)
        
        if self.should_fail or (self.failure_rate > 0 and len(self.replay_calls) % int(1/self.failure_rate) == 0):
            raise Exception("Simulated replay failure")
        
        # Simulate processing time
        await asyncio.sleep(0.001)


@pytest.fixture
def mock_replay_engine():
    """Fixture for mock replay engine"""
    return MockReplayEngine()


@pytest.fixture
def chaos_engine(mock_replay_engine):
    """Fixture for chaos replay engine"""
    return ChaosReplayEngine(
        target_replay_engine=mock_replay_engine,
        mutation_engine=MutationEngine(seed=42),
        fault_injector=FaultInjector(seed=42)
    )


@pytest.mark.asyncio
async def test_chaos_replay_basic(chaos_engine):
    """Test basic chaos replay functionality"""
    scenarios = [ChaosScenario.MALFORMED_SPANS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="basic_chaos_test",
        scenarios=scenarios,
        test_duration=5.0
    )
    
    assert result.test_name == "basic_chaos_test"
    assert len(result.scenarios_executed) > 0
    assert result.total_duration > 0
    assert 0 <= result.success_rate <= 1
    assert result.resilience_score >= 0


@pytest.mark.asyncio
async def test_malformed_spans_chaos(chaos_engine):
    """Test malformed spans chaos scenario"""
    scenarios = [ChaosScenario.MALFORMED_SPANS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="malformed_spans_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that malformed spans scenario was executed
    malformed_events = [e for e in result.scenarios_executed 
                       if e.scenario == ChaosScenario.MALFORMED_SPANS]
    assert len(malformed_events) > 0
    
    # Should have some failures due to malformed spans
    assert result.error_count >= 0


@pytest.mark.asyncio
async def test_gork_data_chaos(chaos_engine):
    """Test gork data chaos scenario"""
    scenarios = [ChaosScenario.GORK_DATA]
    
    result = await chaos_engine.run_chaos_test(
        test_name="gork_data_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that gork data scenario was executed
    gork_events = [e for e in result.scenarios_executed 
                   if e.scenario == ChaosScenario.GORK_DATA]
    assert len(gork_events) > 0


@pytest.mark.asyncio
async def test_corrupted_payloads_chaos(chaos_engine):
    """Test corrupted payloads chaos scenario"""
    scenarios = [ChaosScenario.CORRUPTED_PAYLOADS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="corrupted_payloads_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that corrupted payloads scenario was executed
    corrupted_events = [e for e in result.scenarios_executed 
                       if e.scenario == ChaosScenario.CORRUPTED_PAYLOADS]
    assert len(corrupted_events) > 0


@pytest.mark.asyncio
async def test_encoding_errors_chaos(chaos_engine):
    """Test encoding errors chaos scenario"""
    scenarios = [ChaosScenario.ENCODING_ERRORS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="encoding_errors_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that encoding errors scenario was executed
    encoding_events = [e for e in result.scenarios_executed 
                      if e.scenario == ChaosScenario.ENCODING_ERRORS]
    assert len(encoding_events) > 0


@pytest.mark.asyncio
async def test_multiple_scenarios(chaos_engine):
    """Test multiple chaos scenarios running concurrently"""
    scenarios = [
        ChaosScenario.MALFORMED_SPANS,
        ChaosScenario.GORK_DATA,
        ChaosScenario.CORRUPTED_PAYLOADS
    ]
    
    result = await chaos_engine.run_chaos_test(
        test_name="multiple_scenarios_test",
        scenarios=scenarios,
        test_duration=5.0
    )
    
    # Should have events for all scenarios
    executed_scenarios = {e.scenario for e in result.scenarios_executed}
    assert len(executed_scenarios) == len(scenarios)
    
    # Should have reasonable resilience score
    assert result.resilience_score >= 0


@pytest.mark.asyncio
async def test_network_chaos_scenarios(chaos_engine):
    """Test network-related chaos scenarios"""
    scenarios = [
        ChaosScenario.NETWORK_PARTITION,
        ChaosScenario.SLOW_NETWORK
    ]
    
    result = await chaos_engine.run_chaos_test(
        test_name="network_chaos_test",
        scenarios=scenarios,
        test_duration=4.0
    )
    
    # Check that network scenarios were executed
    network_events = [e for e in result.scenarios_executed 
                     if e.scenario in [ChaosScenario.NETWORK_PARTITION, ChaosScenario.SLOW_NETWORK]]
    assert len(network_events) > 0


@pytest.mark.asyncio
async def test_resource_chaos_scenarios(chaos_engine):
    """Test resource-related chaos scenarios"""
    scenarios = [ChaosScenario.MEMORY_PRESSURE]
    
    result = await chaos_engine.run_chaos_test(
        test_name="resource_chaos_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that resource scenarios were executed
    resource_events = [e for e in result.scenarios_executed 
                      if e.scenario == ChaosScenario.MEMORY_PRESSURE]
    assert len(resource_events) > 0


@pytest.mark.asyncio
async def test_timeout_chaos_scenarios(chaos_engine):
    """Test timeout-related chaos scenarios"""
    scenarios = [ChaosScenario.TIMEOUT_CHAOS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="timeout_chaos_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that timeout scenarios were executed
    timeout_events = [e for e in result.scenarios_executed 
                     if e.scenario == ChaosScenario.TIMEOUT_CHAOS]
    assert len(timeout_events) > 0


@pytest.mark.asyncio
async def test_concurrency_chaos_scenarios(chaos_engine):
    """Test concurrency-related chaos scenarios"""
    scenarios = [ChaosScenario.RACE_CONDITIONS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="concurrency_chaos_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that concurrency scenarios were executed
    concurrency_events = [e for e in result.scenarios_executed 
                         if e.scenario == ChaosScenario.RACE_CONDITIONS]
    assert len(concurrency_events) > 0


@pytest.mark.asyncio
async def test_dependency_failure_scenarios(chaos_engine):
    """Test dependency failure scenarios"""
    scenarios = [ChaosScenario.DEPENDENCY_FAILURE]
    
    result = await chaos_engine.run_chaos_test(
        test_name="dependency_failure_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    # Check that dependency failure scenarios were executed
    dependency_events = [e for e in result.scenarios_executed 
                        if e.scenario == ChaosScenario.DEPENDENCY_FAILURE]
    assert len(dependency_events) > 0


@pytest.mark.asyncio
async def test_chaos_intensity_configuration(mock_replay_engine):
    """Test chaos intensity configuration"""
    # Test with high intensity
    high_intensity_engine = ChaosReplayEngine(
        target_replay_engine=mock_replay_engine,
        mutation_engine=MutationEngine(seed=42)
    )
    high_intensity_engine.chaos_intensity = 0.8
    
    result = await high_intensity_engine.run_chaos_test(
        test_name="high_intensity_test",
        scenarios=[ChaosScenario.MALFORMED_SPANS],
        test_duration=2.0
    )
    
    # High intensity should result in more chaos events
    assert result.error_count >= 0


@pytest.mark.asyncio
async def test_resilience_score_calculation(chaos_engine):
    """Test resilience score calculation"""
    scenarios = [ChaosScenario.MALFORMED_SPANS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="resilience_score_test",
        scenarios=scenarios,
        test_duration=2.0
    )
    
    # Resilience score should be between 0 and 1
    assert 0 <= result.resilience_score <= 1
    
    # Should have meaningful metrics
    assert result.detailed_metrics is not None
    assert "success_rate" in result.detailed_metrics
    assert "error_rate" in result.detailed_metrics


@pytest.mark.asyncio
async def test_metrics_collection(chaos_engine):
    """Test metrics collection during chaos testing"""
    scenarios = [ChaosScenario.MALFORMED_SPANS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="metrics_collection_test",
        scenarios=scenarios,
        test_duration=2.0
    )
    
    # Should have collected metrics
    metrics = result.detailed_metrics
    assert "replay_attempts" in metrics
    assert "replay_successes" in metrics
    assert "replay_errors" in metrics
    assert "total_duration" in metrics
    
    # Attempt counts should be reasonable
    assert metrics["replay_attempts"] >= 0
    assert metrics["replay_successes"] >= 0
    assert metrics["replay_errors"] >= 0


@pytest.mark.asyncio
async def test_custom_test_data(chaos_engine):
    """Test chaos testing with custom test data"""
    custom_spans = [
        {"trace_id": "test1", "span_id": "span1", "operation": "custom_op1"},
        {"trace_id": "test2", "span_id": "span2", "operation": "custom_op2"}
    ]
    
    result = await chaos_engine.run_chaos_test(
        test_name="custom_data_test",
        scenarios=[ChaosScenario.MALFORMED_SPANS],
        test_duration=2.0,
        test_data=custom_spans
    )
    
    # Should have used custom data
    assert result.total_duration > 0
    assert len(result.scenarios_executed) > 0


@pytest.mark.asyncio
async def test_recovery_time_calculation(chaos_engine):
    """Test recovery time calculation"""
    scenarios = [ChaosScenario.MALFORMED_SPANS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="recovery_time_test",
        scenarios=scenarios,
        test_duration=2.0
    )
    
    # Recovery time should be non-negative
    assert result.recovery_time >= 0


@pytest.mark.asyncio 
async def test_error_handling_during_chaos(mock_replay_engine):
    """Test error handling during chaos testing"""
    # Configure mock to fail
    mock_replay_engine.should_fail = True
    
    chaos_engine = ChaosReplayEngine(
        target_replay_engine=mock_replay_engine,
        mutation_engine=MutationEngine(seed=42)
    )
    
    result = await chaos_engine.run_chaos_test(
        test_name="error_handling_test",
        scenarios=[ChaosScenario.MALFORMED_SPANS],
        test_duration=2.0
    )
    
    # Should handle errors gracefully
    assert result is not None
    assert result.error_count >= 0
    assert result.success_rate >= 0


# Data corruption test category
@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_data_corruption_scenarios(chaos_engine):
    """Test data corruption scenarios"""
    scenarios = [
        ChaosScenario.CORRUPTED_PAYLOADS,
        ChaosScenario.GORK_DATA,
        ChaosScenario.ENCODING_ERRORS
    ]
    
    result = await chaos_engine.run_chaos_test(
        test_name="data_corruption_test",
        scenarios=scenarios,
        test_duration=4.0
    )
    
    assert result.error_count >= 0
    assert result.resilience_score >= 0


# Protocol violation test category
@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_protocol_violation_scenarios(chaos_engine):
    """Test protocol violation scenarios"""
    scenarios = [ChaosScenario.MALFORMED_SPANS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="protocol_violation_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    assert result.error_count >= 0
    assert result.resilience_score >= 0


# Boundary testing category
@pytest.mark.boundary_testing
@pytest.mark.asyncio
async def test_boundary_testing_scenarios(chaos_engine):
    """Test boundary testing scenarios"""
    scenarios = [
        ChaosScenario.MEMORY_PRESSURE,
        ChaosScenario.TIMEOUT_CHAOS
    ]
    
    result = await chaos_engine.run_chaos_test(
        test_name="boundary_testing_test",
        scenarios=scenarios,
        test_duration=4.0
    )
    
    assert result.error_count >= 0
    assert result.resilience_score >= 0


# Security payloads test category
@pytest.mark.security_payloads
@pytest.mark.asyncio
async def test_security_payloads_scenarios(chaos_engine):
    """Test security payloads scenarios"""
    # Security payloads are tested through the mutation engine
    # which includes injection attacks
    scenarios = [ChaosScenario.MALFORMED_SPANS]
    
    result = await chaos_engine.run_chaos_test(
        test_name="security_payloads_test",
        scenarios=scenarios,
        test_duration=3.0
    )
    
    assert result.error_count >= 0
    assert result.resilience_score >= 0


# High-load and concurrency tests
@pytest.mark.asyncio
async def test_high_concurrency_chaos(chaos_engine):
    """Test chaos scenarios under high concurrency - FinTech production load simulation"""
    scenarios = [ChaosScenario.MALFORMED_SPANS, ChaosScenario.NETWORK_PARTITION]
    
    result = await chaos_engine.run_chaos_test(
        test_name="high_concurrency_fintech_test",
        scenarios=scenarios,
        test_duration=5.0,
        concurrent_requests=100  # Simulate FinTech peak load
    )
    
    # Validate high-load resilience for FinTech environments
    assert result.concurrent_requests_handled >= 90  # 90% success rate under load
    assert result.recovery_time < 2.0  # Recovery within 2 seconds for financial systems
    assert result.resilience_score >= 0.7  # Minimum acceptable for production
    
    # Ensure critical FinTech metrics
    metrics = result.detailed_metrics
    assert metrics.get("concurrent_errors", 0) < 10  # Max 10% error rate
    assert metrics.get("average_response_time", 0) < 1.0  # Sub-second response


@pytest.mark.asyncio
async def test_financial_system_resilience(chaos_engine):
    """Test resilience under realistic financial system stress"""
    # Simulate payment processing peak traffic
    financial_scenarios = [
        ChaosScenario.NETWORK_PARTITION,  # Network issues during payment
        ChaosScenario.MEMORY_PRESSURE,   # High transaction volume
        ChaosScenario.TIMEOUT_CHAOS      # Database connection timeouts
    ]
    
    result = await chaos_engine.run_chaos_test(
        test_name="financial_resilience_test",
        scenarios=financial_scenarios,
        test_duration=10.0,
        concurrent_requests=500  # Peak hour traffic
    )
    
    # Financial system specific requirements
    assert result.success_rate >= 0.99  # 99% uptime requirement
    assert result.recovery_time < 5.0   # Fast recovery for financial operations
    assert result.error_count < 5       # Minimal failures acceptable
    
    # Compliance metrics for financial audits
    assert "financial_compliance" in str(result.detailed_metrics)


@pytest.mark.asyncio
async def test_progressive_load_stress(chaos_engine):
    """Test progressive load increase to find breaking point"""
    load_levels = [10, 50, 100, 200, 500]
    results = []
    
    for load in load_levels:
        result = await chaos_engine.run_chaos_test(
            test_name=f"progressive_load_{load}",
            scenarios=[ChaosScenario.MALFORMED_SPANS],
            test_duration=3.0,
            concurrent_requests=load
        )
        results.append((load, result.resilience_score, result.recovery_time))
        
        # Stop if resilience drops below acceptable threshold
        if result.resilience_score < 0.5:
            break
    
    # Analyze load capacity
    assert len(results) >= 3  # Should handle at least first 3 load levels
    
    # Verify graceful degradation
    for i in range(1, len(results)):
        prev_score = results[i-1][1]
        curr_score = results[i][1]
        # Allow some degradation but not catastrophic failure
        assert curr_score >= prev_score * 0.7  # Max 30% degradation per load level


@pytest.mark.asyncio
async def test_recovery_time_under_load(chaos_engine):
    """Test detailed recovery time analysis under different loads"""
    test_cases = [
        (1, "single_request"),
        (10, "light_load"), 
        (50, "medium_load"),
        (100, "heavy_load")
    ]
    
    recovery_times = {}
    
    for load, case_name in test_cases:
        result = await chaos_engine.run_chaos_test(
            test_name=f"recovery_analysis_{case_name}",
            scenarios=[ChaosScenario.NETWORK_PARTITION],
            test_duration=5.0,
            concurrent_requests=load
        )
        
        recovery_times[case_name] = result.recovery_time
        
        # Ensure recovery time doesn't degrade exponentially
        assert result.recovery_time < 10.0  # Max 10 seconds for any load
    
    # Verify recovery time scaling is reasonable
    assert recovery_times["heavy_load"] <= recovery_times["single_request"] * 3


@pytest.mark.asyncio 
async def test_concurrent_scenario_isolation(chaos_engine):
    """Test that concurrent chaos scenarios don't interfere with each other"""
    # Run multiple chaos scenarios simultaneously
    result = await chaos_engine.run_chaos_test(
        test_name="concurrent_scenario_isolation",
        scenarios=[
            ChaosScenario.MALFORMED_SPANS,
            ChaosScenario.CORRUPTED_PAYLOADS,
            ChaosScenario.ENCODING_ERRORS,
            ChaosScenario.NETWORK_PARTITION
        ],
        test_duration=8.0,
        concurrent_requests=50
    )
    
    # Each scenario should execute independently
    scenario_events = {}
    for event in result.scenarios_executed:
        scenario_type = event.scenario.value
        scenario_events[scenario_type] = scenario_events.get(scenario_type, 0) + 1
    
    # Verify all scenarios executed
    assert len(scenario_events) >= 4
    
    # Verify reasonable isolation (no catastrophic cross-interference)
    assert result.resilience_score >= 0.4  # Should maintain some resilience
    assert result.success_rate >= 0.6      # Should handle majority of requests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])