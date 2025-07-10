# Risk Scoring Methodology
<!-- cid-risk-methodology -->

## DREAD Framework v2.1

### Formula
```
Risk Score = (D + R + E + A + D2) / 5

Where:
- D  = Damage Potential (0-10)
- R  = Reproducibility (0-10)
- E  = Exploitability (0-10)
- A  = Affected Users (0-10)
- D2 = Discoverability (0-10)
```

### Factor Definitions

#### Damage Potential (D)
**Question**: How much damage would this threat cause if successfully exploited?

| Score | Damage Level | Description | Financial Impact | Examples |
|-------|--------------|-------------|------------------|----------|
| 10 | Catastrophic | Complete system compromise | >$1M | Full cluster takeover, massive PII breach |
| 8-9 | Severe | Major service disruption | $100K-$1M | Service outage, significant data loss |
| 6-7 | Significant | Partial service impact | $10K-$100K | Degraded performance, limited data exposure |
| 4-5 | Moderate | Localized issues | $1K-$10K | Single component failure, minor data leak |
| 2-3 | Minor | Minimal impact | <$1K | Logging issues, cosmetic problems |
| 1 | Negligible | No real impact | $0 | Informational disclosure only |

**Calculation Factors**:
- Financial impact (breach costs, downtime, fines)
- Regulatory impact (GDPR fines, compliance violations)
- Reputational damage (customer trust, brand impact)
- Data sensitivity level (PII, PHI, financial, trade secrets)
- Service availability impact (RTO/RPO breaches)

#### Reproducibility (R)
**Question**: How reliably can this attack be reproduced?

| Score | Reproducibility | Description | Success Rate | Conditions |
|-------|----------------|-------------|--------------|------------|
| 10 | Always | Works every time | 95-100% | No dependencies |
| 8-9 | Very High | Usually successful | 80-94% | Minor timing dependencies |
| 6-7 | High | Often successful | 60-79% | Some environmental factors |
| 4-5 | Moderate | Sometimes works | 40-59% | Multiple dependencies |
| 2-3 | Low | Rarely successful | 20-39% | Complex race conditions |
| 1 | Very Low | Almost never works | 0-19% | Extreme edge cases |

**Consideration Factors**:
- Attack complexity and steps required
- Environmental dependencies (OS, versions, config)
- Timing requirements and race conditions
- Required resources (CPU, memory, network)
- Failure modes and error handling

#### Exploitability (E)
What access level is required?

| Score | Description | Example |
|-------|-------------|---------|
| 0-2 | Admin required | Root access needed |
| 3-5 | Auth user | Valid credentials |
| 6-8 | No auth | Anonymous access |
| 9-10 | Remote | Internet accessible |

#### Affected Users (A)
How many users are impacted?

| Score | Description | Example |
|-------|-------------|---------|
| 0-2 | Individual | Single user |
| 3-5 | Small group | One team |
| 6-8 | Many users | One tenant |
| 9-10 | All users | System-wide |

#### Discoverability (D2)
How easy is it to find this vulnerability?

| Score | Description | Example |
|-------|-------------|---------|
| 0-2 | Very hard | Deep code review |
| 3-5 | Hard | Security scan |
| 6-8 | Easy | Basic testing |
| 9-10 | Obvious | Published CVE |

## Risk Level Mapping

| DREAD Score | Risk Level | Priority | Response Time | Jira Priority |
|-------------|------------|----------|---------------|---------------|
| 8.0-10.0 | Critical | P1 | 24 hours | Blocker |
| 6.0-7.9 | High | P2 | 7 days | Critical |
| 4.0-5.9 | Medium | P3 | 30 days | Major |
| 2.0-3.9 | Low | P4 | 90 days | Minor |
| 0.0-1.9 | Info | P5 | Best effort | Trivial |

## DREAD Calculator {#calculator}

### Example: Token Storm DoS (LLM-2)
```python
def calculate_dread(d, r, e, a, d2):
    """Calculate DREAD score with validation"""
    factors = [d, r, e, a, d2]
    
    # Validate ranges
    for factor in factors:
        if not 0 <= factor <= 10:
            raise ValueError(f"Factor {factor} out of range [0-10]")
    
    return sum(factors) / 5

# Token Storm DoS calculation
d  = 9  # Financial damage, service outage
r  = 8  # Easy to reproduce with known patterns
e  = 7  # Simple prompt crafting required
a  = 6  # Affects all API users
d2 = 9  # Well-documented attack patterns

score = calculate_dread(d, r, e, a, d2)
print(f"DREAD Score: {score:.1f}/10 (High)")
# Output: DREAD Score: 7.8/10 (High)
```

## CVSS 4.0 Mapping

For external compliance, DREAD scores map to CVSS 4.0:

| DREAD | CVSS | Vector Example |
|-------|------|----------------|
| 9.0-10.0 | 9.0-10.0 | CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H |
| 7.0-8.9 | 7.0-8.9 | CVSS:4.0/AV:N/AC:L/AT:P/PR:L/UI:N/VC:H/VI:L/VA:L |
| 4.0-6.9 | 4.0-6.9 | CVSS:4.0/AV:L/AC:H/AT:P/PR:H/UI:R/VC:L/VI:L/VA:L |
| 0.1-3.9 | 0.1-3.9 | CVSS:4.0/AV:L/AC:H/AT:N/PR:H/UI:R/VC:N/VI:N/VA:L |

## Automated Scoring

```yaml
# .github/workflows/dread-validation.yml
name: dread-score-validation
on:
  pull_request:
    paths:
      - 'docs/Security/ThreatModel/**'

jobs:
  validate-scores:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate DREAD scores
        run: |
          python scripts/validate_dread_scores.py \
            --threat-model docs/Security/ThreatModel/ \
            --max-score 10.0 \
            --formula-check true
```

## See Also
- [Risk Matrix](06-risk-matrix.md) - Current threat rankings
- [STRIDE Analysis](03-stride-analysis.md) - Traditional threats
- [Back to Index](README.md)