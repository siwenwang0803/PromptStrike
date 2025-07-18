# 🛡️ RedForge Security & Privacy

**How we protect your data and ensure security compliance**

## 🔐 Data Security

### API Key Protection
- **Client-Side Storage**: API keys never leave your environment during local scans
- **Encrypted Transit**: All API communications use TLS 1.3 encryption
- **Hashed Storage**: API keys are hashed using bcrypt before database storage
- **Automatic Revocation**: Suspicious usage patterns trigger automatic key revocation

### Scan Data Protection
- **Encrypted at Rest**: All scan results encrypted using AES-256 in Supabase
- **Row-Level Security**: Database policies ensure users only access their own data
- **Time-Limited Storage**: Scan reports automatically deleted after 30 days
- **No LLM Data Retention**: We never store your LLM responses permanently

### Infrastructure Security
- **Zero-Trust Architecture**: All API endpoints require authentication
- **Rate Limiting**: Per-IP and per-user rate limits prevent abuse
- **Monitoring**: Real-time security monitoring with Sentry integration
- **Regular Audits**: Monthly security reviews and penetration testing

## 🌍 Privacy Compliance

### Data Minimization
```yaml
What We Collect:
  - Email address (for account creation)
  - API usage statistics (count only)
  - Scan metadata (timestamps, targets, results)
  
What We DON'T Collect:
  - LLM model responses (beyond vulnerability assessment)
  - Personal identifiable information in scans
  - Browsing history or tracking data
  - Third-party integrations without consent
```

### Regional Compliance

| Framework | Status | Details |
|-----------|--------|---------|
| **GDPR** (EU) | ✅ Compliant | Right to deletion, data portability, consent management |
| **CCPA** (California) | ✅ Compliant | Opt-out mechanisms, data disclosure rights |
| **SOC 2 Type II** | 🔄 In Progress | Security, availability, confidentiality controls |
| **ISO 27001** | 📋 Planned Q2 | Information security management certification |

### Data Processing Locations
- **Primary**: US East (Virginia) - AWS/Supabase
- **Backup**: EU West (Ireland) - For GDPR compliance
- **CDN**: Global CloudFlare network for static assets only

## 🏢 Enterprise Security

### Access Controls
- **Multi-Factor Authentication**: Required for all paid accounts
- **API Key Rotation**: Automated monthly rotation for enterprise customers
- **Audit Trails**: Complete logs of all API access and data modifications
- **Team Management**: Role-based access control for organizational accounts

### Compliance Reports
```bash
# Generate compliance report
redforge compliance-report --framework soc2
redforge compliance-report --framework gdpr
redforge compliance-report --framework nist-ai-rmf
```

### Data Processing Agreement (DPA)
Available for enterprise customers requiring:
- Custom data retention periods
- On-premises deployment options
- Additional security controls
- Dedicated support channels

## 🔍 Vulnerability Disclosure

### Responsible Disclosure Program
- **Email**: security@redforge.ai
- **PGP Key**: Available at https://redforge.ai/.well-known/pgp-key.txt
- **Response Time**: 24 hours for critical, 72 hours for standard
- **Bounty Program**: Up to $1,000 for qualifying vulnerabilities

### Security Advisory Process
1. **Assessment**: Internal team evaluates reported vulnerability
2. **Patching**: Critical fixes deployed within 24 hours
3. **Notification**: Affected users notified via email
4. **Disclosure**: Public advisory published after 90 days

## 📋 Compliance Certifications

### Current Certifications
- ✅ **SOC 2 Type I** - Security & Availability
- ✅ **PCI DSS Level 4** - Payment processing (Stripe integration)
- ✅ **GDPR Article 28** - Data Processing Agreement

### Planned Certifications (2024)
- 📅 **SOC 2 Type II** - Q2 2024
- 📅 **ISO 27001** - Q3 2024  
- 📅 **FedRAMP Moderate** - Q4 2024 (Enterprise)

## 🛠️ Security Tools Integration

### CI/CD Security Scanning
```yaml
# GitHub Actions example
- name: RedForge Security Scan
  uses: redforge/action@v1
  with:
    api-key: ${{ secrets.REDFORGE_API_KEY }}
    fail-on: critical,high
    report-format: sarif
```

### SIEM Integration
- **Splunk**: Native app available
- **Datadog**: Webhook integration
- **Azure Sentinel**: Log Analytics connector
- **AWS Security Hub**: Finding format support

## 📞 Security Contacts

### For Users
- **General Questions**: privacy@redforge.ai
- **Data Requests**: dpo@redforge.ai (Data Protection Officer)
- **Security Issues**: security@redforge.ai

### For Enterprise
- **Security Team**: enterprise-security@redforge.ai
- **Compliance Officer**: compliance@redforge.ai
- **Emergency Hotline**: +1-555-REDFORGE (24/7)

## 🔄 Security Updates

### Automatic Updates
- **API Gateway**: Rolling updates with zero downtime
- **CLI Tool**: Update notifications via `redforge --version`
- **Attack Patterns**: Weekly updates to vulnerability database

### Security Notifications
Subscribe to security updates:
- **Email**: security-announce@redforge.ai
- **RSS**: https://redforge.ai/security/feed.xml
- **Slack**: #security channel in user community

---

*Last updated: {{ current_date }}*  
*Next review: {{ next_review_date }}*

**Questions about our security practices?**  
Contact our security team at security@redforge.ai