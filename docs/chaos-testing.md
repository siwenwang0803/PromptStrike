# Chaos Testing Framework

PromptStrike's Chaos Testing Framework provides comprehensive resilience testing for LLM security systems through mutation testing, chaos engineering, and fault injection.

## Overview

The framework tests system resilience under adverse conditions:

- **Mutation Testing**: Data corruption, encoding issues, injection attacks
- **Chaos Engineering**: Network failures, resource exhaustion, service degradation  
- **Span Mutation**: OpenTelemetry tracing corruption for distributed systems
- **Gork Generation**: Garbled data patterns simulating real-world corruption
- **Fault Injection**: Systematic failure scenario testing

## Quick Start

### Prerequisites

```bash
# Install dependencies
poetry install --with chaos

# Or with pip
pip install -r requirements-chaos.txt
```

### Basic Usage

```bash
# Run all chaos tests
poetry run pytest tests/chaos/ -v

# Run specific test categories
poetry run pytest tests/chaos/ -k "mutation" -v
poetry run pytest tests/chaos/ -k "gork" -v

# Generate resilience report
poetry run python -m tests.chaos.resilience_scorer \
  --results-path test-results/ \
  --output-path resilience-report.json \
  --format json
```

### Docker Usage

```bash
# Build chaos testing image
docker build -f docker/Dockerfile.chaos -t promptstrike-chaos .

# Run chaos tests in isolation
docker run --rm \
  -v $(pwd)/test-results:/app/results \
  promptstrike-chaos \
  pytest tests/chaos/ --junit-xml=results/chaos-results.xml

# Generate report
docker run --rm \
  -v $(pwd)/test-results:/app/results \
  promptstrike-chaos \
  python -m tests.chaos.resilience_scorer \
    --results-path results/ \
    --output-path results/resilience-report.json
```

## Configuration

### Chaos Configuration File

Create `chaos-config.yaml` to customize testing:

```yaml
# Chaos Testing Configuration
mutation:
  enabled: true
  types:
    - "data_corruption"
    - "protocol_violation"
    - "security_payloads"
  intensity: 0.3  # 30% mutation rate
  
chaos_replay:
  enabled: true
  scenarios:
    - "malformed_spans"
    - "network_partition"
    - "memory_pressure"
  duration: 120  # seconds
  
span_mutation:
  enabled: true
  malformation_rate: 0.8
  target_fields:
    - "trace_id"
    - "span_id"
    - "operation_name"
    
gork_generation:
  enabled: true
  corruption_rate: 0.9
  categories:
    - "binary_corruption"
    - "encoding_corruption"
    - "protocol_corruption"

# Environment-specific settings
environments:
  development:
    intensity_multiplier: 1.0
    resource_limits:
      memory: "2Gi"
      cpu: "1000m"
      
  staging:
    intensity_multiplier: 0.7
    resource_limits:
      memory: "4Gi" 
      cpu: "2000m"
      
  production:
    intensity_multiplier: 0.3
    resource_limits:
      memory: "8Gi"
      cpu: "4000m"
    # Disable destructive tests in production
    disabled_scenarios:
      - "compression_bomb"
      - "buffer_overflow"
      - "memory_exhaustion"
```

### Environment Variables

```bash
# Chaos testing configuration
export CHAOS_TESTING_MODE=true
export CHAOS_INTENSITY=0.3
export CHAOS_DURATION=120
export MUTATION_TYPE=data_corruption
export SPAN_MALFORMATION_RATE=0.8
export GORK_CORRUPTION_RATE=0.9

# Resource limits
export CHAOS_MEMORY_LIMIT=2Gi
export CHAOS_CPU_LIMIT=1000m

# Reporting
export CHAOS_REPORT_FORMAT=json
export CHAOS_ARTIFACTS_PATH=./test-results
```

## Test Categories

### 1. Mutation Testing

Tests data corruption and injection vulnerabilities:

```python
from tests.chaos.mutation_engine import MutationEngine, MutationType

# Create mutation engine
engine = MutationEngine(seed=42)

# Test data corruption
result = engine.mutate(
    data={"user_input": "Hello World"},
    mutation_types=[
        MutationType.SQL_INJECTION,
        MutationType.XSS_PAYLOADS,
        MutationType.UNICODE_CORRUPTION
    ],
    mutation_rate=0.5
)

print(f"Original: {result.original_data}")
print(f"Mutated: {result.mutated_data}")
print(f"Mutation: {result.mutation_type}")
```

### 2. Chaos Engineering

Tests system resilience under failure conditions:

```python
from tests.chaos.chaos_replay import ChaosReplayEngine, ChaosScenario

# Create chaos engine with mock target
class MockReplayEngine:
    async def replay_span(self, span_data):
        # Your replay logic here
        pass

chaos_engine = ChaosReplayEngine(target_replay_engine=MockReplayEngine())

# Run chaos test
result = await chaos_engine.run_chaos_test(
    test_name="network_resilience_test",
    scenarios=[
        ChaosScenario.NETWORK_PARTITION,
        ChaosScenario.SLOW_NETWORK,
        ChaosScenario.MALFORMED_SPANS
    ],
    test_duration=60.0
)

print(f"Resilience Score: {result.resilience_score:.2f}")
print(f"Success Rate: {result.success_rate:.2%}")
```

### 3. Span Mutation

Tests OpenTelemetry span handling:

```python
from tests.chaos.span_mutator import SpanMutator, SpanMalformationType

# Create span mutator
mutator = SpanMutator(seed=42)

# Test span malformation
span = {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "span_id": "00f067aa0ba902b7", 
    "operation_name": "test_operation"
}

result = mutator.mutate_span(span, SpanMalformationType.INVALID_TRACE_ID)
print(f"Malformed span: {result.malformed_span}")
print(f"Description: {result.description}")
```

### 4. Gork Generation

Tests garbled/corrupted data handling:

```python
from tests.chaos.gork_generator import GorkGenerator, GorkType

# Create gork generator
generator = GorkGenerator(seed=42)

# Generate corrupted data
result = generator.generate_gork(
    data="Hello World",
    gork_type=GorkType.INVALID_UTF8,
    corruption_rate=0.8
)

print(f"Original: {result.original_data}")
print(f"Gork: {result.gork_data}")
print(f"Expected failures: {result.expected_failures}")
```

## CI Integration

### GitHub Actions Workflow

The framework automatically runs in CI:

```yaml
# .github/workflows/chaos-testing.yml
name: Chaos Testing

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  chaos-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        chaos-type: [mutation, chaos-replay, span-mutation, gork]
        
    steps:
    - uses: actions/checkout@v4
    - name: Run chaos tests
      run: |
        poetry run pytest tests/chaos/ \
          -k "${{ matrix.chaos-type }}" \
          --junit-xml=results/${{ matrix.chaos-type }}.xml
```

### Custom CI Commands

```bash
# Run chaos tests with custom configuration
make chaos-test CONFIG=chaos-config.yaml

# Generate resilience report
make chaos-report FORMAT=json

# Run specific chaos scenarios
make chaos-run SCENARIOS="network,memory,corruption"

# Validate system under chaos
make chaos-validate THRESHOLD=0.7
```

## Resource Isolation

### Docker Environment

Use Docker for safe chaos testing isolation:

```dockerfile
# docker/Dockerfile.chaos
FROM python:3.11-slim

# Install chaos testing dependencies
COPY requirements-chaos.txt .
RUN pip install -r requirements-chaos.txt

# Copy chaos testing framework
COPY tests/chaos/ /app/tests/chaos/
WORKDIR /app

# Resource limits
ENV CHAOS_MEMORY_LIMIT=2Gi
ENV CHAOS_CPU_LIMIT=1000m

# Non-root user for security
RUN useradd -m chaosuser
USER chaosuser

ENTRYPOINT ["python", "-m", "pytest"]
```

### Kubernetes Deployment

```yaml
# k8s/chaos-testing-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: chaos-testing
  namespace: testing
spec:
  containers:
  - name: chaos-test
    image: promptstrike-chaos:latest
    resources:
      limits:
        memory: "2Gi"
        cpu: "1000m"
      requests:
        memory: "1Gi" 
        cpu: "500m"
    env:
    - name: CHAOS_TESTING_MODE
      value: "true"
    - name: CHAOS_INTENSITY
      value: "0.3"
    volumeMounts:
    - name: results
      mountPath: /app/results
  volumes:
  - name: results
    emptyDir: {}
  restartPolicy: Never
```

### Resource Monitoring

Monitor resource usage during chaos tests:

```bash
# Monitor memory usage
docker stats promptstrike-chaos

# Check Kubernetes resource usage
kubectl top pod chaos-testing -n testing

# Set resource alerts
kubectl apply -f k8s/chaos-resource-alerts.yaml
```

## Reporting & Metrics

### Resilience Score Calculation

The framework calculates resilience scores (0.0-1.0):

- **Mutation Resilience** (25%): Data corruption handling
- **Chaos Resilience** (30%): Failure scenario recovery  
- **Span Mutation** (20%): Distributed tracing integrity
- **Gork Resilience** (15%): Garbled data processing
- **Error Handling** (10%): Exception management

### Report Formats

Generate reports in multiple formats:

```bash
# JSON report
python -m tests.chaos.resilience_scorer \
  --results-path results/ \
  --format json \
  --output-path resilience.json

# CSV summary
python -m tests.chaos.resilience_scorer \
  --results-path results/ \
  --format csv \
  --output-path resilience.csv

# Human-readable text
python -m tests.chaos.resilience_scorer \
  --results-path results/ \
  --format text \
  --output-path resilience.txt
```

### Historical Tracking

Store results for trend analysis:

```bash
# Archive results with timestamp
mkdir -p chaos-history/$(date +%Y-%m-%d)
cp test-results/* chaos-history/$(date +%Y-%m-%d)/

# Generate trend report
python scripts/chaos-trends.py \
  --history-path chaos-history/ \
  --output-path trend-report.html
```

## Integration with Guardrail SDK

### OTEL Span Capture

Integrate with real OpenTelemetry spans:

```python
from guardrail.sdk import GuardrailClient
from tests.chaos.span_mutator import SpanMutator

# Capture real spans from Guardrail SDK
client = GuardrailClient()
spans = client.get_recent_spans(limit=100)

# Test with real span data
mutator = SpanMutator()
for span in spans:
    result = mutator.mutate_span(span.to_dict())
    # Test replay with mutated span
```

### End-to-End Testing

```python
# Test complete pipeline with chaos
async def test_e2e_with_chaos():
    chaos_engine = ChaosReplayEngine(target_replay_engine=replay_engine)
    
    # Inject chaos during real workload
    async with chaos_engine.chaos_context():
        result = await client.analyze_prompt("test prompt")
        assert result.risk_score is not None
```

## Troubleshooting

### Common Issues

1. **Memory Exhaustion**: Reduce `CHAOS_INTENSITY` or increase resource limits
2. **Test Timeouts**: Increase `CHAOS_DURATION` or reduce test complexity
3. **False Positives**: Review mutation types and exclude non-applicable scenarios

### Debug Mode

```bash
# Enable verbose logging
export CHAOS_LOG_LEVEL=DEBUG

# Run single test with debug output
poetry run pytest tests/chaos/test_mutation.py::test_sql_injection -v -s

# Capture detailed metrics
export CHAOS_DETAILED_METRICS=true
```

### Performance Tuning

```yaml
# chaos-performance.yaml
performance:
  parallel_workers: 4
  batch_size: 100
  timeout_multiplier: 1.5
  memory_optimization: true
  
  # Skip expensive tests in CI
  ci_mode:
    skip_compression_bombs: true
    skip_large_mutations: true
    reduce_gork_complexity: true
```

## Best Practices

1. **Start Small**: Begin with low intensity (0.1-0.3) and increase gradually
2. **Isolate Environments**: Never run chaos tests against production
3. **Monitor Resources**: Set appropriate limits and alerts
4. **Regular Testing**: Schedule chaos tests daily or weekly
5. **Document Failures**: Track and analyze recurring failure patterns
6. **Team Training**: Ensure team understands chaos engineering principles

## Advanced Usage

### Custom Mutations

```python
# Create custom mutation type
class CustomMutation(MutationType):
    CUSTOM_ATTACK = "custom_attack"

# Implement custom strategy
def custom_mutation_strategy(data, rate):
    # Your custom corruption logic
    return mutated_data, ["custom_corruption"]

# Register with engine
engine.mutation_strategies[CustomMutation.CUSTOM_ATTACK] = custom_mutation_strategy
```

### Chaos Scheduling

```python
# Schedule chaos events
from tests.chaos.chaos_scheduler import ChaosScheduler

scheduler = ChaosScheduler()
scheduler.schedule_daily_chaos(
    scenarios=[ChaosScenario.NETWORK_PARTITION],
    duration=30,
    time="02:00"  # 2 AM daily
)
```

For more examples and advanced configurations, see the `/examples` directory in the repository.