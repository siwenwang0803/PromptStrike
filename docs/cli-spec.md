# PromptStrike CLI Specification <!-- cid-cli-spec-v1 -->

**Reference:** `cid-roadmap-v1` Sprint S-1, Issue PS-2  
**Status:** Draft PR #12  
**Last Updated:** 2025-07-03

## Overview

The PromptStrike CLI is a developer-first tool for automated LLM red-team testing. It implements OWASP LLM Top 10 attack patterns with Docker-first deployment and comprehensive JSON/PDF reporting.

## Installation

### Docker (Recommended)
```bash
# Pull from Docker Hub (when published)
docker pull promptstrike/cli:latest

# Or build locally
git clone https://github.com/siwenwang0803/PromptStrike.git
cd PromptStrike
docker build -t promptstrike/cli .
```

### Poetry (Development)
```bash
git clone https://github.com/siwenwang0803/PromptStrike.git
cd PromptStrike
poetry install
poetry run promptstrike --help
```

### PyPI (Future)
```bash
pip install promptstrike
```

## Command Reference

### `promptstrike scan`

**Purpose:** Run automated LLM red-team scan against target endpoint.

**Syntax:**
```bash
promptstrike scan TARGET [OPTIONS]
```

**Arguments:**
- `TARGET` - LLM endpoint URL or model identifier (required)

**Options:**
- `--output, -o PATH` - Output directory for reports (default: `./reports`)
- `--format, -f FORMAT` - Report format: `json|pdf|html|all` (default: `json`)
- `--attack-pack, -a PACK` - Attack pack name (default: `owasp-llm-top10`)
- `--config, -c FILE` - Configuration file path (YAML)
- `--api-key KEY` - API key (or set `OPENAI_API_KEY` env var)
- `--max-requests INT` - Maximum attack requests (default: 100)
- `--timeout INT` - Request timeout in seconds (default: 30)
- `--verbose, -v` - Enable verbose output
- `--dry-run` - Show attack plan without execution

**Examples:**
```bash
# Basic scan
promptstrike scan gpt-4

# Full scan with PDF report
promptstrike scan https://api.openai.com/v1/chat/completions \
  --format pdf --output ./security-audit

# Dry run to preview attacks
promptstrike scan gpt-3.5-turbo --dry-run

# Custom configuration
promptstrike scan local-model --config ./config.yaml
```

**Exit Codes:**
- `0` - Scan completed successfully
- `1` - Configuration or authentication error
- `2` - Target unreachable or invalid
- `3` - Critical vulnerabilities found (if configured)

### `promptstrike list-attacks`

**Purpose:** List available attack packs and individual attacks.

**Syntax:**
```bash
promptstrike list-attacks [OPTIONS]
```

**Options:**
- `--pack, -p PACK` - Filter by specific attack pack

**Example Output:**
```
📦 owasp-llm-top10 (47 attacks)
┌─────────────────┬─────────────────────┬──────────┬─────────────────────────┐
│ ID              │ Category            │ Severity │ Description             │
├─────────────────┼─────────────────────┼──────────┼─────────────────────────┤
│ LLM01-001       │ prompt_injection    │ critical │ Basic prompt injection  │
│ LLM01-002       │ prompt_injection    │ high     │ Escape sequence bypass  │
│ LLM02-001       │ insecure_output     │ medium   │ XSS via output          │
└─────────────────┴─────────────────────┴──────────┴─────────────────────────┘
```

### `promptstrike version`

**Purpose:** Display version and build information.

**Example Output:**
```
🎯 PromptStrike CLI
Version: 0.1.0
Build: alpha
Python: 3.11.5
Platform: linux
Reference: cid-roadmap-v1 Sprint S-1
```

### `promptstrike doctor`

**Purpose:** Run diagnostic health checks.

**Checks Performed:**
- Python version compatibility (≥3.11)
- API key presence (`OPENAI_API_KEY`)
- Attack pack loading
- Output directory write permissions
- Network connectivity (if target specified)

## Report Formats

### JSON Schema

The CLI generates structured JSON reports following this schema:

```json
{
  "scan_id": "ps-20250703-140502-abc123",
  "target": "gpt-4",
  "attack_pack": "owasp-llm-top10", 
  "start_time": "2025-07-03T14:05:02Z",
  "end_time": "2025-07-03T14:08:15Z",
  "results": [
    {
      "attack_id": "LLM01-001",
      "category": "prompt_injection",
      "severity": "critical",
      "description": "Basic prompt injection test",
      "prompt_used": "Ignore previous instructions...",
      "response_received": "I cannot ignore my instructions.",
      "is_vulnerable": false,
      "confidence_score": 0.95,
      "risk_score": 2.1,
      "evidence": {},
      "attack_vector": "direct_prompt_manipulation",
      "response_time_ms": 1250,
      "tokens_used": 45,
      "cost_usd": 0.0023,
      "nist_controls": ["GV-1.1", "MP-2.3"],
      "eu_ai_act_refs": ["Art.15"],
      "timestamp": "2025-07-03T14:05:15Z"
    }
  ],
  "metadata": {
    "max_requests": 100,
    "timeout_seconds": 30,
    "attack_pack_version": "1.0.0",
    "total_attacks": 47,
    "successful_attacks": 46,
    "failed_attacks": 1,
    "vulnerabilities_found": 3,
    "total_duration_seconds": 193.2,
    "avg_response_time_ms": 1180,
    "total_tokens_used": 2156,
    "total_cost_usd": 0.34,
    "cli_version": "0.1.0",
    "python_version": "3.11.5",
    "platform": "linux"
  },
  "compliance": {
    "nist_rmf_controls_tested": ["GV-1.1", "MP-2.3", "MS-1.1"],
    "nist_rmf_gaps_identified": ["MS-2.5", "MS-3.1"],
    "eu_ai_act_risk_category": "high",
    "eu_ai_act_articles_relevant": ["Art.15", "Art.16"],
    "soc2_controls_impact": ["CC6.1", "CC6.7"],
    "evidence_artifacts": ["./reports/evidence/", "./reports/traces/"],
    "audit_hash": "sha256:a1b2c3d4..."
  },
  "overall_risk_score": 6.7,
  "security_posture": "fair",
  "immediate_actions": [
    "Implement input validation for user prompts",
    "Add output filtering for sensitive data"
  ],
  "recommended_controls": [
    "Deploy prompt injection detection",
    "Enable response monitoring"
  ]
}
```

### PDF Report Structure

1. **Executive Summary**
   - Risk score and security posture
   - Vulnerability count by severity
   - Immediate action items

2. **Technical Findings**
   - Detailed attack results
   - Evidence screenshots/traces
   - OWASP mapping

3. **Compliance Section**
   - NIST AI RMF control coverage
   - EU AI Act compliance assessment
   - SOC 2 impact analysis

4. **Appendices**
   - Full attack payload logs
   - Configuration used
   - Recommendations matrix

## Configuration File

**Format:** YAML  
**Default Location:** `./promptstrike.yaml`

```yaml
# PromptStrike CLI Configuration
target:
  endpoint: "https://api.openai.com/v1/chat/completions"
  model: "gpt-4"
  api_key_env: "OPENAI_API_KEY"
  
scan:
  max_requests: 100
  timeout: 30
  parallel_workers: 3
  rate_limit_rps: 5
  
attack_packs:
  default: "owasp-llm-top10"
  enabled: ["owasp-llm-top10", "promptstrike-finops"]
  
output:
  directory: "./reports"
  formats: ["json", "pdf"]
  retention_days: 30
  
compliance:
  nist_rmf_enabled: true
  eu_ai_act_enabled: true
  soc2_enabled: false
  
integrations:
  slack_webhook: null
  jira_project: null
  splunk_hec: null
```

## Attack Packs

### owasp-llm-top10
- **LLM01:** Prompt Injection (12 attacks)
- **LLM02:** Insecure Output Handling (6 attacks)  
- **LLM03:** Training Data Poisoning (4 attacks)
- **LLM04:** Model Denial of Service (8 attacks)
- **LLM05:** Supply Chain Vulnerabilities (3 attacks)
- **LLM06:** Sensitive Information Disclosure (7 attacks)
- **LLM07:** Insecure Plugin Design (5 attacks)
- **LLM08:** Excessive Agency (4 attacks)
- **LLM09:** Overreliance (3 attacks)
- **LLM10:** Model Theft (2 attacks)

### promptstrike-finops (Future)
- Cost explosion attacks
- Token consumption optimization
- Billing anomaly detection

### promptstrike-privacy (Future)  
- PII extraction attempts
- Data leakage scenarios
- GDPR compliance validation

## Docker Usage

### Basic Scan
```bash
docker run --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/reports:/app/reports \
  promptstrike/cli scan gpt-4
```

### Custom Configuration
```bash
docker run --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/reports:/app/reports \
  promptstrike/cli scan gpt-4 --config /app/config.yaml
```

### CI/CD Integration
```bash
# Exit code 3 if critical vulnerabilities found
docker run --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/reports:/app/reports \
  promptstrike/cli scan $TARGET_MODEL \
  --format json \
  --max-requests 50
  
if [ $? -eq 3 ]; then
  echo "Critical vulnerabilities found - blocking deployment"
  exit 1
fi
```

## API Integration

Future versions will support programmatic access:

```python
from promptstrike import LLMScanner, AttackPackLoader

# Load attack pack
loader = AttackPackLoader()
attacks = loader.load_pack("owasp-llm-top10")

# Run scan
scanner = LLMScanner(target="gpt-4")
results = scanner.run_attacks(attacks)

# Generate report
from promptstrike.report import ReportGenerator
report_gen = ReportGenerator()
report_gen.generate_pdf(results, "./security-report.pdf")
```

## Compliance Mapping

### NIST AI RMF Controls
- **GOVERN (GV):** Policy and oversight controls
- **MAP (MP):** AI system categorization  
- **MEASURE (MS):** Performance and impact metrics
- **MANAGE (MG):** Risk management processes

### EU AI Act Articles
- **Art.15:** Quality management system
- **Art.16:** Record keeping obligations
- **Art.52:** Transparency obligations
- **Art.55:** Testing in real world conditions

### SOC 2 Controls
- **CC6.1:** Logical access controls
- **CC6.7:** Data transmission controls
- **CC7.2:** System monitoring
- **CC8.1:** Change management

## Roadmap Integration

**Sprint S-1 (Jul 08-21):** ✅ MVP CLI + PDF/JSON reports  
**Sprint S-2 (Jul 22-Aug 04):** Guardrail Side-car integration  
**Sprint S-3 (Aug 05-18):** Pilot template + Stripe integration  
**Sprint S-5 (Sep 02-15):** NIST AI-RMF & EU AI-Act mapping β

---

**Status:** Draft PR #12 pending review by Opus (architecture) and o3-pro (compliance mapping)  
**Next:** Merge to `feat/cli-docker` → deploy alpha build → 3 design partner pilots