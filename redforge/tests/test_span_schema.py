#!/usr/bin/env python3
"""
Test OTEL Span Schema JSON validation
Validates JSON examples against schema definition from OTEL_SPAN_SCHEMA.md
"""

import json
import pytest
from jsonschema import validate, ValidationError


# JSON Schema definition from OTEL_SPAN_SCHEMA.md
OTEL_SPAN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "trace_id": {
            "type": "string",
            "pattern": "^[a-f0-9]{32}$"
        },
        "span_id": {
            "type": "string",
            "pattern": "^[a-f0-9]{16}$"
        },
        "parent_span_id": {
            "type": "string",
            "pattern": "^[a-f0-9]{16}$"
        },
        "operation_name": {
            "type": "string"
        },
        "start_time": {
            "type": "string",
            "format": "date-time"
        },
        "end_time": {
            "type": "string",
            "format": "date-time"
        },
        "duration": {
            "type": "integer",
            "minimum": 0
        },
        "status": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["OK", "ERROR", "TIMEOUT"]
                },
                "message": {
                    "type": "string"
                }
            },
            "required": ["code"]
        },
        "tags": {
            "type": "object"
        },
        "resource": {
            "type": "object",
            "properties": {
                "service.name": {"type": "string"},
                "service.version": {"type": "string"},
                "deployment.environment": {"type": "string"},
                "redforge.guardrail.version": {"type": "string"}
            }
        },
        "attributes": {
            "type": "object",
            "properties": {
                "llm.provider": {
                    "type": "string",
                    "enum": ["openai", "anthropic", "azure", "google", "aws"]
                },
                "llm.model": {"type": "string"},
                "llm.endpoint": {"type": "string"},
                "llm.api_version": {"type": "string"},
                "llm.request.temperature": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 2.0
                },
                "llm.request.max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100000
                },
                "llm.tokens.prompt": {
                    "type": "integer",
                    "minimum": 0
                },
                "llm.tokens.completion": {
                    "type": "integer",
                    "minimum": 0
                },
                "llm.tokens.total": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100000
                },
                "llm.cost.total_usd": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1000
                },
                "llm.cost.currency": {
                    "type": "string",
                    "enum": ["USD", "EUR", "GBP"]
                },
                "llm.latency.total_ms": {
                    "type": "integer",
                    "minimum": 0
                },
                "redforge.security.risk_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 10
                },
                "redforge.security.risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"]
                },
                "redforge.security.vulnerabilities_detected": {
                    "type": "integer",
                    "minimum": 0
                },
                "http.method": {"type": "string"},
                "http.status_code": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 599
                }
            },
            "required": ["llm.provider", "llm.tokens.total"]
        },
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "name": {"type": "string"},
                    "attributes": {"type": "object"}
                },
                "required": ["timestamp", "name"]
            }
        }
    },
    "required": ["trace_id", "span_id", "attributes"]
}


class TestOTELSpanSchema:
    """Test OTEL span schema validation"""

    def test_base_otel_span_valid(self):
        """Test basic OTEL span structure"""
        base_span = {
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
            "tags": {
                "service.name": "redforge-guardrail",
                "service.version": "0.1.0",
                "span.kind": "client"
            },
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 70
            }
        }
        
        # Should validate without errors
        validate(instance=base_span, schema=OTEL_SPAN_SCHEMA)

    def test_redforge_extensions_valid(self):
        """Test RedForge extensions to OTEL span"""
        extended_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "resource": {
                "service.name": "redforge-guardrail",
                "service.version": "0.1.0",
                "deployment.environment": "production",
                "redforge.guardrail.version": "0.1.0"
            },
            "attributes": {
                "llm.provider": "openai",
                "llm.model": "gpt-4",
                "llm.endpoint": "https://api.openai.com/v1/chat/completions",
                "llm.api_version": "2023-12-01",
                "llm.request.temperature": 0.7,
                "llm.request.max_tokens": 150,
                "llm.tokens.prompt": 25,
                "llm.tokens.completion": 45,
                "llm.tokens.total": 70,
                "llm.cost.total_usd": 0.00014,
                "llm.cost.currency": "USD",
                "llm.latency.total_ms": 1250,
                "redforge.security.risk_score": 2.3,
                "redforge.security.risk_level": "low",
                "redforge.security.vulnerabilities_detected": 0,
                "http.method": "POST",
                "http.status_code": 200
            },
            "events": [
                {
                    "timestamp": "2024-01-01T12:00:00.100Z",
                    "name": "llm.request.start",
                    "attributes": {
                        "llm.request.id": "req_12345"
                    }
                },
                {
                    "timestamp": "2024-01-01T12:00:01.200Z",
                    "name": "redforge.security.analysis_complete",
                    "attributes": {
                        "redforge.security.analysis_duration_ms": 15,
                        "redforge.security.patterns_checked": 47,
                        "redforge.security.risk_score": 2.3
                    }
                }
            ]
        }
        
        # Should validate without errors
        validate(instance=extended_span, schema=OTEL_SPAN_SCHEMA)

    def test_security_extension_valid(self):
        """Test security vulnerability detection schema"""
        security_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 70,
                "redforge.security.risk_score": 7.5,
                "redforge.security.risk_level": "high",
                "redforge.security.vulnerabilities_detected": 1,
                "redforge.security.vulnerabilities": [
                    {
                        "id": "vuln_001",
                        "category": "prompt_injection",
                        "severity": "high",
                        "confidence": 0.87,
                        "description": "Potential system prompt manipulation attempt",
                        "matched_patterns": ["ignore previous", "system:"],
                        "risk_score": 7.5,
                        "remediation": "Implement input validation and prompt sanitization"
                    }
                ]
            }
        }
        
        # Should validate without errors
        validate(instance=security_span, schema=OTEL_SPAN_SCHEMA)

    def test_error_span_valid(self):
        """Test error handling span schema"""
        error_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "status": {
                "code": "ERROR",
                "message": "Rate limit exceeded"
            },
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 0,
                "http.status_code": 429,
                "error.type": "rate_limit",
                "error.category": "client",
                "error.code": "429",
                "error.message": "Rate limit exceeded. Try again in 60 seconds.",
                "error.retry_after": 60,
                "error.recoverable": True,
                "error.impact": "request_delayed"
            }
        }
        
        # Should validate without errors
        validate(instance=error_span, schema=OTEL_SPAN_SCHEMA)

    def test_minimal_valid_span(self):
        """Test minimal valid span with only required fields"""
        minimal_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 50
            }
        }
        
        # Should validate without errors
        validate(instance=minimal_span, schema=OTEL_SPAN_SCHEMA)

    def test_invalid_trace_id_format(self):
        """Test validation fails for invalid trace_id format"""
        invalid_span = {
            "trace_id": "invalid-trace-id",  # Invalid format
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 50
            }
        }
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_span, schema=OTEL_SPAN_SCHEMA)

    def test_invalid_span_id_format(self):
        """Test validation fails for invalid span_id format"""
        invalid_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "invalid-span",  # Invalid format
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 50
            }
        }
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_span, schema=OTEL_SPAN_SCHEMA)

    def test_invalid_provider(self):
        """Test validation fails for invalid LLM provider"""
        invalid_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "invalid_provider",  # Not in enum
                "llm.tokens.total": 50
            }
        }
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_span, schema=OTEL_SPAN_SCHEMA)

    def test_invalid_risk_score_range(self):
        """Test validation fails for risk score outside valid range"""
        invalid_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 50,
                "redforge.security.risk_score": 15.0  # Outside 0-10 range
            }
        }
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_span, schema=OTEL_SPAN_SCHEMA)

    def test_invalid_temperature_range(self):
        """Test validation fails for temperature outside valid range"""
        invalid_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 50,
                "llm.request.temperature": 3.0  # Outside 0-2 range
            }
        }
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_span, schema=OTEL_SPAN_SCHEMA)

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing"""
        invalid_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            # Missing required span_id
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 50
            }
        }
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_span, schema=OTEL_SPAN_SCHEMA)

    def test_missing_required_attributes(self):
        """Test validation fails when required attributes are missing"""
        invalid_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                # Missing required llm.provider and llm.tokens.total
                "llm.model": "gpt-4"
            }
        }
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_span, schema=OTEL_SPAN_SCHEMA)

    def test_cost_tracking_schema_valid(self):
        """Test cost tracking schema extensions"""
        cost_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 70,
                "llm.cost.total_usd": 0.00014,
                "llm.cost.currency": "USD",
                "llm.cost.pricing_model": "token_based",
                "llm.cost.input_price_per_1k": 0.002,
                "llm.cost.output_price_per_1k": 0.004,
                "llm.cost.organization_id": "org_12345",
                "llm.cost.project_id": "proj_67890"
            }
        }
        
        # Should validate without errors
        validate(instance=cost_span, schema=OTEL_SPAN_SCHEMA)

    def test_performance_metrics_valid(self):
        """Test performance metrics schema"""
        performance_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 70,
                "llm.latency.total_ms": 1250,
                "llm.latency.first_token_ms": 850,
                "llm.latency.tokens_per_second": 36.0,
                "llm.throughput.requests_per_second": 2.5,
                "llm.throughput.concurrent_requests": 5
            }
        }
        
        # Should validate without errors
        validate(instance=performance_span, schema=OTEL_SPAN_SCHEMA)

    def test_compliance_metadata_valid(self):
        """Test compliance tracking metadata"""
        compliance_span = {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "attributes": {
                "llm.provider": "openai",
                "llm.tokens.total": 70,
                "redforge.compliance.nist_controls": ["GOVERN-1.1", "MAP-1.1"],
                "redforge.compliance.eu_ai_act_risk": "minimal",
                "redforge.compliance.audit_required": False
            }
        }
        
        # Should validate without errors
        validate(instance=compliance_span, schema=OTEL_SPAN_SCHEMA)


class TestSchemaExamples:
    """Test that all examples from OTEL_SPAN_SCHEMA.md are valid"""
    
    def test_documentation_examples_validate(self):
        """Test that schema examples from documentation are all valid"""
        # This test ensures our documentation examples match our schema
        # In a real implementation, you might parse the markdown file directly
        
        examples = [
            # Base OTEL Span example
            {
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
                "tags": {
                    "service.name": "redforge-guardrail",
                    "service.version": "0.1.0",
                    "span.kind": "client"
                },
                "attributes": {
                    "llm.provider": "openai",
                    "llm.tokens.total": 70
                }
            }
        ]
        
        for example in examples:
            validate(instance=example, schema=OTEL_SPAN_SCHEMA)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])