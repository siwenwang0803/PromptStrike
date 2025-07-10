# STRIDE Threat Analysis
<!-- cid-stride-analysis -->

## Overview
Traditional STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) analysis for the Guardrail PoC architecture.

## Threat Catalog

### S1: Sidecar Container Impersonation
**Category**: Spoofing  
**DREAD Score**: 7.0/10 (High)  
**Jira**: [PS-31](https://jira.redforge.ai/PS-31)  
**Owner**: Platform Security Team  
**Due**: 2024-01-15

#### DREAD Breakdown
- **Damage**: 9 (Complete security bypass)
- **Reproducibility**: 7 (Container image attacks)
- **Exploitability**: 6 (Requires registry access)
- **Affected Users**: 8 (All pod users)
- **Discoverability**: 5 (Container scanning needed)

#### Description
Attacker deploys malicious container impersonating the legitimate guardrail sidecar, bypassing all security controls.

#### Attack Vectors
1. **Registry Poisoning**: Replace legitimate image with malicious version
2. **Manifest Tampering**: Modify deployment to use attacker image
3. **Supply Chain**: Compromise base image or build pipeline

#### Technical Details
```yaml
# Malicious deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guardrail-malicious
spec:
  template:
    spec:
      containers:
      - name: guardrail-sidecar
        image: attacker.com/fake-guardrail:latest  # Malicious image
        ports:
        - containerPort: 8001
```

#### Mitigations
```yaml
# Container signing verification
apiVersion: v1
kind: Pod
metadata:
  annotations:
    cosign.sigstore.dev/verify: "true"
spec:
  containers:
  - name: guardrail-sidecar
    image: ghcr.io/redforge/guardrail-sidecar@sha256:abc123...
    # Use digest instead of tag for immutability
```

```bash
# Admission controller for image verification
#!/bin/bash
# webhook-verify-images.sh

IMAGE=$1
COSIGN_VERIFY_OUTPUT=$(cosign verify \
  --certificate-identity-regexp ".*@redforge.ai" \
  --certificate-oidc-issuer-regexp ".*github.*" \
  "$IMAGE" 2>&1)

if [ $? -eq 0 ]; then
    echo "Image verification passed"
    exit 0
else
    echo "BLOCKED: Image verification failed: $COSIGN_VERIFY_OUTPUT"
    exit 1
fi
```

---

### T1: Log File Tampering
**Category**: Tampering  
**DREAD Score**: 6.6/10 (High)  
**Jira**: [PS-32](https://jira.redforge.ai/PS-32)  
**Owner**: Platform Security Team  
**Due**: 2024-01-20

#### DREAD Breakdown
- **Damage**: 7 (Evidence destruction)
- **Reproducibility**: 8 (File system access)
- **Exploitability**: 5 (Container compromise needed)
- **Affected Users**: 7 (Audit impact)
- **Discoverability**: 6 (Log analysis required)

#### Description
Attacker modifies log files in shared volume to hide malicious activity or corrupt evidence for compliance audits.

#### Attack Scenarios
1. **Direct File Modification**: Edit log files to remove attack traces
2. **Log Injection**: Insert false entries to confuse analysis
3. **Timestamp Manipulation**: Alter chronological evidence

#### Impact Analysis
- **Compliance Risk**: SOC 2, PCI DSS audit failures
- **Forensic Loss**: Inability to investigate incidents
- **Legal Risk**: Corrupted evidence in litigation
- **Detection Evasion**: Hide ongoing attacks

#### Technical Implementation
```python
# Log integrity protection
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Any

class LogIntegrityProtector:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        
    def sign_log_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create tamper-evident log entry"""
        
        # Normalize entry for consistent hashing
        normalized = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        
        # Generate integrity hash
        integrity_hash = hmac.new(
            self.secret_key,
            normalized.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create signed entry
        signed_entry = {
            **entry,
            "_integrity": {
                "hash": integrity_hash,
                "algorithm": "HMAC-SHA256",
                "signed_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
        
        return signed_entry
    
    def verify_log_entry(self, entry: Dict[str, Any]) -> bool:
        """Verify log entry hasn't been tampered"""
        
        if "_integrity" not in entry:
            return False
            
        # Extract integrity data
        integrity_data = entry.pop("_integrity")
        stored_hash = integrity_data["hash"]
        
        # Recalculate hash
        normalized = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        calculated_hash = hmac.new(
            self.secret_key,
            normalized.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        return hmac.compare_digest(stored_hash, calculated_hash)

# Usage in sidecar
protector = LogIntegrityProtector(os.environ["LOG_SIGNING_KEY"])

# When logging
log_entry = {
    "timestamp": "2024-01-09T10:30:00Z",
    "event": "llm_request",
    "user_id": "user123",
    "prompt_hash": "sha256:abc123...",
    "risk_score": 0.3
}

signed_entry = protector.sign_log_entry(log_entry)
```

#### Mitigations
```yaml
# ConfigMap for log integrity
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-integrity-config
data:
  config.yaml: |
    log_protection:
      enabled: true
      signing_algorithm: "HMAC-SHA256"
      key_rotation_days: 30
      backup_verification: true
      immutable_storage: true
    
    monitoring:
      integrity_check_interval: "5m"
      alert_on_tampering: true
      forensic_mode: true
    
    compliance:
      nist_csf: "PR.DS-6"  # Data integrity
      sox_404: "ITGC-07"   # IT controls
      iso27001: "A.12.3.1" # Information backup
```

---

### R1: Security Event Repudiation
**Category**: Repudiation  
**DREAD Score**: 4.8/10 (Medium)  
**Jira**: [PS-36](https://jira.redforge.ai/PS-36)  
**Owner**: Privacy Team  
**Due**: 2024-02-15

#### DREAD Breakdown
- **Damage**: 9 (Legal/compliance impact)
- **Reproducibility**: 3 (Requires access)
- **Exploitability**: 2 (Complex attack)
- **Affected Users**: 7 (Organization-wide)
- **Discoverability**: 3 (Hard to detect)

#### Description
Users or attackers deny performing actions by exploiting weak audit trails or lack of non-repudiation controls.

#### Scenarios
1. **Missing Audit Trails**: No evidence of user actions
2. **Weak Authentication**: Shared credentials enable denial
3. **Log Gaps**: Missing critical security events

#### Mitigations
```python
# Non-repudiation service
class NonRepudiationService:
    def __init__(self, signing_key: str, blockchain_client):
        self.signing_key = signing_key
        self.blockchain = blockchain_client
        
    def create_audit_record(self, user_id: str, action: str, 
                          timestamp: datetime, evidence: Dict) -> str:
        """Create tamper-proof audit record"""
        
        record = {
            "user_id": user_id,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "evidence": evidence,
            "client_ip": self._get_client_ip(),
            "user_agent": self._get_user_agent(),
            "session_id": self._get_session_id()
        }
        
        # Digital signature
        signature = self._sign_record(record)
        
        # Blockchain anchoring
        tx_hash = self.blockchain.anchor_record(record, signature)
        
        return tx_hash
```

---

### I1: PII Exposure in Logs
**Category**: Information Disclosure  
**DREAD Score**: 6.0/10 (High)  
**Jira**: [PS-35](https://jira.redforge.ai/PS-35)  
**Owner**: Privacy Team  
**Due**: 2024-01-22

#### DREAD Breakdown
- **Damage**: 8 (Privacy breach, GDPR fines)
- **Reproducibility**: 6 (Log access required)
- **Exploitability**: 4 (Volume access needed)
- **Affected Users**: 7 (All users)
- **Discoverability**: 5 (Data inspection needed)

#### Description
Personally Identifiable Information (PII) leaked through verbose logging, accessible to unauthorized parties with volume access.

#### PII Risk Categories
- **Direct Identifiers**: Names, SSNs, emails
- **Quasi-identifiers**: ZIP codes, birthdates, IP addresses
- **Sensitive Data**: Health info, financial data, biometrics

#### Detection Patterns
```python
import re
from typing import List, Dict

class PIIDetector:
    def __init__(self):
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "phone": r'\b\d{3}-\d{3}-\d{4}\b',
            "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }
        
    def scan_text(self, text: str) -> List[Dict]:
        """Scan text for PII patterns"""
        findings = []
        
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": self._calculate_confidence(pii_type, match.group())
                })
                
        return findings
    
    def mask_pii(self, text: str) -> str:
        """Replace PII with masked values"""
        masked_text = text
        
        for pii_type, pattern in self.patterns.items():
            if pii_type == "email":
                masked_text = re.sub(pattern, "[EMAIL_REDACTED]", masked_text)
            elif pii_type == "ssn":
                masked_text = re.sub(pattern, "XXX-XX-XXXX", masked_text)
            elif pii_type == "credit_card":
                masked_text = re.sub(pattern, "XXXX-XXXX-XXXX-XXXX", masked_text)
                
        return masked_text
```

#### Mitigations
```yaml
# PII protection configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: pii-protection-config
data:
  rules.yaml: |
    pii_detection:
      enabled: true
      sensitivity_level: high
      
    masking_rules:
      - pattern: "email"
        replacement: "[EMAIL_REDACTED]"
        log_finding: true
        
      - pattern: "ssn" 
        replacement: "XXX-XX-XXXX"
        log_finding: true
        alert_security: true
        
      - pattern: "credit_card"
        replacement: "XXXX-XXXX-XXXX-XXXX"
        log_finding: true
        alert_security: true
        compliance_event: true
    
    compliance:
      gdpr_article_5: true      # Data minimization
      ccpa_section_1798: true   # Consumer privacy
      sox_404: true             # Internal controls
```

---

### D1: Service Disruption via Resource Exhaustion
**Category**: Denial of Service  
**DREAD Score**: 4.8/10 (Medium)  
**Jira**: [PS-37](https://jira.redforge.ai/PS-37)  
**Owner**: SRE Team  
**Due**: 2024-02-20

#### DREAD Breakdown
- **Damage**: 6 (Service outage)
- **Reproducibility**: 5 (Requires volume)
- **Exploitability**: 4 (Need pod access)
- **Affected Users**: 5 (Limited scope)
- **Discoverability**: 4 (Monitoring required)

#### Description
Attacker exhausts pod resources (CPU, memory, disk) causing service disruption for legitimate users.

#### Attack Methods
1. **Memory Exhaustion**: Allocate excessive memory
2. **CPU Starvation**: Spawn high-CPU processes  
3. **Disk Filling**: Write large files to shared volume
4. **Connection Flooding**: Exhaust network connections

#### Mitigations
```yaml
# Resource limits and quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: guardrail-quota
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4" 
    limits.memory: 8Gi
    persistentvolumeclaims: "2"
    count/pods: "10"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: guardrail-limits
spec:
  limits:
  - default:
      cpu: 500m
      memory: 1Gi
    defaultRequest:
      cpu: 100m
      memory: 256Mi
    type: Container
```

---

### E1: Container Privilege Escalation
**Category**: Elevation of Privilege  
**DREAD Score**: 4.8/10 (Medium)  
**Jira**: [PS-38](https://jira.redforge.ai/PS-38)  
**Owner**: Platform Security Team  
**Due**: 2024-02-10

#### DREAD Breakdown
- **Damage**: 8 (Full system compromise)
- **Reproducibility**: 4 (Complex exploit)
- **Exploitability**: 3 (Requires vulnerability)
- **Affected Users**: 6 (Node impact)
- **Discoverability**: 3 (Advanced scanning)

#### Description
Container escape leading to node compromise and cluster-wide privilege escalation.

#### Attack Vectors
1. **Kernel Exploits**: CVE exploitation
2. **Container Runtime Bugs**: runc, containerd vulnerabilities
3. **Misconfiguration**: Privileged containers, host mounts

#### Mitigations
```yaml
# Pod Security Standards
apiVersion: v1
kind: Pod
metadata:
  name: guardrail-secure
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: guardrail-sidecar
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
      runAsNonRoot: true
```

## STRIDE Summary Matrix

| Threat | Category | Score | Owner | Due Date | Mitigation |
|--------|----------|-------|-------|----------|------------|
| S1 | Spoofing | 7.0 | Platform Sec | 2024-01-15 | Container signing |
| T1 | Tampering | 6.6 | Platform Sec | 2024-01-20 | Log integrity |
| R1 | Repudiation | 4.8 | Privacy | 2024-02-15 | Audit trails |
| I1 | Info Disclosure | 6.0 | Privacy | 2024-01-22 | PII masking |
| D1 | DoS | 4.8 | SRE | 2024-02-20 | Resource limits |
| E1 | Privilege Escalation | 4.8 | Platform Sec | 2024-02-10 | Pod security |

## See Also
- [Risk Matrix](06-risk-matrix.md) - Combined risk analysis
- [LLM Threats](04-llm-threats.md) - AI-specific threats
- [Mitigations](07-mitigations.md) - Implementation guides
- [Back to Index](README.md)