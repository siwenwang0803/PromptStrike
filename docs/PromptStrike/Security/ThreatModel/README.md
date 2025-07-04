# PromptStrike Guardrail Threat Model v2
<!-- cid-guardrail-threat-model-index -->

## Executive Summary

The PromptStrike Guardrail sidecar deployment introduces unique security challenges in Kubernetes environments. This comprehensive threat model addresses traditional infrastructure risks, LLM-specific vulnerabilities, and supply chain threats using a structured DREAD scoring methodology.

### Risk Assessment Overview
- **Overall Risk Level**: Medium-High (6.8/10 DREAD)
- **Critical Risks**: 3 (requiring 24-hour response)
- **High Risks**: 8 (requiring 7-day remediation)
- **Medium Risks**: 4 (requiring 30-day remediation)
- **LLM-Specific Risks**: 4 newly identified
- **Supply Chain Risks**: 2 newly identified

### Key Improvements in v2
- ✅ **Quantified Risk Scoring**: DREAD methodology with 5-factor formulas
- ✅ **LLM-Specific Threats**: Token storms, prompt replay, data extraction
- ✅ **Supply Chain Security**: Dependency injection, SBOM risks, CI/CD threats
- ✅ **Jira Integration**: Automated ticket linking and tracking
- ✅ **Policy-as-Code**: CI validation with conftest and trivy
- ✅ **Modular Structure**: Maintainable multi-file architecture

## Document Structure

1. [Risk Scoring Methodology](01-risk-methodology.md) - DREAD framework with detailed formulas
2. [Architecture Overview](02-architecture.md) - System design and data flows
3. [STRIDE Analysis](03-stride-analysis.md) - Traditional threat categories
4. [LLM-Specific Threats](04-llm-threats.md) ⭐ NEW - AI/ML attack vectors
5. [Supply Chain Threats](05-supply-chain.md) ⭐ NEW - Dependencies and CI/CD
6. [Risk Matrix](06-risk-matrix.md) - Prioritized threat rankings
7. [Mitigations](07-mitigations.md) - Security control implementations
8. [Compliance Mapping](08-compliance.md) - Regulatory requirements
9. [Incident Response](09-incident-response.md) - Detection and response
10. [Evidence & Audit](10-evidence-audit.md) - Forensics and compliance

## Quick Links
- 🚨 [Critical Threats](06-risk-matrix.md#critical-threats)
- 📋 [Mitigation Checklist](07-mitigations.md#checklist)
- 🎯 [Sprint S-2 Actions](06-risk-matrix.md#sprint-s2)
- 📊 [DREAD Calculator](01-risk-methodology.md#calculator)

## Version Control
- **Version**: 2.1
- **Last Updated**: 2024-01-09
- **Next Review**: Sprint S-3
- **Owner**: Security Engineering Team
- **Status**: Ready for Audit

## Recent Updates
- ✅ Added quantified DREAD scoring with 5-factor formula
- ✅ Integrated LLM-specific threats (Token Storm, Prompt Replay)
- ✅ Added supply chain security (SC-1, SC-2)
- ✅ Implemented Jira ticket tracking
- ✅ Split into manageable sub-documents

## Compliance Summary
- **NIST AI-RMF**: 85% coverage
- **EU AI Act**: Article 9, 10, 12, 15 addressed
- **SOC 2**: CC6.1, CC6.3, CC6.7 controls
- **ISO 27001**: Annex A controls mapped

## Contact
- **Security Team**: security@promptstrike.ai
- **Jira Project**: [PSTRIKE](https://jira.promptstrike.ai/browse/PSTRIKE)
- **Slack**: #security-guardrail