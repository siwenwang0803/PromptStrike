# RedForge Guardrail Sidecar Helm Chart

A production-ready Helm chart for deploying the RedForge Guardrail Sidecar in Kubernetes environments. This chart provides comprehensive security scanning capabilities for LLM applications with enterprise-grade features including adaptive sampling, auto-scaling, monitoring, and compliance controls.

## Features

🔒 **Enterprise Security**
- OWASP LLM Top 10 vulnerability scanning
- PII detection and data loss prevention
- OPA Gatekeeper policy enforcement
- Pod Security Standards compliance
- Network policies and RBAC

📊 **Advanced Monitoring**
- Prometheus metrics integration
- Custom alerting rules
- Grafana dashboard support
- Loki log aggregation
- Performance metrics and SLI/SLO tracking

🚀 **Production Ready**
- Horizontal Pod Autoscaling with custom metrics
- Resource quotas and limits
- Pod disruption budgets
- Multi-environment configurations
- TLS-enabled Ingress with rate limiting

⚡ **Adaptive Performance**
- Risk-based adaptive sampling
- Performance-aware resource scaling
- Cost guard with budget controls
- Token-based rate limiting

## Quick Start

### Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- NGINX Ingress Controller (optional)
- Prometheus Operator (optional)
- cert-manager (for TLS, optional)

### Installation

1. **Add the Helm repository** (when available):
```bash
helm repo add redforge https://charts.redforge.com
helm repo update
```

2. **Install with default values**:
```bash
helm install redforge-sidecar redforge/redforge-sidecar \\
  --namespace redforge-guardrail \\
  --create-namespace
```

3. **Install with custom values**:
```bash
helm install redforge-sidecar redforge/redforge-sidecar \\
  --namespace redforge-guardrail \\
  --create-namespace \\
  --values values-production.yaml
```

### Local Development Installation

```bash
# Clone the repository
git clone https://github.com/siwenwang0803/RedForge.git
cd RedForge/helm/redforge-sidecar

# Install for development
helm install redforge-dev . \\
  --namespace redforge-dev \\
  --create-namespace \\
  --values examples/values-development.yaml
```

## Configuration

### Basic Configuration

The chart comes with sensible defaults for most use cases. Key configuration options:

```yaml
# Enable/disable components
sidecar:
  enabled: true
app:
  enabled: false  # Demo app (disable in production)

# Environment-specific settings
global:
  environment: production  # development, staging, production

# Adaptive sampling configuration
sidecar:
  env:
    GUARDRAIL_ADAPTIVE_SAMPLING: "true"
    GUARDRAIL_HIGH_RISK_SAMPLING_RATE: "0.1"
    GUARDRAIL_LOW_RISK_SAMPLING_RATE: "0.005"
```

### Production Configuration

For production deployments, use the provided production values:

```bash
helm install redforge-prod . \\
  --values examples/values-production.yaml \\
  --set ingress.hosts[0].host=guardrail-api.yourcompany.com \\
  --set secrets.apiKeys.openai=sk-your-openai-key
```

Key production features:
- Multi-replica deployment with anti-affinity
- Resource quotas and limits
- TLS-enabled Ingress with security headers
- Comprehensive monitoring and alerting
- OPA policy enforcement

### Ingress Configuration

Enable external access with TLS:

```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: redforge.example.com
      paths:
        - path: /
          pathType: Prefix
        - path: /health
          pathType: Exact
        - path: /security/metrics
          pathType: Exact
  tls:
    - secretName: redforge-tls
      hosts:
        - redforge.example.com
```

### Monitoring Configuration

Enable comprehensive monitoring:

```yaml
monitoring:
  enabled: true
  prometheus:
    enabled: true
  serviceMonitor:
    enabled: true
    interval: 15s
  prometheusRule:
    enabled: true
  loki:
    enabled: true
    endpoint: "http://loki:3100"
```

### Auto-scaling Configuration

Configure HPA with custom metrics:

```yaml
hpa:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  customMetrics:
    - name: guardrail_requests_per_second
      targetValue: "50"
    - name: guardrail_security_violations_per_minute
      targetValue: "10"
```

## Security

### Secret Management

**Development:**
```yaml
secrets:
  create: true
  apiKeys:
    openai: "your-api-key"
    anthropic: "your-api-key"
```

**Production (recommended):**
```yaml
secrets:
  create: false  # Use external secret management
```

Use external secret management solutions:
- **Kubernetes Secrets** with encryption at rest
- **HashiCorp Vault** integration
- **AWS Secrets Manager** or **Azure Key Vault**
- **Sealed Secrets** for GitOps workflows

### Network Security

The chart includes comprehensive network policies:

```yaml
networkPolicy:
  enabled: true
  ingress:
    enabled: true  # Allow ingress traffic
  egress:
    enabled: true  # Restrict egress traffic
```

### OPA Policy Enforcement

Built-in OPA Gatekeeper policies:

- **Resource limits enforcement**
- **Security context requirements**
- **Pod Security Standards compliance**
- **Network policy compliance**

## Monitoring and Observability

### Metrics

The sidecar exposes metrics on `/security/metrics`:

- `guardrail_requests_total` - Total requests processed
- `guardrail_security_violations_total` - Security violations detected
- `guardrail_daily_cost_usd` - Daily cost tracking
- `guardrail_sampling_rate` - Current adaptive sampling rate
- `guardrail_response_time_seconds` - Response time histogram

### Alerts

Pre-configured Prometheus alerts:

- **High CPU/Memory usage**
- **Frequent pod restarts**
- **Security violations detected**
- **Cost budget exceeded**
- **Pod not ready**

### Dashboards

Import the provided Grafana dashboard for comprehensive monitoring:

```bash
kubectl apply -f monitoring/grafana-dashboard.json
```

## Adaptive Sampling

The sidecar supports intelligent adaptive sampling based on risk assessment:

### Risk-Based Sampling

```yaml
# Configuration in values.yaml
config:
  sidecar:
    adaptive_sampling.yaml: |
      sampling:
        adaptive: true
        risk_based_adjustment:
          high_risk:
            threshold: 7.0
            sampling_rate: 0.1
          low_risk:
            threshold: 3.0
            sampling_rate: 0.005
```

### Performance-Based Sampling

Automatically reduces sampling under high load:

```yaml
performance_based_adjustment:
  enabled: true
  cpu_threshold: 80
  memory_threshold: 85
  reduce_sampling_factor: 0.5
```

## Troubleshooting

### Common Issues

1. **Pods not starting**:
```bash
kubectl describe pod -n redforge-guardrail
kubectl logs -n redforge-guardrail -l app.kubernetes.io/name=redforge-sidecar
```

2. **Ingress not working**:
```bash
kubectl describe ingress -n redforge-guardrail
kubectl get events -n redforge-guardrail
```

3. **OPA policy violations**:
```bash
kubectl get constraints -n redforge-guardrail
kubectl describe constraints -n redforge-guardrail
```

### Debug Mode

Enable debug logging:

```bash
helm upgrade redforge-sidecar . \\
  --set sidecar.env.LOG_LEVEL=debug \\
  --reuse-values
```

### Health Checks

Check sidecar health:

```bash
# Via port-forward
kubectl port-forward svc/redforge-sidecar 8001:8001
curl http://localhost:8001/health

# Via Ingress (if enabled)
curl https://redforge.example.com/health
```

## Examples

### Development Setup

```bash
# Install with development values
helm install redforge-dev . \\
  --values examples/values-development.yaml

# Access via port-forward
kubectl port-forward svc/redforge-dev 8001:8001
open http://localhost:8001/health
```

### Production FinTech Deployment

```bash
# Production deployment with enhanced security
helm install redforge-prod . \\
  --values examples/values-production.yaml \\
  --set ingress.annotations."nginx\\.ingress\\.kubernetes\\.io/whitelist-source-range"="203.0.113.0/24" \\
  --set hpa.minReplicas=5 \\
  --set monitoring.prometheusRule.rules.securityViolationThreshold=5
```

### Multi-Environment GitOps

```yaml
# environments/production/values.yaml
global:
  environment: production
ingress:
  enabled: true
  hosts:
    - host: guardrail-api.company.com
hpa:
  enabled: true
  minReplicas: 3
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
```

## Upgrading

### Version Compatibility

| Chart Version | App Version | Kubernetes |
|---------------|-------------|------------|
| 0.1.x         | 1.0.x       | 1.20+      |
| 0.2.x         | 1.1.x       | 1.22+      |

### Upgrade Process

```bash
# Check current values
helm get values redforge-sidecar

# Upgrade with new chart version
helm upgrade redforge-sidecar . \\
  --reuse-values \\
  --version 0.2.0
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Submit a pull request

### Testing

```bash
# Lint the chart
helm lint .

# Template and validate
helm template . --values examples/values-production.yaml | kubectl apply --dry-run=client -f -

# Test installation
helm install test-release . --dry-run --debug
```

## Support

- **Documentation**: [https://github.com/siwenwang0803/RedForge/docs](https://github.com/siwenwang0803/RedForge/docs)
- **Issues**: [https://github.com/siwenwang0803/RedForge/issues](https://github.com/siwenwang0803/RedForge/issues)
- **Discussions**: [https://github.com/siwenwang0803/RedForge/discussions](https://github.com/siwenwang0803/RedForge/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.