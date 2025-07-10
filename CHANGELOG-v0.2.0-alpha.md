# Changelog - v0.2.0-alpha

## Sprint S-2 / Pilot-0 Completion (2025-07-10)

### 🎯 Major Features Added in This Release

- **Guardrail Side-car α**: Kubernetes deployment with published Helm charts for real-time monitoring and one-command install.
- **Enhanced Chaos Testing**: Resilience scoring framework, 30+ tests with mutation types (data corruption, protocol violation, etc.).
- **Community Feedback System**: Multi-source collection (GitHub, telemetry, surveys), automated analysis, insights generation, and roadmap creation.
- **PCI DSS Compliance Integration**: Framework with merchant level assessment (Level 1-4, service provider), detailed reports.
- **Pydantic v2 Migration**: Backward-compatible upgrade for better validation and type safety.
- **Enterprise Readiness**: DOD (Definition of Done) verification for production deployment.

### 🔧 Updates to Core Components

#### CLI Enhancements
- Added `community` subcommands for feedback management:
  - `collect` - Gather feedback from multiple sources
  - `analyze` - Generate insights and analytics
  - `priorities` - Show prioritized feedback
  - `roadmap` - Create development roadmaps
  - `update` - Update feedback status
  - `stats` - Show feedback statistics

#### Deployment Improvements
- **Helm Repository**: Live Helm repo for production K8s deployments
- **Multi-stage Docker**: Further optimized builds for smaller images
- **Kubernetes Sidecar**: Production-ready deployment patterns

#### Testing Framework
- **Chaos Engineering**: Expanded with resilience scorer and new mutation types
- **Smoke Testing**: Comprehensive validation for CI/CD pipelines
- **Load Testing**: K6 integration for performance validation

### 🚀 Installation & Usage Updates

#### New Helm Install
```bash
# Add Helm repository
helm repo add redforge https://siwenwang0803.github.io/RedForge

# Install guardrail sidecar
helm install guardrail redforge/redforge-sidecar \
  --namespace redforge \
  --set openai.apiKey=$OPENAI_API_KEY
```

#### Community Tools
```bash
# Collect feedback from last 30 days
redforge community collect --days 30

# Generate 4-quarter roadmap
redforge community roadmap --quarters 4

# Show feedback analytics
redforge community stats
```

#### Enhanced Compliance
```bash
# Generate PCI DSS report
redforge pci-dss scan-results.json --level level_1 --version 4.0

# Multi-framework compliance report
redforge report scan-results.json --framework multi --export pdf
```

### 📊 Sprint S-2 Metrics

- **Helm Charts**: One-command deployment verified in design partner environments
- **Chaos Tests**: 30+ scenarios implemented, 81% resilience score achieved
- **Community System**: Automated feedback lifecycle with multi-source integration
- **Compliance**: Added PCI DSS support, total 4 frameworks (NIST, EU AI Act, SOC2, PCI)
- **Target Achieved**: Enterprise-ready with DOD compliance; ready for pilot programs

### 🔒 Security & Performance

- **Resource Monitoring**: CPU ≤ 200m, Memory ≤ 180Mi constraints enforced
- **Load Testing**: 500 RPS validated with constant-arrival-rate
- **Monitoring**: Prometheus + Grafana with 10 alert rules
- **Cost Protection**: FP rate 0.000%, TP rate 98.069% for token storm detection

### 🔄 Breaking Changes

**None** - This release maintains full backward compatibility with v0.1.0-alpha.

### 📋 Upgrade Guide

#### From v0.1.0-alpha
```bash
# pip upgrade
pip install --upgrade redforge

# Docker upgrade
docker pull redforge/cli:v0.2.0-alpha

# Helm upgrade
helm upgrade guardrail redforge/redforge-sidecar
```

#### New Configuration Options
Add these sections to your `redforge.yaml`:
```yaml
chaos_testing:
  enabled: true
  resilience_threshold: 0.8
  
community:
  feedback_collection: true
  github_integration: true
```

### 🎯 Next: Sprint S-3 (Aug 05-18)

#### Upcoming in v0.3.0-beta
- **Pilot Templates**: Enterprise onboarding automation
- **Stripe Integration**: Payment processing for pilot programs ($15k revenue target)
- **Usage Analytics**: Multi-tenant support and monitoring
- **Continuous Scanning**: Real-time vulnerability detection
- **Advanced Compliance**: Enhanced gap analysis and remediation

#### Migration Notes
- v0.3.0 may introduce payment-related configuration fields
- File GitHub issues for migration assistance
- Backward compatibility will be maintained

---

**Build**: Sprint S-2 / Pilot-0  
**Reference**: cid-roadmap-v2  
**Target**: Live in 1 design-partner environment, enterprise readiness  
**Date**: July 10, 2025  
**Status**: ✅ Production Ready

## Previous Versions

For changes in v0.1.0-alpha and earlier, see [CHANGELOG-v0.1.0-alpha.md](CHANGELOG-v0.1.0-alpha.md).