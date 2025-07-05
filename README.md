# PromptStrike Helm Repository

This repository hosts the official Helm charts for PromptStrike.

## Quick Start

```bash
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update
helm install guardrail promptstrike/promptstrike-guardrail --set openai.apiKey=$OPENAI_API_KEY
```

## Available Charts

- **promptstrike-guardrail** - LLM security sidecar with OpenTelemetry monitoring

## Documentation

For detailed documentation, visit the [main repository](https://github.com/siwenwang0803/PromptStrike).