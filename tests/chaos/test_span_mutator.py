"""
Test suite for span mutator and malformed span generator
"""

import pytest
import uuid
import time
from datetime import datetime

from tests.chaos.span_mutator import SpanMutator, SpanMalformationType


@pytest.fixture
def span_mutator():
    """Fixture for span mutator"""
    return SpanMutator(seed=42)


@pytest.fixture
def valid_span():
    """Fixture for valid span data"""
    return {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7",
        "parent_span_id": None,
        "operation_name": "test_operation",
        "start_time": 1640995200000000000,
        "end_time": 1640995200100000000,
        "duration": 100000000,
        "tags": {"service": "test", "version": "1.0"},
        "logs": [],
        "status": {"code": "OK", "message": ""}
    }


def test_span_mutator_initialization(span_mutator):
    """Test span mutator initialization"""
    assert span_mutator is not None
    assert span_mutator.valid_span_template is not None
    assert span_mutator.malformation_strategies is not None


def test_invalid_trace_id_mutation(span_mutator, valid_span):
    """Test invalid trace ID mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_TRACE_ID
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_TRACE_ID
    assert result.malformed_span["trace_id"] != valid_span["trace_id"]
    assert result.target_field == "trace_id"


def test_invalid_span_id_mutation(span_mutator, valid_span):
    """Test invalid span ID mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_SPAN_ID
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_SPAN_ID
    assert result.malformed_span["span_id"] != valid_span["span_id"]
    assert result.target_field == "span_id"


def test_duplicate_span_id_mutation(span_mutator, valid_span):
    """Test duplicate span ID mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.DUPLICATE_SPAN_ID
    )
    
    assert result.malformation_type == SpanMalformationType.DUPLICATE_SPAN_ID
    assert result.malformed_span["span_id"] == "duplicate_span_id"
    assert result.target_field == "span_id"


def test_missing_ids_mutation(span_mutator, valid_span):
    """Test missing IDs mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.MISSING_IDS
    )
    
    assert result.malformation_type == SpanMalformationType.MISSING_IDS
    assert "trace_id" not in result.malformed_span or "span_id" not in result.malformed_span


def test_future_timestamp_mutation(span_mutator, valid_span):
    """Test future timestamp mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.FUTURE_TIMESTAMP
    )
    
    assert result.malformation_type == SpanMalformationType.FUTURE_TIMESTAMP
    assert result.malformed_span["start_time"] > time.time_ns()


def test_negative_timestamp_mutation(span_mutator, valid_span):
    """Test negative timestamp mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.NEGATIVE_TIMESTAMP
    )
    
    assert result.malformation_type == SpanMalformationType.NEGATIVE_TIMESTAMP
    assert result.malformed_span["start_time"] < 0


def test_invalid_timestamp_format_mutation(span_mutator, valid_span):
    """Test invalid timestamp format mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_TIMESTAMP_FORMAT
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_TIMESTAMP_FORMAT
    assert isinstance(result.malformed_span["start_time"], str)


def test_negative_duration_mutation(span_mutator, valid_span):
    """Test negative duration mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.NEGATIVE_DURATION
    )
    
    assert result.malformation_type == SpanMalformationType.NEGATIVE_DURATION
    assert result.malformed_span["duration"] < 0


def test_infinite_duration_mutation(span_mutator, valid_span):
    """Test infinite duration mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INFINITE_DURATION
    )
    
    assert result.malformation_type == SpanMalformationType.INFINITE_DURATION
    assert result.malformed_span["duration"] == float('inf')


def test_orphaned_span_mutation(span_mutator, valid_span):
    """Test orphaned span mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.ORPHANED_SPAN
    )
    
    assert result.malformation_type == SpanMalformationType.ORPHANED_SPAN
    assert result.malformed_span["parent_span_id"] == "nonexistent_parent"


def test_circular_parent_child_mutation(span_mutator, valid_span):
    """Test circular parent-child mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.CIRCULAR_PARENT_CHILD
    )
    
    assert result.malformation_type == SpanMalformationType.CIRCULAR_PARENT_CHILD
    assert result.malformed_span["parent_span_id"] == result.malformed_span["span_id"]


def test_oversized_attributes_mutation(span_mutator, valid_span):
    """Test oversized attributes mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.OVERSIZED_ATTRIBUTES
    )
    
    assert result.malformation_type == SpanMalformationType.OVERSIZED_ATTRIBUTES
    assert len(result.malformed_span["tags"]) > 10


def test_invalid_attribute_types_mutation(span_mutator, valid_span):
    """Test invalid attribute types mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_ATTRIBUTE_TYPES
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_ATTRIBUTE_TYPES
    # Should have non-string attribute values
    has_non_string = False
    for value in result.malformed_span["tags"].values():
        if not isinstance(value, str):
            has_non_string = True
            break
    assert has_non_string


def test_binary_attributes_mutation(span_mutator, valid_span):
    """Test binary attributes mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.BINARY_ATTRIBUTES
    )
    
    assert result.malformation_type == SpanMalformationType.BINARY_ATTRIBUTES
    # Should have binary data in attributes
    has_binary = False
    for value in result.malformed_span["tags"].values():
        if isinstance(value, bytes):
            has_binary = True
            break
    assert has_binary


def test_invalid_event_timestamps_mutation(span_mutator, valid_span):
    """Test invalid event timestamps mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_EVENT_TIMESTAMPS
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_EVENT_TIMESTAMPS
    assert len(result.malformed_span["logs"]) > 0


def test_oversized_events_mutation(span_mutator, valid_span):
    """Test oversized events mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.OVERSIZED_EVENTS
    )
    
    assert result.malformation_type == SpanMalformationType.OVERSIZED_EVENTS
    assert len(result.malformed_span["logs"]) > 50


def test_invalid_span_kind_mutation(span_mutator, valid_span):
    """Test invalid span kind mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_SPAN_KIND
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_SPAN_KIND
    assert result.malformed_span["kind"] not in ["CLIENT", "SERVER", "PRODUCER", "CONSUMER", "INTERNAL"]


def test_invalid_status_code_mutation(span_mutator, valid_span):
    """Test invalid status code mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_STATUS_CODE
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_STATUS_CODE
    assert result.malformed_span["status"]["code"] not in ["OK", "ERROR", "TIMEOUT"]


def test_invalid_utf8_mutation(span_mutator, valid_span):
    """Test invalid UTF-8 mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_UTF8
    )
    
    assert result.malformation_type == SpanMalformationType.INVALID_UTF8
    # Should have invalid UTF-8 in string fields
    operation_name = result.malformed_span["operation_name"]
    assert '\xff' in operation_name or '\xfe' in operation_name


def test_mixed_encoding_mutation(span_mutator, valid_span):
    """Test mixed encoding mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.MIXED_ENCODING
    )
    
    assert result.malformation_type == SpanMalformationType.MIXED_ENCODING
    # Should have mixed encoding issues
    operation_name = result.malformed_span["operation_name"]
    assert len(operation_name) > len(valid_span["operation_name"])


def test_control_characters_mutation(span_mutator, valid_span):
    """Test control characters mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.CONTROL_CHARACTERS
    )
    
    assert result.malformation_type == SpanMalformationType.CONTROL_CHARACTERS
    # Should have control characters
    operation_name = result.malformed_span["operation_name"]
    has_control = any(ord(c) < 32 for c in operation_name)
    assert has_control


def test_deep_nesting_mutation(span_mutator, valid_span):
    """Test deep nesting mutation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.DEEP_NESTING
    )
    
    assert result.malformation_type == SpanMalformationType.DEEP_NESTING
    # Should have deeply nested structure
    nested_data = result.malformed_span["nested_data"]
    depth = 0
    current = nested_data
    while isinstance(current, dict) and "nested" in current:
        depth += 1
        current = current["nested"]
    assert depth > 100


def test_malformed_span_generator(span_mutator, valid_span):
    """Test malformed span generator"""
    generator = span_mutator.create_malformed_span_generator(
        base_span=valid_span,
        malformation_types=[
            SpanMalformationType.INVALID_TRACE_ID,
            SpanMalformationType.NEGATIVE_DURATION,
            SpanMalformationType.OVERSIZED_ATTRIBUTES
        ]
    )
    
    malformed_spans = list(generator.generate_malformed_spans(count=5))
    assert len(malformed_spans) == 5
    
    # Each span should be different
    for span in malformed_spans:
        assert span != valid_span


def test_random_malformation(span_mutator, valid_span):
    """Test random malformation selection"""
    result = span_mutator.mutate_span(valid_span)  # No specific type
    
    assert result.malformation_type in SpanMalformationType
    assert result.malformed_span != valid_span


def test_batch_mutation(span_mutator):
    """Test batch mutation of multiple spans"""
    spans = [
        {"trace_id": f"trace_{i}", "span_id": f"span_{i}", "operation": f"op_{i}"}
        for i in range(10)
    ]
    
    results = span_mutator.batch_mutate_spans(
        spans, 
        malformation_types=[
            SpanMalformationType.INVALID_TRACE_ID,
            SpanMalformationType.NEGATIVE_DURATION
        ]
    )
    
    assert len(results) == 10
    for result in results:
        assert result.malformation_type in [
            SpanMalformationType.INVALID_TRACE_ID,
            SpanMalformationType.NEGATIVE_DURATION
        ]


def test_malformation_validation(span_mutator, valid_span):
    """Test malformation validation"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_TRACE_ID
    )
    
    # Should be able to validate the malformation
    is_valid = span_mutator.validate_span(result.malformed_span)
    assert not is_valid  # Should be invalid due to malformation


def test_malformation_severity_scoring(span_mutator, valid_span):
    """Test malformation severity scoring"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_TRACE_ID
    )
    
    severity = span_mutator.get_malformation_severity(result.malformation_type)
    assert severity > 0


def test_malformation_recovery(span_mutator, valid_span):
    """Test malformation recovery suggestions"""
    result = span_mutator.mutate_span(
        valid_span, 
        SpanMalformationType.INVALID_TRACE_ID
    )
    
    recovery = span_mutator.get_recovery_suggestions(result.malformation_type)
    assert len(recovery) > 0
    assert isinstance(recovery[0], str)


def test_span_corruption_statistics(span_mutator, valid_span):
    """Test span corruption statistics"""
    results = []
    
    for _ in range(20):
        result = span_mutator.mutate_span(valid_span)
        results.append(result)
    
    stats = span_mutator.get_corruption_statistics(results)
    assert "malformation_counts" in stats
    assert "severity_distribution" in stats
    assert "success_rate" in stats


def test_realistic_malformation_scenarios(span_mutator):
    """Test realistic malformation scenarios"""
    # Test realistic span that might come from production
    production_span = {
        "trace_id": "550e8400-e29b-41d4-a716-446655440000",
        "span_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "parent_span_id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
        "operation_name": "http_request",
        "start_time": 1640995200123456789,
        "end_time": 1640995200223456789,
        "duration": 100000000,
        "tags": {
            "http.method": "GET",
            "http.url": "https://api.example.com/users",
            "http.status_code": "200",
            "service.name": "user-service",
            "service.version": "1.2.3"
        },
        "logs": [
            {
                "timestamp": 1640995200150000000,
                "level": "info",
                "message": "Processing request"
            }
        ],
        "status": {
            "code": "OK",
            "message": ""
        }
    }
    
    # Test various malformations
    malformation_types = [
        SpanMalformationType.INVALID_TRACE_ID,
        SpanMalformationType.NEGATIVE_DURATION,
        SpanMalformationType.OVERSIZED_ATTRIBUTES,
        SpanMalformationType.INVALID_UTF8,
        SpanMalformationType.CIRCULAR_PARENT_CHILD
    ]
    
    for malformation_type in malformation_types:
        result = span_mutator.mutate_span(production_span, malformation_type)
        assert result.malformation_type == malformation_type
        assert result.malformed_span != production_span

# Additional tests for remaining malformation types to ensure full coverage
@pytest.mark.parametrize("malformation_type,target_field,assertion", [
    (SpanMalformationType.TIMESTAMP_OVERFLOW, "start_time", lambda v: isinstance(v, int)),
    (SpanMalformationType.DURATION_LONGER_THAN_TRACE, "duration", lambda v: v > 0),
    (SpanMalformationType.INVALID_PARENT_ID, "parent_span_id", lambda v: v == "INVALID_PARENT_ID"),
    (SpanMalformationType.RESERVED_ATTRIBUTE_NAMES, "tags", lambda v: "__proto__" in v),
    (SpanMalformationType.MALFORMED_EVENT_STRUCTURE, "logs", lambda v: isinstance(v, list) and any(isinstance(item, (str, dict)) for item in v)),
    (SpanMalformationType.INVALID_RESOURCE_ATTRIBUTES, "resource", lambda v: isinstance(v, dict) and any(not isinstance(val, str) for val in v.values())),
    (SpanMalformationType.MISSING_SERVICE_NAME, "resource", lambda v: "service.name" not in v),
    (SpanMalformationType.CONFLICTING_RESOURCES, "resource", lambda v: any("override" in k for k in v)),
    (SpanMalformationType.MALFORMED_LINKS, "links", lambda v: isinstance(v, list) and any(not isinstance(item, dict) for item in v)),
])
def test_specific_malformation_strategies(span_mutator, valid_span, malformation_type, target_field, assertion):
    """Test specific malformation strategies for remaining types"""
    result = span_mutator.mutate_span(valid_span.copy(), malformation_type)
    assert result.malformation_type == malformation_type
    malformed = result.malformed_span.get(target_field)
    assert assertion(malformed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
