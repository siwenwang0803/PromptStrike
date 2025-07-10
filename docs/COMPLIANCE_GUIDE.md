# RedForge Compliance Guide

**Enterprise-Grade Compliance Support for LLM Security Assessments**

RedForge provides comprehensive compliance support for regulatory frameworks across industries including Financial Services, Healthcare, and Technology. This guide covers supported frameworks, compliance reporting, and enterprise RBAC features.

## 🎯 Supported Compliance Frameworks

### **Tier 1: Core AI/Technology Frameworks**
- **NIST AI Risk Management Framework (AI-RMF 1.0)** - Complete mapping to GOVERN, MAP, MEASURE, MANAGE functions
- **EU AI Act (Regulation 2024/1689)** - Risk categorization and obligations mapping
- **ISO 27001:2022** - Information Security Management controls
- **SOC 2 Type II** - Trust Service Criteria (Security, Availability, Privacy)

### **Tier 2: Privacy & Data Protection**
- **GDPR** - General Data Protection Regulation compliance
- **CCPA** - California Consumer Privacy Act requirements
- **HIPAA** - Healthcare data protection (Administrative, Physical, Technical Safeguards)

### **Tier 3: Industry-Specific**
- **PCI DSS** - Payment Card Industry Data Security Standard
- **FFIEC** - Federal Financial Institutions Examination Council guidelines
- **NYDFS 23 NYCRR 500** - New York Department of Financial Services cybersecurity requirements

## 🔍 Compliance Assessment Features

### **Automated Framework Mapping**
Every RedForge attack maps to relevant compliance controls:

```python
# Example: Prompt Injection → Multiple Frameworks
{
  "nist_ai_rmf": {
    "control": "GOVERN-1.1",
    "function": "GOVERN",
    "implementation": "Implement input validation and sanitization"
  },
  "eu_ai_act": {
    "article": "Article 9", 
    "risk_category": "high",
    "requirement": "Establish risk management system"
  },
  "iso_27001": {
    "control": "A.8.2",
    "domain": "Asset Management",
    "implementation": "Classify and handle inputs appropriately"
  }
}
```

### **Compliance Scoring**
- **Overall Compliance Score**: 0-100% based on vulnerability findings vs. framework requirements
- **Framework-Specific Scores**: Individual scores for each regulatory framework
- **Gap Analysis**: Identifies specific controls that need attention
- **Risk Assessment**: Maps technical findings to business risk levels

### **Evidence Preservation**
- **Cryptographic Audit Trail**: SHA-256 hashes for integrity verification
- **Evidence Artifacts**: Scan results, attack details, compliance mappings
- **Timestamped Reports**: Immutable audit records for regulatory submissions

## 📊 Compliance Reporting

### **CLI Report Generation**

Generate compliance reports from scan results:

```bash
# Multi-framework compliance report
redforge report scan_results.json --framework multi --format comprehensive

# Specific framework report
redforge report scan_results.json --framework nist_ai_rmf --format audit

# Export to different formats
redforge report scan_results.json --framework eu_ai_act --output compliance_report.json --export json
redforge report scan_results.json --framework iso_27001 --output audit_report.yaml --export yaml
redforge report scan_results.json --framework soc2 --output findings.csv --export csv
```

### **Report Templates**

Choose from specialized templates for different audiences:

| Template | Description | Target Audience |
|----------|-------------|-----------------|
| `comprehensive` | Full technical report with mappings | Security Teams |
| `executive` | High-level business impact summary | C-Suite, Board |
| `audit` | Formal audit report with evidence | External Auditors |
| `fintech` | Financial services compliance focus | FinTech Compliance |
| `healthcare` | HIPAA and healthcare-focused | Healthcare Compliance |
| `gdpr` | Privacy impact assessment | Privacy Officers |
| `regulatory_filing` | Formal regulatory submission format | Regulators |

### **Industry-Specific Examples**

**Financial Services (FinTech):**
```bash
redforge report scan_results.json \\
  --framework multi \\
  --format fintech \\
  --output fintech_compliance_report.json
```

**Healthcare:**
```bash
redforge report scan_results.json \\
  --framework hipaa \\
  --format healthcare \\
  --output hipaa_assessment.json
```

**EU Operations:**
```bash
redforge report scan_results.json \\
  --framework eu_ai_act \\
  --format gdpr \\
  --output eu_ai_compliance.json
```

## 🔐 Enterprise RBAC

RedForge includes enterprise-grade Role-Based Access Control for compliance and audit requirements.

### **Pre-Defined Roles**

| Role | Description | Permissions |
|------|-------------|-------------|
| **Auditor** | Read-only access to reports and metrics | `read:reports`, `view:metrics`, `access:health` |
| **Security Analyst** | Security analysis and report generation | `read:reports`, `generate:reports`, `view:metrics`, `view:scan-results` |
| **Compliance Officer** | Compliance reporting and audit access | `read:reports`, `export:compliance`, `view:audit-logs`, `access:evidence` |
| **Admin** | Full administrative access | `admin:all`, `manage:keys`, `write:config`, `manage:rbac` |
| **Developer** | Development and testing access | `read:reports`, `view:metrics`, `test:endpoints` |

### **Kubernetes RBAC Integration**

Configure enterprise RBAC in your Helm values:

```yaml
rbac:
  enterprise:
    enabled: true
    customRoles: true
    
    # User assignments
    userBindings:
      - user: "security-team@company.com"
        role: "security-analyst"
      - user: "compliance@company.com"
        role: "compliance-officer"
      - user: "audit-team@company.com"
        role: "auditor"
    
    # Service account automation
    serviceAccountBindings:
      - serviceAccount: "compliance-exporter"
        role: "compliance-officer"
      - serviceAccount: "ci-scanner"
        role: "developer"
```

### **Custom Role Creation**

Create custom roles for specific organizational needs:

```yaml
rbac:
  enterprise:
    roles:
      - name: "fintech-auditor"
        description: "FinTech-specific auditing role"
        permissions:
          - "read:reports"
          - "export:compliance"
          - "view:audit-logs"
          - "access:pci-dss"
          - "access:ffiec"
        namespaces: ["redforge-production"]
```

## 🏢 Industry Use Cases

### **Financial Services**
**Requirements**: NYDFS 500, FFIEC, PCI DSS, SOC 2
**Use Case**: Quarterly cybersecurity assessments, vendor risk management

```bash
# Comprehensive FinTech assessment
redforge scan gpt-4 --output fintech_q4_scan.json
redforge report fintech_q4_scan.json \\
  --framework multi \\
  --format fintech \\
  --output Q4_2024_Cybersecurity_Assessment.json
```

**Key Benefits**:
- ✅ NYDFS 500 penetration testing requirements (§500.02(g))
- ✅ FFIEC cybersecurity maturity assessment
- ✅ PCI DSS vulnerability management
- ✅ Automated evidence collection for audits

### **Healthcare**
**Requirements**: HIPAA, GDPR (if EU operations), SOC 2
**Use Case**: PHI protection assessment, HIPAA compliance validation

```bash
# HIPAA compliance assessment
redforge scan claude-3-sonnet --output healthcare_scan.json
redforge report healthcare_scan.json \\
  --framework hipaa \\
  --format healthcare \\
  --output HIPAA_Security_Assessment.json
```

**Key Benefits**:
- ✅ HIPAA Administrative Safeguards (§164.308)
- ✅ Technical Safeguards assessment (§164.312)
- ✅ PHI confidentiality validation
- ✅ Breach risk analysis documentation

### **Technology Companies**
**Requirements**: SOC 2, ISO 27001, EU AI Act (if applicable)
**Use Case**: Product security validation, customer trust reports

```bash
# Comprehensive tech company assessment
redforge scan your-llm-api --output tech_company_scan.json
redforge report tech_company_scan.json \\
  --framework multi \\
  --format comprehensive \\
  --output Security_Assessment_Report.json
```

**Key Benefits**:
- ✅ SOC 2 Type II readiness assessment
- ✅ ISO 27001 control effectiveness validation
- ✅ Customer security questionnaire responses
- ✅ Vendor security assessments

### **EU AI System Providers**
**Requirements**: EU AI Act, GDPR, ISO 27001
**Use Case**: High-risk AI system compliance, CE marking preparation

```bash
# EU AI Act compliance assessment
redforge scan your-ai-system --output eu_ai_scan.json
redforge report eu_ai_scan.json \\
  --framework eu_ai_act \\
  --format regulatory_filing \\
  --output EU_AI_Act_Compliance_Report.json
```

**Key Benefits**:
- ✅ Risk categorization validation (Article 6)
- ✅ Quality management system requirements (Article 16)
- ✅ Conformity assessment preparation
- ✅ Post-market monitoring compliance

## 📋 Compliance Checklist Templates

### **SOC 2 Type II Readiness**
- [ ] Security criteria assessment (CC6.x controls)
- [ ] Availability monitoring implementation (A1.x controls)
- [ ] Privacy controls validation (P1.x controls)
- [ ] Vendor management documentation (CC9.x controls)
- [ ] Incident response procedures (CC7.x controls)

### **NIST AI-RMF Implementation**
- [ ] GOVERN function implementation
- [ ] MAP function risk assessment
- [ ] MEASURE function metrics collection
- [ ] MANAGE function operational controls
- [ ] Gap analysis and remediation plan

### **EU AI Act High-Risk Systems**
- [ ] Risk management system (Article 9)
- [ ] Data governance procedures (Article 10)
- [ ] Human oversight implementation (Article 14)
- [ ] Accuracy and robustness testing (Article 15)
- [ ] Quality management system (Article 16)

## 🚀 Getting Started

### 1. **Initial Assessment**
```bash
# Run comprehensive scan
redforge scan your-llm-endpoint --output initial_scan.json

# Generate multi-framework report
redforge report initial_scan.json --framework multi --format executive
```

### 2. **Choose Your Framework**
Based on your industry and requirements:
- **FinTech**: Start with NYDFS 500 + FFIEC
- **Healthcare**: Focus on HIPAA + SOC 2
- **Tech**: Begin with SOC 2 + ISO 27001
- **EU**: Prioritize EU AI Act + GDPR

### 3. **Configure RBAC**
Set up appropriate access controls:
```yaml
# values.yaml
rbac:
  enterprise:
    enabled: true
    userBindings:
      - user: "your-compliance-team@company.com"
        role: "compliance-officer"
```

### 4. **Establish Monitoring**
- Schedule regular scans (monthly/quarterly)
- Set up compliance dashboards
- Configure automated reporting
- Implement continuous compliance monitoring

## 🤝 Professional Services

For enterprise deployments requiring specialized compliance support:

- **Compliance Assessment Services**: Expert-led framework implementation
- **Custom Framework Mapping**: Industry-specific requirement mapping
- **Audit Preparation**: Regulatory examination readiness
- **Training Programs**: Team education on AI security compliance

Contact: [enterprise@redforge.com](mailto:enterprise@redforge.com)

## 📞 Support

- **Documentation**: [https://docs.redforge.com/compliance](https://docs.redforge.com/compliance)
- **Issues**: [GitHub Issues](https://github.com/siwenwang0803/RedForge/issues)
- **Enterprise Support**: [enterprise@redforge.com](mailto:enterprise@redforge.com)
- **Community**: [GitHub Discussions](https://github.com/siwenwang0803/RedForge/discussions)

---

*This guide covers RedForge's compliance capabilities as of Sprint S-1. Additional frameworks and features are continuously being added based on enterprise customer requirements.*