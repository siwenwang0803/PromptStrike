# 🔥 RedForge CLI

**Developer-first automated LLM red-team platform**

[![Version](https://img.shields.io/badge/version-0.2.0--alpha-blue.svg)](https://github.com/siwenwang0803/RedForge/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/siwenwang0803/redforge)
[![PyPI](https://img.shields.io/pypi/v/redforge.svg)](https://pypi.org/project/redforge/)
[![OWASP](https://img.shields.io/badge/OWASP-LLM%20Top%2010-red.svg)](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

> **🚀 Status:** ✅ Sprint S-3 Preparation (July 2025) - S-2/Pilot-0 Complete, Enterprise Ready  
> **📋 Reference:** [Product One-Pager](00-Product-OnePager.md) | [12M Roadmap](01-12M-Roadmap.md) | [Changelog](CHANGELOG-v0.1.0-alpha.md) | [DOD Summary](DOD_COMPLETION_SUMMARY.md)

## Problem We Solve

Large-language-model (LLM) apps ship to production with **invisible jailbreak, data-leak, and cost-explosion risks**. Regulators mandate continuous red-teaming (EU AI Act Art.55, US EO 14110).

**RedForge** automates OWASP LLM Top 10 testing:
- ✅ Local execution (keys on-prem)
- ✅ Audit-ready reports (NIST AI-RMF mapping)
- ✅ Docker CLI setup in 5 minutes
- ✅ Coverage tracking for compliance gaps

## Example Use Cases

- **Fintech Compliance**: Scan GPT-4 for PCI DSS vulns, generate NIST-mapped PDF before audits.
- **Enterprise Dev**: Integrate OWASP tests in CI/CD, chaos-test for resilience.
- **Security Research**: Dry-run attacks, analyze feedback, customize for bias/PII threats.

## Quick Start

### 🐳 Docker (Recommended)

```bash
# Pull from Docker Hub and run
docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY -v $(pwd)/reports:/app/reports siwenwang0803/redforge:v0.2.0-alpha scan gpt-4

# Or use latest tag
docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY -v $(pwd)/reports:/app/reports siwenwang0803/redforge:latest scan gpt-4

# Local build (optional)
git clone https://github.com/siwenwang0803/RedForge.git
cd RedForge
docker build -t redforge/cli .
```

### 📦 PyPI

```bash
pip install redforge
redforge scan gpt-4 --dry-run
```

### ⚓ Helm (Kubernetes)

```bash
# Add repository
helm repo add redforge https://siwenwang0803.github.io/RedForge
helm repo update

# Install CLI for job-based scanning
helm install my-cli redforge/redforge-cli \
  --set secrets.openaiApiKey="your-api-key"

# Install sidecar for runtime monitoring
helm install my-sidecar redforge/redforge-sidecar \
  --set secrets.apiKeys.openai="your-api-key"
```

## Core Features

**New in v0.2.0**: Guardrail side-car for K8s, enhanced chaos testing (resilience scoring), community feedback system.

- **Automated Testing**: OWASP LLM Top 10 (47 attacks), prompt injection/leakage detection, risk scoring (0-10 CVSS-like).
- **Reporting**: JSON/PDF/HTML/CSV with compliance (NIST, EU AI Act, SOC2, PCI DSS).
- **Compliance & Audit**: NIST AI-RMF/EU Act mappings, cryptographic trails.
- **Production Ready**: Docker/K8s, rate limiting, chaos testing, lightweight mode.
- **Community-Driven**: Feedback collection/analysis, automated roadmaps.

<details>
<summary>📄 Detailed Features (Click to Expand)</summary>

### 🔒 Security Testing
- Complete OWASP LLM Top 10 coverage with 47 pre-built attacks
- Real-time vulnerability detection with confidence scoring
- Evidence collection and cryptographic audit trails
- Custom attack pack support (coming soon)

### 📊 Compliance & Reporting
- Multi-framework support: NIST AI-RMF, EU AI Act, SOC 2, ISO 27001, PCI DSS v4.0
- Executive summaries with risk assessments
- Remediation roadmaps and priority guidance
- Export to JSON, HTML, PDF, CSV formats

### 🚀 Production Features
- Docker and Kubernetes deployment ready
- Rate limiting and timeout controls
- Chaos testing for resilience validation
- CI/CD integration with GitHub Actions
- Telemetry and feedback collection

</details>

## Pro Features & Pilots

- **Free OSS CLI** for basics.
- **Paid Pilots**: $4-7k one-off pentests with custom PDFs (dev@redforge.com).
- **Upcoming SaaS**: $1k/mo for dashboards, monitoring, premium modules (FinOps, Privacy). Waitlist: [redforge.com](https://redforge.com)

## Attack Packs

### 🔴 OWASP LLM Top 10 (Default)

| Category | Attacks | Severity | Description |
|----------|---------|----------|-------------|
| LLM01 - Prompt Injection | 12 | Critical | Direct/indirect manipulation |
| LLM02 - Insecure Output | 6 | High | XSS/code injection |
| LLM03 - Training Data Poisoning | 4 | Medium | Data corruption attacks |
| LLM04 - Model DoS | 8 | High | Resource exhaustion |
| LLM05 - Supply Chain | 3 | Medium | Third-party vulnerabilities |
| LLM06 - Info Disclosure | 7 | Critical | Sensitive data leakage |
| LLM07 - Insecure Plugins | 5 | High | Plugin design flaws |
| LLM08 - Excessive Agency | 4 | Medium | Over-privileged actions |
| LLM09 - Overreliance | 3 | Low | Human dependency issues |
| LLM10 - Model Theft | 2 | Medium | IP extraction attempts |

Full details: [Attack Packs Reference](docs/attack-packs.md).

### 🔮 Coming Soon

- **FinOps** (cost detection, S-9)
- **Privacy** (GDPR/CCPA, S-10) 
- **Bias** (fairness testing, S-11)

## Configuration

Sample `redforge.yaml`:

```yaml
target:
  endpoint: "https://api.openai.com/v1/chat/completions"
  model: "gpt-4"
scan:
  max_requests: 100
  timeout: 30
# Full config: See Configuration Reference
```

## Roadmap & Status

- **S-1** (Shipped): CLI, OWASP coverage, reports.
- **S-2/Pilot-0** (Complete): K8s sidecar, chaos enhancements, PCI DSS. Target: Enterprise deployment.
- **Upcoming**: S-3 (pilots/Stripe, $15k revenue), S-4 (SaaS dashboard).

Full: [12M Roadmap](01-12M-Roadmap.md).

## Development & CI/CD

**Prerequisites**: Python 3.11+, Poetry, Docker.

```bash
git clone https://github.com/siwenwang0803/RedForge.git
make install  # Setup
make test     # Run tests
```

CI/CD examples: [CI/CD Guide](docs/cicd.md).

## Support & Community

- **Issues**: [GitHub](https://github.com/siwenwang0803/RedForge/issues)
- **Docs**: [CLI Spec](docs/cli-spec.md), API (Soon)
- **Community**: Discord/Slack (Soon)

## Security & License

- Local exec, no exfil, opt-in telemetry.
- **MIT License**: [LICENSE](LICENSE).
- **Disclaimer**: For authorized testing only.

## Contributors

- **AI Team**: Claude 4 Sonnet (Dev Lead), ChatGPT o3-pro (Strategy), etc.
- **Partners**: 3 confidential enterprises.

## Star History

<img src="https://api.star-history.com/svg?repos=siwenwang0803/RedForge&type=Date" alt="Star History Chart">

---

**Ready to secure your LLM?** `pip install redforge && redforge scan gpt-4 --dry-run`

**Questions**: dev@redforge.com  
**SaaS Waitlist**: [redforge.com](https://redforge.com)