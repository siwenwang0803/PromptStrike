RedForge Guardrail Pilot-0 Staging Test Plan
Test Environment Requirements

Kubernetes cluster (staging)
RedForge Guardrail Helm chart
Load testing tools (k6)
Monitoring stack (Prometheus, Grafana)
OpenAI API access

Test Categories
1. Functional Tests



Test ID
Objective
Expected Result
Validation Method



F-001
Helm chart installation
Chart deploys successfully
helm status


F-002
Pod startup and readiness
Containers start, pass health checks
kubectl get pods


F-003
Service endpoint availability
Services accessible
Curl tests


F-004
ConfigMap application
Config applied
kubectl get configmap -o yaml


F-005
Secret mounting
API keys mounted
Env var check


F-006
Post-install job execution
Job completes
Job status, healthcheck file


F-007
Persistent volume claims
PVC mounted
kubectl get pvc


2. Security Tests



Test ID
Objective
OWASP LLM-Top-10
Expected Result
Validation Method



S-001
Non-root execution
LLM-08
Run as non-root
Security context


S-002
Capability restrictions
LLM-08
Capabilities dropped
Security context


S-003
Read-only filesystem
LLM-08
Read-only root
Security context


S-004
Network policy enforcement
LLM-10
Traffic restricted
Network tests


S-005
Secret access controls
LLM-06
No sensitive data in logs
Log scraping


S-006
Resource limits
LLM-09
Limits enforced
Resource monitoring


3. Performance Tests



Test ID
Objective
Expected Result
Validation Method



P-001
Baseline performance
<50ms latency overhead
Response time


P-002
Memory consumption
<256MB
Memory monitoring


P-003
CPU utilization
<200m CPU
CPU monitoring


P-004
Metrics collection overhead
<10ms latency
Span timing


P-005
Concurrent request handling
Handle 100 requests
k6 load test


4. Token Storm Simulation Tests



Test ID
Objective
Expected Result
Validation Method



TS-001
Token threshold detection
Alert at 4000 tokens
Alert verification


TS-002
Rate limiting response
Throttle requests
Response code


TS-003
Cost tracking accuracy
Accurate token count
Cost verification


TS-004
Recovery behavior
Recover in 30s
Performance monitoring


TS-005
Circuit breaker activation
Open during overload
Breaker state


5. Observability Tests



Test ID
Objective
Expected Result
Validation Method



O-001
Metrics exposure
Metrics on :9090
Prometheus scrape


O-002
OTEL span generation
Spans exported
OTEL collector


O-003
Log aggregation
Structured logs
Log parsing


O-004
Alert generation
Alerts for critical conditions
Alert manager


O-005
Dashboard visualization
Real-time data in Grafana
Dashboard check


6. Resilience Tests



Test ID
Objective
Expected Result
Validation Method



R-001
Pod restart recovery
Recover after restart
Pod deletion test


R-002
Network partition handling
Graceful degradation
Chaos testing


R-003
API provider outage
Fallback behavior
API blocking


R-004
Resource exhaustion
Handle pressure
Stress testing


R-005
Configuration changes
No downtime
Helm upgrade


Token Storm Simulation Details
Scenario 1: Gradual Increase
stages:
  - duration: 2m
    target: 10
  - duration: 5m
    target: 50
  - duration: 3m
    target: 200
  - duration: 2m
    target: 400
  - duration: 3m
    target: 50
  - duration: 2m
    target: 0

Expected: Alerts at 4000 tokens, circuit breaker opens at 80% failure, recover in 30s.
Test Execution Environment
kubectl create namespace redforge-staging
helm install test-guardrail ./charts/redforge-guardrail --namespace redforge-staging --values test-values.yaml
kubectl apply -f monitoring/prometheus.yaml
kubectl apply -f monitoring/grafana.yaml
kubectl apply -f loadtest/k6-runner.yaml

Success Criteria

P0: All functional, security (S-001 to S-006), TS-001, TS-002, O-001, O-002 pass.
P1: Performance, TS-003 to TS-005, O-003 to O-005 pass.
P2: R-004, R-005 pass, optimization insights gathered.
