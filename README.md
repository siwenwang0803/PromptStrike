# 🎯 PromptStrike Helm Repository

**Developer-first automated LLM red-team platform**

This repository hosts the official Helm charts for PromptStrike.

## 🚀 Quick Start

### Add Repository

```bash
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update
```

### Install Charts

#### CLI Chart
```bash
# Install CLI for job-based scanning
helm install my-cli promptstrike/promptstrike-cli \
  --set secrets.openaiApiKey="your-api-key"

# Enable scheduled scans
helm install my-cli promptstrike/promptstrike-cli \
  --set secrets.openaiApiKey="your-api-key" \
  --set job.enabled=true \
  --set job.target="gpt-4"
```

#### Sidecar Chart
```bash
# Install guardrail sidecar
helm install my-sidecar promptstrike/promptstrike-sidecar \
  --set secrets.apiKeys.openai="your-api-key"
```

## 📦 Available Charts

| Chart | Version | App Version | Description |
|-------|---------|-------------|-------------|
| **promptstrike-cli** | 0.2.0 | 0.2.0-alpha | PromptStrike CLI for automated LLM security scans |
| **promptstrike-sidecar** | 0.2.0 | 0.2.0-alpha | Guardrail sidecar for runtime security monitoring |

## 📋 Chart Details

### PromptStrike CLI
- **Image**: `siwenwang0803/promptstrike:v0.2.0-alpha`
- **Purpose**: Run OWASP LLM Top 10 security scans as Kubernetes Jobs
- **Features**: Scheduled scans, persistent reports, compliance mapping
- **Deployment**: Job-based execution with optional CronJob scheduling

### PromptStrike Sidecar
- **Image**: `promptstrike/guardrail-sidecar:latest`
- **Purpose**: Runtime security monitoring for LLM applications
- **Features**: Real-time threat detection, cost protection, observability
- **Deployment**: Sidecar pattern with your existing applications

## 🔧 Configuration Examples

### CLI Chart Values
```yaml
# Enable job for automated scanning
job:
  enabled: true
  target: "gpt-4"
  schedule: "0 2 * * *"  # Daily at 2 AM

# API key configuration
secrets:
  openaiApiKey: "your-api-key"

# Persistence for reports
persistence:
  enabled: true
  size: 5Gi
```

### Sidecar Chart Values
```yaml
# API keys
secrets:
  apiKeys:
    openai: "your-openai-key"

# Monitoring configuration
monitoring:
  enabled: true
  prometheus:
    enabled: true
  serviceMonitor:
    enabled: true

# Auto-scaling
hpa:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
```

## 🎯 Use Cases

- **CI/CD Integration**: Automated security scanning in pipelines
- **Runtime Protection**: Real-time LLM application monitoring
- **Compliance Auditing**: NIST AI-RMF, EU AI Act, PCI DSS reporting
- **Cost Management**: Token usage monitoring and budget controls
- **Threat Detection**: Prompt injection and data leakage prevention

## 📚 Documentation

For detailed documentation, configuration guides, and examples:
- **Main Repository**: [GitHub](https://github.com/siwenwang0803/PromptStrike)
- **CLI Documentation**: [CLI Spec](https://github.com/siwenwang0803/PromptStrike/blob/main/docs/cli-spec.md)
- **Docker Hub**: [siwenwang0803/promptstrike](https://hub.docker.com/r/siwenwang0803/promptstrike)
- **PyPI Package**: [promptstrike](https://pypi.org/project/promptstrike/)

## 🛡️ Security & Compliance

- **Local Execution**: API keys never leave your infrastructure
- **RBAC Support**: Enterprise role-based access control
- **Security Policies**: Pod security standards and network policies
- **Audit Trails**: Cryptographic evidence for compliance
- **Multi-framework**: NIST AI-RMF, EU AI Act, SOC2, PCI DSS, ISO 27001

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/siwenwang0803/PromptStrike/issues)
- **Email**: dev@promptstrike.com
- **Enterprise**: Custom pilots available ($4-7k)

---

**🚀 Ready to secure your LLM applications?**

```bash
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm install my-promptstrike promptstrike/promptstrike-cli --set secrets.openaiApiKey="your-key"
```