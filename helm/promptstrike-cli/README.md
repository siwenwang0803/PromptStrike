# PromptStrike CLI Helm Chart

This Helm chart deploys the PromptStrike CLI for running automated LLM red-team scans in Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- OpenAI API key

## Installation

### Add Helm Repository

```bash
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update
```

### Install Chart

```bash
# Install with API key
helm install my-promptstrike promptstrike/promptstrike-cli \
  --set secrets.openaiApiKey="your-openai-api-key"

# Install with job enabled for automated scans
helm install my-promptstrike promptstrike/promptstrike-cli \
  --set secrets.openaiApiKey="your-openai-api-key" \
  --set job.enabled=true \
  --set job.target="gpt-4"
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `cli.enabled` | Enable PromptStrike CLI | `true` |
| `cli.image.repository` | CLI image repository | `siwenwang0803/promptstrike` |
| `cli.image.tag` | CLI image tag | `v0.2.0-alpha` |
| `secrets.openaiApiKey` | OpenAI API key | `""` |
| `job.enabled` | Enable scheduled scan job | `false` |
| `job.target` | Target LLM to scan | `gpt-3.5-turbo` |
| `persistence.enabled` | Enable persistent storage for reports | `true` |
| `persistence.size` | Storage size | `1Gi` |

## Usage

### One-time Scan

```bash
# Run a scan job
kubectl create job --from=cronjob/my-promptstrike-scan manual-scan-$(date +%s)
```

### View Results

```bash
# Get pod logs
kubectl logs job/my-promptstrike-scan

# Access reports (if persistence enabled)
kubectl exec -it deployment/my-promptstrike -- ls /app/reports
```

### Automated Scans

Enable the job scheduler:

```bash
helm upgrade my-promptstrike promptstrike/promptstrike-cli \
  --set job.enabled=true \
  --set job.schedule="0 2 * * *"  # Daily at 2 AM
```

## Security

- Runs as non-root user (1000:1000)
- Read-only root filesystem
- Minimal capabilities
- Network policies supported

## Monitoring

Enable ServiceMonitor for Prometheus:

```bash
helm upgrade my-promptstrike promptstrike/promptstrike-cli \
  --set monitoring.enabled=true \
  --set monitoring.serviceMonitor.enabled=true
```

## Uninstallation

```bash
helm uninstall my-promptstrike
```