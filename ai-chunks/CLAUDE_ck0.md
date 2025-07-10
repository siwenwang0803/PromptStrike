<!-- source: CLAUDE.md idx:0 lines:192 -->

```md
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Install dependencies (requires Poetry 1.7+)
make install

# Enter Poetry shell environment
make dev

# Run CLI commands with current code (no poetry run needed)
python -m redforge.cli --help
```

### Building and Running
```bash
# Build the package
make build

# Run CLI help
make cli-help

# Run CLI commands directly
poetry run redforge scan gpt-4 --dry-run

# Alternative: run without Poetry prefix (useful during development)
python -m redforge.cli scan gpt-4 --dry-run

# Docker build
make docker-build

# Docker run
make docker-run ARGS="scan gpt-4"
```

### Testing
```bash
# Run all tests with coverage
make test

# Run fast tests only (skip slow integration tests)
make test-fast

# Run specific test file
poetry run pytest tests/test_cli.py -v

# Run tests matching pattern
poetry run pytest -k "test_scan" -v

# Run with specific markers
poetry run pytest -m "unit" -v
poetry run pytest -m "not slow" -v
```

### Code Quality
```bash
# Format code automatically
make format

# Run all linting checks
make lint

# Check formatting without changes
make lint-check

# Run type checking
poetry run mypy redforge/

# Run all checks (lint + test)
make check
```

### Common CLI Testing
```bash
# Test dry run scan
make cli-dry-run

# Health check
make cli-doctor

# List available attacks
make cli-list

# Validate report schema
make schema-export

# Sprint S-1 checklist
make s1-checklist
```

## Architecture

### Core Modules

**CLI Entry Point** (`redforge/cli.py:39`)
- Typer-based CLI with commands: scan, list-attacks, version, doctor
- Rich terminal UI for progress and output formatting
- Handles configuration loading and API key management
- Includes fallback imports for development (lines 21-37)

**Scanner Core** (`redforge/core/scanner.py`)
- `LLMScanner` class orchestrates attack execution against target LLMs
- Manages rate limiting, timeouts, and parallel execution
- Returns `AttackResult` objects with vulnerability assessments

**Attack System** (`redforge/core/attacks.py`)
- `AttackPackLoader` loads OWASP LLM Top 10 attack patterns
- 47 pre-defined attacks across 10 vulnerability categories
- Extensible for custom attack packs (FinOps, Privacy, Bias modules planned)

**Report Generation** (`redforge/core/report.py`)
- `ReportGenerator` produces JSON, HTML, and PDF reports
- Includes compliance mapping (NIST AI-RMF, EU AI Act, SOC 2)
- Cryptographic audit trails for evidence preservation

**Data Models** (`redforge/models/scan_result.py:138`)
- Pydantic v2 models ensure type safety and validation
- Key models:
  - `ScanResult`: Complete scan with all attack outcomes
  - `AttackResult`: Individual attack test result (line 41)
  - `ScanMetadata`: Execution statistics and environment info (line 87)
  - `ComplianceReport`: Regulatory framework mapping (line 119)
- Enums for standardization:
  - `SeverityLevel`: critical, high, medium, low, info (line 13)
  - `AttackCategory`: OWASP LLM Top 10 + RedForge extensions (line 22)

### Key Design Patterns

1. **Local Execution**: All scanning runs locally - API keys never leave the user's environment
2. **Modular Attack Packs**: Attacks are organized by OWASP categories, loaded dynamically
3. **Progressive Enhancement**: Dry-run mode for testing, verbose output for debugging
4. **Compliance-First**: Every attack result maps to regulatory frameworks
5. **Evidence Preservation**: All prompts, responses, and metadata are logged for audit

### Configuration

The system uses a layered configuration approach:
1. Default values in code
2. `redforge.yaml` configuration file (optional)
3. Environment variables (e.g., `OPENAI_API_KEY`)
4. CLI arguments (highest precedence)

### Error Handling

- Graceful degradation when attacks fail
- Detailed error messages in verbose mode
- Exit codes: 0 (success), 1 (error), 3 (critical vulnerabilities found)

## Important Implementation Details

### OWASP LLM Top 10 Coverage
From the CLI spec (docs/cli-spec.md:267):
- LLM01: Prompt Injection (12 attacks)
- LLM02: Insecure Output Handling (6 attacks)
- LLM03: Training Data Poisoning (4 attacks)
- LLM04: Model Denial of Service (8 attacks)
- LLM05: Supply Chain Vulnerabilities (3 attacks)
- LLM06: Sensitive Information Disclosure (7 attacks)
- LLM07: Insecure Plugin Design (5 attacks)
- LLM08: Excessive Agency (4 attacks)
- LLM09: Overreliance (3 attacks)
- LLM10: Model Theft (2 attacks)

### Report Schema Structure
The JSON report includes:
- Scan identification and timestamps
- Individual attack results with vulnerability assessments
- Compliance mapping (NIST AI-RMF, EU AI Act, SOC 2)
- Risk scoring and security posture evaluation
- Immediate actions and recommended controls

### Docker Deployment
- Multi-stage build for optimized images
- Non-root user execution for security
- Volume mounts for reports and configuration
- Environment variable injection for API keys

## Sprint Context

Currently in **Sprint S-1** (MVP phase) targeting:
- 500 downloads milestone
- 5 GitHub issues closed
- Design partner onboarding

Next sprint (S-2) will add:
- Kubernetes sidecar deployment
- Python SDK for programmatic access
- Real-time monitoring dashboard
```