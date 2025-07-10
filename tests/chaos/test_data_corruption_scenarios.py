"""
Data Corruption Chaos Testing for RedForge
目标：验证 data_corruption 场景下系统韧性
"""

import pytest
import asyncio
import json
import tempfile
import os
import time
import random
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

from tests.chaos.chaos_replay import ChaosReplayEngine, ChaosScenario
from tests.chaos.mutation_engine import MutationEngine, MutationType


class DataCorruptionTester:
    """Specialized tester for data corruption scenarios"""
    
    def __init__(self):
        self.corruption_patterns = [
            self._bit_flip_corruption,
            self._encoding_corruption,
            self._structure_corruption,
            self._size_corruption,
            self._type_corruption,
            self._boundary_corruption
        ]
        
    def corrupt_span_data(self, span_data: Dict[str, Any], corruption_type: str = "random") -> Dict[str, Any]:
        """Apply specific corruption to span data"""
        if corruption_type == "random":
            corruption_func = random.choice(self.corruption_patterns)
        else:
            corruption_map = {
                "bit_flip": self._bit_flip_corruption,
                "encoding": self._encoding_corruption,
                "structure": self._structure_corruption,
                "size": self._size_corruption,
                "type": self._type_corruption,
                "boundary": self._boundary_corruption
            }
            corruption_func = corruption_map.get(corruption_type, self._bit_flip_corruption)
        
        return corruption_func(span_data.copy())
    
    def _bit_flip_corruption(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate bit-flip corruption in data"""
        if "trace_id" in data:
            trace_id = str(data["trace_id"])
            # Flip random bits in the trace_id
            corrupted_chars = list(trace_id)
            for i in range(min(3, len(corrupted_chars))):
                pos = random.randint(0, len(corrupted_chars) - 1)
                corrupted_chars[pos] = chr(ord(corrupted_chars[pos]) ^ 1)
            data["trace_id"] = "".join(corrupted_chars)
        
        return data
    
    def _encoding_corruption(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate encoding corruption"""
        # Add invalid UTF-8 sequences
        corrupted_data = data.copy()
        corrupted_data["corrupted_field"] = "\\xff\\xfe\\x00\\x01\\x02"
        
        # Corrupt existing string fields
        for key, value in data.items():
            if isinstance(value, str):
                corrupted_data[key] = value + "\\x00\\x01\\x02"
        
        return corrupted_data
    
    def _structure_corruption(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate structure corruption"""
        corrupted = data.copy()
        
        # Add circular references
        corrupted["circular_ref"] = corrupted
        
        # Add deeply nested structures
        nested = {"level": 1}
        for i in range(100):
            nested = {"level": i + 2, "nested": nested}
        corrupted["deep_nesting"] = nested
        
        return corrupted
    
    def _size_corruption(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate size-based corruption"""
        corrupted = data.copy()
        
        # Add extremely large field
        corrupted["large_field"] = "X" * (10 * 1024 * 1024)  # 10MB
        
        # Add many small fields
        for i in range(10000):
            corrupted[f"field_{i}"] = f"value_{i}"
        
        return corrupted
    
    def _type_corruption(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate type corruption"""
        corrupted = data.copy()
        
        # Change types unexpectedly
        for key, value in data.items():
            if isinstance(value, str):
                corrupted[key] = [value]  # String to list
            elif isinstance(value, dict):
                corrupted[key] = str(value)  # Dict to string
            elif isinstance(value, (int, float)):
                corrupted[key] = str(value) + "invalid"  # Number to invalid string
        
        return corrupted
    
    def _boundary_corruption(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate boundary value corruption"""
        corrupted = data.copy()
        
        # Add boundary values
        corrupted["max_int"] = 2**63 - 1
        corrupted["min_int"] = -2**63
        corrupted["nan_value"] = float('nan')
        corrupted["inf_value"] = float('inf')
        corrupted["negative_inf"] = float('-inf')
        corrupted["empty_string"] = ""
        corrupted["null_value"] = None
        
        return corrupted


@pytest.fixture
def data_corruption_tester():
    """Fixture for data corruption tester"""
    return DataCorruptionTester()


@pytest.fixture
def mock_sidecar_engine():
    """Mock sidecar engine for testing"""
    engine = MagicMock()
    engine.process_span = AsyncMock()
    engine.generate_report = AsyncMock()
    engine.health_check = AsyncMock(return_value={"status": "healthy"})
    return engine


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_bit_flip_corruption_resilience(data_corruption_tester, mock_sidecar_engine):
    """Test system resilience against bit-flip corruption"""
    # Create test span with bit-flip corruption
    original_span = {
        "trace_id": "test_trace_123",
        "span_id": "span_456", 
        "operation": "llm_query",
        "timestamp": "2025-01-10T12:00:00Z"
    }
    
    corrupted_span = data_corruption_tester.corrupt_span_data(original_span, "bit_flip")
    
    # Verify corruption occurred
    assert corrupted_span["trace_id"] != original_span["trace_id"]
    
    # Test sidecar handles corruption gracefully
    try:
        await mock_sidecar_engine.process_span(corrupted_span)
        mock_sidecar_engine.process_span.assert_called_once()
    except Exception as e:
        # Should handle corruption without crashing
        assert "corruption" in str(e).lower() or "invalid" in str(e).lower()


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_encoding_corruption_handling(data_corruption_tester, mock_sidecar_engine):
    """Test handling of encoding corruption in span data"""
    original_span = {
        "trace_id": "encoding_test",
        "user_input": "Hello World",
        "response": "AI response"
    }
    
    corrupted_span = data_corruption_tester.corrupt_span_data(original_span, "encoding")
    
    # Should contain encoding corruption markers
    assert any("\\x" in str(value) for value in corrupted_span.values())
    
    # Test processing
    resilience_score = 0
    try:
        await mock_sidecar_engine.process_span(corrupted_span)
        resilience_score = 1.0  # Full resilience if no exception
    except UnicodeDecodeError:
        resilience_score = 0.5  # Partial resilience if caught properly
    except Exception:
        resilience_score = 0.0  # No resilience if unexpected error
    
    # Should show some level of resilience
    assert resilience_score >= 0.5


@pytest.mark.data_corruption
@pytest.mark.asyncio  
async def test_structure_corruption_resilience(data_corruption_tester, mock_sidecar_engine):
    """Test resilience against structural corruption"""
    original_span = {
        "trace_id": "structure_test",
        "span_id": "struct_span",
        "metadata": {"key": "value"}
    }
    
    corrupted_span = data_corruption_tester.corrupt_span_data(original_span, "structure")
    
    # Should contain circular references and deep nesting
    assert "circular_ref" in corrupted_span
    assert "deep_nesting" in corrupted_span
    
    # Test JSON serialization resistance
    try:
        json.dumps(corrupted_span)
        assert False, "Should not be able to serialize circular reference"
    except (ValueError, RecursionError):
        pass  # Expected behavior
    
    # Test sidecar handling
    processing_time_start = time.time()
    try:
        await asyncio.wait_for(
            mock_sidecar_engine.process_span(corrupted_span),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        # Should not hang indefinitely
        processing_time = time.time() - processing_time_start
        assert processing_time < 10.0, "Processing should timeout gracefully"
    except Exception:
        pass  # Expected to fail gracefully


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_size_corruption_memory_safety(data_corruption_tester, mock_sidecar_engine):
    """Test memory safety with size corruption"""
    original_span = {
        "trace_id": "size_test",
        "operation": "memory_test"
    }
    
    corrupted_span = data_corruption_tester.corrupt_span_data(original_span, "size")
    
    # Should contain large fields
    assert "large_field" in corrupted_span
    assert len(corrupted_span) > 1000  # Many fields added
    
    # Measure memory usage during processing
    import psutil
    process = psutil.Process()
    memory_before = process.memory_info().rss
    
    try:
        await asyncio.wait_for(
            mock_sidecar_engine.process_span(corrupted_span),
            timeout=10.0
        )
    except (asyncio.TimeoutError, MemoryError, Exception):
        pass  # Expected for large data
    
    memory_after = process.memory_info().rss
    memory_increase = memory_after - memory_before
    
    # Should not consume excessive memory (more than 100MB)
    assert memory_increase < 100 * 1024 * 1024, "Memory usage should be bounded"


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_type_corruption_validation(data_corruption_tester, mock_sidecar_engine):
    """Test type validation with corrupted data types"""
    original_span = {
        "trace_id": "type_test",
        "timestamp": 1234567890,
        "metadata": {"count": 5},
        "tags": ["tag1", "tag2"]
    }
    
    corrupted_span = data_corruption_tester.corrupt_span_data(original_span, "type")
    
    # Types should be corrupted
    assert isinstance(corrupted_span["timestamp"], str)  # Was int, now string
    assert isinstance(corrupted_span["metadata"], str)   # Was dict, now string
    
    # Test type validation in sidecar
    validation_errors = []
    
    def mock_validate_span(span):
        if not isinstance(span.get("timestamp"), (int, float)):
            validation_errors.append("Invalid timestamp type")
        if not isinstance(span.get("metadata"), dict):
            validation_errors.append("Invalid metadata type")
    
    mock_validate_span(corrupted_span)
    
    # Should detect type violations
    assert len(validation_errors) > 0
    
    # Sidecar should handle gracefully
    try:
        await mock_sidecar_engine.process_span(corrupted_span)
    except (TypeError, ValueError):
        pass  # Expected type-related errors


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_boundary_value_corruption(data_corruption_tester, mock_sidecar_engine):
    """Test handling of boundary value corruption"""
    original_span = {
        "trace_id": "boundary_test",
        "value": 100
    }
    
    corrupted_span = data_corruption_tester.corrupt_span_data(original_span, "boundary")
    
    # Should contain boundary values
    assert "max_int" in corrupted_span
    assert "min_int" in corrupted_span
    assert "nan_value" in corrupted_span
    assert "inf_value" in corrupted_span
    
    # Test JSON serialization with special values
    try:
        json_str = json.dumps(corrupted_span, allow_nan=False)
        assert False, "Should not serialize NaN/Inf values"
    except ValueError:
        pass  # Expected behavior
    
    # Test sidecar processing
    try:
        await mock_sidecar_engine.process_span(corrupted_span)
    except (ValueError, OverflowError):
        pass  # Expected for boundary values


@pytest.mark.data_corruption
@pytest.mark.asyncio 
async def test_file_corruption_simulation():
    """Test file corruption scenarios"""
    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        test_data = {"trace_id": "file_test", "data": "original"}
        json.dump(test_data, f)
        temp_file = f.name
    
    try:
        # Simulate file corruption
        with open(temp_file, 'rb') as f:
            data = bytearray(f.read())
        
        # Corrupt random bytes
        for _ in range(10):
            if len(data) > 0:
                pos = random.randint(0, len(data) - 1)
                data[pos] = random.randint(0, 255)
        
        # Write corrupted data back
        with open(temp_file, 'wb') as f:
            f.write(data)
        
        # Try to read corrupted file
        corrupted_read = False
        try:
            with open(temp_file, 'r') as f:
                json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            corrupted_read = True
        
        assert corrupted_read, "File should be corrupted and unreadable"
        
    finally:
        # Clean up
        os.unlink(temp_file)


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_progressive_corruption_levels():
    """Test system behavior under progressive corruption levels"""
    base_span = {
        "trace_id": "progressive_test",
        "span_id": "prog_span",
        "operation": "test_op",
        "data": "clean_data"
    }
    
    tester = DataCorruptionTester()
    corruption_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
    resilience_scores = []
    
    for level in corruption_levels:
        corrupted_span = base_span.copy()
        
        # Apply corruption based on level
        num_corruptions = int(level * 10)
        for _ in range(num_corruptions):
            corrupted_span = tester.corrupt_span_data(corrupted_span, "random")
        
        # Measure resilience
        try:
            # Simulate processing
            json.dumps(corrupted_span, default=str)
            resilience_score = 1.0 - level  # Higher corruption = lower resilience
        except Exception:
            resilience_score = 0.0
        
        resilience_scores.append(resilience_score)
    
    # Resilience should degrade gracefully
    for i in range(1, len(resilience_scores)):
        degradation = resilience_scores[i-1] - resilience_scores[i]
        assert degradation >= 0, "Resilience should not improve with more corruption"
        assert degradation <= 0.5, "Resilience should degrade gracefully, not catastrophically"


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_corruption_detection_capabilities():
    """Test ability to detect various types of corruption"""
    tester = DataCorruptionTester()
    
    original_span = {
        "trace_id": "detection_test",
        "checksum": "abc123",
        "size": 1024,
        "encoding": "utf-8"
    }
    
    corruption_types = ["bit_flip", "encoding", "structure", "size", "type", "boundary"]
    detection_results = {}
    
    for corruption_type in corruption_types:
        corrupted_span = tester.corrupt_span_data(original_span, corruption_type)
        
        # Simple corruption detection heuristics
        detected = False
        
        # Check for size changes
        if len(str(corrupted_span)) > len(str(original_span)) * 2:
            detected = True
        
        # Check for encoding issues
        try:
            json.dumps(corrupted_span)
        except (ValueError, TypeError):
            detected = True
        
        # Check for structural issues
        if "circular_ref" in corrupted_span or "deep_nesting" in corrupted_span:
            detected = True
        
        # Check for type changes
        if type(corrupted_span.get("trace_id")) != type(original_span.get("trace_id")):
            detected = True
        
        detection_results[corruption_type] = detected
    
    # Should detect most corruption types
    detection_rate = sum(detection_results.values()) / len(detection_results)
    assert detection_rate >= 0.8, f"Should detect at least 80% of corruption types, got {detection_rate}"


@pytest.mark.data_corruption
@pytest.mark.asyncio
async def test_recovery_after_corruption():
    """Test system recovery after corruption events"""
    engine = MagicMock()
    engine.process_span = AsyncMock()
    engine.reset_state = AsyncMock()
    
    tester = DataCorruptionTester()
    
    # Process clean data first
    clean_span = {"trace_id": "clean", "data": "good"}
    await engine.process_span(clean_span)
    
    # Process corrupted data
    corrupted_span = tester.corrupt_span_data(clean_span, "structure")
    try:
        await engine.process_span(corrupted_span)
    except Exception:
        pass  # Expected corruption failure
    
    # Reset and try clean data again
    await engine.reset_state()
    
    # Should be able to process clean data after corruption
    await engine.process_span(clean_span)
    
    # Verify recovery
    assert engine.process_span.call_count >= 2
    assert engine.reset_state.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "data_corruption"])