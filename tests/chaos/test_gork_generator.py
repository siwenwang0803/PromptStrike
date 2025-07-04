"""
Test suite for gork (garbled data) generator
"""

import pytest
import json
import base64
import zlib
from tests.chaos.gork_generator import GorkGenerator, GorkType


@pytest.fixture
def gork_generator():
    """Fixture for gork generator"""
    return GorkGenerator(seed=42)


@pytest.fixture
def sample_data():
    """Fixture for sample data to be gorked"""
    return {
        "text": "Hello World",
        "number": 42,
        "binary": b"binary_data",
        "json": {"key": "value"},
        "list": [1, 2, 3, 4, 5]
    }


def test_gork_generator_initialization(gork_generator):
    """Test gork generator initialization"""
    assert gork_generator is not None
    assert gork_generator.gork_strategies is not None
    assert len(gork_generator.gork_strategies) > 0


def test_random_binary_gork(gork_generator, sample_data):
    """Test random binary gork generation"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.RANDOM_BINARY
    )
    
    assert result.gork_type == GorkType.RANDOM_BINARY
    assert result.gork_data != sample_data
    assert len(result.corruption_points) > 0
    assert len(result.expected_failures) > 0


def test_null_byte_injection_gork(gork_generator, sample_data):
    """Test null byte injection gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.NULL_BYTE_INJECTION
    )
    
    assert result.gork_type == GorkType.NULL_BYTE_INJECTION
    assert result.gork_data != sample_data
    # Should have null bytes in the data
    if isinstance(result.gork_data, str):
        assert '\x00' in result.gork_data


def test_high_bit_set_gork(gork_generator, sample_data):
    """Test high bit set gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.HIGH_BIT_SET
    )
    
    assert result.gork_type == GorkType.HIGH_BIT_SET
    assert result.gork_data != sample_data


def test_invalid_utf8_gork(gork_generator, sample_data):
    """Test invalid UTF-8 gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.INVALID_UTF8
    )
    
    assert result.gork_type == GorkType.INVALID_UTF8
    assert result.gork_data != sample_data
    # Should have invalid UTF-8 sequences
    if isinstance(result.gork_data, str):
        assert any(ord(c) > 127 for c in result.gork_data)


def test_mixed_encoding_gork(gork_generator, sample_data):
    """Test mixed encoding gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.MIXED_ENCODING
    )
    
    assert result.gork_type == GorkType.MIXED_ENCODING
    assert result.gork_data != sample_data


def test_overlong_utf8_gork(gork_generator, sample_data):
    """Test overlong UTF-8 gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.OVERLONG_UTF8
    )
    
    assert result.gork_type == GorkType.OVERLONG_UTF8
    assert result.gork_data != sample_data


def test_bom_corruption_gork(gork_generator, sample_data):
    """Test BOM corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.BOM_CORRUPTION
    )
    
    assert result.gork_type == GorkType.BOM_CORRUPTION
    assert result.gork_data != sample_data


def test_protobuf_corruption_gork(gork_generator, sample_data):
    """Test protobuf corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.PROTOBUF_CORRUPTION
    )
    
    assert result.gork_type == GorkType.PROTOBUF_CORRUPTION
    assert result.gork_data != sample_data


def test_json_corruption_gork(gork_generator, sample_data):
    """Test JSON corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.JSON_CORRUPTION
    )
    
    assert result.gork_type == GorkType.JSON_CORRUPTION
    assert result.gork_data != sample_data
    
    # If the result is a string, it might be corrupted JSON
    if isinstance(result.gork_data, str):
        try:
            json.loads(result.gork_data)
            assert False, "Should have corrupted JSON"
        except json.JSONDecodeError:
            pass  # Expected


def test_xml_corruption_gork(gork_generator, sample_data):
    """Test XML corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.XML_CORRUPTION
    )
    
    assert result.gork_type == GorkType.XML_CORRUPTION
    assert result.gork_data != sample_data


def test_gzip_corruption_gork(gork_generator, sample_data):
    """Test GZIP corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.GZIP_CORRUPTION
    )
    
    assert result.gork_type == GorkType.GZIP_CORRUPTION
    assert result.gork_data != sample_data


def test_compression_bomb_gork(gork_generator, sample_data):
    """Test compression bomb gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.COMPRESSION_BOMB
    )
    
    assert result.gork_type == GorkType.COMPRESSION_BOMB
    assert result.gork_data != sample_data
    # Should be significantly larger than original
    if isinstance(result.gork_data, (str, bytes)):
        assert len(str(result.gork_data)) > len(str(sample_data))


def test_base64_corruption_gork(gork_generator, sample_data):
    """Test Base64 corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.BASE64_CORRUPTION
    )
    
    assert result.gork_type == GorkType.BASE64_CORRUPTION
    assert result.gork_data != sample_data


def test_hex_corruption_gork(gork_generator, sample_data):
    """Test hex corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.HEX_CORRUPTION
    )
    
    assert result.gork_type == GorkType.HEX_CORRUPTION
    assert result.gork_data != sample_data


def test_unicode_direction_gork(gork_generator, sample_data):
    """Test Unicode direction gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.UNICODE_DIRECTION
    )
    
    assert result.gork_type == GorkType.UNICODE_DIRECTION
    assert result.gork_data != sample_data


def test_zero_width_chars_gork(gork_generator, sample_data):
    """Test zero-width characters gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.ZERO_WIDTH_CHARS
    )
    
    assert result.gork_type == GorkType.ZERO_WIDTH_CHARS
    assert result.gork_data != sample_data


def test_epoch_corruption_gork(gork_generator, sample_data):
    """Test epoch corruption gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.EPOCH_CORRUPTION
    )
    
    assert result.gork_type == GorkType.EPOCH_CORRUPTION
    assert result.gork_data != sample_data


def test_hash_collision_gork(gork_generator, sample_data):
    """Test hash collision gork"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.HASH_COLLISION
    )
    
    assert result.gork_type == GorkType.HASH_COLLISION
    assert result.gork_data != sample_data


def test_random_gork_generation(gork_generator, sample_data):
    """Test random gork generation"""
    result = gork_generator.generate_gork(sample_data)  # No specific type
    
    assert result.gork_type in GorkType
    assert result.gork_data != sample_data
    assert len(result.corruption_points) > 0
    assert len(result.expected_failures) > 0


def test_batch_gork_generation(gork_generator):
    """Test batch gork generation"""
    data_samples = [
        "simple string",
        {"key": "value"},
        [1, 2, 3],
        42,
        b"binary_data"
    ]
    
    results = gork_generator.batch_generate_gork(
        data_samples, 
        gork_types=[
            GorkType.RANDOM_BINARY,
            GorkType.INVALID_UTF8,
            GorkType.JSON_CORRUPTION
        ]
    )
    
    assert len(results) == len(data_samples)
    for result in results:
        assert result.gork_type in [
            GorkType.RANDOM_BINARY,
            GorkType.INVALID_UTF8,
            GorkType.JSON_CORRUPTION
        ]


def test_gork_severity_levels(gork_generator, sample_data):
    """Test gork severity levels"""
    # Test different severity levels
    high_severity_types = [
        GorkType.COMPRESSION_BOMB,
        GorkType.BUFFER_OVERFLOW,
        GorkType.HEAP_CORRUPTION
    ]
    
    for gork_type in high_severity_types:
        result = gork_generator.generate_gork(sample_data, gork_type)
        severity = gork_generator.get_gork_severity(gork_type)
        assert severity == "high"


def test_gork_with_custom_corruption_rate(gork_generator, sample_data):
    """Test gork with custom corruption rate"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.RANDOM_BINARY,
        corruption_rate=0.8
    )
    
    assert result.gork_type == GorkType.RANDOM_BINARY
    assert result.gork_data != sample_data
    # Higher corruption rate should result in more corruption points
    assert len(result.corruption_points) > 0


def test_gork_with_span_data(gork_generator):
    """Test gork generation with span data"""
    span_data = {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7",
        "operation_name": "test_operation",
        "start_time": 1640995200000000000,
        "end_time": 1640995200100000000,
        "tags": {"service": "test", "version": "1.0"}
    }
    
    result = gork_generator.generate_gork(
        span_data, 
        GorkType.PROTOBUF_CORRUPTION
    )
    
    assert result.gork_type == GorkType.PROTOBUF_CORRUPTION
    assert result.gork_data != span_data


def test_gork_test_suite_generation(gork_generator, sample_data):
    """Test gork test suite generation"""
    test_suite = gork_generator.generate_gork_test_suite(
        sample_data,
        include_categories=[
            "binary_corruption",
            "encoding_corruption",
            "protocol_corruption"
        ]
    )
    
    assert len(test_suite) > 0
    # Should have different gork types
    gork_types = {result.gork_type for result in test_suite}
    assert len(gork_types) > 1


def test_gork_validation(gork_generator, sample_data):
    """Test gork validation"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.INVALID_UTF8
    )
    
    # Should be able to validate the corruption
    is_valid = gork_generator.validate_gork(result)
    assert not is_valid  # Should be invalid due to corruption


def test_gork_recovery_suggestions(gork_generator, sample_data):
    """Test gork recovery suggestions"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.INVALID_UTF8
    )
    
    suggestions = gork_generator.get_recovery_suggestions(result.gork_type)
    assert len(suggestions) > 0
    assert isinstance(suggestions[0], str)


def test_gork_statistics(gork_generator, sample_data):
    """Test gork statistics collection"""
    results = []
    
    for _ in range(10):
        result = gork_generator.generate_gork(sample_data)
        results.append(result)
    
    stats = gork_generator.get_gork_statistics(results)
    assert "gork_type_distribution" in stats
    assert "corruption_point_average" in stats
    assert "severity_distribution" in stats


def test_network_corruption_gork(gork_generator, sample_data):
    """Test network corruption gork types"""
    network_types = [
        GorkType.PACKET_CORRUPTION,
        GorkType.TCP_CORRUPTION,
        GorkType.ETHERNET_CORRUPTION
    ]
    
    for gork_type in network_types:
        result = gork_generator.generate_gork(sample_data, gork_type)
        assert result.gork_type == gork_type
        assert result.gork_data != sample_data


def test_memory_corruption_gork(gork_generator, sample_data):
    """Test memory corruption gork types"""
    memory_types = [
        GorkType.HEAP_CORRUPTION,
        GorkType.STACK_CORRUPTION,
        GorkType.BUFFER_OVERFLOW,
        GorkType.USE_AFTER_FREE
    ]
    
    for gork_type in memory_types:
        result = gork_generator.generate_gork(sample_data, gork_type)
        assert result.gork_type == gork_type
        assert result.gork_data != sample_data


def test_filesystem_corruption_gork(gork_generator, sample_data):
    """Test filesystem corruption gork types"""
    fs_types = [
        GorkType.INODE_CORRUPTION,
        GorkType.METADATA_CORRUPTION,
        GorkType.BLOCK_CORRUPTION
    ]
    
    for gork_type in fs_types:
        result = gork_generator.generate_gork(sample_data, gork_type)
        assert result.gork_type == gork_type
        assert result.gork_data != sample_data


def test_cryptographic_corruption_gork(gork_generator, sample_data):
    """Test cryptographic corruption gork types"""
    crypto_types = [
        GorkType.HASH_COLLISION,
        GorkType.SIGNATURE_CORRUPTION,
        GorkType.CERTIFICATE_CORRUPTION
    ]
    
    for gork_type in crypto_types:
        result = gork_generator.generate_gork(sample_data, gork_type)
        assert result.gork_type == gork_type
        assert result.gork_data != sample_data


def test_gork_with_large_data(gork_generator):
    """Test gork generation with large data"""
    large_data = {
        "large_string": "A" * 10000,
        "large_list": list(range(1000)),
        "large_dict": {f"key_{i}": f"value_{i}" for i in range(1000)}
    }
    
    result = gork_generator.generate_gork(
        large_data, 
        GorkType.RANDOM_BINARY
    )
    
    assert result.gork_type == GorkType.RANDOM_BINARY
    assert result.gork_data != large_data


def test_gork_with_nested_data(gork_generator):
    """Test gork generation with deeply nested data"""
    nested_data = {"level": 0}
    current = nested_data
    for i in range(1, 10):
        current["nested"] = {"level": i}
        current = current["nested"]
    
    result = gork_generator.generate_gork(
        nested_data, 
        GorkType.JSON_CORRUPTION
    )
    
    assert result.gork_type == GorkType.JSON_CORRUPTION
    assert result.gork_data != nested_data


def test_gork_deterministic_with_seed(gork_generator):
    """Test gork generation is deterministic with seed"""
    data = {"test": "data"}
    
    result1 = gork_generator.generate_gork(data, GorkType.RANDOM_BINARY)
    result2 = gork_generator.generate_gork(data, GorkType.RANDOM_BINARY)
    
    # With same seed, should produce same result
    assert result1.gork_data == result2.gork_data


def test_gork_expected_failures(gork_generator, sample_data):
    """Test gork expected failures are populated"""
    result = gork_generator.generate_gork(
        sample_data, 
        GorkType.INVALID_UTF8
    )
    
    assert len(result.expected_failures) > 0
    # Should have descriptive failure modes
    for failure in result.expected_failures:
        assert isinstance(failure, str)
        assert len(failure) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])