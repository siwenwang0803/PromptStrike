# Statement of Work (SoW) v0.2 - RedForge Pilot-0
**FinTech Design Partner Integration**

---

## 1. Project Overview

### 1.1 Engagement Summary
**Client**: [FinTech Design Partner]  
**Project**: RedForge Guardrail Implementation - Pilot-0  
**Duration**: 6 weeks (Sprint S-2 through S-4)  
**Total Value**: $3,000 USD  
**Start Date**: TBD  
**Completion Date**: TBD  

### 1.2 Objectives
- Deploy RedForge Guardrail sidecar in client's Kubernetes production environment
- Implement real-time LLM security monitoring for customer-facing chatbot
- Establish NIST AI-RMF compliance baseline for regulatory requirements
- Validate commercial viability of Guardrail β product

### 1.3 Success Criteria
- ✅ **Functional**: <15% latency overhead on production LLM traffic
- ✅ **Security**: Detection of prompt injection, data leakage, and malicious activity
- ✅ **Compliance**: NIST AI-RMF and SOC 2 evidence generation
- ✅ **Business**: Signed contract and invoice payment by Sprint S-2 end

---

## 2. Scope of Work

### 2.1 Phase 1: Environment Assessment (Week 1)
**Deliverables:**
- Infrastructure assessment and compatibility analysis
- Security requirements gathering
- Kubernetes cluster readiness evaluation
- Integration architecture design

**Client Responsibilities:**
- Provide access to staging Kubernetes cluster
- Complete environment checklist (Appendix A)
- Identify LLM endpoints for monitoring
- Assign technical point of contact

**RedForge Responsibilities:**
- Conduct technical discovery sessions
- Document current LLM architecture
- Identify integration touchpoints
- Deliver implementation plan

### 2.2 Phase 2: Guardrail Deployment (Weeks 2-3)
**Deliverables:**
- RedForge Guardrail sidecar deployment
- Custom configuration for client environment
- Integration testing and validation
- Performance baseline establishment

**Client Responsibilities:**
- Provide deployment access and credentials
- Support testing and validation activities
- Review and approve configuration changes
- Participate in performance testing

**RedForge Responsibilities:**
- Deploy and configure Guardrail sidecar
- Implement custom security rules for FinTech use cases
- Conduct integration testing
- Establish monitoring and alerting

### 2.3 Phase 3: Security Validation (Weeks 4-5)
**Deliverables:**
- Security assessment and penetration testing
- Vulnerability detection validation
- Compliance evidence collection
- Performance optimization

**Client Responsibilities:**
- Provide representative LLM traffic patterns
- Participate in security testing
- Review security findings and recommendations
- Validate compliance requirements

**RedForge Responsibilities:**
- Execute comprehensive security testing
- Generate NIST AI-RMF compliance reports
- Optimize performance and resource usage
- Document security posture improvements

### 2.4 Phase 4: Production Rollout (Week 6)
**Deliverables:**
- Production deployment and cutover
- Monitoring dashboard setup
- Operational runbooks and documentation
- Post-deployment support (30 days)

**Client Responsibilities:**
- Approve production deployment plan
- Execute change management procedures
- Monitor production metrics
- Provide feedback on operational experience

**RedForge Responsibilities:**
- Execute production deployment
- Provide operational training
- Monitor system performance
- Deliver post-deployment support

---

## 3. Technical Requirements

### 3.1 Infrastructure Prerequisites
- **Kubernetes**: v1.25+ with RBAC enabled
- **Container Runtime**: Docker or containerd
- **Storage**: Persistent volumes for report storage (100GB minimum)
- **Network**: HTTPS/TLS connectivity to LLM providers
- **Monitoring**: Prometheus/Grafana (optional but recommended)

### 3.2 LLM Integration Support
- **Supported Providers**: OpenAI, Anthropic, Azure OpenAI, AWS Bedrock
- **API Formats**: REST/HTTP with JSON payloads
- **Authentication**: Bearer tokens, API keys, OAuth 2.0
- **Traffic Volume**: Up to 1,000 requests/minute

### 3.3 Security Requirements
- **Pod Security Standards**: Restricted mode enforcement
- **Network Policies**: Zero-trust networking
- **RBAC**: Minimal privilege access controls
- **Secrets Management**: Kubernetes Secrets or external vault
- **Audit Logging**: Complete activity trail

### 3.4 Compliance Requirements
- **NIST AI-RMF**: Risk management framework implementation
- **SOC 2 Type II**: Security controls evidence
- **Data Privacy**: GDPR/CCPA compliance support
- **Financial Services**: Regulatory requirements (PCI-DSS, FFIEC)

---

## 4. Deliverables

### 4.1 Software Components
1. **Guardrail Sidecar Container** - Production-ready container image
2. **Kubernetes Manifests** - Deployment, service, and configuration files
3. **Integration Scripts** - Custom setup and configuration automation
4. **Monitoring Dashboards** - Grafana dashboards for operational visibility

### 4.2 Documentation
1. **Technical Architecture Document** - System design and data flow
2. **Deployment Guide** - Step-by-step installation instructions
3. **Operational Runbook** - Troubleshooting and maintenance procedures
4. **Security Assessment Report** - Vulnerability analysis and recommendations

### 4.3 Evidence Templates
1. **NIST AI-RMF Evidence Pack** - Compliance documentation templates
2. **SOC 2 Control Mapping** - Security controls implementation evidence
3. **Audit Trail Samples** - Representative logging and monitoring outputs
4. **Risk Assessment Matrix** - Identified risks and mitigation strategies

---

## 5. Investment & Payment Terms

### 5.1 Project Investment
**Total Project Value**: $3,000 USD

**Payment Schedule**:
- **Phase 1 Completion**: $1,000 (33%)
- **Phase 3 Completion**: $1,500 (50%)
- **Phase 4 Completion**: $500 (17%)

### 5.2 Payment Terms
- **Net Terms**: 15 days from invoice date
- **Payment Methods**: Wire transfer, ACH, corporate check
- **Currency**: USD only
- **Late Fees**: 1.5% monthly on overdue amounts

### 5.3 Additional Services (Optional)
- **Extended Support**: $500/month post-deployment
- **Custom Rule Development**: $150/hour
- **Additional Training**: $200/hour
- **Emergency Response**: $300/hour (4-hour minimum)

---

## 6. Timeline & Milestones

| Week | Phase | Key Milestones | Deliverables |
|------|-------|----------------|--------------|
| 1 | Assessment | Environment evaluated | Technical assessment report |
| 2 | Deployment | Staging deployment complete | Working sidecar in staging |
| 3 | Integration | Integration testing complete | Performance baseline |
| 4 | Validation | Security testing complete | Security assessment report |
| 5 | Optimization | Performance tuning complete | Optimized configuration |
| 6 | Production | Production deployment | Live monitoring system |

---

## 7. Roles & Responsibilities

### 7.1 RedForge Team
- **Technical Lead**: End-to-end technical delivery
- **Security Engineer**: Security assessment and hardening
- **DevOps Engineer**: Deployment and infrastructure
- **Customer Success**: Project management and client relationship

### 7.2 Client Team
- **Technical Point of Contact**: Daily coordination and decision-making
- **Infrastructure Engineer**: Kubernetes cluster management
- **Security Architect**: Security requirements and validation
- **Legal/Compliance**: Contract and regulatory oversight

---

## 8. Risk Management

### 8.1 Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| Kubernetes version incompatibility | Low | High | Pre-deployment compatibility testing |
| LLM API rate limiting | Medium | Medium | Graceful degradation implementation |
| Performance overhead | Medium | High | Comprehensive performance testing |
| Security vulnerability | Low | High | Security-first development practices |

### 8.2 Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| Delayed client approvals | Medium | Medium | Clear milestone definitions |
| Scope creep | Medium | High | Formal change control process |
| Resource availability | Low | High | Dedicated team assignment |
| Compliance gaps | Low | High | Continuous compliance validation |

---

## 9. Success Metrics

### 9.1 Technical KPIs
- **Latency Overhead**: <15% increase in LLM response time
- **Uptime**: >99.5% sidecar availability
- **Detection Rate**: >90% accuracy for known attack patterns
- **False Positive Rate**: <5% for legitimate traffic

### 9.2 Business KPIs
- **Time to Value**: Production deployment within 6 weeks
- **Client Satisfaction**: >8/10 satisfaction score
- **Contract Renewal**: Agreement for extended engagement
- **Reference Customer**: Approval for case study development

---

## 10. Terms & Conditions

### 10.1 Intellectual Property
- RedForge retains all IP rights to core software
- Client retains rights to custom configurations and data
- Mutual agreement required for any public case studies
- Client grants RedForge right to use as reference customer

### 10.2 Confidentiality
- Mutual NDA required (see separate NDA template)
- Client data remains confidential and is not used for training
- RedForge may collect anonymized usage metrics
- All client infrastructure details remain confidential

### 10.3 Limitation of Liability
- RedForge liability limited to project value ($3,000)
- No liability for indirect, consequential, or punitive damages
- Client responsible for backup and disaster recovery
- 30-day warranty period for delivered software

### 10.4 Termination
- Either party may terminate with 30-day written notice
- Client pays for work completed through termination date
- RedForge provides transition assistance for 30 days
- Confidentiality obligations survive termination

---

## Appendix A: Environment Checklist

### Infrastructure Assessment
- [ ] Kubernetes cluster version and configuration
- [ ] Available compute and storage resources
- [ ] Network connectivity and firewall rules
- [ ] Security policies and compliance requirements
- [ ] Backup and disaster recovery procedures

### LLM Environment
- [ ] Current LLM providers and models in use
- [ ] API endpoints and authentication methods
- [ ] Traffic volumes and patterns
- [ ] Existing monitoring and logging systems
- [ ] Performance SLAs and requirements

### Security Requirements
- [ ] Organizational security policies
- [ ] Compliance frameworks (SOC 2, NIST, etc.)
- [ ] Data classification and handling requirements
- [ ] Incident response procedures
- [ ] Audit and reporting requirements

### Technical Contacts
- [ ] Primary technical contact information
- [ ] Infrastructure/DevOps team contacts
- [ ] Security team contacts
- [ ] Legal/compliance team contacts
- [ ] Executive sponsor information

---

**Document Control**
- Version: 0.2
- Date: Sprint S-2
- Author: RedForge Customer Success
- Approved By: [Client Legal] & [RedForge Legal]
- Next Review: Sprint S-3