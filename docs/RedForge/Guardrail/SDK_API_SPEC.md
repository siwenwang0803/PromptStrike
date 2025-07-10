# Guardrail Python SDK – API Spec v0.1
<!-- cid-sdk-spec-v0.1 -->

## Overview

The RedForge Guardrail SDK provides real-time LLM security monitoring capabilities for production applications. It intercepts prompt/response traffic, applies security analysis, and generates compliance reports using the same JSON schema as the CLI scanner.

### Key Features
- **Traffic Interception**: Async middleware for httpx, OpenAI, and Anthropic clients
- **Real-time Analysis**: Live vulnerability detection with <15ms latency overhead
- **Fuzzer Replay**: Automated nightly security testing with attack packs
- **Compliance Reporting**: NIST AI-RMF, EU AI Act, SOC 2 compatible outputs
- **Error Resilience**: Graceful degradation with retry and fallback mechanisms

## Core Functions

### Traffic Capture

#### `capture(request, response, config=None)`
Intercepts and analyzes HTTP request/response pairs for LLM API calls.

**Parameters:**
- `request: httpx.Request` - The outgoing HTTP request
- `response: httpx.Response` - The received HTTP response  
- `config: Optional[GuardrailConfig]` - Configuration overrides

**Returns:**
- `Span` - OpenTelemetry compatible span with security metadata

**Exceptions:**
- `NetworkError` - Network connectivity issues
- `AnalysisTimeoutError` - Analysis exceeded timeout
- `InvalidRequestError` - Malformed request data

**Example:**
```python
import httpx
from redforge.guardrail import capture, NetworkError

async with httpx.AsyncClient() as client:
    request = client.build_request("POST", "https://api.openai.com/v1/chat/completions", json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}]
    })
    
    try:
        response = await client.send(request)
        # Capture and analyze the traffic
        span = await capture(request, response)
        print(f"Risk Score: {span.risk_score}, Vulnerabilities: {span.vulnerabilities}")
    except NetworkError as e:
        print(f"Network error: {e}")
        # Continue without security analysis if fail_open=True
```

#### `capture_middleware(sampling_rate=1.0, config=None)`
Factory function to create httpx middleware for automatic traffic capture.

**Parameters:**
- `sampling_rate: float = 1.0` - Percentage of requests to capture (0.0-1.0)
- `config: Optional[GuardrailConfig]` - Configuration overrides

**Returns:**
- `httpx.AsyncClient` - Configured client with capture middleware

**Example:**
```python
from redforge.guardrail import capture_middleware, GuardrailConfig

config = GuardrailConfig(
    fail_open=True,  # Allow requests even if analysis fails
    max_retries=3,
    analysis_timeout_ms=50
)

# Create client with 10% sampling
client = capture_middleware(sampling_rate=0.1, config=config)

# All requests are automatically captured
response = await client.post("https://api.openai.com/v1/chat/completions", json=payload)
```

### Fuzzer Replay

#### `replay(fuzzer_pack, target_config, output_dir=None, batch_size=10)`
Executes automated security testing against target LLM endpoints.

**Parameters:**
- `fuzzer_pack: str` - Attack pack name ("owasp_llm_top10", "finops", "privacy") 
- `target_config: TargetConfig` - LLM endpoint configuration
- `output_dir: Optional[Path] = None` - Directory for reports (default: ./reports)
- `batch_size: int = 10` - Number of concurrent attacks

**Returns:**
- `ReplayResult` - Summary of fuzzing session with vulnerability counts

**Exceptions:**
- `AuthenticationError` - Invalid API credentials
- `RateLimitError` - API rate limit exceeded
- `FuzzerPackNotFoundError` - Invalid attack pack name

**Example:**
```python
from redforge.guardrail import replay, TargetConfig, RateLimitError

config = TargetConfig(
    endpoint="https://api.openai.com/v1/chat/completions",
    api_key="sk-...",
    model="gpt-4"
)

try:
    result = await replay("owasp_llm_top10", config, output_dir=Path("./security_reports"))
    print(f"Found {result.vulnerabilities_found} vulnerabilities in {result.duration_seconds}s")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
```

### Report Generation

#### `report(spans, output_dir, format="json", batch_size=1000)`
Generates compliance reports from captured traffic spans.

**Parameters:**
- `spans: List[Span]` - Traffic spans to analyze
- `output_dir: Path` - Output directory for reports
- `format: str = "json"` - Report format ("json", "html", "pdf")
- `batch_size: int = 1000` - Process spans in batches for memory efficiency

**Returns:**
- `Path` - Path to generated report file

**Exceptions:**
- `ReportGenerationError` - Failed to generate report
- `InsufficientDataError` - Not enough spans for meaningful analysis

**Example:**
```python
from redforge.guardrail import report, InsufficientDataError

try:
    # Generate comprehensive security report
    report_path = await report(
        spans=collected_spans,
        output_dir=Path("./compliance_reports"),
        format="json"
    )
    print(f"Report generated: {report_path}")
except InsufficientDataError:
    print("Need at least 100 spans for report generation")
```

### Health Check

#### `health_check()`
Returns the current health status of the Guardrail SDK.

**Returns:**
- `HealthStatus` - SDK health metrics

**Example:**
```python
from redforge.guardrail import health_check

status = await health_check()
print(f"SDK Version: {status.sdk_version}")
print(f"Analysis Latency: {status.analysis_latency_ms}ms")
print(f"Queue Depth: {status.queue_depth}")
```

## Data Models

### `Span`
OpenTelemetry compatible span with RedForge security extensions.

```python
class Span(BaseModel):
    """OpenTelemetry span with security metadata"""
    
    # Core OTEL fields
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    
    # HTTP request/response
    request: HttpRequest
    response: HttpResponse
    
    # Security analysis
    risk_score: float = Field(ge=0.0, le=10.0)
    vulnerabilities: List[VulnerabilityFinding] = Field(default_factory=list)
    
    # Performance metrics
    latency_ms: int = Field(ge=0)
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    
    # Compliance metadata
    nist_controls: List[str] = Field(default_factory=list)
    eu_ai_act_refs: List[str] = Field(default_factory=list)
    
    # Error tracking
    analysis_errors: List[str] = Field(default_factory=list)
    degraded_mode: bool = False
```

### `VulnerabilityFinding`
Individual security vulnerability detected in traffic.

```python
class VulnerabilityFinding(BaseModel):
    """Security vulnerability finding"""
    
    finding_id: str
    category: AttackCategory  # Reuse from core models
    severity: SeverityLevel   # Reuse from core models
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Evidence
    matched_patterns: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)
    
    # Remediation
    remediation_advice: str
    references: List[str] = Field(default_factory=list)
    
    # Detection metadata
    detection_timestamp: datetime
    detector_version: str
```

### `TargetConfig`
LLM endpoint configuration for fuzzer replay.

```python
class TargetConfig(BaseModel):
    """LLM target configuration"""
    
    endpoint: str = Field(..., description="API endpoint URL")
    api_key: str = Field(..., description="API authentication key")
    model: str = Field(..., description="Model name")
    
    # Rate limiting
    max_requests_per_minute: int = Field(default=60, ge=1)
    timeout_seconds: int = Field(default=30, ge=1)
    
    # Provider-specific settings
    provider: Literal["openai", "anthropic", "azure", "generic"] = "generic"
    headers: Dict[str, str] = Field(default_factory=dict)
    
    # Retry configuration
    max_retries: int = Field(default=3, ge=0)
    retry_delay_seconds: float = Field(default=1.0, ge=0.1)
    
    async def validate_credentials(self) -> bool:
        """Validate API credentials are valid"""
        # Implementation to test credentials
        pass
```

### `ReplayResult`
Summary of fuzzer replay session.

```python
class ReplayResult(BaseModel):
    """Fuzzer replay session results"""
    
    # Session metadata
    session_id: str
    fuzzer_pack: str
    target_endpoint: str
    start_time: datetime
    end_time: datetime
    
    # Execution stats
    total_attacks: int = Field(ge=0)
    successful_attacks: int = Field(ge=0)
    failed_attacks: int = Field(ge=0)
    rate_limited_attacks: int = Field(ge=0)
    
    # Vulnerability summary
    vulnerabilities_found: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    medium_count: int = Field(ge=0)
    low_count: int = Field(ge=0)
    
    # Performance metrics
    duration_seconds: float = Field(ge=0.0)
    avg_latency_ms: float = Field(ge=0.0)
    total_cost_usd: Optional[float] = None
    
    # Error tracking
    errors_encountered: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Report paths
    json_report_path: Path
    html_report_path: Optional[Path] = None
    pdf_report_path: Optional[Path] = None
```

### `HealthStatus`
SDK health and performance metrics.

```python
class HealthStatus(BaseModel):
    """SDK health status"""
    
    sdk_version: str
    status: Literal["healthy", "degraded", "unhealthy"]
    
    # Performance metrics
    analysis_latency_ms: float
    queue_depth: int
    active_analyses: int
    
    # Resource usage
    memory_usage_mb: float
    cpu_usage_percent: float
    
    # Error tracking
    last_error: Optional[str] = None
    error_count_24h: int = 0
    
    # Cache status
    cache_hit_rate: float
    patterns_cached: int
    
    # Uptime
    uptime_seconds: int
    spans_processed_total: int
```

## Configuration

### `GuardrailConfig`
Global configuration for Guardrail SDK behavior.

```python
class GuardrailConfig(BaseModel):
    """Guardrail SDK configuration"""
    
    # Analysis settings
    enable_realtime_analysis: bool = True
    sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    max_response_length: int = Field(default=2000, ge=100)
    
    # Performance tuning
    analysis_timeout_ms: int = Field(default=50, ge=10)
    max_concurrent_analyses: int = Field(default=10, ge=1)
    batch_size: int = Field(default=100, ge=1)
    
    # Error handling
    fail_open: bool = Field(default=True, description="Allow requests if analysis fails")
    max_retries: int = Field(default=3, ge=0)
    retry_delay_ms: int = Field(default=100, ge=10)
    
    # Output settings
    output_format: Literal["json", "otel"] = "json"
    compress_spans: bool = True
    span_retention_hours: int = Field(default=168, ge=1)  # 7 days
    
    # Security settings
    mask_sensitive_data: bool = True
    log_full_requests: bool = False
    
    # Compliance requirements
    required_nist_controls: List[str] = Field(default_factory=list)
    required_eu_ai_act_articles: List[str] = Field(default_factory=list)
    
    # Callbacks
    on_vulnerability_found: Optional[Callable] = None
    on_analysis_error: Optional[Callable] = None
    on_rate_limit: Optional[Callable] = None
    
    # Cache settings
    enable_pattern_cache: bool = True
    cache_ttl_seconds: int = Field(default=3600, ge=60)
    max_cache_size_mb: int = Field(default=100, ge=10)
```

## Usage Examples

### 1. Basic Traffic Monitoring

```python
import asyncio
from redforge.guardrail import capture_middleware, GuardrailConfig

async def main():
    # Configure guardrail
    config = GuardrailConfig(
        sampling_rate=0.1,  # 10% sampling
        enable_realtime_analysis=True
    )
    
    # Create instrumented client
    client = capture_middleware(config=config)
    
    # Normal LLM usage - automatically monitored
    response = await client.post("https://api.openai.com/v1/chat/completions", json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "What is the capital of France?"}]
    })
    
    print(f"Response: {response.json()}")

asyncio.run(main())
```

### 2. Scheduled Security Testing

```python
import asyncio
from pathlib import Path
from redforge.guardrail import replay, TargetConfig

async def nightly_security_scan():
    """Automated nightly security testing"""
    
    # Configure target
    config = TargetConfig(
        endpoint="https://api.openai.com/v1/chat/completions",
        api_key="sk-...",
        model="gpt-4",
        max_requests_per_minute=30  # Rate limit for production
    )
    
    # Run comprehensive security scan
    result = await replay(
        fuzzer_pack="owasp_llm_top10",
        target_config=config,
        output_dir=Path("./nightly_reports")
    )
    
    # Alert on critical vulnerabilities
    if result.critical_count > 0:
        print(f"🚨 CRITICAL: {result.critical_count} critical vulnerabilities found!")
        # Send alert to security team
        
    print(f"Scan complete: {result.vulnerabilities_found} total vulnerabilities")
    return result

# Schedule with cron or task scheduler
asyncio.run(nightly_security_scan())
```

### 3. Kubernetes Sidecar Integration

```python
from fastapi import FastAPI
from redforge.guardrail import capture_middleware, report
from pathlib import Path

app = FastAPI()

# Global guardrail client
guardrail_client = capture_middleware(sampling_rate=0.05)  # 5% sampling

@app.post("/chat")
async def chat_endpoint(request: dict):
    """Chat endpoint with automatic security monitoring"""
    
    # LLM call is automatically captured and analyzed
    response = await guardrail_client.post(
        "https://api.openai.com/v1/chat/completions",
        json=request
    )
    
    return response.json()

@app.post("/security/report")
async def generate_security_report():
    """Generate security report from captured traffic"""
    
    # Collect spans from last 24h
    spans = guardrail_client.get_spans(hours=24)
    
    # Generate report
    report_path = await report(
        spans=spans,
        output_dir=Path("/var/reports"),
        format="json"
    )
    
    return {"report_path": str(report_path)}
```

## Exception Hierarchy

```python
# Base exception
class RedForgeError(Exception):
    """Base exception for all RedForge errors"""
    pass

# Network errors
class NetworkError(RedForgeError):
    """Network connectivity or timeout issues"""
    pass

class AnalysisTimeoutError(NetworkError):
    """Analysis exceeded configured timeout"""
    timeout_ms: int

# Authentication errors
class AuthenticationError(RedForgeError):
    """API authentication failed"""
    provider: str
    
# Rate limiting
class RateLimitError(RedForgeError):
    """API rate limit exceeded"""
    retry_after: int  # seconds
    requests_remaining: int

# Analysis errors
class AnalysisError(RedForgeError):
    """Security analysis failed"""
    pass

class InvalidRequestError(AnalysisError):
    """Request data is malformed or invalid"""
    pass

class InsufficientDataError(AnalysisError):
    """Not enough data for meaningful analysis"""
    required_count: int
    actual_count: int

# Configuration errors
class ConfigurationError(RedForgeError):
    """Invalid SDK configuration"""
    pass

class FuzzerPackNotFoundError(ConfigurationError):
    """Requested attack pack not found"""
    pack_name: str
    available_packs: List[str]

# Report generation errors
class ReportGenerationError(RedForgeError):
    """Failed to generate report"""
    format: str
```

## Performance Optimizations

### Span Batching

```python
class SpanBatcher:
    """Efficiently batch spans for processing and storage"""
    
    def __init__(self, batch_size: int = 100, flush_interval_seconds: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval_seconds
        self._queue: asyncio.Queue[Span] = asyncio.Queue()
        self._lock = asyncio.Lock()
        
    async def add_span(self, span: Span) -> None:
        """Add span to batch queue"""
        await self._queue.put(span)
        
        # Auto-flush if batch is full
        if self._queue.qsize() >= self.batch_size:
            await self.flush()
    
    async def flush(self) -> List[Span]:
        """Flush all queued spans"""
        async with self._lock:
            spans = []
            while not self._queue.empty():
                spans.append(await self._queue.get())
            return spans
```

### Attack Pattern Cache

```python
class AttackPatternCache:
    """Cache attack patterns to reduce analysis latency"""
    
    def __init__(self, ttl_seconds: int = 3600, max_size_mb: int = 100):
        self.ttl = ttl_seconds
        self.max_size = max_size_mb
        self._cache: Dict[str, CachedPattern] = {}
        self._access_times: Dict[str, datetime] = {}
        
    async def get_patterns(self, category: str) -> Optional[List[Pattern]]:
        """Get cached patterns for category"""
        if category in self._cache:
            self._access_times[category] = datetime.utcnow()
            return self._cache[category].patterns
        return None
        
    async def set_patterns(self, category: str, patterns: List[Pattern]) -> None:
        """Cache patterns for category"""
        # Implement LRU eviction if needed
        self._cache[category] = CachedPattern(
            patterns=patterns,
            cached_at=datetime.utcnow()
        )
```

### Concurrency Control

```python
class ConcurrencyLimiter:
    """Limit concurrent analyses to prevent resource exhaustion"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
        
    async def __aenter__(self):
        await self.semaphore.acquire()
        self.active_count += 1
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.active_count -= 1
        self.semaphore.release()
```

## Usage Examples

### 1. Basic Traffic Monitoring with Error Handling

```python
import asyncio
from redforge.guardrail import capture_middleware, GuardrailConfig, NetworkError

async def main():
    # Configure guardrail with error handling
    config = GuardrailConfig(
        sampling_rate=0.1,  # 10% sampling
        enable_realtime_analysis=True,
        fail_open=True,  # Continue on analysis failure
        on_vulnerability_found=lambda v: print(f"Found: {v.category}"),
        on_analysis_error=lambda e: print(f"Error: {e}")
    )
    
    # Create instrumented client
    client = capture_middleware(config=config)
    
    try:
        # Normal LLM usage - automatically monitored
        response = await client.post("https://api.openai.com/v1/chat/completions", json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "What is the capital of France?"}]
        })
        
        print(f"Response: {response.json()}")
    except NetworkError as e:
        print(f"Network issue: {e}")
        # Application continues if fail_open=True

asyncio.run(main())
```

### 2. Scheduled Security Testing with Retry

```python
import asyncio
from pathlib import Path
from redforge.guardrail import replay, TargetConfig, RateLimitError, AuthenticationError

async def nightly_security_scan():
    """Automated nightly security testing with error handling"""
    
    # Configure target
    config = TargetConfig(
        endpoint="https://api.openai.com/v1/chat/completions",
        api_key="sk-...",
        model="gpt-4",
        max_requests_per_minute=30,  # Rate limit for production
        max_retries=3,
        retry_delay_seconds=2.0
    )
    
    # Validate credentials first
    try:
        if not await config.validate_credentials():
            raise AuthenticationError("Invalid API key")
    except AuthenticationError as e:
        print(f"Auth failed: {e}")
        return
    
    # Run comprehensive security scan
    retry_count = 0
    while retry_count < 3:
        try:
            result = await replay(
                fuzzer_pack="owasp_llm_top10",
                target_config=config,
                output_dir=Path("./nightly_reports"),
                batch_size=5  # Smaller batches for production
            )
            
            # Alert on critical vulnerabilities
            if result.critical_count > 0:
                print(f"🚨 CRITICAL: {result.critical_count} critical vulnerabilities found!")
                # Send alert to security team
                
            print(f"Scan complete: {result.vulnerabilities_found} total vulnerabilities")
            return result
            
        except RateLimitError as e:
            print(f"Rate limited. Waiting {e.retry_after} seconds...")
            await asyncio.sleep(e.retry_after)
            retry_count += 1
    
    print("Max retries exceeded")

# Schedule with cron or task scheduler
asyncio.run(nightly_security_scan())
```

### 3. Kubernetes Sidecar Integration with Health Checks

```python
from fastapi import FastAPI, HTTPException
from redforge.guardrail import capture_middleware, report, health_check, SpanBatcher
from pathlib import Path

app = FastAPI()

# Global guardrail client with batching
guardrail_client = capture_middleware(sampling_rate=0.05)  # 5% sampling
span_batcher = SpanBatcher(batch_size=100, flush_interval_seconds=10.0)

@app.post("/chat")
async def chat_endpoint(request: dict):
    """Chat endpoint with automatic security monitoring"""
    
    try:
        # LLM call is automatically captured and analyzed
        response = await guardrail_client.post(
            "https://api.openai.com/v1/chat/completions",
            json=request
        )
        
        return response.json()
    except Exception as e:
        # Guardrail configured with fail_open=True
        # So requests continue even if analysis fails
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_endpoint():
    """Health check endpoint for k8s probes"""
    
    status = await health_check()
    
    if status.status == "unhealthy":
        raise HTTPException(status_code=503, detail="Service unhealthy")
    
    return {
        "status": status.status,
        "version": status.sdk_version,
        "latency_ms": status.analysis_latency_ms,
        "queue_depth": status.queue_depth
    }

@app.post("/security/report")
async def generate_security_report():
    """Generate security report from captured traffic"""
    
    try:
        # Flush any pending spans
        pending_spans = await span_batcher.flush()
        
        # Collect spans from last 24h
        spans = guardrail_client.get_spans(hours=24)
        spans.extend(pending_spans)
        
        # Generate report
        report_path = await report(
            spans=spans,
            output_dir=Path("/var/reports"),
            format="json",
            batch_size=1000  # Process in chunks
        )
        
        return {"report_path": str(report_path), "span_count": len(spans)}
        
    except InsufficientDataError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Need at least {e.required_count} spans, got {e.actual_count}"
        )
```

## Integration Patterns

### OpenAI Client Integration with Retry

```python
from openai import AsyncOpenAI
from redforge.guardrail import capture, NetworkError, RateLimitError
import asyncio

class GuardrailOpenAI(AsyncOpenAI):
    """OpenAI client with built-in security monitoring and retry"""
    
    def __init__(self, *args, max_retries=3, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
    
    async def chat_completions_create_with_retry(self, **kwargs):
        """Create chat completion with automatic retry and security monitoring"""
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Make original request
                response = await super().chat.completions.create(**kwargs)
                
                # Capture for security analysis
                span = await capture(
                    request=kwargs,
                    response=response,
                )
                
                # Check for vulnerabilities
                if span.risk_score > 8.0:
                    print(f"High risk detected: {span.risk_score}")
                
                return response
                
            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(e.retry_after)
                    continue
                    
            except NetworkError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
        raise last_error

# Usage
client = GuardrailOpenAI(api_key="sk-...")
response = await client.chat_completions_create_with_retry(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Anthropic Client Integration

```python
from anthropic import AsyncAnthropic
from redforge.guardrail import capture, GuardrailConfig

class GuardrailAnthropic(AsyncAnthropic):
    """Anthropic client with built-in security monitoring"""
    
    def __init__(self, *args, guardrail_config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardrail_config = guardrail_config or GuardrailConfig()
    
    async def messages_create(self, **kwargs):
        request_data = kwargs.copy()
        response = await super().messages.create(**kwargs)
        
        # Security analysis with config
        span = await capture(
            request=request_data,
            response=response,
            config=self.guardrail_config
        )
        
        # Add span to response metadata
        response._guardrail_span = span
        
        return response
```

## Performance Considerations

### Latency Overhead
- Target: <15ms additional latency per request
- Async processing ensures minimal blocking
- Pattern caching reduces repeated analysis overhead
- Configurable sampling rates for high-volume applications

### Memory Management
- Spans are compressed and batched for efficient storage
- Automatic cleanup of spans older than retention period
- Weak references for large objects
- Memory limit enforcement with LRU eviction

### Rate Limiting
- Respects API provider rate limits
- Exponential backoff with jitter
- Queue management for burst traffic
- Circuit breaker pattern for failing endpoints

### Resource Monitoring

```python
# Monitor resource usage
status = await health_check()
if status.memory_usage_mb > 500:
    # Trigger garbage collection
    await guardrail_client.cleanup_old_spans()
```

## Compliance Integration

### NIST AI-RMF Mapping

```python
from redforge.guardrail import capture, GuardrailConfig

config = GuardrailConfig(
    required_nist_controls=[
        "GOVERN-1.1",  # AI governance
        "MAP-1.1",     # Risk assessment
        "MEASURE-2.1", # Impact assessment
        "MANAGE-1.1"   # Risk management
    ]
)
```

### EU AI Act Compliance

```python
config = GuardrailConfig(
    required_eu_ai_act_articles=[
        "Article 9",   # Risk management system
        "Article 10",  # Data governance
        "Article 11",  # Documentation
        "Article 12"   # Record-keeping
    ]
)
```

## Installation & Setup

```bash
# Install SDK
pip install redforge[guardrail]

# Configuration
export REDFORGE_API_KEY="your-api-key"
export REDFORGE_OUTPUT_DIR="/var/reports"
export REDFORGE_FAIL_OPEN="true"

# Kubernetes deployment
kubectl apply -f redforge-guardrail-sidecar.yaml
```

### Kubernetes Sidecar Configuration

```yaml
# redforge-guardrail-sidecar.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redforge-config
data:
  config.yaml: |
    sampling_rate: 0.1
    fail_open: true
    analysis_timeout_ms: 50
    max_concurrent_analyses: 10
    span_retention_hours: 168
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-guardrail
spec:
  template:
    spec:
      containers:
      - name: main-app
        image: your-app:latest
        env:
        - name: REDFORGE_SIDECAR_URL
          value: "http://localhost:8081"
      - name: redforge-guardrail
        image: redforge/guardrail:0.1.0
        ports:
        - containerPort: 8081
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

**Next Steps:**
1. Implement core SDK functions in `redforge/guardrail/` module
2. Create comprehensive test suite with error injection
3. Build example applications demonstrating error handling
4. Performance benchmarks for latency and resource usage
5. Integration guides for major LLM providers