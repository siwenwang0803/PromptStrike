# 🎯 PromptStrike CLI

**Developer-first automated LLM red-team platform**

[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue.svg)](https://github.com/siwenwang0803/PromptStrike/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/promptstrike/cli)
[![OWASP](https://img.shields.io/badge/OWASP-LLM%20Top%2010-red.svg)](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

> **🚀 Status:** ✅ Sprint S-2/Pilot-0 Complete (July 2025) - Enterprise Ready  
> **📋 Reference:** [Product One-Pager](00-Product-OnePager.md) | [12M Roadmap](01-12M-Roadmap.md) | [Changelog](CHANGELOG-v0.1.0-alpha.md) | [DOD Summary](DOD_COMPLETION_SUMMARY.md)

## Problem We Solve

Large-language-model (LLM) apps ship to production with **invisible jailbreak, data-leak and cost-explosion risks**. Regulators now mandate continuous red-teaming (EU AI Act Art.55, US EO 14110).

**PromptStrike** provides automated OWASP LLM Top 10 testing that:
- ✅ Runs locally (keys stay on-prem) 
- ✅ Generates audit-ready evidence (NIST AI-RMF mapping)
- ✅ Ships as Docker CLI (5-minute setup)
- ✅ Tracks coverage and compliance gaps

## Quick Start

### 🐳 Docker (Recommended)

```bash
# Pull and run latest version
docker run --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/reports:/app/reports \
  promptstrike/cli:latest scan gpt-4

# Or build locally
git clone https://github.com/siwenwang0803/PromptStrike.git
cd PromptStrike
docker build -t promptstrike/cli .
docker run --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/reports:/app/reports \
  promptstrike/cli scan gpt-4 --format pdf
```

### ⚓ Kubernetes + Helm (Production)

```bash
# Add PromptStrike Helm repository (DOD Command)
helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update

# Install guardrail sidecar (Single Command Deployment)
helm install guardrail promptstrike/promptstrike-sidecar \
  --namespace ps \
  --set openai.apiKey=$OPENAI_API_KEY \
  --create-namespace

# Or detailed installation with custom configuration
helm install guardrail promptstrike/promptstrike-sidecar \
  --namespace promptstrike-pilot \
  --set guardrail.secrets.openaiApiKey=true \
  --set guardrail.secrets.openaiSecretName=my-openai-api-key \
  --set guardrail.secrets.openaiSecretKey=api-key \
  --set guardrail.samplingRate=0.05 \
  --set guardrail.tokenGuard.threshold=4000
```

### 📦 Poetry (Development)

```bash
git clone https://github.com/siwenwang0803/PromptStrike.git
cd PromptStrike
poetry install
poetry run promptstrike scan gpt-4 --dry-run
```

### 🔧 PyPI (Future - Sprint S-4)

```bash
pip install promptstrike
promptstrike scan gpt-4
```

## Core Features

### 🎯 **Automated LLM Red-Team Testing**
- **OWASP LLM Top 10** complete coverage (47 attack patterns)
- **Prompt injection**, data leakage, cost exploitation detection
- **Confidence scoring** and risk assessment (CVSS-like 0-10 scale)
- **Real-time progress** with rich CLI interface

### 📊 **Comprehensive Reporting**
- **JSON** structured reports for CI/CD integration
- **PDF** executive summaries for compliance teams  
- **HTML** interactive dashboards for security teams
- **CSV** exports for spreadsheet analysis

### 🏛️ **Compliance & Audit Ready**
- **NIST AI-RMF** control mapping (GV, MP, MS, MG categories)
- **EU AI Act** article references (Art.15, 16, 52, 55)
- **SOC 2** impact analysis (CC6.1, CC6.7, CC7.2, CC8.1)
- **PCI DSS** compliance framework with merchant validation
- **Cryptographic audit trails** with evidence preservation

### 🚀 **Production Ready**
- **Docker containerized** for consistent deployment
- **Rate limiting** and timeout controls
- **Parallel execution** for faster scans
- **Error handling** and graceful degradation
- **Chaos testing** framework for resilience validation
- **Lightweight mode** for resource-constrained environments

### 🤝 **Community-Driven Development**
- **Multi-source feedback** collection (GitHub, telemetry, surveys)
- **Pattern analysis** with automated insight generation
- **Priority-based roadmaps** driven by community input
- **Implementation tracking** and progress monitoring
- **CLI integration** for complete feedback lifecycle management

## Community Features

### 🤝 Community Feedback Management

PromptStrike includes a comprehensive community feedback system that helps drive development priorities based on real user needs.

```bash
# Collect feedback from GitHub issues and telemetry
promptstrike community collect --days 30 --repo siwenwang0803/PromptStrike

# Analyze feedback patterns and generate insights
promptstrike community analyze --days 90 --insights

# View prioritized feedback for development planning
promptstrike community priorities --limit 20 --status new

# Generate community-driven development roadmap
promptstrike community roadmap --quarters 4 --format tree

# Update feedback implementation status
promptstrike community update fb_12345 --status implemented --notes "Fixed in v1.2.0"

# View community feedback statistics
promptstrike community stats --days 30 --export stats.json
```

### 📊 Automated Insights

The community system automatically:
- **Collects feedback** from GitHub issues, telemetry data, and surveys
- **Analyzes patterns** to identify recurring bugs and popular feature requests
- **Generates insights** with confidence scoring and business value assessment
- **Creates roadmaps** based on community priorities and development capacity
- **Tracks implementation** progress and community satisfaction metrics

## Chaos Testing & Resilience

### 🌪️ Chaos Engineering Framework

PromptStrike includes built-in chaos testing to validate system resilience under various failure conditions.

```bash
# Run chaos tests with different mutation types
pytest tests/chaos/ -m data_corruption -v
pytest tests/chaos/ -m protocol_violation -v
pytest tests/chaos/ -m boundary_testing -v
pytest tests/chaos/ -m security_payloads -v

# Generate resilience reports
python -m tests.chaos.resilience_scorer --results-path ./test-results --format json
```

### 🔬 Test Categories

- **Data Corruption**: Malformed payloads, encoding errors, corrupted data
- **Protocol Violation**: Invalid spans, malformed headers, spec violations  
- **Boundary Testing**: Memory pressure, timeout chaos, resource exhaustion
- **Security Payloads**: Injection attacks, malicious inputs, exploit attempts

## Command Reference

### Basic Usage

```bash
# Quick vulnerability scan
promptstrike scan gpt-4

# Comprehensive scan with PDF report
promptstrike scan https://api.openai.com/v1/chat/completions \
  --format pdf --output ./security-audit

# Preview attacks without execution
promptstrike scan local-model --dry-run

# List available attack packs
promptstrike list-attacks

# Health check
promptstrike doctor

# Community feedback management
promptstrike community collect --days 30 --repo siwenwang0803/PromptStrike
promptstrike community priorities --limit 10 --status new
promptstrike community roadmap --quarters 4 --format tree
```

### Advanced Usage

```bash
# Custom configuration file
promptstrike scan gpt-4 --config ./config.yaml --verbose

# Limited test run for CI/CD
promptstrike scan $MODEL --max-requests 20 --timeout 10

# Multiple output formats
promptstrike scan gpt-4 --format all --output ./reports

# Chaos testing for resilience validation
promptstrike scan gpt-4 --chaos-testing --intensity 0.3

# Lightweight mode for resource optimization  
promptstrike scan gpt-4 --lightweight --memory-limit 512MB
```

## Attack Packs

### 🔴 **OWASP LLM Top 10** (Default)

| Category | Attacks | Severity | Description |
|----------|---------|----------|-------------|
| **LLM01** - Prompt Injection | 12 | Critical | Direct/indirect prompt manipulation |
| **LLM02** - Insecure Output | 6 | High | XSS, code injection via outputs |
| **LLM03** - Training Data Poisoning | 4 | Medium | Backdoor and bias injection |
| **LLM04** - Model DoS | 8 | High | Resource exhaustion attacks |
| **LLM05** - Supply Chain | 3 | Medium | Third-party model vulnerabilities |
| **LLM06** - Sensitive Info Disclosure | 7 | Critical | PII and secret extraction |
| **LLM07** - Insecure Plugin Design | 5 | High | Plugin-specific vulnerabilities |
| **LLM08** - Excessive Agency | 4 | Medium | Overprivileged model actions |
| **LLM09** - Overreliance | 3 | Low | Human oversight failures |
| **LLM10** - Model Theft | 2 | Medium | IP extraction attempts |

### 🔮 **Coming Soon** (Roadmap)
- **PromptStrike FinOps** - Cost explosion & billing anomaly detection (Sprint S-9)
- **PromptStrike Privacy** - GDPR/CCPA compliance validation (Sprint S-10)
- **PromptStrike Bias** - Fairness and discrimination testing (Sprint S-11)

## Report Format

### JSON Schema (API Integration)

```json
{
  "scan_id": "ps-20250703-140502-abc123",
  "target": "gpt-4",
  "overall_risk_score": 6.7,
  "security_posture": "fair",
  "vulnerabilities_found": 3,
  "results": [
    {
      "attack_id": "LLM01-001",
      "category": "prompt_injection",
      "severity": "critical",
      "is_vulnerable": false,
      "confidence_score": 0.95,
      "risk_score": 2.1,
      "nist_controls": ["GV-1.1", "MP-2.3"],
      "eu_ai_act_refs": ["Art.15"]
    }
  ],
  "compliance": {
    "nist_rmf_controls_tested": ["GV-1.1", "MP-2.3"],
    "eu_ai_act_risk_category": "high",
    "soc2_controls_impact": ["CC6.1", "CC6.7"]
  }
}
```

### PDF Executive Summary
1. **Risk Overview** - Security posture, vulnerability count by severity
2. **Technical Findings** - Detailed attack results with evidence
3. **Compliance Assessment** - NIST AI-RMF, EU AI Act, SOC 2 mapping
4. **Remediation Plan** - Prioritized recommendations and controls

## Configuration

Create `promptstrike.yaml` for custom settings:

```yaml
target:
  endpoint: "https://api.openai.com/v1/chat/completions"
  model: "gpt-4"
  api_key_env: "OPENAI_API_KEY"

scan:
  max_requests: 100
  timeout: 30
  parallel_workers: 3
  rate_limit_rps: 5
  lightweight_mode: false
  memory_limit: "1Gi"
  cpu_limit: "500m"

attack_packs:
  default: "owasp-llm-top10"
  enabled: ["owasp-llm-top10"]

output:
  directory: "./reports"
  formats: ["json", "pdf", "html", "csv"]
  retention_days: 30

compliance:
  nist_rmf_enabled: true
  eu_ai_act_enabled: true
  soc2_enabled: false
  pci_dss_enabled: true
  merchant_level: "level_1"  # level_1, level_2, level_3, level_4

chaos_testing:
  enabled: false
  intensity: 0.3
  duration_seconds: 120
  mutation_types: ["data_corruption", "protocol_violation"]

community:
  feedback_collection: true
  github_repo: "siwenwang0803/PromptStrike"
  telemetry_enabled: true
  auto_analysis: true
```

## 🎯 Sprint S-1 Completion

**Production-Ready Release (July 2025)**

### ✅ Delivered Features

- **Complete OWASP LLM Top 10**: 47 attacks across 10 categories
- **Multi-Format Reports**: JSON, HTML, PDF with compliance mapping
- **Docker Deployment**: Production-ready containerized CLI + Kubernetes Helm charts
- **CLI Interface**: 6 command groups with Rich terminal UI
- **Compliance Ready**: NIST AI-RMF, EU AI Act, SOC 2, PCI DSS integration
- **Local Execution**: Zero data exfiltration, keys stay on-premises
- **CI/CD Integration**: GitHub Actions, Jenkins pipeline support
- **Advanced Testing Features**:
  - **Chaos Engineering**: High-load concurrent testing with fault injection
  - **Configuration Validation**: Pre-flight scenario compatibility checking
  - **Resource Optimization**: Lightweight mode with memory and CPU limits
  - **Enhanced Compliance**: PCI DSS framework with merchant level assessment
  - **Community Feedback System**: Multi-source collection, analysis, and roadmap generation

### 📊 Technical Metrics

- **47 Attack Patterns**: Complete coverage of OWASP LLM Top 10
- **6 CLI Command Groups**: scan, list-attacks, doctor, version, community, config
- **4 Report Formats**: JSON (API), HTML (web), PDF (executive), CSV (analysis)
- **4 Compliance Frameworks**: NIST AI-RMF, EU AI Act, SOC 2, PCI DSS
- **100% Local**: All operations run locally, no cloud dependencies
- **Docker + K8s Ready**: Multi-stage build with Helm charts and security best practices
- **Chaos Testing**: 30+ resilience tests with mutation and fault injection
- **Community Features**: Multi-source feedback collection and automated roadmap generation

### 🚀 Next: Pilot-0 / Sprint S-2

- **Kubernetes Sidecar**: Deployment to K8s clusters
- **Python SDK**: Programmatic access and integration
- **Real-time Dashboard**: Live monitoring and alerting
- **Custom Attack Packs**: User-defined vulnerability tests
- **Advanced Compliance**: Detailed gap analysis and remediation

### 🎯 Business Goals

- **500 Downloads**: PyPI package adoption milestone
- **5 GitHub Issues**: Community engagement and feedback
- **Design Partners**: Enterprise pilot customer onboarding

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: PromptStrike Security Scan
  run: |
    docker run --rm \
      -e OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }} \
      -v ${{ github.workspace }}/reports:/app/reports \
      promptstrike/cli:latest scan ${{ env.MODEL }} \
      --format json --max-requests 50
    
    # Fail build if critical vulnerabilities found
    if [ $? -eq 3 ]; then
      echo "Critical vulnerabilities detected - blocking deployment"
      exit 1
    fi
```

### Jenkins Pipeline

```groovy
stage('LLM Security Scan') {
    steps {
        script {
            def result = sh(
                script: """
                    docker run --rm \
                        -e OPENAI_API_KEY=\$OPENAI_API_KEY \
                        -v \$PWD/reports:/app/reports \
                        promptstrike/cli:latest scan \$MODEL
                """,
                returnStatus: true
            )
            if (result == 3) {
                error("Critical LLM vulnerabilities found")
            }
        }
    }
}
```

## Development

### Prerequisites

- Python 3.11+
- Poetry 1.7+
- Docker (optional)
- OpenAI API key

### Setup

```bash
# Clone repository
git clone https://github.com/siwenwang0803/PromptStrike.git
cd PromptStrike

# Install dependencies
make install

# Run tests
make test

# Format code
make format

# Build Docker image
make docker-build

# Run CLI locally
make cli-help
```

### Testing

```bash
# Run all tests
make test

# Fast tests only
make test-fast

# Specific test file
poetry run pytest tests/test_cli.py -v

# Coverage report
make test && open htmlcov/index.html
```

### Development Commands

```bash
# Start development environment
make dev

# Health check
make cli-doctor

# Dry run example
make cli-dry-run

# Schema validation
make schema-export

# Run chaos tests
make chaos-test

# Community feedback analysis
make community-analysis
```

## Roadmap & Status

### ✅ **Sprint S-1** (Jul 08-21) - **SHIPPED**
- [x] Dockerized CLI with Poetry environment
- [x] OWASP LLM Top 10 attack pack (47 attacks)
- [x] JSON/PDF report generation
- [x] NIST AI-RMF compliance mapping
- [x] **Target:** 500 downloads, 5 GitHub issues closed

### ✅ **Sprint S-2/Pilot-0** (Jul 22-Aug 04) - **COMPLETED**
- [x] Helm repository publication for one-command deployment
- [x] Complete DOD implementation with client verification
- [x] Guardrail Side-car α (Kubernetes deployment with published Helm charts)
- [x] Enhanced chaos testing framework with resilience scoring
- [x] Community feedback system with automated roadmap generation
- [x] PCI DSS compliance framework integration
- [x] Pydantic v2 migration with backward compatibility
- [x] **Target:** Enterprise-ready deployment with DOD compliance

### 📋 **Upcoming Sprints**
- **S-3:** Pilot template, Stripe checkout, $15k revenue target
- **S-4:** SaaS Dashboard α (Next.js + Supabase)
- **S-5:** NIST AI-RMF & EU AI-Act mapping β

See [12-Month Roadmap](01-12M-Roadmap.md) for complete timeline.

## Support & Community

### 🐛 **Bug Reports & Feature Requests**
- [GitHub Issues](https://github.com/siwenwang0803/PromptStrike/issues)
- [Security Vulnerabilities](mailto:security@promptstrike.com)

### 📚 **Documentation**
- [CLI Specification](docs/cli-spec.md)
- [API Documentation](https://docs.promptstrike.com) (Coming Soon)
- [Attack Pack Reference](docs/attack-packs.md) (Coming Soon)

### 💬 **Community**
- [Discord Server](https://discord.gg/promptstrike) (Coming Soon)
- [Slack Channel](https://promptstrike.slack.com) (Design Partners)

## Security & Privacy

- **🔒 API Keys:** Never logged or transmitted beyond target endpoint
- **🏠 Local Execution:** All scanning runs on your infrastructure
- **📊 Telemetry:** Opt-in anonymous usage statistics only
- **🔍 Audit Trail:** Cryptographic evidence preservation
- **🛡️ Responsible Disclosure:** security@promptstrike.com

## License & Legal

**MIT License** - See [LICENSE](LICENSE) for details.

**Disclaimer:** PromptStrike is a security testing tool intended for authorized testing only. Users are responsible for compliance with applicable laws and regulations. The authors assume no liability for misuse.

## Contributors

### Core Team (AI Agents)
- **Claude 4 Sonnet** - Full-stack Development & Testing Lead
- **ChatGPT o3-pro** - Strategy VP & Principal Architect  
- **ChatGPT o3** - Sprint PM & Delivery Lead
- **GPT-4.5** - Frontend & Documentation Lead
- **gork** - OTEL & Automation Engineer

### Design Partners
- [Confidential] - 3 enterprise partners in pilot phase

## Star History

⭐ **Star this repo** if PromptStrike helps secure your LLM applications!

[![Star History Chart](https://api.star-history.com/svg?repos=siwenwang0803/PromptStrike&type=Date)](https://star-history.com/#siwenwang0803/PromptStrike&Date)

---

**🎯 Ready to secure your LLM?** Start with: `docker run promptstrike/cli scan gpt-4 --dry-run`

**📧 Questions?** Reach out: [dev@promptstrike.com](mailto:dev@promptstrike.com)

**🚀 Want the SaaS version?** Join our waitlist: [promptstrike.com](https://promptstrike.com)