"""
Span Mutator and Malformed Span Generator

Specialized mutation tools for OpenTelemetry-style spans and distributed tracing data.
Focuses on creating malformed spans that test resilience of replay engines.
"""

import uuid
import random
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class SpanMalformationType(Enum):
    """Types of span malformations"""
    # ID corruption
    INVALID_TRACE_ID = "invalid_trace_id"
    INVALID_SPAN_ID = "invalid_span_id"
    DUPLICATE_SPAN_ID = "duplicate_span_id"
    MISSING_IDS = "missing_ids"
    
    # Timestamp corruption
    FUTURE_TIMESTAMP = "future_timestamp"
    NEGATIVE_TIMESTAMP = "negative_timestamp"
    INVALID_TIMESTAMP_FORMAT = "invalid_timestamp_format"
    TIMESTAMP_OVERFLOW = "timestamp_overflow"
    
    # Duration corruption
    NEGATIVE_DURATION = "negative_duration"
    INFINITE_DURATION = "infinite_duration"
    DURATION_LONGER_THAN_TRACE = "duration_longer_than_trace"
    
    # Hierarchy corruption
    ORPHANED_SPAN = "orphaned_span"
    CIRCULAR_PARENT_CHILD = "circular_parent_child"
    INVALID_PARENT_ID = "invalid_parent_id"
    DEEP_NESTING = "deep_nesting"
    
    # Attribute corruption
    OVERSIZED_ATTRIBUTES = "oversized_attributes"
    INVALID_ATTRIBUTE_TYPES = "invalid_attribute_types"
    RESERVED_ATTRIBUTE_NAMES = "reserved_attribute_names"
    BINARY_ATTRIBUTES = "binary_attributes"
    
    # Event corruption
    INVALID_EVENT_TIMESTAMPS = "invalid_event_timestamps"
    OVERSIZED_EVENTS = "oversized_events"
    MALFORMED_EVENT_STRUCTURE = "malformed_event_structure"
    
    # Resource corruption
    INVALID_RESOURCE_ATTRIBUTES = "invalid_resource_attributes"
    MISSING_SERVICE_NAME = "missing_service_name"
    CONFLICTING_RESOURCES = "conflicting_resources"
    
    # Protocol corruption
    INVALID_SPAN_KIND = "invalid_span_kind"
    INVALID_STATUS_CODE = "invalid_status_code"
    MALFORMED_LINKS = "malformed_links"
    
    # Encoding corruption
    INVALID_UTF8 = "invalid_utf8"
    MIXED_ENCODING = "mixed_encoding"
    CONTROL_CHARACTERS = "control_characters"

@dataclass
class SpanMalformation:
    """Details of a span malformation"""
    malformation_type: SpanMalformationType
    target_field: str
    original_value: Any
    malformed_value: Any
    description: str

class SpanMutator:
    """
    Specialized mutator for OpenTelemetry spans and tracing data.
    Creates realistic malformations that could occur in distributed systems.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)
        
        # Valid span structure template
        self.valid_span_template = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "parent_span_id": None,
            "operation_name": "example_operation",
            "start_time": 1640995200000000000,  # nanoseconds
            "end_time": 1640995200100000000,
            "duration": 100000000,  # nanoseconds
            "tags": {},
            "logs": [],
            "status": {
                "code": "OK",
                "message": ""
            },
            "kind": "SPAN_KIND_INTERNAL",
            "resource": {
                "service.name": "example_service",
                "service.version": "1.0.0"
            }
        }
        
        # Malformation strategies
        self.malformation_strategies = {
            SpanMalformationType.INVALID_TRACE_ID: self._malform_trace_id,
            SpanMalformationType.INVALID_SPAN_ID: self._malform_span_id,
            SpanMalformationType.DUPLICATE_SPAN_ID: self._malform_duplicate_span_id,
            SpanMalformationType.MISSING_IDS: self._malform_missing_ids,
            SpanMalformationType.FUTURE_TIMESTAMP: self._malform_future_timestamp,
            SpanMalformationType.NEGATIVE_TIMESTAMP: self._malform_negative_timestamp,
            SpanMalformationType.INVALID_TIMESTAMP_FORMAT: self._malform_timestamp_format,
            SpanMalformationType.TIMESTAMP_OVERFLOW: self._malform_timestamp_overflow,
            SpanMalformationType.NEGATIVE_DURATION: self._malform_negative_duration,
            SpanMalformationType.INFINITE_DURATION: self._malform_infinite_duration,
            SpanMalformationType.DURATION_LONGER_THAN_TRACE: self._malform_duration_overflow,
            SpanMalformationType.ORPHANED_SPAN: self._malform_orphaned_span,
            SpanMalformationType.CIRCULAR_PARENT_CHILD: self._malform_circular_reference,
            SpanMalformationType.INVALID_PARENT_ID: self._malform_invalid_parent,
            SpanMalformationType.DEEP_NESTING: self._malform_deep_nesting,
            SpanMalformationType.OVERSIZED_ATTRIBUTES: self._malform_oversized_attributes,
            SpanMalformationType.INVALID_ATTRIBUTE_TYPES: self._malform_attribute_types,
            SpanMalformationType.RESERVED_ATTRIBUTE_NAMES: self._malform_reserved_names,
            SpanMalformationType.BINARY_ATTRIBUTES: self._malform_binary_attributes,
            SpanMalformationType.INVALID_EVENT_TIMESTAMPS: self._malform_event_timestamps,
            SpanMalformationType.OVERSIZED_EVENTS: self._malform_oversized_events,
            SpanMalformationType.MALFORMED_EVENT_STRUCTURE: self._malform_event_structure,
            SpanMalformationType.INVALID_RESOURCE_ATTRIBUTES: self._malform_resource_attributes,
            SpanMalformationType.MISSING_SERVICE_NAME: self._malform_missing_service_name,
            SpanMalformationType.CONFLICTING_RESOURCES: self._malform_conflicting_resources,
            SpanMalformationType.INVALID_SPAN_KIND: self._malform_span_kind,
            SpanMalformationType.INVALID_STATUS_CODE: self._malform_status_code,
            SpanMalformationType.MALFORMED_LINKS: self._malform_links,
            SpanMalformationType.INVALID_UTF8: self._malform_utf8,
            SpanMalformationType.MIXED_ENCODING: self._malform_mixed_encoding,
            SpanMalformationType.CONTROL_CHARACTERS: self._malform_control_characters,
        }
    
    def create_malformed_span(self, 
                            base_span: Optional[Dict[str, Any]] = None,
                            malformation_types: Optional[List[SpanMalformationType]] = None,
                            malformation_intensity: float = 0.3) -> tuple[Dict[str, Any], List[SpanMalformation]]:
        """
        Create a malformed span with specified malformations.
        
        Args:
            base_span: Base span to malform (uses template if None)
            malformation_types: Types of malformations to apply
            malformation_intensity: Probability of applying each malformation
            
        Returns:
            Tuple of (malformed_span, list_of_malformations)
        """
        if base_span is None:
            base_span = self._create_base_span()
        
        if malformation_types is None:
            malformation_types = list(SpanMalformationType)
        
        malformed_span = base_span.copy()
        malformations = []
        
        for malformation_type in malformation_types:
            if self.random.random() < malformation_intensity:
                try:
                    strategy = self.malformation_strategies[malformation_type]
                    malformation = strategy(malformed_span)
                    if malformation:
                        malformations.append(malformation)
                except Exception as e:
                    # Log error but continue with other malformations
                    continue
        
        return malformed_span, malformations
    
    def _create_base_span(self) -> Dict[str, Any]:
        """Create a valid base span for malformation"""
        base_span = self.valid_span_template.copy()
        
        # Randomize some fields
        base_span["trace_id"] = self._generate_valid_trace_id()
        base_span["span_id"] = self._generate_valid_span_id()
        base_span["operation_name"] = f"operation_{self.random.randint(1, 1000)}"
        
        # Realistic timestamp
        now = int(time.time() * 1_000_000_000)  # nanoseconds
        base_span["start_time"] = now
        base_span["end_time"] = now + self.random.randint(1_000_000, 100_000_000)  # 1ms to 100ms
        base_span["duration"] = base_span["end_time"] - base_span["start_time"]
        
        return base_span
    
    def _generate_valid_trace_id(self) -> str:
        """Generate a valid trace ID"""
        return ''.join([f'{self.random.randint(0, 15):x}' for _ in range(32)])
    
    def _generate_valid_span_id(self) -> str:
        """Generate a valid span ID"""
        return ''.join([f'{self.random.randint(0, 15):x}' for _ in range(16)])
    
    def mutate_span(self, span: Dict[str, Any], 
                   malformation_type: Optional[SpanMalformationType] = None) -> SpanMalformation:
        """
        Mutate a single span with a specific malformation type.
        
        Args:
            span: Span to mutate
            malformation_type: Type of malformation (random if None)
            
        Returns:
            SpanMalformation result
        """
        if malformation_type is None:
            malformation_type = self.random.choice(list(SpanMalformationType))
        
        original_span = span.copy()
        strategy = self.malformation_strategies[malformation_type]
        malformation = strategy(span)
        
        if malformation is None:
            # Create default malformation if strategy returned None
            malformation = SpanMalformation(
                malformation_type=malformation_type,
                target_field="unknown",
                original_value="unknown",
                malformed_value="unknown",
                description=f"Applied {malformation_type.value} malformation"
            )
        
        # Add malformed_span to the result
        malformation.malformed_span = span
        return malformation
    
    def batch_mutate_spans(self, spans: List[Dict[str, Any]], 
                          malformation_types: Optional[List[SpanMalformationType]] = None) -> List[SpanMalformation]:
        """Batch mutate multiple spans"""
        results = []
        for span in spans:
            malformation_type = None
            if malformation_types:
                malformation_type = self.random.choice(malformation_types)
            result = self.mutate_span(span, malformation_type)
            results.append(result)
        return results
    
    def validate_span(self, span: Dict[str, Any]) -> bool:
        """Validate if a span is properly formed"""
        try:
            # Check required fields
            required_fields = ["trace_id", "span_id", "operation_name"]
            for field in required_fields:
                if field not in span:
                    return False
            
            # Check trace_id format (32 hex chars)
            trace_id = span["trace_id"]
            if not isinstance(trace_id, str) or len(trace_id) != 32:
                return False
            
            # Check span_id format (16 hex chars)
            span_id = span["span_id"]
            if not isinstance(span_id, str) or len(span_id) != 16:
                return False
            
            # Check timestamps
            if "start_time" in span and "end_time" in span:
                if span["start_time"] > span["end_time"]:
                    return False
            
            return True
        except:
            return False
    
    def get_malformation_severity(self, malformation_type: SpanMalformationType) -> float:
        """Get severity score for a malformation type (0.0 to 1.0)"""
        severity_map = {
            SpanMalformationType.INVALID_TRACE_ID: 0.9,
            SpanMalformationType.INVALID_SPAN_ID: 0.9,
            SpanMalformationType.MISSING_IDS: 1.0,
            SpanMalformationType.CIRCULAR_PARENT_CHILD: 0.8,
            SpanMalformationType.DEEP_NESTING: 0.7,
            SpanMalformationType.OVERSIZED_ATTRIBUTES: 0.6,
            SpanMalformationType.OVERSIZED_EVENTS: 0.6,
            SpanMalformationType.BINARY_ATTRIBUTES: 0.5,
            SpanMalformationType.CONTROL_CHARACTERS: 0.5,
            SpanMalformationType.NEGATIVE_DURATION: 0.7,
            SpanMalformationType.INFINITE_DURATION: 0.8,
            SpanMalformationType.FUTURE_TIMESTAMP: 0.6,
            SpanMalformationType.NEGATIVE_TIMESTAMP: 0.7,
        }
        return severity_map.get(malformation_type, 0.5)
    
    def get_recovery_suggestions(self, malformation_type: SpanMalformationType) -> List[str]:
        """Get recovery suggestions for a malformation type"""
        suggestions = {
            SpanMalformationType.INVALID_TRACE_ID: [
                "Validate trace ID format before processing",
                "Implement trace ID sanitization",
                "Add error handling for malformed trace IDs"
            ],
            SpanMalformationType.OVERSIZED_ATTRIBUTES: [
                "Implement attribute size limits",
                "Add attribute truncation logic",
                "Monitor attribute memory usage"
            ],
            SpanMalformationType.CIRCULAR_PARENT_CHILD: [
                "Implement cycle detection in span hierarchy",
                "Add parent-child relationship validation",
                "Limit span hierarchy depth"
            ],
            SpanMalformationType.NEGATIVE_DURATION: [
                "Validate duration before storing",
                "Add timestamp consistency checks",
                "Implement duration calculation validation"
            ]
        }
        return suggestions.get(malformation_type, ["Review error handling for this malformation type"])
    
    def get_corruption_statistics(self, results: List[SpanMalformation]) -> Dict[str, Any]:
        """Get statistics about span corruptions"""
        if not results:
            return {"malformation_counts": {}, "severity_distribution": {}, "success_rate": 0.0}
        
        malformation_counts = {}
        severity_sum = 0.0
        
        for result in results:
            malformation_type = result.malformation_type.value
            malformation_counts[malformation_type] = malformation_counts.get(malformation_type, 0) + 1
            severity_sum += self.get_malformation_severity(result.malformation_type)
        
        avg_severity = severity_sum / len(results)
        
        return {
            "malformation_counts": malformation_counts,
            "severity_distribution": {"average": avg_severity},
            "success_rate": 1.0,  # All malformations succeeded
            "total_malformations": len(results)
        }
    
    def create_malformed_span_generator(self, base_span: Dict[str, Any], 
                                       malformation_types: List[SpanMalformationType]):
        """Create a generator for malformed spans"""
        return MalformedSpanGenerator(self, base_span, malformation_types)
    
    # Malformation strategy implementations
    
    def _malform_trace_id(self, span: Dict[str, Any]) -> SpanMalformation:
        """Malform trace ID"""
        original = span.get("trace_id", "")
        
        # Various trace ID corruptions
        corruptions = [
            "invalid_trace_id",
            "00000000000000000000000000000000",  # All zeros
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",  # Invalid hex
            "",  # Empty
            "short",  # Too short
            "x" * 100,  # Too long
        ]
        
        malformed = self.random.choice(corruptions)
        span["trace_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_TRACE_ID,
            target_field="trace_id",
            original_value=original,
            malformed_value=malformed,
            description="Corrupted trace ID with invalid format"
        )
    
    def _malform_span_id(self, span: Dict[str, Any]) -> SpanMalformation:
        """Malform span ID"""
        original = span.get("span_id", "")
        
        corruptions = [
            "invalid_span",
            "0000000000000000",  # All zeros
            "GGGGGGGGGGGGGGGG",  # Invalid hex
            "",  # Empty
            "x" * 50,  # Too long
        ]
        
        malformed = self.random.choice(corruptions)
        span["span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_SPAN_ID,
            target_field="span_id",
            original_value=original,
            malformed_value=malformed,
            description="Corrupted span ID with invalid format"
        )
    
    def _malform_duplicate_span_id(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create duplicate span ID"""
        original = span.get("span_id", "")
        malformed = "duplicate_span_id"
        span["span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.DUPLICATE_SPAN_ID,
            target_field="span_id",
            original_value=original,
            malformed_value=malformed,
            description="Created duplicate span ID"
        )
    
    def _malform_missing_ids(self, span: Dict[str, Any]) -> SpanMalformation:
        """Remove required IDs"""
        removed_fields = []
        
        if "trace_id" in span:
            del span["trace_id"]
            removed_fields.append("trace_id")
        
        if "span_id" in span and self.random.random() < 0.5:
            del span["span_id"]
            removed_fields.append("span_id")
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MISSING_IDS,
            target_field=",".join(removed_fields),
            original_value="present",
            malformed_value="missing",
            description=f"Removed required IDs: {removed_fields}"
        )
    
    def _malform_future_timestamp(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set timestamp in future"""
        original = span.get("start_time", 0)
        
        # Set timestamp 1 year in future
        future_time = int(time.time() * 1_000_000_000) + (365 * 24 * 60 * 60 * 1_000_000_000)
        span["start_time"] = future_time
        span["end_time"] = future_time + 1_000_000  # 1ms later
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.FUTURE_TIMESTAMP,
            target_field="start_time",
            original_value=original,
            malformed_value=future_time,
            description="Set timestamp in future"
        )
    
    def _malform_negative_timestamp(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set negative timestamp"""
        original = span.get("start_time", 0)
        malformed = -1000000000
        span["start_time"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.NEGATIVE_TIMESTAMP,
            target_field="start_time",
            original_value=original,
            malformed_value=malformed,
            description="Set negative timestamp"
        )
    
    def _malform_timestamp_format(self, span: Dict[str, Any]) -> SpanMalformation:
        """Malform timestamp format"""
        original = span.get("start_time", 0)
        malformed = "invalid_timestamp_format"
        span["start_time"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_TIMESTAMP_FORMAT,
            target_field="start_time",
            original_value=original,
            malformed_value=malformed,
            description="Corrupted timestamp format"
        )
    
    def _malform_timestamp_overflow(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create timestamp overflow"""
        original = span.get("start_time", 0)
        malformed = 2**63 - 1  # Max 64-bit signed int
        span["start_time"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.TIMESTAMP_OVERFLOW,
            target_field="start_time",
            original_value=original,
            malformed_value=malformed,
            description="Created timestamp overflow"
        )
    
    def _malform_negative_duration(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set negative duration"""
        original = span.get("duration", 0)
        malformed = -1000000
        span["duration"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.NEGATIVE_DURATION,
            target_field="duration",
            original_value=original,
            malformed_value=malformed,
            description="Set negative duration"
        )
    
    def _malform_infinite_duration(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set infinite duration"""
        original = span.get("duration", 0)
        malformed = float('inf')
        span["duration"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INFINITE_DURATION,
            target_field="duration",
            original_value=original,
            malformed_value=malformed,
            description="Set infinite duration"
        )
    
    def _malform_duration_overflow(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create duration longer than trace"""
        original = span.get("duration", 0)
        malformed = 10**15  # Very long duration
        span["duration"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.DURATION_LONGER_THAN_TRACE,
            target_field="duration",
            original_value=original,
            malformed_value=malformed,
            description="Set duration longer than trace"
        )
    
    def _malform_orphaned_span(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create orphaned span"""
        original = span.get("parent_span_id")
        malformed = "nonexistent_parent"
        span["parent_span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.ORPHANED_SPAN,
            target_field="parent_span_id",
            original_value=original,
            malformed_value=malformed,
            description="Created orphaned span"
        )
    
    def _malform_circular_reference(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create circular parent-child reference"""
        span_id = span.get("span_id", "test_span")
        span["parent_span_id"] = span_id
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.CIRCULAR_PARENT_CHILD,
            target_field="parent_span_id",
            original_value=span.get("parent_span_id"),
            malformed_value=span_id,
            description="Created circular parent-child reference"
        )
    
    def _malform_invalid_parent(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set invalid parent ID"""
        original = span.get("parent_span_id")
        malformed = "INVALID_PARENT_ID"
        span["parent_span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_PARENT_ID,
            target_field="parent_span_id",
            original_value=original,
            malformed_value=malformed,
            description="Set invalid parent ID"
        )
    
    def _malform_deep_nesting(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create deeply nested structure"""
        nested_data = {}
        current = nested_data
        
        for i in range(200):  # Create deep nesting
            current["nested"] = {"level": i}
            current = current["nested"]
        
        span["nested_data"] = nested_data
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.DEEP_NESTING,
            target_field="nested_data",
            original_value=None,
            malformed_value="deeply_nested_structure",
            description="Created deeply nested structure"
        )
    
    def _malform_oversized_attributes(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create oversized attributes"""
        original = span.get("tags", {})
        
        # Add many large attributes
        large_tags = {}
        for i in range(100):
            large_tags[f"large_attr_{i}"] = "X" * 1000
        
        span["tags"] = large_tags
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.OVERSIZED_ATTRIBUTES,
            target_field="tags",
            original_value=original,
            malformed_value="oversized_attributes",
            description="Created oversized attributes"
        )
    
    def _malform_attribute_types(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set invalid attribute types"""
        original = span.get("tags", {})
        
        invalid_tags = {
            "object_attr": {"nested": "object"},
            "list_attr": [1, 2, 3],
            "function_attr": lambda x: x,
            "bytes_attr": b"binary_data",
            "none_attr": None
        }
        
        span["tags"] = invalid_tags
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_ATTRIBUTE_TYPES,
            target_field="tags",
            original_value=original,
            malformed_value=invalid_tags,
            description="Set invalid attribute types"
        )
    
    def _malform_reserved_names(self, span: Dict[str, Any]) -> SpanMalformation:
        """Use reserved attribute names"""
        original = span.get("tags", {})
        
        reserved_tags = {
            "__proto__": "prototype_pollution",
            "constructor": "constructor_injection",
            "eval": "code_injection",
            "document": "dom_injection"
        }
        
        span["tags"] = reserved_tags
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.RESERVED_ATTRIBUTE_NAMES,
            target_field="tags",
            original_value=original,
            malformed_value=reserved_tags,
            description="Used reserved attribute names"
        )
    
    def _malform_binary_attributes(self, span: Dict[str, Any]) -> SpanMalformation:
        """Add binary data to attributes"""
        original = span.get("tags", {})
        
        binary_tags = {
            "binary_data": b"\x00\x01\x02\x03\xff\xfe\xfd",
            "encoded_binary": b"binary_attribute_data"
        }
        
        span["tags"] = binary_tags
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.BINARY_ATTRIBUTES,
            target_field="tags",
            original_value=original,
            malformed_value=binary_tags,
            description="Added binary data to attributes"
        )
    
    def _malform_event_timestamps(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create invalid event timestamps"""
        invalid_events = [
            {"timestamp": -1, "message": "negative_timestamp"},
            {"timestamp": "invalid", "message": "string_timestamp"},
            {"timestamp": float('inf'), "message": "infinite_timestamp"}
        ]
        
        span["logs"] = invalid_events
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_EVENT_TIMESTAMPS,
            target_field="logs",
            original_value=[],
            malformed_value=invalid_events,
            description="Created invalid event timestamps"
        )
    
    def _malform_oversized_events(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create oversized events"""
        large_events = []
        for i in range(100):
            large_events.append({
                "timestamp": int(time.time() * 1_000_000_000),
                "message": "X" * 10000,  # 10KB message
                "data": list(range(1000))  # Large data
            })
        
        span["logs"] = large_events
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.OVERSIZED_EVENTS,
            target_field="logs",
            original_value=[],
            malformed_value="oversized_events",
            description="Created oversized events"
        )
    
    def _malform_event_structure(self, span: Dict[str, Any]) -> SpanMalformation:
        """Malform event structure"""
        malformed_events = [
            "string_instead_of_object",
            {"missing_timestamp": "no_timestamp_field"},
            {"timestamp": time.time(), "circular": None}
        ]
        
        # Create circular reference
        malformed_events[2]["circular"] = malformed_events[2]
        
        span["logs"] = malformed_events
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MALFORMED_EVENT_STRUCTURE,
            target_field="logs",
            original_value=[],
            malformed_value=malformed_events,
            description="Malformed event structure"
        )
    
    def _malform_resource_attributes(self, span: Dict[str, Any]) -> SpanMalformation:
        """Malform resource attributes"""
        original = span.get("resource", {})
        
        invalid_resource = {
            "service.name": 12345,  # Should be string
            "service.version": {"nested": "object"},  # Should be string
            "invalid.attribute": None
        }
        
        span["resource"] = invalid_resource
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_RESOURCE_ATTRIBUTES,
            target_field="resource",
            original_value=original,
            malformed_value=invalid_resource,
            description="Malformed resource attributes"
        )
    
    def _malform_missing_service_name(self, span: Dict[str, Any]) -> SpanMalformation:
        """Remove service name from resource"""
        original = span.get("resource", {})
        
        malformed_resource = original.copy() if original else {}
        if "service.name" in malformed_resource:
            del malformed_resource["service.name"]
        
        span["resource"] = malformed_resource
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MISSING_SERVICE_NAME,
            target_field="resource",
            original_value=original,
            malformed_value=malformed_resource,
            description="Removed service name from resource"
        )
    
    def _malform_conflicting_resources(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create conflicting resource attributes"""
        conflicting_resource = {
            "service.name": "service_a",
            "service.name.override": "service_b",  # Conflicting
            "service.version": "1.0.0",
            "service.version.actual": "2.0.0"  # Conflicting
        }
        
        span["resource"] = conflicting_resource
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.CONFLICTING_RESOURCES,
            target_field="resource",
            original_value=span.get("resource", {}),
            malformed_value=conflicting_resource,
            description="Created conflicting resource attributes"
        )
    
    def _malform_span_kind(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set invalid span kind"""
        original = span.get("kind", "SPAN_KIND_INTERNAL")
        malformed = "INVALID_SPAN_KIND"
        span["kind"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_SPAN_KIND,
            target_field="kind",
            original_value=original,
            malformed_value=malformed,
            description="Set invalid span kind"
        )
    
    def _malform_status_code(self, span: Dict[str, Any]) -> SpanMalformation:
        """Set invalid status code"""
        original = span.get("status", {})
        
        malformed_status = {
            "code": "INVALID_STATUS",
            "message": "Invalid status code"
        }
        
        span["status"] = malformed_status
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_STATUS_CODE,
            target_field="status",
            original_value=original,
            malformed_value=malformed_status,
            description="Set invalid status code"
        )
    
    def _malform_links(self, span: Dict[str, Any]) -> SpanMalformation:
        """Create malformed links"""
        malformed_links = [
            {"trace_id": "invalid", "span_id": "invalid"},
            {"circular_reference": True},
            "string_instead_of_object"
        ]
        
        span["links"] = malformed_links
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MALFORMED_LINKS,
            target_field="links",
            original_value=[],
            malformed_value=malformed_links,
            description="Created malformed links"
        )
    
    def _malform_utf8(self, span: Dict[str, Any]) -> SpanMalformation:
        """Add invalid UTF-8"""
        original = span.get("operation_name", "")
        
        # Invalid UTF-8 sequences
        malformed = original + "\xff\xfe\x00\x01"
        span["operation_name"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_UTF8,
            target_field="operation_name",
            original_value=original,
            malformed_value=malformed,
            description="Added invalid UTF-8 sequences"
        )
    
    def _malform_mixed_encoding(self, span: Dict[str, Any]) -> SpanMalformation:
        """Add mixed encoding issues"""
        original = span.get("operation_name", "")
        
        # Mix UTF-8 with other encodings
        malformed = original + "résumé\x00\xff混合编码"
        span["operation_name"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MIXED_ENCODING,
            target_field="operation_name",
            original_value=original,
            malformed_value=malformed,
            description="Added mixed encoding issues"
        )
    
    def _malform_control_characters(self, span: Dict[str, Any]) -> SpanMalformation:
        """Add control characters"""
        original = span.get("operation_name", "")
        
        # Add various control characters
        control_chars = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0e\x0f"
        malformed = original + control_chars
        span["operation_name"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.CONTROL_CHARACTERS,
            target_field="operation_name",
            original_value=original,
            malformed_value=malformed,
            description="Added control characters"
        )


class MalformedSpanGenerator:
    """Generator for creating sequences of malformed spans"""
    
    def __init__(self, mutator: SpanMutator, base_span: Dict[str, Any], 
                 malformation_types: List[SpanMalformationType]):
        self.mutator = mutator
        self.base_span = base_span
        self.malformation_types = malformation_types
    
    def generate_malformed_spans(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate a sequence of malformed spans"""
        spans = []
        
        for _ in range(count):
            # Create a copy of the base span
            span_copy = self.base_span.copy()
            
            # Apply random malformation
            malformation_type = self.mutator.random.choice(self.malformation_types)
            malformation = self.mutator.mutate_span(span_copy, malformation_type)
            
            spans.append(malformation.malformed_span)
        
        return spans
    
    def _generate_valid_span_id(self) -> str:
        """Generate a valid span ID"""
        return ''.join([f'{self.random.randint(0, 15):x}' for _ in range(16)])
    
    # Malformation strategy implementations
    
    def _malform_trace_id(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Malform trace ID"""
        original = span.get("trace_id")
        
        malformed_values = [
            "",  # Empty
            "invalid",  # Wrong format
            "123",  # Too short
            "x" * 100,  # Too long
            "GGGGGGGG" + "0" * 24,  # Invalid hex
            None,  # Null
            12345,  # Wrong type
            "4bf92f35-77b3-4da6-a3ce-929d0e0e4736",  # UUID format (wrong)
        ]
        
        malformed = self.random.choice(malformed_values)
        span["trace_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_TRACE_ID,
            target_field="trace_id",
            original_value=original,
            malformed_value=malformed,
            description=f"Trace ID malformed: {original} -> {malformed}"
        )
    
    def _malform_span_id(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Malform span ID"""
        original = span.get("span_id")
        
        malformed_values = [
            "",  # Empty
            "invalid",  # Wrong format
            "12",  # Too short
            "x" * 50,  # Too long
            "GGGGGGGGGGGGGGGG",  # Invalid hex
            None,  # Null
            67890,  # Wrong type
        ]
        
        malformed = self.random.choice(malformed_values)
        span["span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_SPAN_ID,
            target_field="span_id",
            original_value=original,
            malformed_value=malformed,
            description=f"Span ID malformed: {original} -> {malformed}"
        )
    
    def _malform_duplicate_span_id(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create duplicate span ID scenario"""
        original = span.get("span_id")
        
        # Use trace_id as span_id (invalid)
        malformed = span.get("trace_id", "duplicate_id")
        span["span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.DUPLICATE_SPAN_ID,
            target_field="span_id",
            original_value=original,
            malformed_value=malformed,
            description="Span ID duplicated from trace ID"
        )
    
    def _malform_missing_ids(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Remove required ID fields"""
        fields_to_remove = ["trace_id", "span_id"]
        field = self.random.choice(fields_to_remove)
        
        original = span.get(field)
        if field in span:
            del span[field]
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MISSING_IDS,
            target_field=field,
            original_value=original,
            malformed_value=None,
            description=f"Required field {field} removed"
        )
    
    def _malform_future_timestamp(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Set timestamp in far future"""
        original = span.get("start_time")
        
        # Year 2100
        future_timestamp = int(datetime(2100, 1, 1).timestamp() * 1_000_000_000)
        span["start_time"] = future_timestamp
        span["end_time"] = future_timestamp + 1_000_000  # 1ms later
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.FUTURE_TIMESTAMP,
            target_field="start_time",
            original_value=original,
            malformed_value=future_timestamp,
            description="Timestamp set to far future (year 2100)"
        )
    
    def _malform_negative_timestamp(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Set negative timestamp"""
        original = span.get("start_time")
        
        malformed = -abs(original) if original else -1000000000
        span["start_time"] = malformed
        span["end_time"] = malformed + 1000000
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.NEGATIVE_TIMESTAMP,
            target_field="start_time",
            original_value=original,
            malformed_value=malformed,
            description="Timestamp set to negative value"
        )
    
    def _malform_timestamp_format(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Use invalid timestamp format"""
        original = span.get("start_time")
        
        malformed_values = [
            "2023-01-01T00:00:00Z",  # ISO format instead of nanoseconds
            "invalid_timestamp",
            "1640995200.123",  # Seconds with decimal
            "now",
            "",
        ]
        
        malformed = self.random.choice(malformed_values)
        span["start_time"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_TIMESTAMP_FORMAT,
            target_field="start_time",
            original_value=original,
            malformed_value=malformed,
            description=f"Invalid timestamp format: {malformed}"
        )
    
    def _malform_timestamp_overflow(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create timestamp overflow"""
        original = span.get("start_time")
        
        # Max 64-bit signed integer
        malformed = 2**63 - 1
        span["start_time"] = malformed
        span["end_time"] = malformed  # Same time = zero duration
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.TIMESTAMP_OVERFLOW,
            target_field="start_time",
            original_value=original,
            malformed_value=malformed,
            description="Timestamp overflow (max 64-bit int)"
        )
    
    def _malform_negative_duration(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Set negative duration"""
        original = span.get("duration")
        
        # End time before start time
        start_time = span.get("start_time", 0)
        span["end_time"] = start_time - 1000000  # 1ms before start
        span["duration"] = -1000000
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.NEGATIVE_DURATION,
            target_field="duration",
            original_value=original,
            malformed_value=-1000000,
            description="Negative duration (end before start)"
        )
    
    def _malform_infinite_duration(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Set infinite duration"""
        original = span.get("duration")
        
        malformed = float('inf')
        span["duration"] = malformed
        span["end_time"] = float('inf')
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INFINITE_DURATION,
            target_field="duration",
            original_value=original,
            malformed_value=malformed,
            description="Infinite duration"
        )
    
    def _malform_duration_overflow(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Duration longer than entire trace"""
        original = span.get("duration")
        
        # 1 year in nanoseconds
        malformed = 365 * 24 * 60 * 60 * 1_000_000_000
        span["duration"] = malformed
        span["end_time"] = span.get("start_time", 0) + malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.DURATION_LONGER_THAN_TRACE,
            target_field="duration",
            original_value=original,
            malformed_value=malformed,
            description="Duration longer than reasonable trace time (1 year)"
        )
    
    def _malform_orphaned_span(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create orphaned span with invalid parent"""
        original = span.get("parent_span_id")
        
        # Invalid parent span ID
        malformed = "nonexistent_parent_id"
        span["parent_span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.ORPHANED_SPAN,
            target_field="parent_span_id",
            original_value=original,
            malformed_value=malformed,
            description="Orphaned span with nonexistent parent"
        )
    
    def _malform_circular_reference(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create circular parent-child reference"""
        original = span.get("parent_span_id")
        
        # Parent points to self
        malformed = span.get("span_id")
        span["parent_span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.CIRCULAR_PARENT_CHILD,
            target_field="parent_span_id",
            original_value=original,
            malformed_value=malformed,
            description="Circular reference (span is its own parent)"
        )
    
    def _malform_invalid_parent(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Invalid parent ID format"""
        original = span.get("parent_span_id")
        
        malformed_values = [
            "invalid_parent",
            123456,  # Wrong type
            "",  # Empty
            "too_long_parent_id_" * 10,
        ]
        
        malformed = self.random.choice(malformed_values)
        span["parent_span_id"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_PARENT_ID,
            target_field="parent_span_id",
            original_value=original,
            malformed_value=malformed,
            description=f"Invalid parent ID format: {malformed}"
        )
    
    def _malform_deep_nesting(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create extremely deep nesting structure"""
        original = span.get("tags", {})
        
        # Create deeply nested tags
        nested_data = span
        for i in range(1000):  # Very deep nesting
            nested_data[f"level_{i}"] = {}
            nested_data = nested_data[f"level_{i}"]
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.DEEP_NESTING,
            target_field="tags",
            original_value=original,
            malformed_value="<deeply_nested_structure>",
            description="Created deeply nested structure (1000 levels)"
        )
    
    def _malform_oversized_attributes(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create oversized attributes"""
        original = span.get("tags", {})
        
        # Add huge attributes
        span["tags"] = {
            "huge_attribute": "X" * 1_000_000,  # 1MB attribute
            "many_attributes": {f"attr_{i}": f"value_{i}" for i in range(10000)},
            "binary_data": b"\\x00\\x01\\x02" * 100000,
        }
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.OVERSIZED_ATTRIBUTES,
            target_field="tags",
            original_value=original,
            malformed_value="<oversized_attributes>",
            description="Added oversized attributes (1MB+ data)"
        )
    
    def _malform_attribute_types(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Use invalid attribute types"""
        original = span.get("tags", {})
        
        # Add invalid types
        span["tags"] = {
            "function_attribute": lambda x: x,  # Function (not serializable)
            "class_attribute": SpanMutator,  # Class
            "complex_attribute": 1 + 2j,  # Complex number
            "circular_ref": span,  # Circular reference
            "generator_attribute": (x for x in range(10)),  # Generator
        }
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_ATTRIBUTE_TYPES,
            target_field="tags",
            original_value=original,
            malformed_value="<invalid_types>",
            description="Added non-serializable attribute types"
        )
    
    def _malform_reserved_names(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Use reserved attribute names"""
        original = span.get("tags", {})
        
        # Reserved/dangerous names
        span["tags"] = {
            "__proto__": "prototype_pollution",
            "constructor": "constructor_access",
            "eval": "code_execution",
            "process": "process_access",
            "__class__": "class_access",
            "__globals__": "globals_access",
        }
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.RESERVED_ATTRIBUTE_NAMES,
            target_field="tags",
            original_value=original,
            malformed_value="<reserved_names>",
            description="Used reserved/dangerous attribute names"
        )
    
    def _malform_binary_attributes(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Add binary data in text attributes"""
        original = span.get("tags", {})
        
        span["tags"] = {
            "binary_string": "\\x00\\x01\\x02\\x03\\xff\\xfe\\xfd\\xfc",
            "null_bytes": "data\\x00injection",
            "control_chars": "\\x01\\x02\\x03\\x07\\x08\\x0c",
            "mixed_encoding": "UTF-8: \\xc3\\xa9 Latin-1: \\xe9",
        }
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.BINARY_ATTRIBUTES,
            target_field="tags",
            original_value=original,
            malformed_value="<binary_data>",
            description="Added binary data in text attributes"
        )
    
    def _malform_event_timestamps(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create invalid event timestamps"""
        original = span.get("logs", [])
        
        span["logs"] = [
            {
                "timestamp": -1000000000,  # Negative
                "fields": {"message": "negative timestamp event"}
            },
            {
                "timestamp": float('inf'),  # Infinite
                "fields": {"message": "infinite timestamp event"}
            },
            {
                "timestamp": "invalid_timestamp",  # Wrong type
                "fields": {"message": "invalid timestamp format"}
            }
        ]
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_EVENT_TIMESTAMPS,
            target_field="logs",
            original_value=original,
            malformed_value="<invalid_timestamps>",
            description="Added events with invalid timestamps"
        )
    
    def _malform_oversized_events(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create oversized events"""
        original = span.get("logs", [])
        
        # Add huge events
        huge_events = []
        for i in range(1000):  # Many events
            huge_events.append({
                "timestamp": int(time.time() * 1_000_000_000),
                "fields": {
                    "message": "X" * 10000,  # 10KB per event
                    "huge_data": list(range(1000))  # Large data structure
                }
            })
        
        span["logs"] = huge_events
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.OVERSIZED_EVENTS,
            target_field="logs",
            original_value=original,
            malformed_value="<oversized_events>",
            description="Added 1000 oversized events (10MB+ total)"
        )
    
    def _malform_event_structure(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Malform event structure"""
        original = span.get("logs", [])
        
        span["logs"] = [
            "invalid_event_string",  # String instead of object
            {
                # Missing timestamp
                "fields": {"message": "missing timestamp"}
            },
            {
                "timestamp": int(time.time() * 1_000_000_000),
                # Missing fields
            },
            {
                "timestamp": int(time.time() * 1_000_000_000),
                "fields": None  # Null fields
            }
        ]
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MALFORMED_EVENT_STRUCTURE,
            target_field="logs",
            original_value=original,
            malformed_value="<malformed_structure>",
            description="Added events with malformed structure"
        )
    
    def _malform_resource_attributes(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Malform resource attributes"""
        original = span.get("resource", {})
        
        span["resource"] = {
            "service.name": None,  # Null service name
            "service.version": 12345,  # Wrong type
            "invalid.resource": "X" * 100000,  # Huge attribute
            "": "empty_key",  # Empty key
            123: "numeric_key",  # Numeric key
        }
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_RESOURCE_ATTRIBUTES,
            target_field="resource",
            original_value=original,
            malformed_value="<invalid_resource>",
            description="Malformed resource attributes"
        )
    
    def _malform_missing_service_name(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Remove required service name"""
        original = span.get("resource", {}).get("service.name")
        
        if "resource" in span and "service.name" in span["resource"]:
            del span["resource"]["service.name"]
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MISSING_SERVICE_NAME,
            target_field="resource.service.name",
            original_value=original,
            malformed_value=None,
            description="Removed required service.name from resource"
        )
    
    def _malform_conflicting_resources(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create conflicting resource information"""
        original = span.get("resource", {})
        
        span["resource"] = {
            "service.name": "service_a",
            "service.name.override": "service_b",  # Conflicting
            "service.version": "1.0.0",
            "service.version.alt": "2.0.0",  # Conflicting
            "deployment.environment": "production",
            "environment": "development",  # Conflicting
        }
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.CONFLICTING_RESOURCES,
            target_field="resource",
            original_value=original,
            malformed_value="<conflicting_resources>",
            description="Added conflicting resource attributes"
        )
    
    def _malform_span_kind(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Use invalid span kind"""
        original = span.get("kind")
        
        invalid_kinds = [
            "INVALID_KIND",
            "SPAN_KIND_UNKNOWN_TYPE",
            123,  # Numeric
            None,
            "",
            "client",  # Lowercase (should be uppercase)
        ]
        
        malformed = self.random.choice(invalid_kinds)
        span["kind"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_SPAN_KIND,
            target_field="kind",
            original_value=original,
            malformed_value=malformed,
            description=f"Invalid span kind: {malformed}"
        )
    
    def _malform_status_code(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Use invalid status code"""
        original = span.get("status", {})
        
        invalid_statuses = [
            {"code": "INVALID_STATUS"},
            {"code": 999},  # Numeric instead of string
            {"code": None},
            {"message": "error", "code": ""},  # Empty code
            "OK",  # String instead of object
        ]
        
        malformed = self.random.choice(invalid_statuses)
        span["status"] = malformed
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_STATUS_CODE,
            target_field="status",
            original_value=original,
            malformed_value=malformed,
            description=f"Invalid status: {malformed}"
        )
    
    def _malform_links(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Create malformed links"""
        original = span.get("links", [])
        
        span["links"] = [
            {
                "trace_id": "invalid_trace_id",
                "span_id": "invalid_span_id",
                "attributes": {"link": "malformed"}
            },
            {
                # Missing required fields
                "attributes": {"incomplete": "link"}
            },
            "invalid_link_string",  # String instead of object
            {
                "trace_id": None,  # Null trace ID
                "span_id": None,   # Null span ID
            }
        ]
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MALFORMED_LINKS,
            target_field="links",
            original_value=original,
            malformed_value="<malformed_links>",
            description="Added malformed span links"
        )
    
    def _malform_utf8(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Inject invalid UTF-8"""
        original = span.get("operation_name")
        
        # Invalid UTF-8 sequences
        invalid_utf8 = [
            "\\xff\\xfe",  # Invalid UTF-8 byte sequence
            "\\xc0\\x80",  # Overlong encoding
            "\\xed\\xa0\\x80",  # High surrogate
        ]
        
        malformed = self.random.choice(invalid_utf8)
        span["operation_name"] = f"operation_{malformed}"
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.INVALID_UTF8,
            target_field="operation_name",
            original_value=original,
            malformed_value=malformed,
            description="Injected invalid UTF-8 sequences"
        )
    
    def _malform_mixed_encoding(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Mix different text encodings"""
        original = span.get("operation_name")
        
        # Mixed encoding sequences
        mixed_encoding = "UTF-8_résumé_Latin1_\\xe9_Binary_\\x00\\x01"
        span["operation_name"] = mixed_encoding
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.MIXED_ENCODING,
            target_field="operation_name",
            original_value=original,
            malformed_value=mixed_encoding,
            description="Mixed text encodings in operation name"
        )
    
    def _malform_control_characters(self, span: Dict[str, Any]) -> Optional[SpanMalformation]:
        """Inject control characters"""
        original = span.get("operation_name")
        
        # Control characters
        control_chars = "\\x00\\x01\\x02\\x03\\x07\\x08\\x0c\\x0e\\x0f"
        span["operation_name"] = f"operation{control_chars}name"
        
        return SpanMalformation(
            malformation_type=SpanMalformationType.CONTROL_CHARACTERS,
            target_field="operation_name",
            original_value=original,
            malformed_value=control_chars,
            description="Injected control characters"
        )

class MalformedSpanGenerator:
    """
    High-level generator for creating collections of malformed spans
    for comprehensive chaos testing.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.span_mutator = SpanMutator(seed)
        self.random = random.Random(seed)
    
    def generate_malformed_trace(self, 
                                span_count: int = 10,
                                malformation_intensity: float = 0.5) -> List[Dict[str, Any]]:
        """
        Generate a complete malformed trace with multiple spans.
        
        Args:
            span_count: Number of spans in the trace
            malformation_intensity: Intensity of malformations
            
        Returns:
            List of malformed spans forming a trace
        """
        trace_id = self.span_mutator._generate_valid_trace_id()
        spans = []
        
        # Generate root span
        root_span = self._create_root_span(trace_id)
        malformed_root, _ = self.span_mutator.create_malformed_span(
            root_span, malformation_intensity=malformation_intensity
        )
        spans.append(malformed_root)
        
        # Generate child spans
        for i in range(span_count - 1):
            parent_span_id = spans[self.random.randint(0, len(spans) - 1)]["span_id"]
            child_span = self._create_child_span(trace_id, parent_span_id, i)
            
            malformed_child, _ = self.span_mutator.create_malformed_span(
                child_span, malformation_intensity=malformation_intensity
            )
            spans.append(malformed_child)
        
        return spans
    
    def generate_chaos_span_suite(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate a comprehensive suite of chaos spans covering all malformation types.
        
        Returns:
            Dictionary mapping malformation types to example spans
        """
        suite = {}
        
        for malformation_type in SpanMalformationType:
            # Create spans focused on specific malformation
            malformed_span, _ = self.span_mutator.create_malformed_span(
                malformation_types=[malformation_type],
                malformation_intensity=1.0  # Always apply
            )
            
            suite[malformation_type.value] = [malformed_span]
        
        return suite
    
    def _create_root_span(self, trace_id: str) -> Dict[str, Any]:
        """Create a root span for the trace"""
        return {
            "trace_id": trace_id,
            "span_id": self.span_mutator._generate_valid_span_id(),
            "parent_span_id": None,
            "operation_name": "root_operation",
            "start_time": int(time.time() * 1_000_000_000),
            "end_time": int(time.time() * 1_000_000_000) + 100_000_000,
            "duration": 100_000_000,
            "tags": {"span.kind": "server"},
            "logs": [],
            "status": {"code": "OK"},
            "kind": "SPAN_KIND_SERVER",
            "resource": {
                "service.name": "test_service",
                "service.version": "1.0.0"
            }
        }
    
    def _create_child_span(self, trace_id: str, parent_span_id: str, index: int) -> Dict[str, Any]:
        """Create a child span"""
        start_time = int(time.time() * 1_000_000_000) + (index * 1_000_000)
        
        return {
            "trace_id": trace_id,
            "span_id": self.span_mutator._generate_valid_span_id(),
            "parent_span_id": parent_span_id,
            "operation_name": f"child_operation_{index}",
            "start_time": start_time,
            "end_time": start_time + 10_000_000,  # 10ms duration
            "duration": 10_000_000,
            "tags": {"span.kind": "internal", "operation.index": index},
            "logs": [],
            "status": {"code": "OK"},
            "kind": "SPAN_KIND_INTERNAL",
            "resource": {
                "service.name": "test_service",
                "service.version": "1.0.0"
            }
        }