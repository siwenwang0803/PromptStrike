# Changelog - v0.1.0-alpha

## Sprint S-1 Completion (2025-07-03)

### 🎯 Major Features

- **Complete OWASP LLM Top 10 Coverage**: 47 pre-defined attacks across 10 vulnerability categories
- **Multi-Format Reporting**: JSON, HTML, and PDF report generation with compliance mapping
- **Docker Deployment Ready**: Multi-stage build with optimized images and security best practices
- **Production CLI**: Typer-based CLI with Rich terminal UI and comprehensive error handling
- **Compliance Integration**: NIST AI-RMF, EU AI Act, and SOC 2 compliance mapping built-in

### 🔧 Core Components

#### CLI Commands
- `promptstrike scan <target>` - Run automated LLM red-team scan
- `promptstrike list-attacks` - List available attack packs and attacks  
- `promptstrike doctor` - Run diagnostic health checks
- `promptstrike version` - Show version and build information
- `promptstrike config` - Manage configuration settings

#### Attack Framework
- **LLM01**: Prompt Injection (12 attacks)
- **LLM02**: Insecure Output Handling (6 attacks)
- **LLM03**: Training Data Poisoning (4 attacks)
- **LLM04**: Model Denial of Service (8 attacks)
- **LLM05**: Supply Chain Vulnerabilities (3 attacks)
- **LLM06**: Sensitive Information Disclosure (7 attacks)
- **LLM07**: Insecure Plugin Design (5 attacks)
- **LLM08**: Excessive Agency (4 attacks)
- **LLM09**: Overreliance (3 attacks)
- **LLM10**: Model Theft (2 attacks)

#### Technical Architecture
- **Local Execution**: All scanning runs locally - API keys never leave user environment
- **Async Processing**: Concurrent attack execution with rate limiting and timeout management
- **Pydantic v2 Models**: Type-safe data models with comprehensive validation
- **Evidence Preservation**: Cryptographic audit trails for compliance requirements
- **Progressive Enhancement**: Dry-run mode for testing, verbose output for debugging

### 🚀 Installation & Usage

```bash
# Install via pip
pip install promptstrike

# Run basic scan
promptstrike scan gpt-4 --dry-run

# Health check
promptstrike doctor

# List available attacks
promptstrike list-attacks
```

### 📋 Report Schema

Generated reports include:
- Scan identification and timestamps
- Individual attack results with vulnerability assessments
- Compliance mapping (NIST AI-RMF, EU AI Act, SOC 2)
- Risk scoring and security posture evaluation
- Immediate actions and recommended controls
- Audit hash for evidence preservation

### 🔒 Security Features

- **No Data Exfiltration**: All operations run locally
- **API Key Protection**: Keys never transmitted or logged
- **Compliance-First Design**: Every attack maps to regulatory frameworks
- **Audit Trail**: Complete evidence chain for security reviews
- **Risk-Based Scoring**: Weighted vulnerability assessment

### 🛠️ Technical Fixes

- **Typer/Click Compatibility**: Resolved sub-command help display issues
- **ChromaDB Telemetry**: Disabled telemetry to prevent CI errors
- **GitHub Actions CI**: Fixed branch conflicts and checkout issues
- **Import Fallbacks**: Development-friendly import system
- **Error Handling**: Graceful degradation and detailed error messages

### 📊 Sprint S-1 Metrics

- **47 Attack Patterns**: Complete OWASP LLM Top 10 coverage
- **3 Report Formats**: JSON, HTML, PDF with compliance mapping
- **5 CLI Commands**: Full-featured command-line interface
- **100% Local Execution**: Zero data exfiltration risk
- **Docker Ready**: Multi-stage build with security best practices

---

## Sprint S-2 Completion (2025-07-10)

### 🚀 Major Enhancements

- **PCI DSS Compliance Framework**: Complete v4.0 and v3.2.1 support with merchant level classification
- **Community Feedback System**: GitHub integration, telemetry analysis, priority scoring
- **Enhanced Compliance Reporting**: Multi-framework support, executive summaries, remediation roadmaps
- **Chaos Testing Integration**: Resilience validation with comprehensive fault injection
- **Advanced CLI Commands**: `report`, `pci-dss`, `community` management tools

### 🔧 New Features

#### PCI DSS Support
- Merchant level assessment (Level 1-4, Service Provider)
- Automated control mapping and compliance scoring
- Executive summaries with business impact analysis
- Remediation roadmaps with phased implementation

#### Community Feedback Loop
- GitHub issue collection and classification
- Telemetry-based feedback analysis
- Priority scoring for development planning
- Analytics and trend identification

#### Enhanced Compliance
- 10+ framework support (NIST, EU AI Act, SOC 2, ISO 27001, GDPR, CCPA, HIPAA, etc.)
- Cross-framework analysis and gap identification
- Consolidated recommendations
- Evidence artifact generation

### 📊 Sprint S-2 Metrics

- **10+ Compliance Frameworks**: Enterprise-grade regulatory support
- **Chaos Testing**: 81% resilience score validation
- **Community Feedback**: Automated collection and prioritization
- **Production Deployment**: Kubernetes sidecar with resource monitoring

### 🎯 Next: Pilot-0 / Sprint S-3

Upcoming features:
- Python SDK for programmatic access
- Real-time monitoring dashboard
- Custom attack pack creation
- Enterprise pilot partnerships

---

**Build**: Sprint S-2/Pilot-0  
**Reference**: cid-roadmap-v1  
**Target**: Enterprise partnerships, pilot revenue  
**Date**: July 10, 2025  
**Status**: ✅ Enterprise Ready