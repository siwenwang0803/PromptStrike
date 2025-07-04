"""
Test OTEL Span Schema validation
Validates the schema against example data and ensures proper structure
"""

import pytest
import json
from datetime import datetime
from typing import Dict, Any

def create_sample_span() -> Dict[str, Any]:
    """Create a sample OTEL span following PromptStrike schema"""
    return {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7",
        "parent_span_id": "00f067aa0ba902b6",
        "operation_name": "llm.chat.completion",
        "start_time": "2024-01-01T12:00:00.000Z",
        "end_time": "2024-01-01T12:00:01.250Z",
        "duration": 1250,
        "status": {
            "code": "OK",
            "message": "Request completed successfully"
        },
        "resource": {
            "service.name": "promptstrike-guardrail",
            "service.version": "0.1.0",
            "deployment.environment": "production",
            "promptstrike.guardrail.version": "0.1.0"
        },
        "attributes": {
            # LLM Provider Information
            "llm.provider": "openai",
            "llm.model": "gpt-4",
            "llm.endpoint": "https://api.openai.com/v1/chat/completions",
            "llm.api_version": "2023-12-01",
            
            # Token Usage
            "llm.tokens.prompt": 25,
            "llm.tokens.completion": 45,
            "llm.tokens.total": 70,
            
            # Cost Tracking
            "llm.cost.input_tokens_usd": 0.00005,
            "llm.cost.output_tokens_usd": 0.00009,
            "llm.cost.total_usd": 0.00014,
            "llm.cost.currency": "USD",
            
            # Performance Metrics
            "llm.latency.total_ms": 1250,
            "llm.latency.first_token_ms": 850,
            "llm.latency.tokens_per_second": 36.0,
            
            # Security Analysis
            "promptstrike.security.risk_score": 2.3,
            "promptstrike.security.risk_level": "low",
            "promptstrike.security.vulnerabilities_detected": 0,
            "promptstrike.security.analysis_version": "v1.0",
            
            # HTTP Details
            "http.method": "POST",
            "http.url": "https://api.openai.com/v1/chat/completions",
            "http.status_code": 200,
            "http.request_content_length": 256,
            "http.response_content_length": 512
        },
        "events": [
            {
                "timestamp": "2024-01-01T12:00:00.100Z",
                "name": "llm.request.start",
                "attributes": {
                    "llm.request.id": "req_12345",
                    "llm.request.size_bytes": 256
                }
            },
            {
                "timestamp": "2024-01-01T12:00:01.200Z",
                "name": "promptstrike.security.analysis_complete",
                "attributes": {
                    "promptstrike.security.analysis_duration_ms": 15,
                    "promptstrike.security.patterns_checked": 47,
                    "promptstrike.security.risk_score": 2.3
                }
            }
        ]
    }

def test_span_has_required_fields():
    """Test that span contains all required OTEL fields"""
    span = create_sample_span()
    
    # Core OTEL fields
    assert "trace_id" in span
    assert "span_id" in span
    assert "start_time" in span
    assert "end_time" in span
    assert "status" in span
    assert "attributes" in span
    
    # PromptStrike extensions
    assert "resource" in span
    assert "events" in span

def test_trace_id_format():
    """Test trace_id follows OTEL format (32 hex chars)"""
    span = create_sample_span()
    trace_id = span["trace_id"]
    
    assert len(trace_id) == 32
    assert all(c in "0123456789abcdef" for c in trace_id)

def test_span_id_format():
    """Test span_id follows OTEL format (16 hex chars)"""
    span = create_sample_span()
    span_id = span["span_id"]
    
    assert len(span_id) == 16
    assert all(c in "0123456789abcdef" for c in span_id)

def test_llm_attributes():
    """Test LLM-specific attributes are present and valid"""
    span = create_sample_span()
    attrs = span["attributes"]
    
    # Required LLM attributes
    assert "llm.provider" in attrs
    assert attrs["llm.provider"] in ["openai", "anthropic", "azure", "google", "aws"]
    
    assert "llm.tokens.total" in attrs
    assert isinstance(attrs["llm.tokens.total"], int)
    assert attrs["llm.tokens.total"] >= 0
    
    assert "llm.cost.total_usd" in attrs
    assert isinstance(attrs["llm.cost.total_usd"], (int, float))
    assert attrs["llm.cost.total_usd"] >= 0

def test_security_attributes():
    """Test PromptStrike security attributes are valid"""
    span = create_sample_span()
    attrs = span["attributes"]
    
    # Security attributes
    assert "promptstrike.security.risk_score" in attrs
    risk_score = attrs["promptstrike.security.risk_score"]
    assert isinstance(risk_score, (int, float))
    assert 0 <= risk_score <= 10
    
    assert "promptstrike.security.vulnerabilities_detected" in attrs
    assert isinstance(attrs["promptstrike.security.vulnerabilities_detected"], int)
    assert attrs["promptstrike.security.vulnerabilities_detected"] >= 0

def test_performance_attributes():
    """Test performance metrics are valid"""
    span = create_sample_span()
    attrs = span["attributes"]
    
    # Performance metrics
    assert "llm.latency.total_ms" in attrs
    assert isinstance(attrs["llm.latency.total_ms"], int)
    assert attrs["llm.latency.total_ms"] > 0
    
    assert "llm.latency.tokens_per_second" in attrs
    assert isinstance(attrs["llm.latency.tokens_per_second"], (int, float))
    assert attrs["llm.latency.tokens_per_second"] > 0

def test_events_structure():
    """Test events array has proper structure"""
    span = create_sample_span()
    events = span["events"]
    
    assert isinstance(events, list)
    assert len(events) > 0
    
    for event in events:
        assert "timestamp" in event
        assert "name" in event
        assert "attributes" in event
        assert isinstance(event["attributes"], dict)

def test_json_serializable():
    """Test span can be serialized to JSON"""
    span = create_sample_span()
    
    try:
        json_str = json.dumps(span)
        parsed = json.loads(json_str)
        assert parsed == span
    except (TypeError, ValueError) as e:
        pytest.fail(f"Span is not JSON serializable: {e}")

def test_schema_field_count():
    """Test schema has reasonable number of fields (≤12 top-level fields)"""
    span = create_sample_span()
    
    top_level_fields = len(span.keys())
    assert top_level_fields <= 12, f"Too many top-level fields: {top_level_fields}"

def test_attribute_field_count():
    """Test attributes section has reasonable number of fields"""
    span = create_sample_span()
    attrs = span["attributes"]
    
    attr_count = len(attrs.keys())
    assert attr_count <= 50, f"Too many attribute fields: {attr_count}"

def test_vulnerability_span():
    """Test span with vulnerability detection"""
    span = create_sample_span()
    
    # Modify to include vulnerability
    span["attributes"]["promptstrike.security.risk_score"] = 8.5
    span["attributes"]["promptstrike.security.vulnerabilities_detected"] = 2
    span["attributes"]["promptstrike.security.risk_level"] = "high"
    
    # Add vulnerability details
    span["attributes"]["promptstrike.security.vulnerabilities"] = [
        {
            "id": "vuln_001",
            "category": "prompt_injection",
            "severity": "high",
            "confidence": 0.87,
            "description": "Potential system prompt manipulation attempt"
        }
    ]
    
    # Validate high-risk span
    assert span["attributes"]["promptstrike.security.risk_score"] > 7.0
    assert span["attributes"]["promptstrike.security.vulnerabilities_detected"] > 0
    assert span["attributes"]["promptstrike.security.risk_level"] == "high"

def test_cost_tracking_span():
    """Test span with detailed cost tracking"""
    span = create_sample_span()
    
    # Add detailed cost tracking
    span["attributes"]["llm.cost.pricing_model"] = "token_based"
    span["attributes"]["llm.cost.input_price_per_1k"] = 0.002
    span["attributes"]["llm.cost.output_price_per_1k"] = 0.004
    span["attributes"]["llm.cost.organization_id"] = "org_12345"
    span["attributes"]["llm.cost.daily_spend_usd"] = 12.34
    
    # Validate cost tracking
    assert span["attributes"]["llm.cost.pricing_model"] == "token_based"
    assert span["attributes"]["llm.cost.input_price_per_1k"] > 0
    assert span["attributes"]["llm.cost.output_price_per_1k"] > 0
    assert span["attributes"]["llm.cost.daily_spend_usd"] >= 0

def test_compliance_attributes():
    """Test compliance-related attributes"""
    span = create_sample_span()
    
    # Add compliance attributes
    span["attributes"]["promptstrike.compliance.nist_controls"] = ["GOVERN-1.1", "MAP-1.1"]
    span["attributes"]["promptstrike.compliance.eu_ai_act_risk"] = "minimal"
    span["attributes"]["promptstrike.compliance.audit_required"] = False
    
    # Validate compliance attributes
    nist_controls = span["attributes"]["promptstrike.compliance.nist_controls"]
    assert isinstance(nist_controls, list)
    assert len(nist_controls) > 0
    
    eu_risk = span["attributes"]["promptstrike.compliance.eu_ai_act_risk"]
    assert eu_risk in ["minimal", "limited", "high", "unacceptable"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])