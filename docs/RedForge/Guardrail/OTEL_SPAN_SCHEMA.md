# OTEL Span Schema v0.1 - RedForge Guardrail
<!-- cid-otel-span-schema-v0.1 -->

## Overview

This document defines the OpenTelemetry (OTEL) span schema for RedForge Guardrail traffic monitoring. The schema extends standard OTEL spans with LLM-specific metadata including tokens, latency, cost, and security analysis.

### Key Design Principles
- **OTEL Compatibility**: Full compliance with OpenTelemetry semantic conventions
- **Security-First**: Built-in vulnerability detection and risk scoring
- **Cost Awareness**: Token usage and cost tracking for financial monitoring
- **Compliance Ready**: NIST AI-RMF and EU AI Act metadata inclusion

## Core Span Structure

### Base OTEL Span
```json
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
  }
}
```

### RedForge Extensions
```json
{
  "resource": {
    "service.name": "redforge-guardrail",
    "service.version": "0.1.0",
    "deployment.environment": "production",
    "redforge.guardrail.version": "0.1.0"
  },
  "attributes": {
    // LLM Provider Information
    "llm.provider": "openai",
    "llm.model": "gpt-4",
    "llm.endpoint": "https://api.openai.com/v1/chat/completions",
    "llm.api_version": "2023-12-01",
    
    // Request/Response Metadata
    "llm.request.temperature": 0.7,
    "llm.request.max_tokens": 150,
    "llm.request.top_p": 1.0,
    "llm.request.frequency_penalty": 0.0,
    "llm.request.presence_penalty": 0.0,
    
    // Token Usage
    "llm.tokens.prompt": 25,
    "llm.tokens.completion": 45,
    "llm.tokens.total": 70,
    
    // Cost Tracking
    "llm.cost.input_tokens_usd": 0.00005,
    "llm.cost.output_tokens_usd": 0.00009,
    "llm.cost.total_usd": 0.00014,
    "llm.cost.currency": "USD",
    
    // Performance Metrics
    "llm.latency.total_ms": 1250,
    "llm.latency.first_token_ms": 850,
    "llm.latency.tokens_per_second": 36.0,
    
    // Security Analysis
    "redforge.security.risk_score": 2.3,
    "redforge.security.risk_level": "low",
    "redforge.security.vulnerabilities_detected": 0,
    "redforge.security.analysis_version": "v1.0",
    
    // Compliance Metadata
    "redforge.compliance.nist_controls": ["GOVERN-1.1", "MAP-1.1"],
    "redforge.compliance.eu_ai_act_risk": "minimal",
    "redforge.compliance.audit_required": false,
    
    // Content Analysis
    "llm.content.prompt_length": 125,
    "llm.content.response_length": 234,
    "llm.content.language": "en",
    "llm.content.moderation_flagged": false,
    
    // HTTP Details
    "http.method": "POST",
    "http.url": "https://api.openai.com/v1/chat/completions",
    "http.status_code": 200,
    "http.request_content_length": 256,
    "http.response_content_length": 512,
    "http.user_agent": "redforge-guardrail/0.1.0"
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
      "timestamp": "2024-01-01T12:00:00.850Z",
      "name": "llm.response.first_token",
      "attributes": {
        "llm.response.first_token_latency_ms": 750
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
    },
    {
      "timestamp": "2024-01-01T12:00:01.250Z",
      "name": "llm.response.complete",
      "attributes": {
        "llm.response.id": "resp_67890",
        "llm.response.finish_reason": "stop",
        "llm.response.size_bytes": 512
      }
    }
  ]
}
```

## Security Extension Schema

### Vulnerability Detection
```json
{
  "attributes": {
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
    ],
    "redforge.security.attack_vectors": [
      {
        "vector": "direct_injection",
        "technique": "instruction_override",
        "mitre_tactic": "TA0001",
        "severity": "high"
      }
    ],
    "redforge.security.content_analysis": {
      "sentiment": "neutral",
      "toxicity_score": 0.1,
      "pii_detected": false,
      "sensitive_topics": [],
      "language_anomalies": false
    }
  }
}
```

### Compliance Tracking
```json
{
  "attributes": {
    "redforge.compliance.nist_rmf": {
      "controls_tested": ["GOVERN-1.1", "MAP-1.1", "MEASURE-2.1"],
      "controls_passed": ["GOVERN-1.1", "MAP-1.1"],
      "controls_failed": ["MEASURE-2.1"],
      "overall_compliance": "partial"
    },
    "redforge.compliance.eu_ai_act": {
      "risk_category": "minimal",
      "articles_applicable": ["Article 9", "Article 10"],
      "documentation_required": true,
      "assessment_date": "2024-01-01T12:00:00.000Z"
    },
    "redforge.compliance.soc2": {
      "controls_impact": ["CC6.1", "CC6.7"],
      "evidence_required": true,
      "audit_trail": "span_trace_4bf92f3577b34da6a3ce929d0e0e4736"
    }
  }
}
```

## Cost Tracking Schema

### Token Economics
```json
{
  "attributes": {
    "llm.cost.pricing_model": "token_based",
    "llm.cost.input_price_per_1k": 0.002,
    "llm.cost.output_price_per_1k": 0.004,
    "llm.cost.calculation_method": "exact",
    "llm.cost.billing_period": "2024-01",
    "llm.cost.organization_id": "org_12345",
    "llm.cost.project_id": "proj_67890",
    "llm.cost.budget_remaining_usd": 450.25,
    "llm.cost.daily_spend_usd": 12.34
  }
}
```

### Financial Monitoring
```json
{
  "attributes": {
    "llm.cost.alert_thresholds": {
      "daily_limit_usd": 100.0,
      "request_limit_usd": 1.0,
      "token_limit_per_request": 4000
    },
    "llm.cost.optimization": {
      "cache_hit": false,
      "compression_ratio": 0.85,
      "estimated_savings_usd": 0.00003
    },
    "llm.cost.allocation": {
      "department": "engineering",
      "team": "ai-platform",
      "environment": "production",
      "cost_center": "CC-2024-001"
    }
  }
}
```

## Performance Metrics Schema

### Latency Breakdown
```json
{
  "attributes": {
    "llm.latency.dns_resolution_ms": 12,
    "llm.latency.tcp_connection_ms": 45,
    "llm.latency.tls_handshake_ms": 78,
    "llm.latency.request_send_ms": 5,
    "llm.latency.server_processing_ms": 1050,
    "llm.latency.response_receive_ms": 60,
    "llm.latency.total_ms": 1250,
    "llm.latency.p95_ms": 1400,
    "llm.latency.p99_ms": 2100
  }
}
```

### Throughput Metrics
```json
{
  "attributes": {
    "llm.throughput.requests_per_second": 2.5,
    "llm.throughput.tokens_per_second": 36.0,
    "llm.throughput.concurrent_requests": 5,
    "llm.throughput.queue_depth": 2,
    "llm.throughput.rate_limit_remaining": 950,
    "llm.throughput.rate_limit_reset_time": "2024-01-01T13:00:00.000Z"
  }
}
```

## Error Handling Schema

### Error Classification
```json
{
  "status": {
    "code": "ERROR",
    "message": "Rate limit exceeded"
  },
  "attributes": {
    "error.type": "rate_limit",
    "error.category": "client",
    "error.code": "429",
    "error.message": "Rate limit exceeded. Try again in 60 seconds.",
    "error.retry_after": 60,
    "error.recoverable": true,
    "error.impact": "request_delayed"
  }
}
```

### Security Errors
```json
{
  "attributes": {
    "redforge.security.blocked": true,
    "redforge.security.block_reason": "high_risk_content",
    "redforge.security.action_taken": "request_blocked",
    "redforge.security.alert_sent": true,
    "redforge.security.incident_id": "INC-2024-001"
  }
}
```

## Sampling and Cardinality

### Sampling Strategy
```json
{
  "attributes": {
    "sampling.priority": 1,
    "sampling.rate": 0.1,
    "sampling.decision": "sampled",
    "sampling.reason": "high_risk_content"
  }
}
```

### Cardinality Control
- **High Cardinality**: `trace_id`, `span_id`, `llm.request.id`
- **Medium Cardinality**: `llm.model`, `llm.provider`, `user_id`
- **Low Cardinality**: `llm.provider`, `environment`, `service.name`

## Schema Validation

### JSON Schema Definition
```json
{
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
    "attributes": {
      "type": "object",
      "properties": {
        "llm.provider": {
          "type": "string",
          "enum": ["openai", "anthropic", "azure", "google", "aws"]
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
        "redforge.security.risk_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 10
        }
      },
      "required": ["llm.provider", "llm.tokens.total"]
    }
  },
  "required": ["trace_id", "span_id", "attributes"]
}
```

## Integration Examples

### Python SDK Integration
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Create RedForge span
with tracer.start_as_current_span("llm.chat.completion") as span:
    span.set_attributes({
        "llm.provider": "openai",
        "llm.model": "gpt-4",
        "llm.tokens.total": 70,
        "llm.cost.total_usd": 0.00014,
        "redforge.security.risk_score": 2.3
    })
    
    # Add security analysis event
    span.add_event("redforge.security.analysis_complete", {
        "redforge.security.analysis_duration_ms": 15,
        "redforge.security.patterns_checked": 47
    })
```

### Kubernetes Integration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-config
data:
  otel-config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
    exporters:
      jaeger:
        endpoint: jaeger:14250
        tls:
          insecure: true
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [jaeger]
```

## Compliance Reporting

### NIST AI-RMF Mapping
```json
{
  "nist_rmf_report": {
    "assessment_date": "2024-01-01T12:00:00.000Z",
    "controls": [
      {
        "control_id": "GOVERN-1.1",
        "status": "implemented",
        "evidence_spans": ["trace_4bf92f3577b34da6a3ce929d0e0e4736"],
        "last_validated": "2024-01-01T12:00:00.000Z"
      }
    ],
    "overall_compliance": "75%",
    "risk_level": "acceptable"
  }
}
```

### EU AI Act Documentation
```json
{
  "eu_ai_act_report": {
    "system_category": "general_purpose",
    "risk_level": "minimal",
    "documentation_date": "2024-01-01T12:00:00.000Z",
    "monitoring_spans": ["trace_4bf92f3577b34da6a3ce929d0e0e4736"],
    "compliance_status": "compliant"
  }
}
```

## Performance Considerations

### Span Size Optimization
- **Target Size**: <2KB per span
- **Compression**: Enable gzip compression
- **Sampling**: Adaptive sampling based on risk score
- **Batching**: Batch size 1024 spans

### Storage Requirements
- **Retention**: 90 days for compliance spans
- **Indexing**: Index on risk_score, provider, timestamp
- **Partitioning**: Partition by date and provider

## Future Extensions

### Planned v0.2 Features
- **Multi-modal Support**: Image, audio, video analysis
- **Real-time Alerting**: Streaming analytics
- **Advanced ML**: Anomaly detection
- **Custom Metrics**: User-defined security metrics

---

**Next Steps:**
1. Implement OTEL SDK integration in guardrail sidecar
2. Add Jaeger/Zipkin export configuration
3. Create compliance dashboard from span data
4. Performance testing with high-volume traffic